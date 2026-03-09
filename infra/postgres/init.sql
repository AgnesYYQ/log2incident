CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO products (id, name, price)
VALUES
    ('p1', 'Keyboard', 49.99),
    ('p2', 'Monitor', 199.00),
    ('p3', 'Mouse', 24.50)
ON CONFLICT (id) DO NOTHING;
