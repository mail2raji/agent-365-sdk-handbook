"""Phase 0 smoke test — proves the SDK is installed.

Run from the repo root:
    python Phase0_Setup\phase0_smoke.py

Expected output: seven '✅' lines, one for each imported symbol.
If you see ModuleNotFoundError, your virtual environment is not active.

KID-FRIENDLY VERSION:
    This file is a "taste test". Imagine you just bought a brand-new
    Lego box. Before building anything, you open the box and check:
    "Are all the pieces inside?" That's what this file does — it tries
    to grab every important Lego piece from the SDK. If any piece is
    missing, Python yells. If all pieces are there, you see 7 checkmarks.
"""

# ----- Grab Lego pieces from the SDK's main toy box -----
# `microsoft_agents.hosting.core` is the "main box" of agent parts.
# Think of `from X import (A, B, C)` like saying:
#   "From the toy bin, please give me the red brick, the wheel, and the door."
from microsoft_agents.hosting.core import (
    AgentApplication,   # The agent's BRAIN. Hangs all our handlers (rules) on itself.
    TurnContext,        # The CURRENT chat moment. Holds who said what, right now.
    TurnState,          # The agent's MEMORY for this chat (like a sticky note).
    MemoryStorage,      # A SHOEBOX for sticky notes — forgets when the agent restarts.
)

# `hosting.aiohttp` is the "phone line" Lego piece.
# `CloudAdapter` is the phone that answers when Teams or the Emulator calls.
from microsoft_agents.hosting.aiohttp import CloudAdapter

# `Activity` = one MESSAGE going into or out of the agent (like one envelope).
# `ActivityTypes` = the LIST of envelope-types: "message", "typing", etc.
from microsoft_agents.activity import Activity, ActivityTypes


def main() -> None:
    # If we got here, every import above worked — no missing Lego pieces.
    # Now we just print each piece so you can SEE them with your own eyes.
    print("✅ Imports succeeded")
    print(" - AgentApplication:", AgentApplication)   # the brain class
    print(" - TurnContext:     ", TurnContext)        # "this chat moment"
    print(" - TurnState:       ", TurnState)          # "sticky note"
    print(" - MemoryStorage:   ", MemoryStorage)      # "shoebox for notes"
    print(" - CloudAdapter:    ", CloudAdapter)       # "phone line"
    print(" - Activity:        ", Activity)           # "one envelope"
    print(" - ActivityTypes:   ", ActivityTypes)      # "list of envelope kinds"


# `if __name__ == "__main__"` means:
#   "Only run main() if YOU started this file directly with `python phase0_smoke.py`."
# If another file imported us, we sit quietly and do nothing — like a polite guest.
if __name__ == "__main__":
    main()
