from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ProductCard(BaseModel):
    product_id: str
    name: str
    price: float
    image_url: str
    description: str
    garment_type: str

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    user_id: int | None = None
    page_context: "PageContext | None" = None

class PageContext(BaseModel):
    product_id: str
    name: str
    description: str
    price: float
    colors: str = ""

class ChatReply(BaseModel):
    message: str
    products: list[ProductCard] = Field(default_factory=list)
    history: list[dict[str, str]] = Field(default_factory=list)

class ProductLookup(BaseModel):
    product_id: str
    name: str
    description: str
    price: float

class PriceLookup(BaseModel):
    product_id: str
    name: str
    price: float

class StockBySize(BaseModel):
    size: str
    quantity: int
    in_stock: bool

class StockLookup(BaseModel):
    product_id: str
    name: str
    sizes: list[StockBySize]

class AuditEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    tool_name: str
    args: dict[str, str] = Field(default_factory=dict)
    result: str
    stop_reason: str
