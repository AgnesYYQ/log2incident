import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, beforeEach, vi } from 'vitest';

import App from './App';

function mockFetchHandler(handler) {
  const fetchMock = vi.fn(async (url, options = {}) => handler(url, options));
  global.fetch = fetchMock;
  return fetchMock;
}

describe('App', () => {
  beforeEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
  });

  it('shows immediate username error for unknown username', async () => {
    const fetchMock = mockFetchHandler((url) => {
      const endpoint = String(url);
      if (endpoint.includes('/auth/validate-username?username=baduser')) {
        return {
          ok: true,
          json: async () => ({ exists: false, message: 'Unknown username' }),
        };
      }
      return {
        ok: true,
        json: async () => ({ exists: true, message: 'Username looks good' }),
      };
    });

    render(<App />);

    const usernameInput = screen.getByLabelText('Username');
    await userEvent.clear(usernameInput);
    await userEvent.type(usernameInput, 'baduser');

    expect(await screen.findByText('Unknown username')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign In' })).toBeDisabled();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled();
    });
  });

  it('shows accumulated wrong password attempts from backend', async () => {
    mockFetchHandler((url, options) => {
      const endpoint = String(url);
      const method = options.method || 'GET';

      if (endpoint.includes('/auth/validate-username')) {
        return {
          ok: true,
          json: async () => ({ exists: true, message: 'Username looks good' }),
        };
      }

      if (endpoint.includes('/auth/login') && method === 'POST') {
        return {
          ok: false,
          json: async () => ({
            detail: {
              message: 'Wrong password. Attempt #2',
              wrong_password_attempts: 2,
            },
          }),
        };
      }

      return {
        ok: false,
        json: async () => ({ detail: 'Unexpected request in test' }),
      };
    });

    render(<App />);

    await userEvent.type(screen.getByLabelText('Password'), 'bad-password');
    await userEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(await screen.findByText('Wrong password. Attempt #2')).toBeInTheDocument();
    expect(screen.getByText('Wrong password attempts: 2')).toBeInTheDocument();
  });

  it('logs in, loads products, and updates product price', async () => {
    const fetchMock = mockFetchHandler((url, options) => {
      const endpoint = String(url);
      const method = options.method || 'GET';

      if (endpoint.includes('/auth/validate-username')) {
        return {
          ok: true,
          json: async () => ({ exists: true, message: 'Username looks good' }),
        };
      }

      if (endpoint.includes('/auth/login') && method === 'POST') {
        return {
          ok: true,
          json: async () => ({ success: true, message: 'Login successful', wrong_password_attempts: 0 }),
        };
      }

      if (endpoint.endsWith('/products') && method === 'GET') {
        return {
          ok: true,
          json: async () => ([
            { id: 'p1', name: 'Keyboard', price: 49.99, updated_at: '2026-03-08T00:00:00Z' },
            { id: 'p2', name: 'Monitor', price: 199.0, updated_at: '2026-03-08T00:00:00Z' },
          ]),
        };
      }

      if (endpoint.includes('/products/p1/price') && method === 'PATCH') {
        return {
          ok: true,
          json: async () => ({ id: 'p1', name: 'Keyboard', price: 59.99, updated_at: '2026-03-08T01:00:00Z' }),
        };
      }

      return {
        ok: false,
        json: async () => ({ detail: 'Unexpected request in test' }),
      };
    });

    render(<App />);

    await userEvent.type(screen.getByLabelText('Password'), 'demo123');
    await userEvent.click(screen.getByRole('button', { name: 'Sign In' }));

    expect(await screen.findByRole('heading', { name: 'Product Pricing Desk' })).toBeInTheDocument();

    const keyboardRow = screen.getByText('Keyboard').closest('tr');
    expect(keyboardRow).not.toBeNull();

    const priceInput = within(keyboardRow).getByRole('spinbutton');
    await userEvent.clear(priceInput);
    await userEvent.type(priceInput, '59.99');
    await userEvent.click(within(keyboardRow).getByRole('button', { name: 'Save' }));

    expect(await screen.findByText('$59.99')).toBeInTheDocument();

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/products/p1/price'),
      expect.objectContaining({ method: 'PATCH' })
    );
  });
});
