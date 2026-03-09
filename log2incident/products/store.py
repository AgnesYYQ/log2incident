import json
from decimal import Decimal
from typing import Any, Dict, List, Optional

import psycopg
from psycopg.rows import dict_row
from redis import Redis
from redis.exceptions import RedisError

from config.config import get_postgres_dsn, get_redis_url


class ProductStore:
    """Postgres is source-of-truth; Redis is a read-through/write-through cache."""

    def __init__(self):
        self.postgres_dsn = get_postgres_dsn()
        self.redis = Redis.from_url(get_redis_url(), decode_responses=True)

    def _cache_key(self, product_id: str) -> str:
        return f"product:{product_id}"

    def _set_cache(self, product: Dict[str, Any]) -> None:
        try:
            self.redis.set(self._cache_key(product["id"]), json.dumps(product), ex=3600)
        except RedisError:
            # Cache outage should not block source-of-truth operations.
            return

    def ensure_schema(self) -> None:
        with psycopg.connect(self.postgres_dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS products (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        price NUMERIC(12, 2) NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                cur.execute("SELECT COUNT(*) AS count FROM products")
                count = cur.fetchone()["count"]
                if count == 0:
                    cur.executemany(
                        "INSERT INTO products (id, name, price) VALUES (%s, %s, %s)",
                        [
                            ("p1", "Keyboard", Decimal("49.99")),
                            ("p2", "Monitor", Decimal("199.00")),
                            ("p3", "Mouse", Decimal("24.50")),
                        ],
                    )
            conn.commit()

    def list_products(self) -> List[Dict[str, Any]]:
        with psycopg.connect(self.postgres_dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, price, updated_at FROM products ORDER BY id"
                )
                rows = cur.fetchall()

        products = [
            {
                "id": row["id"],
                "name": row["name"],
                "price": float(row["price"]),
                "updated_at": row["updated_at"].isoformat(),
            }
            for row in rows
        ]
        for product in products:
            self._set_cache(product)
        return products

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        try:
            cached = self.redis.get(self._cache_key(product_id))
            if cached:
                return json.loads(cached)
        except RedisError:
            pass

        with psycopg.connect(self.postgres_dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, price, updated_at FROM products WHERE id = %s",
                    (product_id,),
                )
                row = cur.fetchone()

        if not row:
            return None

        product = {
            "id": row["id"],
            "name": row["name"],
            "price": float(row["price"]),
            "updated_at": row["updated_at"].isoformat(),
        }
        self._set_cache(product)
        return product

    def update_price(self, product_id: str, new_price: float) -> Optional[Dict[str, Any]]:
        with psycopg.connect(self.postgres_dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE products
                    SET price = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING id, name, price, updated_at
                    """,
                    (Decimal(str(new_price)), product_id),
                )
                row = cur.fetchone()
            conn.commit()

        if not row:
            return None

        product = {
            "id": row["id"],
            "name": row["name"],
            "price": float(row["price"]),
            "updated_at": row["updated_at"].isoformat(),
        }
        # Immediate write-through cache sync after Postgres update.
        self._set_cache(product)
        return product
