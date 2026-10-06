# Problem 2 — Title not yet provided

We're starting HW 4 now, please save everything in the HW 4 folder. Same as before: create AI\_prompts.md and keep a running log for this session. Every time I send you a prompt, append it exactly as I typed it, under a heading with the problem number and title, with a short note on what you changed or added. Log follow-ups the same way, plus one sentence on what was missing from the first prompt. Start by logging this message under Problem 2, then wait for my next message.

**Change note:** Created `AI_prompts.md` in the HW 4 folder and logged the initial session instructions under Problem 2. The problem title was not included in the prompt.

# Problem 2 — Schema and Field Inventory

Ok we're on Problem 2 now, look at data/campus\_customs.db and understand the fields of each table. At minimum, cover catalogue, inventory, and users. 

Then start output/harness.md. For each table, list its fields and one short line on why each field matters for the shop or the chatbot. I'll keep growing this file in later problems (models, tools, safety, specs), so keep it organized in sections.

Make the technical decisions yourself and finish without stopping to ask me. When you're done, show me the table/field breakdown.

**Change note:** Inspected the SQLite schema and created `output/harness.md` with organized field-by-field rationale for `catalogue`, `inventory`, `users`, and `chat_messages`.

**What was missing from the first prompt:** It did not specify the Problem 2 database/schema task, the required tables, or the destination and contents of `output/harness.md`.

# Problem 3 — React Storefront and FastAPI Product Service

Ok we're on Problem 3 now, scaffold a React + Vite + TypeScript front end. Add a nav bar linking to Home, Products, About Us, Log in, Create account. 

Research yalebulldogblue.com for Campus Customs style and tone, then write the Home and About Us page content in your own words and voice, don't copy the original site text.

Products page: pull from data/campus\_customs.db catalogue table, show product images (paths are in the db), name, price, short description. Clicking a product card opens a single-item page with a large image on one side and full product text on the other (description, price, sizes/stock when available).

Add a floating chat panel in the bottom right. It doesn't need to talk to an agent yet, a stub that will call the backend later is enough for this problem.

Start a simple FastAPI app in backend/main.py just to serve products and images from the database. This will grow into the full agent backend in Problem 5, so structure it in a way that's easy to extend rather than throwaway.

Make the technical decisions yourself and finish without stopping to ask me. When you're done, tell me how to run both the frontend and backend, and flag anything I should double-check.

**Change note:** Researched the public site for its licensed Yale merchandise positioning, upbeat campus-pride tone, Open Sans-style utility typography, and Yale-blue/white palette. Built a React/Vite/TypeScript storefront, FastAPI product/image service, product detail routes, original Home/About copy, and a backend-ready chat stub.

**What was missing from the first prompt:** It did not specify the Problem 3 frontend/backend build, page navigation, product-detail behavior, image serving, or chat-panel requirements.

# Problem 4 — Account Registration and Login

Problem 4 now, build a normal create-account and login flow. Create account needs first name, last name, email, password, and a confirm-password field. Log in needs email and password.
New accounts go into the users table. Store passwords securely, hashed, not plaintext, so a human or an AI reading the database can't recover them.
There's already a seed test user in the db: [test@campuscustoms.yale.edu](mailto:test@campuscustoms.yale.edu) / password. Confirm you can log in as that user, and that creating a brand-new account also works end to end.
Update output/harness.md with how auth works, what gets stored for a user and how passwords are protected.
Make the technical decisions yourself and finish without stopping to ask me. When you're done, tell me how you tested both the existing test user and a newly created one.

**Change note:** Added account registration and login forms, FastAPI auth endpoints, PBKDF2-SHA256 password hashing with per-account random salts, validation, duplicate-email handling, and authentication documentation in `output/harness.md`.

**What was missing from the first prompt:** It did not specify account creation, login, password protection, or the user-table authentication contract.

# Problem 5 — PydanticAI Shop Chatbot

Ok now on to problem 5 build the shop chatbot as a PydanticAI agent behind FastAPI, plugged into the front end's chat widget. Put the API app in backend/main.py, that's what gets run with Uvicorn. Keep the agent as four files next to it, same structure as HW3:

- backend/prompts/prompt.md, system prompt, you'll grow this file in later problems
- backend/agent.py, agent entry and wiring
- backend/tools.py, tools the agent can call
- backend/models.py, Pydantic/PydanticAI structured types

In prompt.md, write Campus Customs voice and safety basics, you'll expand tools and safety further later. Add or update types in models.py for chat replies and product cards as needed.

In main.py, expose a chat route so a message from the website returns a real agent reply, plus whatever else the frontend needs for products and auth. Use my AI model API key, check the .env setup from earlier homeworks for how that's wired.

Update output/harness.md noting how the frontend talks to FastAPI and how the agent is loaded (prompt file plus model).

The backend needs to run from backend/ like this: uvicorn main:app --reload --port 8000

Make the technical decisions yourself and finish without stopping to ask me. When you're done, tell me how to run it and confirm a real chat message gets a real agent response, not a stub.

**Change note:** Added the requested PydanticAI agent structure, Campus Customs prompt and safety rules, catalogue/inventory tools, structured chat models, `/api/chat` route, and a frontend chat widget that sends and renders real responses.

**What was missing from the first prompt:** It did not specify a real model-backed chatbot, the four-file agent structure, prompt/tool/model contracts, or FastAPI chat integration.

# Problem 6 — Database-backed Product and Stock Lookups

For problem 6, give the agent tools that look up real information from campus\_customs.db: product description, price, and how many are in stock by size when the customer asks. The agent must use the database, no inventing prices or quantities, and if a size is out of stock it should say so clearly rather than guessing. 

Expand prompts/prompt.md so the agent knows to call these tools for price and stock questions. Add or update return types in models.py for the lookup results.

In output/harness.md, list each tool and explain which model fields you chose for lookup results and why.

Make the technical decisions yourself and finish without stopping to ask me. When you're done, show me a sample question and answer for each tool (description, price, stock by size, including an out-of-stock case).

**Change note:** Added explicit structured database tools for product descriptions, prices, and size-level stock; strengthened the system prompt against invented values; documented tool return fields and verified live examples, including an out-of-stock size.

**What was missing from the first prompt:** It did not specify authoritative database lookups, structured lookup return types, or explicit out-of-stock behavior.

# Problem 7 — Agent Search Results as Dynamic Product Cards

Problem 7 now, when a customer asks about a type of item in chat, like "what hoodies do you have?", the agent should search the catalogue and the website should dynamically show those matching items as product cards (image, name, price, short info). 

This is an API contract: the agent returns structured product matches, and the front end renders them on the page from that response.

Clicking one of these dynamically-loaded cards needs to open the same single-item detail page you built in Problem 3, large image plus full info, the same as any other product card on the site.

Update prompts/prompt.md and output/harness.md so it's clear how search results get from the agent to the page.

Make the technical decisions yourself and finish without stopping to ask me. When you're done, show me a sample search query, the structured response, and confirm clicking one of the resulting cards opens the correct detail page.

**Change note:** Connected catalogue-search results from the structured agent reply to a page-level dynamic product-card section, reused the existing product detail route, and documented the API-to-UI contract.

**What was missing from the first prompt:** It did not specify that agent search results must be structured, rendered dynamically outside the chat transcript, or linked to the existing detail page.

# Problem 8 — Persistent User Chat History and Page Context

Now for problem 8, when a shopper is logged in, save their chat history to the database in an appropriate table and reload it when they return. Guests can still chat, but history only needs to persist for logged-in users. 

The agent should know who is chatting, name and email, pass that through agent deps or an equivalent clear pattern, and/or tools the agent can call.

Also pass enough page context that if someone is on a product page and asks "do you have this in pink?", the agent knows which item they mean. You can put that page context into the agent's context, it doesn't have to go through a tool call.

Document in output/harness.md: how user chat history is stored, what customer fields the agent sees, and how page context is passed.

Make the technical decisions yourself and finish without stopping to ask me. When you're done, show me a logged-in test where chat history persists after reload, and a product-page test where a vague follow-up question resolves correctly using page context.

**Change note:** Added authenticated chat persistence in `chat_messages`, user and page context dependencies for PydanticAI, history reload, local frontend auth state, and product-page context propagation.

**What was missing from the first prompt:** It did not specify user-scoped chat persistence, customer identity context, or contextual product follow-ups.

# Problem 9 — Campus Customs Usability Improvements

For the next one, choose and implement 2 front-end usability improvements and 2 agent/backend usability improvements for Campus Customs. Front-end means things that make the site look better and easier to use. Agent/backend means things that make the agent's output better, more accurate, safer, faster, or cheaper, new tools or efficiency changes both count.

Use your own judgment on what to add.

Write output/usability.md before or as you build. For each improvement, say what you added and why it helps a Campus Customs shopper or the business.

Make sure all four improvements actually show up and work in the running app, not just described in the write-up.

Finish without stopping to ask me. When you're done, tell me what you chose and how to see each one working.

**Change note:** Added two live storefront improvements—catalogue filtering/sorting and chat quick prompts—and two live backend improvements—conversation-aware agent context and cached catalogue searches. Documented them in `output/usability.md`.

**What was missing from the first prompt:** It did not prescribe particular usability changes; judgment was intentionally left open for selecting four improvements.

# Problem 10 — Collegiate Club Storefront Design

Ok, next add creative design so the site feels like a real Campus Customs storefront, fonts, color, hierarchy, motion, product presentation, chat feel. 

For the color direction, look at yaleclubnyc.org and pull a palette inspired by it, deep navy/Yale blue, cream or ivory, warm gold or brass accents, that traditional collegiate club feel, rather than a generic bright e-commerce look. Yale's official Yale Blue is #00356B if you want an anchor point, but study the actual site for the fuller palette and type treatment.

Go for imaginative, intentional design, not default-template styling. Apply it consistently across pages, product cards, the single-item view, and the chat panel.

Write output/design.md: what you changed and why it should help customers stick around and buy. Keep it concrete and short.

Finish without stopping to ask me. When you're done, tell me what the overall direction was.

**Change note:** Researched Yale Club NYC’s formal club presentation and applied a navy/ivory/brass visual system with editorial typography, layered surfaces, motion, and coordinated product/detail/chat styling. Added `output/design.md`.

**What was missing from the first prompt:** It did not specify a design system, palette source, typography direction, or concrete visual deliverable.

# Problem 11 — Live App Check Screenshots

Now for 11, test the live site and document it in output/app\_check.html, a page I can double-click to open. Take real screenshots while actually testing the running app, don't mock these up.

Cover three checks:

1. Chat checking the inventory level of an item, honest stock/price pulled from the database.
2. Dynamic search-result cards appearing on the page after a category question, like "what hoodies do you have?"
3. One of the usability features you added in Problem 9, your choice which.

For each check, include a heading, the real screenshot, and one or two sentences on what the screenshot proves.

Put the screenshot image files in output/app\_check\_images/ and link them from app\_check.html with relative paths, like app\_check\_images/inventory.png.

Finish without stopping to ask me. When you're done, confirm app\_check.html opens correctly and all three screenshots actually show what they claim to show.

**Change note:** Ran the live Vite frontend and FastAPI backend with Edge, captured genuine inventory-chat, dynamic hoodie-search, and catalogue-filter screenshots, and created the double-clickable `output/app_check.html` report with relative image links.

**What was missing from the first prompt:** It did not specify a live browser test, screenshot filenames, or the HTML report structure.

# Problem 12 — Package and Publish HW 4

Ok last step, put everything in a folder named hw4 and push it to a new public GitHub repository. Don't put my real .env, campus\_customs.db, or product images in the repo. Use a .gitignore for these, and include .env.example with PORTKEY\_API\_KEY and model settings as placeholders only. 

Expected layout:
hw4/
  AI\_prompts.md, requirements.txt, .env.example, .gitignore, README.md
  frontend/ (Vite React TypeScript app)
  backend/ (main.py, agent.py, models.py, tools.py, prompts/prompt.md)
  output/ (harness.md, design.md, usability.md, app\_check.html, app\_check\_images/, audit\_trail.json)

data/ (campus\_customs.db, products/) stays local only, not pushed to git.

README.md should explain how to run the frontend and backend after someone places the data pack locally, assume they're starting fresh.

Before pushing, scan every file for anything that looks like a real API key or secret, and confirm data/, .env, and node\_modules aren't tracked. Tell me if you find anything.

Create the GitHub repo and push, or tell me exactly what to run if you can't do it directly. Confirm the layout matches, confirm .env/db/images aren't in the repo, and give me the repo URL.

**Change note:** Assembled the clean `hw4` package with source, documentation, screenshots, audit trail, README, requirements, placeholder environment file, and ignore rules. Git/GitHub tools are unavailable in this environment, so no remote repository was created or pushed.

**What was missing from the first prompt:** It did not request repository packaging, exclusion of local data/secrets, a fresh-start README, or GitHub publication.
