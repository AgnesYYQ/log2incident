import { useEffect, useMemo, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw payload;
  }

  return response.json();
}

function ProductTable({ products, onUpdatePrice, savingProductId }) {
  return (
    <div className="panel">
      <div className="panel-head">
        <h2>Products (Postgres + Redis)</h2>
        <p>Postgres is the source of truth. Redis is synced immediately on price updates.</p>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Price</th>
              <th>Update</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <ProductRow
                key={product.id}
                product={product}
                onUpdatePrice={onUpdatePrice}
                saving={savingProductId === product.id}
              />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ProductRow({ product, onUpdatePrice, saving }) {
  const [price, setPrice] = useState(String(product.price));

  useEffect(() => {
    setPrice(String(product.price));
  }, [product.price]);

  return (
    <tr>
      <td>{product.id}</td>
      <td>{product.name}</td>
      <td>${Number(product.price).toFixed(2)}</td>
      <td>
        <div className="price-cell">
          <input
            type="number"
            min="0"
            step="0.01"
            value={price}
            onChange={(event) => setPrice(event.target.value)}
          />
          <button
            disabled={saving}
            onClick={() => onUpdatePrice(product.id, Number(price))}
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </td>
    </tr>
  );
}

export default function App() {
  const [username, setUsername] = useState('demo');
  const [password, setPassword] = useState('');
  const [usernameError, setUsernameError] = useState('');
  const [loginError, setLoginError] = useState('');
  const [wrongPasswordAttempts, setWrongPasswordAttempts] = useState(0);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [products, setProducts] = useState([]);
  const [productsError, setProductsError] = useState('');
  const [savingProductId, setSavingProductId] = useState('');

  const canSubmit = useMemo(() => username.length > 0 && password.length > 0, [username, password]);

  useEffect(() => {
    if (!username.trim()) {
      setUsernameError('');
      return;
    }

    const timeout = setTimeout(async () => {
      try {
        const result = await apiRequest(`/auth/validate-username?username=${encodeURIComponent(username)}`);
        setUsernameError(result.exists ? '' : result.message);
      } catch {
        setUsernameError('Cannot validate username right now');
      }
    }, 250);

    return () => clearTimeout(timeout);
  }, [username]);

  async function fetchProducts() {
    try {
      const data = await apiRequest('/products');
      setProducts(data);
      setProductsError('');
    } catch (error) {
      const message = error?.detail || 'Unable to load products';
      setProductsError(typeof message === 'string' ? message : 'Unable to load products');
    }
  }

  async function handleLogin(event) {
    event.preventDefault();
    setLoginError('');

    try {
      await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      });
      setIsLoggedIn(true);
      setWrongPasswordAttempts(0);
      setPassword('');
      fetchProducts();
    } catch (error) {
      const detail = error?.detail || {};
      const message = detail.message || 'Login failed';
      setLoginError(message);
      setWrongPasswordAttempts(detail.wrong_password_attempts || 0);
    }
  }

  async function handleUpdatePrice(productId, price) {
    if (!Number.isFinite(price) || price < 0) {
      setProductsError('Price must be a non-negative number');
      return;
    }

    setSavingProductId(productId);
    try {
      const updated = await apiRequest(`/products/${productId}/price`, {
        method: 'PATCH',
        body: JSON.stringify({ price }),
      });

      setProducts((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      setProductsError('');
    } catch (error) {
      const message = error?.detail || 'Unable to update price';
      setProductsError(typeof message === 'string' ? message : 'Unable to update price');
    } finally {
      setSavingProductId('');
    }
  }

  if (!isLoggedIn) {
    return (
      <main className="auth-layout">
        <section className="auth-panel">
          <p className="eyebrow">Log2Incident Commerce Console</p>
          <h1>Sign in to the Product Control Room</h1>
          <form onSubmit={handleLogin}>
            <label>
              Username
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="demo"
                autoComplete="username"
              />
            </label>
            {usernameError && <p className="error-text">{usernameError}</p>}

            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
              />
            </label>
            {loginError && <p className="error-text">{loginError}</p>}
            {wrongPasswordAttempts > 0 && (
              <p className="attempt-text">Wrong password attempts: {wrongPasswordAttempts}</p>
            )}

            <button type="submit" disabled={!canSubmit || !!usernameError}>Sign In</button>
          </form>
          <p className="hint">Try demo/demo123 or admin/admin123</p>
        </section>
      </main>
    );
  }

  return (
    <main className="dashboard-layout">
      <header>
        <h1>Product Pricing Desk</h1>
        <button onClick={() => setIsLoggedIn(false)}>Logout</button>
      </header>

      {productsError && <p className="error-text block">{productsError}</p>}
      <ProductTable
        products={products}
        onUpdatePrice={handleUpdatePrice}
        savingProductId={savingProductId}
      />
    </main>
  );
}
