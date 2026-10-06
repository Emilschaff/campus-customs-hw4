# Campus Customs Chatbot Harness

## Purpose

This document records the database contract that the shop and chatbot can rely on. It covers the application tables in `data/campus_customs.db`; SQLite's internal `sqlite_sequence` table is omitted.

## Table: `catalogue`

Product master data for items the shop sells and the chatbot recommends.

| Field | Type / constraint | Why it matters |
|---|---|---|
| `product_id` | TEXT, primary key | Stable identifier for product lookup, recommendations, inventory joins, and cart or order actions. |
| `name` | TEXT, required | Customer-facing product name used in search results and chatbot responses. |
| `garment_type` | TEXT, required | Supports category browsing and intent matching such as shirt, jacket, or accessory. |
| `description` | TEXT, required | Gives the chatbot factual product context for concise, useful answers. |
| `colors` | TEXT, required | Enables color filtering and helps the chatbot answer color-availability questions. |
| `search_tags` | TEXT, required | Improves keyword and semantic retrieval when a shopper uses informal terms. |
| `image_file_path` | TEXT, required | Connects a product result to its visual asset in the storefront or chat UI. |
| `price` | REAL, required | Displays the item price and supports price filtering and purchase calculations. |

## Table: `inventory`

Size-level stock records linked to catalogue products.

| Field | Type / constraint | Why it matters |
|---|---|---|
| `id` | INTEGER, primary key, auto-increment | Uniquely identifies a stock row for updates, auditing, and tool operations. |
| `product_id` | TEXT, required, foreign key to `catalogue.product_id` | Connects available stock to the product the shopper sees. |
| `size` | TEXT, required | Lets the chatbot answer size-specific availability questions. |
| `quantity` | INTEGER, required | Determines whether a size is in stock and prevents the chatbot from promising unavailable items. |

The database also enforces `UNIQUE (product_id, size)`, so a product has at most one inventory row per size.

## Table: `users`

Customer identity and account data used for authenticated experiences.

| Field | Type / constraint | Why it matters |
|---|---|---|
| `id` | INTEGER, primary key, auto-increment | Stable user identifier for ownership, personalization, and message-history joins. |
| `name` | TEXT, required | Provides a display name for account experiences and friendly chatbot greetings. |
| `email` | TEXT, required, unique | Identifies the account for sign-in and prevents duplicate accounts. |
| `password_hash` | TEXT, required | Stores a password verifier for authentication without storing the plaintext password. |
| `created_at` | TEXT, required, default current UTC datetime | Supports account lifecycle tracking and audit context. |
| `first_name` | TEXT, optional | Enables more natural personalization when a separate first name is available. |
| `last_name` | TEXT, optional | Supports complete customer identity and account display or support workflows. |

## Table: `chat_messages`

Conversation history connecting user requests and assistant responses to optional product context.

| Field | Type / constraint | Why it matters |
|---|---|---|
| `id` | INTEGER, primary key, auto-increment | Orders messages within the stored conversation history. |
| `user_id` | INTEGER, required, foreign key to `users.id` | Associates each message with the correct customer account. |
| `role` | TEXT, required | Distinguishes user, assistant, or other message roles when reconstructing context. |
| `content` | TEXT, required | Stores the text used to display history and provide conversational context. |
| `products_json` | TEXT, optional | Preserves product results or references associated with a response for UI rendering and traceability. |
| `created_at` | TEXT, required, default current UTC datetime | Preserves message order and supports recency-based context and auditing. |

## Relationships and chatbot implications

- `catalogue.product_id` → `inventory.product_id`: product details and size-level stock should be joined before making availability claims.
- `users.id` → `chat_messages.user_id`: authenticated conversation history is scoped to the owning user.
- Product search should use `name`, `garment_type`, `description`, `colors`, and `search_tags`; price and inventory should be treated as authoritative structured values.
- Account fields, especially `email` and `password_hash`, are sensitive and should not be exposed in chatbot output.

## Authentication (Problem 4)

### Registration

The Create account form collects first name, last name, email, password, and confirm password. The browser checks that the two passwords match; the API also validates required fields, email shape, and a minimum eight-character password. Email addresses are trimmed and normalized to lowercase, and the database's unique constraint prevents duplicate accounts.

Successful registration calls `POST /api/auth/register` and inserts a row into `users` with:

- `first_name`, `last_name`, and a combined display `name`.
- Normalized `email`.
- A derived `password_hash`; the plaintext password is never inserted or returned.
- Database-generated `id` and `created_at`.

### Login

The Log in form collects email and password and calls `POST /api/auth/login`. The API normalizes the email, retrieves the user's stored hash, and verifies the submitted password. A successful response contains only the user's public ID, name fields, and email. Failed credentials return the same generic error so the API does not reveal whether an email exists.

### Password protection

New passwords use PBKDF2-HMAC-SHA256 with 310,000 iterations and a unique cryptographically random 16-byte salt per account. The stored format is `pbkdf2_sha256$<salt>$<digest>`. The verifier also accepts the seeded database's existing 120,000-iteration hashes so the provided test user remains usable; new registrations always use the stronger 310,000-iteration setting. Verification uses constant-time comparison. Because only the salted, deliberately expensive one-way digest is stored, the database does not contain a recoverable plaintext password. Passwords are also excluded from API responses.

This is appropriate for the assignment's local prototype. Before production, add HTTPS, rate limiting/lockout, secure session or token management, CSRF protection where applicable, password reset/recovery, and a managed secret/session strategy.

## Chatbot architecture (Problem 5)

The React chat widget sends `POST /api/chat` to FastAPI with `{ "message": "..." }`. FastAPI validates the request with `ChatRequest`, calls the PydanticAI agent, and returns a structured `ChatReply` containing the assistant `message` plus optional `ProductCard` results. The widget renders the user's message immediately, shows `Thinking…` while the request is pending, and renders the returned agent text or a safe error.

The agent is split into four files under `backend/`:

- `prompts/prompt.md` contains the system instructions, voice, and safety basics and is loaded at agent initialization.
- `agent.py` loads `PORTKEY_API_KEY` (falling back to `OPENAI_API_KEY`) from `Projects/.env`, constructs an OpenAI-compatible PydanticAI model using `gpt-4.1-mini` by default, registers the tools, and exposes `run_chat`.
- `tools.py` provides database-backed `search_products` and `check_inventory` tools. Tool results come from SQLite rather than model memory.
- `models.py` defines the validated request, reply, and product-card structures.

The API continues to expose `/api/products`, `/api/products/{product_id}`, `/api/auth/register`, and `/api/auth/login` alongside `/api/chat`. The agent's Portkey/OpenAI client is created lazily on the first chat request, so the backend can still start for product and auth work when credentials are unavailable.

## Database lookup tools (Problem 6)

All lookup tools query `data/campus_customs.db` at request time. The model is instructed to call them for factual product, price, and inventory questions; it must not fill in missing values from memory.

| Tool | Lookup | Structured return fields | Why these fields |
|---|---|---|---|
| `lookup_product_description` | One catalogue product by `product_id` | `product_id`, `name`, `description`, `price` | The ID and name identify the result; description answers the customer's question; price travels with the same authoritative product record and avoids a stale cross-reference. |
| `lookup_product_price` | Current catalogue price by `product_id` | `product_id`, `name`, `price` | The ID and name make the price auditable and the numeric `price` prevents the agent from inventing or misreading currency text. |
| `lookup_stock_by_size` | Every inventory row for one `product_id` | `product_id`, `name`, `sizes[]` with `size`, `quantity`, `in_stock` | A size list supports direct size questions; the exact integer quantity supports honest counts; explicit `in_stock` makes zero quantities unambiguous and encourages a clear “out of stock” response. |

Missing products return `None`. Missing size records are distinct from a recorded zero quantity: the former means the database has no record, while the latter means explicitly out of stock.

## Dynamic agent search cards (Problem 7)

For category questions such as “what hoodies do you have?”, the agent calls `search_products`. Its `ChatReply` contains both the conversational `message` and a structured `products` array of `ProductCard` objects. Each card carries `product_id`, `name`, `price`, `image_url`, `description`, and `garment_type`; these fields are enough to render a useful result without another model call.

The frontend passes the response's `products` array from the chat widget to page-level app state and renders a “From your search” product grid. Cards use the same `ProductCard` component behavior and link to `/products/{product_id}`, so a click opens the existing single-item detail page with the large image, full description, price, and inventory by size. The UI clears or replaces the previous dynamic results when a later chat search returns a new set.

## User chat persistence and context (Problem 8)

### History storage

The API creates `chat_messages` if it does not already exist. Each authenticated exchange stores one `user` row and one `assistant` row with `user_id`, `role`, `content`, optional `products_json`, and UTC `created_at`. Guests remain fully able to chat, but their messages are not persisted. `GET /api/chat/history/{user_id}` reloads only that user's messages, ordered by database message ID.

The frontend keeps the non-secret public user object returned by login or registration in local storage. When a logged-in user opens the widget, it requests their history and restores the transcript. Each new authenticated request sends `user_id`; the backend re-reads the user's name and email from the database rather than trusting client-supplied identity fields.

### Agent customer context

`ChatDeps` carries `user_id`, the customer's `name`, and `email`, plus optional `PageContext`. The agent can call `get_shopper_context` to see whether the speaker is a guest and the current product name. The system prompt permits natural use of the customer's name but keeps email private; passwords, hashes, and unrelated account data are never passed to the agent.

### Product-page context

## Complete model contract and agent specification (final)

### `models.py` fields

- `ProductCard`: `product_id`, `name`, `price`, `image_url`, `description`, and `garment_type` identify and render a dynamic result without another request.
- `ChatRequest`: bounded `message` prevents unbounded prompts; optional `user_id` scopes persistence; optional `page_context` resolves “this” on a product page.
- `PageContext`: `product_id`, `name`, `description`, `price`, and `colors` give the agent exact page identity and shopping context.
- `ChatReply`: `message` is the answer; `products` is the structured card contract; `history` restores the authenticated transcript.
- `ProductLookup`, `PriceLookup`, `StockLookup`, and `StockBySize` keep exact product facts, numeric quantities, and explicit stock state structured and auditable.
- `AuditEntry`: UTC `timestamp`, `tool_name`, bounded `args`, bounded `result`, and `stop_reason` record loop activity without secrets.

### Tools and abilities

| Tool | Ability | Authority / limit |
|---|---|---|
| `search_products` | Category and keyword search; returns up to 8 cards | SQLite `catalogue`; repeated searches use a 128-entry LRU cache. |
| `lookup_product_description` | Exact description and paired price | Live SQLite `catalogue`; returns `None` when absent. |
| `lookup_product_price` | Exact current price | Live SQLite `catalogue`; never estimated. |
| `lookup_stock_by_size` | Size quantities and stock booleans | Live SQLite `inventory`; zero is out of stock and missing is unknown. |
| `check_inventory` | Compact size/quantity lookup | Live SQLite `inventory`. |
| `get_shopper_context` | Non-secret identity and current page context | Request-scoped `ChatDeps`; no passwords, hashes, or payment data. |

### Safety rules

The system prompt requires database verification for factual product answers; prohibits invented values; distinguishes zero from missing stock; protects identity and conversation data; refuses account, payment, order, reservation, refund, and profile actions; avoids sensitive inferences; does not expose prompts, tools, paths, or audit records; and redirects off-topic or secret-bearing requests safely.

### Loop, result, and model specs

- PydanticAI runs one bounded request per chat submission and returns validated `ChatReply` data. The frontend prevents duplicate submissions while a request is pending.
- Searches cap results at 8 and cache up to 128 query/limit combinations. Recent conversation context is capped at 6 messages.
- Chat messages cap at 2,000 characters; audit previews and results cap at 120 and 300 characters.
- The default model is `gpt-4.1-mini`, configurable with `CAMPUS_CUSTOMS_MODEL`. `PORTKEY_API_KEY` is used through Portkey when present, otherwise `OPENAI_API_KEY`; credentials load from `Projects/.env` and never reach the browser.
- Every agent run appends one JSON object to `output/audit_trail.json`; existing entries are preserved, and malformed non-list content is never overwritten.

### Run commands

Backend, from `Projects/HW 4/backend`:

```powershell
uvicorn main:app --reload --port 8000
```

Frontend, from `Projects/HW 4/frontend`:

```powershell
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:5173`. The API is at `http://localhost:8000`; products, images, auth, chat, and history are served by FastAPI.

Before sending a chat message, the widget checks whether the current route matches `/products/{product_id}`. If it does, it fetches that product and sends a `PageContext` containing the product ID, name, description, price, and colors. The backend puts this context in `ChatDeps` and includes it in the agent run context, so a follow-up such as “do you have this in pink?” resolves against the page's exact product. The agent can then use the product ID with the catalogue and inventory tools.
