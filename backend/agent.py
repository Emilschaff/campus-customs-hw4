from pathlib import Path
import os
import json
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic import BaseModel
from models import AuditEntry, ChatReply, PageContext
from tools import search_products, check_inventory, lookup_product_description, lookup_product_price, lookup_stock_by_size

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parents[1] / ".env")
load_dotenv(ROOT.parent / ".env", override=False)
_agent: Agent | None = None
AUDIT_PATH = ROOT.parent / "output" / "audit_trail.json"

def append_audit(tool_name: str, args: dict[str, str], result: str, stop_reason: str) -> None:
    """Append one bounded, non-sensitive agent-loop record without replacing prior entries."""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if AUDIT_PATH.exists():
        existing = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        if not isinstance(existing, list):
            raise ValueError("audit_trail.json must contain a JSON list; refusing to overwrite it")
    else:
        existing = []
    entry = AuditEntry(tool_name=tool_name, args=args, result=result[:300], stop_reason=stop_reason)
    existing.append(entry.model_dump(mode="json"))
    AUDIT_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")

class ChatDeps(BaseModel):
    user_id: int | None = None
    name: str | None = None
    email: str | None = None
    page_context: PageContext | None = None
    conversation_history: list[dict[str, str]] = []

def get_shopper_context(ctx: RunContext[ChatDeps]) -> str:
    """Return the non-secret identity and current page context available to this chat."""
    shopper = f"{ctx.deps.name} <{ctx.deps.email}>" if ctx.deps.name and ctx.deps.email else "guest shopper"
    page = ctx.deps.page_context.name if ctx.deps.page_context else "no product page"
    return f"Shopper: {shopper}. Current product page: {page}."

def get_agent() -> Agent:
    global _agent
    if _agent is not None:
        return _agent
    api_key = os.getenv("PORTKEY_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set PORTKEY_API_KEY or OPENAI_API_KEY in Projects/.env")
    if os.getenv("PORTKEY_API_KEY"):
        client = AsyncOpenAI(base_url="https://api.portkey.ai/v1", api_key=api_key, default_headers={"x-portkey-api-key": api_key, "x-portkey-provider": "openai"})
    else:
        client = AsyncOpenAI(api_key=api_key)
    model = OpenAIChatModel(os.getenv("CAMPUS_CUSTOMS_MODEL", "gpt-4.1-mini"), provider=OpenAIProvider(openai_client=client))
    _agent = Agent(model, output_type=ChatReply, system_prompt=(ROOT / "prompts" / "prompt.md").read_text(encoding="utf-8"))
    _agent.tool(search_products)
    _agent.tool(check_inventory)
    _agent.tool(lookup_product_description)
    _agent.tool(lookup_product_price)
    _agent.tool(lookup_stock_by_size)
    _agent.tool(get_shopper_context)
    return _agent

async def run_chat(message: str, deps: ChatDeps | None = None) -> ChatReply:
    context = deps or ChatDeps()
    history_note = f"\nRecent conversation:\n{context.conversation_history}" if context.conversation_history else ""
    context_note = f"\nPage context: {context.page_context.model_dump_json()}" if context.page_context else ""
    try:
        result = await get_agent().run(message + history_note + context_note, deps=context)
        reply = result.output
        append_audit("agent_loop", {"message_preview": message[:120], "user_id": str(context.user_id or "guest")}, reply.message, "structured reply returned")
        return reply
    except Exception as exc:
        append_audit("agent_loop", {"message_preview": message[:120], "user_id": str(context.user_id or "guest")}, type(exc).__name__, "agent error")
        raise
