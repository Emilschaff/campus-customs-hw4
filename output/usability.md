# Campus Customs Usability Improvements

## Front end 1: catalogue filters and sorting

Added a search box, garment-type filter, and sort control to the Products page. Matching happens immediately in the browser after the catalogue loads, so shoppers can narrow 102 products without extra API calls. Sorting by featured order, name, or price makes browsing practical for both gift shoppers and budget-conscious students.

## Front end 2: chat quick prompts

Added visible starter prompts inside the chat panel: “Show me hoodies”, “What’s under $50?”, and “Check a size”. Clicking one submits it immediately. This makes the agent discoverable for first-time shoppers and demonstrates the main supported shopping tasks without requiring users to invent a prompt.

## Agent/backend 1: conversation-aware agent context

The backend now passes the most recent saved user/assistant turns into `ChatDeps` and the agent run. The model can resolve follow-ups such as “show me the cheaper one” against the current conversation, while limiting the context to the latest six messages to control latency and token cost. Guests still receive normal single-turn chat.

## Agent/backend 2: cached catalogue search

Catalogue search now uses a bounded in-process LRU cache keyed by the query and result limit. Repeated questions during a chat session reuse the same database result instead of repeating an identical SQLite scan. Product and inventory lookups remain live and uncached, so price and stock answers continue to reflect current database values.

## How to verify

Run the backend and frontend using the existing HW 4 instructions. Visit Products to use the controls, open the chat panel to use quick prompts, ask a follow-up that refers to an earlier recommendation, and repeat a category search to exercise the cached search path.
