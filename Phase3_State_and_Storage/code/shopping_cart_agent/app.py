"""Shopping-Cart Agent — Phase 3 example.
Demonstrates conversation-scoped and user-scoped state.

KID-FRIENDLY VERSION:
    Imagine two sticky notes for each kid in a store:
      1. CART note — what's in the basket RIGHT NOW (conversation-scoped).
         If the kid leaves and comes back to a new chat, the cart is empty.
      2. LANGUAGE note — sticks to the kid forever (user-scoped).
         No matter which chat they open, they're still greeted in the
         language they picked once.
    Both notes live on the brain (AGENT_APP) under `state.conversation`
    and `state.user`.
"""
# Allow new-style type hints on older Pythons.
from __future__ import annotations

# `re` = regex toy (search text for patterns). We use it to parse commands
# like "add bread" or "lang de".
import re
# Diary so we can debug what the agent did.
import logging

from microsoft_agents.hosting.core import (
    AgentApplication,   # the BRAIN
    MemoryStorage,      # SHOEBOX of notes — erased on restart
    TurnContext,        # "this chat moment"
    TurnState,          # ALL the sticky notes for this chat
)
from start_server import start_server   # phone line + lemonade stand

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("cart")

# The agent brain. MemoryStorage = whiteboard that's erased on restart.
AGENT_APP = AgentApplication(storage=MemoryStorage())

# Look-up table: language code → greeting word.
GREETINGS = {"en": "Hello!", "de": "Hallo!", "fr": "Bonjour!"}


# -- Helpers --
# These four little helpers read/write the sticky notes. We wrap them in
# functions so the rest of the file stays clean. Example:
#   `state.conversation["cart"]` is a dict — `.get("cart", [])` means
#   "give me the cart list, or an empty list if there isn't one yet".

def get_cart(state: TurnState) -> list[str]:
    # CONVERSATION scope = this chat only. Different chat → different cart.
    return state.conversation.get("cart", [])


def set_cart(state: TurnState, cart: list[str]) -> None:
    state.conversation["cart"] = cart


def get_lang(state: TurnState) -> str:
    # USER scope = follows the person across all chats.
    return state.user.get("lang", "en")


def set_lang(state: TurnState, lang: str) -> None:
    state.user["lang"] = lang


# -- Welcome --
# Run this whenever a new person joins the chat.
@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:   # skip the bot itself
            await context.send_activity(
                "🛒 Cart Agent ready. Commands:\n"
                "- `add <item>` / `remove <item>`\n"
                "- `cart` / `clear` / `total`\n"
                "- `lang en|de|fr` (per-user preference)\n"
                "- `hi` (greeted in your language)"
            )


# -- Add: "add apple" --
# `^add\s+(.+)$` means: start with "add", then one+ spaces, then capture
# EVERYTHING else as group(1). So "add big red apple" → group(1) = "big red apple".
ADD_RE = re.compile(r"^add\s+(.+)$", re.IGNORECASE)


@AGENT_APP.message(ADD_RE)
async def add_item(context: TurnContext, state: TurnState):
    # `.match(...).group(1)` grabs the bit inside the parentheses above.
    item = ADD_RE.match(context.activity.text).group(1).strip()
    cart = get_cart(state)                  # read current cart from sticky note
    cart.append(item)                       # add the new item
    set_cart(state, cart)                   # write back to sticky note
    await context.send_activity(f"✅ Added *{item}*. Cart now has {len(cart)} item(s).")


# -- Remove: "remove banana" --
# Same idea as ADD_RE but for removing.
REMOVE_RE = re.compile(r"^remove\s+(.+)$", re.IGNORECASE)


@AGENT_APP.message(REMOVE_RE)
async def remove_item(context: TurnContext, state: TurnState):
    item = REMOVE_RE.match(context.activity.text).group(1).strip()
    cart = get_cart(state)
    if item in cart:
        cart.remove(item)               # take it out of the list
        set_cart(state, cart)           # save the smaller list back
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
# Only accept en/de/fr (the bit inside parentheses is the allowed list).
LANG_RE = re.compile(r"^lang\s+(en|de|fr)$", re.IGNORECASE)


@AGENT_APP.message(LANG_RE)
async def set_language(context: TurnContext, state: TurnState):
    lang = LANG_RE.match(context.activity.text).group(1).lower()
    set_lang(state, lang)               # saved to USER scope → sticks across chats
    await context.send_activity(f"Language saved to **{lang}** for your profile.")


# -- Greet in chosen language --
# Any of these three plain words → say hi in the user's saved language.
@AGENT_APP.message(["hi", "hello", "hey"])
async def greet(context: TurnContext, state: TurnState):
    lang = get_lang(state)
    # `.get(key, default)` = lookup; fall back to English if lang is weird.
    await context.send_activity(GREETINGS.get(lang, GREETINGS["en"]))


# -- Catch-all --
# Any message we didn't recognise → show a hint. Must be registered LAST.
@AGENT_APP.activity("message")
async def default(context: TurnContext, _state: TurnState):
    await context.send_activity(
        "Try: `add bread`, `cart`, `clear`, `total`, `lang de`, `hi`."
    )


if __name__ == "__main__":
    start_server(AGENT_APP, None)
