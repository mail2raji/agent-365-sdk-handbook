"""Shopping-Cart Agent — Phase 3 example.
Demonstrates conversation-scoped and user-scoped state.
"""
from __future__ import annotations

import re
import logging

from microsoft_agents.hosting.core import (
    AgentApplication,
    MemoryStorage,
    TurnContext,
    TurnState,
)
from start_server import start_server

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cart")

AGENT_APP = AgentApplication(storage=MemoryStorage())

GREETINGS = {"en": "Hello!", "de": "Hallo!", "fr": "Bonjour!"}


# -- Helpers --
def get_cart(state: TurnState) -> list[str]:
    return state.conversation.get("cart", [])


def set_cart(state: TurnState, cart: list[str]) -> None:
    state.conversation["cart"] = cart


def get_lang(state: TurnState) -> str:
    return state.user.get("lang", "en")


def set_lang(state: TurnState, lang: str) -> None:
    state.user["lang"] = lang


# -- Welcome --
@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            await context.send_activity(
                "🛒 Cart Agent ready. Commands:\n"
                "- `add <item>` / `remove <item>`\n"
                "- `cart` / `clear` / `total`\n"
                "- `lang en|de|fr` (per-user preference)\n"
                "- `hi` (greeted in your language)"
            )


# -- Add: "add apple" --
ADD_RE = re.compile(r"^add\s+(.+)$", re.IGNORECASE)


@AGENT_APP.message(ADD_RE)
async def add_item(context: TurnContext, state: TurnState):
    item = ADD_RE.match(context.activity.text).group(1).strip()
    cart = get_cart(state)
    cart.append(item)
    set_cart(state, cart)
    await context.send_activity(f"✅ Added *{item}*. Cart now has {len(cart)} item(s).")


# -- Remove: "remove banana" --
REMOVE_RE = re.compile(r"^remove\s+(.+)$", re.IGNORECASE)


@AGENT_APP.message(REMOVE_RE)
async def remove_item(context: TurnContext, state: TurnState):
    item = REMOVE_RE.match(context.activity.text).group(1).strip()
    cart = get_cart(state)
    if item in cart:
        cart.remove(item)
        set_cart(state, cart)
        await context.send_activity(f"🗑️ Removed *{item}*.")
    else:
        await context.send_activity(f"🤔 *{item}* is not in your cart.")


# -- Cart --
@AGENT_APP.message("cart")
async def show_cart(context: TurnContext, state: TurnState):
    cart = get_cart(state)
    if not cart:
        await context.send_activity("Your cart is empty.")
    else:
        bullets = "\n".join(f"- {x}" for x in cart)
        await context.send_activity(f"🛒 Your cart:\n{bullets}")


# -- Clear --
@AGENT_APP.message("clear")
async def clear_cart(context: TurnContext, state: TurnState):
    set_cart(state, [])
    await context.send_activity("🧹 Cart cleared.")


# -- Total --
@AGENT_APP.message("total")
async def total(context: TurnContext, state: TurnState):
    n = len(get_cart(state))
    await context.send_activity(f"💰 Total: ${n}.00 ({n} item(s) × $1)")


# -- Set language (USER scope) --
LANG_RE = re.compile(r"^lang\s+(en|de|fr)$", re.IGNORECASE)


@AGENT_APP.message(LANG_RE)
async def set_language(context: TurnContext, state: TurnState):
    lang = LANG_RE.match(context.activity.text).group(1).lower()
    set_lang(state, lang)
    await context.send_activity(f"Language saved to **{lang}** for your profile.")


# -- Greet in chosen language --
@AGENT_APP.message(["hi", "hello", "hey"])
async def greet(context: TurnContext, state: TurnState):
    lang = get_lang(state)
    await context.send_activity(GREETINGS.get(lang, GREETINGS["en"]))


# -- Catch-all --
@AGENT_APP.activity("message")
async def default(context: TurnContext, _state: TurnState):
    await context.send_activity(
        "Try: `add bread`, `cart`, `clear`, `total`, `lang de`, `hi`."
    )


if __name__ == "__main__":
    start_server(AGENT_APP, None)
