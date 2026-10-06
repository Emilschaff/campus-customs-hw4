from pathlib import Path
import sqlite3
import hashlib
import hmac
import secrets
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from agent import run_chat
from models import ChatReply, ChatRequest, PageContext
from agent import ChatDeps

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "campus_customs.db"
PRODUCTS_DIR = ROOT / "data" / "products"

app = FastAPI(title="Campus Customs API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/images", StaticFiles(directory=PRODUCTS_DIR), name="images")

with sqlite3.connect(DB_PATH) as conn:
    conn.execute("CREATE TABLE IF NOT EXISTS chat_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, products_json TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')), FOREIGN KEY (user_id) REFERENCES users(id))")

def fetch(query: str, params: tuple = ()):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute(query, params).fetchall()]

def product(row: dict) -> dict:
    row["image_url"] = f"/images/{Path(row.pop('image_file_path')).name}"
    return row

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"

def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, salt, expected = stored.split("$", 2)
        if algorithm != "pbkdf2_sha256": return False
        for iterations in (310_000, 120_000):
            actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
            if hmac.compare_digest(actual, expected): return True
        return False
    except ValueError: return False

class AccountRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=200)

class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/auth/register", status_code=201)
def register(request: AccountRequest):
    email = request.email.strip().lower()
    if "@" not in email: raise HTTPException(status_code=422, detail="Enter a valid email address")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)", (f"{request.first_name.strip()} {request.last_name.strip()}", email, hash_password(request.password), request.first_name.strip(), request.last_name.strip()))
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError: raise HTTPException(status_code=409, detail="An account with that email already exists")
    return {"user": {"id": user_id, "first_name": request.first_name.strip(), "last_name": request.last_name.strip(), "email": email}}

@app.post("/api/auth/login")
def login(request: LoginRequest):
    rows = fetch("SELECT id, first_name, last_name, email, password_hash FROM users WHERE email = ?", (request.email.strip().lower(),))
    if not rows or not verify_password(request.password, rows[0]["password_hash"]): raise HTTPException(status_code=401, detail="Email or password is incorrect")
    row = rows[0]
    return {"user": {"id": row["id"], "first_name": row["first_name"], "last_name": row["last_name"], "email": row["email"]}}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/chat", response_model=ChatReply)
async def chat(request: ChatRequest):
    try:
        user = None
        if request.user_id is not None:
            rows = fetch("SELECT id, first_name, last_name, email FROM users WHERE id = ?", (request.user_id,))
            if rows: user = rows[0]
        deps = ChatDeps(user_id=user["id"] if user else None, name=f"{user['first_name']} {user['last_name']}" if user else None, email=user["email"] if user else None, page_context=request.page_context)
        history = fetch("SELECT role, content FROM chat_messages WHERE user_id = ? ORDER BY id", (user["id"],)) if user else []
        deps.conversation_history = history[-6:]
        reply = await run_chat(request.message, deps)
        if user:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'user', ?, NULL)", (user["id"], request.message))
                conn.execute("INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)", (user["id"], reply.message, reply.model_dump_json()))
        reply.history = history + [{"role": "user", "content": request.message}, {"role": "assistant", "content": reply.message}] if user else []
        return reply
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"The shopping assistant is temporarily unavailable ({type(exc).__name__}).") from exc

@app.get("/api/chat/history/{user_id}")
def chat_history(user_id: int):
    return {"messages": fetch("SELECT role, content, created_at FROM chat_messages WHERE user_id = ? ORDER BY id", (user_id,))}

@app.get("/api/products")
def products():
    return [product(row) for row in fetch("SELECT product_id, name, garment_type, description, colors, search_tags, image_file_path, price FROM catalogue ORDER BY name")]

@app.get("/api/products/{product_id}")
def product_detail(product_id: str):
    rows = fetch("SELECT product_id, name, garment_type, description, colors, search_tags, image_file_path, price FROM catalogue WHERE product_id = ?", (product_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Product not found")
    item = product(rows[0])
    item["inventory"] = fetch("SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY size", (product_id,))
    return item
