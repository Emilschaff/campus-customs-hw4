from pathlib import Path
import sqlite3
from functools import lru_cache
from pydantic_ai import RunContext
from models import ProductCard, PriceLookup, ProductLookup, StockBySize, StockLookup

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "campus_customs.db"

def _rows(query: str, params: tuple = ()) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(query, params).fetchall()]

def _card(row: dict) -> ProductCard:
    return ProductCard(product_id=row["product_id"], name=row["name"], price=row["price"], image_url=f"/images/{Path(row['image_file_path']).name}", description=row["description"], garment_type=row["garment_type"])

@lru_cache(maxsize=128)
def _cached_search(query: str, max_results: int) -> tuple[ProductCard, ...]:
    """Find catalogue products matching a shopper's words, then return concise product cards."""
    raw_terms = [term.lower().strip("?!.,") for term in query.replace(",", " ").split() if len(term) > 2]
    terms = list(dict.fromkeys(raw_terms + [term[:-3] + "ie" if term.endswith("ies") else term[:-1] for term in raw_terms if term.endswith("ies") or term.endswith("s")]))[:8]
    if not terms: return ()
    clauses = " OR ".join(["lower(name || ' ' || garment_type || ' ' || description || ' ' || colors || ' ' || search_tags) LIKE ?"] * len(terms))
    rows = _rows(f"SELECT product_id, name, garment_type, description, image_file_path, price FROM catalogue WHERE {clauses} ORDER BY name LIMIT ?", tuple(f"%{term}%" for term in terms) + (max(1, min(max_results, 8)),))
    return tuple(_card(row) for row in rows)

def search_products(ctx: RunContext[None], query: str, max_results: int = 5) -> list[ProductCard]:
    """Find catalogue products matching a shopper's words, using a bounded cache for repeated searches."""
    return list(_cached_search(query.strip().lower(), max(1, min(max_results, 8))))

def check_inventory(ctx: RunContext[None], product_id: str) -> list[str]:
    """Check sizes and quantities for one catalogue product; never guess stock."""
    rows = _rows("SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY size", (product_id,))
    return [f"{row['size']}: {row['quantity']} available" for row in rows]

def lookup_product_description(ctx: RunContext[None], product_id: str) -> ProductLookup | None:
    """Look up the authoritative product description and price by catalogue product ID."""
    rows = _rows("SELECT product_id, name, description, price FROM catalogue WHERE product_id = ?", (product_id,))
    return ProductLookup(**rows[0]) if rows else None

def lookup_product_price(ctx: RunContext[None], product_id: str) -> PriceLookup | None:
    """Look up the authoritative current price by catalogue product ID; never estimate a price."""
    rows = _rows("SELECT product_id, name, price FROM catalogue WHERE product_id = ?", (product_id,))
    return PriceLookup(**rows[0]) if rows else None

def lookup_stock_by_size(ctx: RunContext[None], product_id: str) -> StockLookup | None:
    """Look up every recorded size and quantity; quantity zero means explicitly out of stock."""
    product_rows = _rows("SELECT product_id, name FROM catalogue WHERE product_id = ?", (product_id,))
    if not product_rows:
        return None
    stock_rows = _rows("SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY size", (product_id,))
    return StockLookup(product_id=product_id, name=product_rows[0]["name"], sizes=[StockBySize(size=row["size"], quantity=row["quantity"], in_stock=row["quantity"] > 0) for row in stock_rows])
