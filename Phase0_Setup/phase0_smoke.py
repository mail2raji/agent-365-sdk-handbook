"""Phase 0 smoke test — proves the SDK is installed.

Run from the repo root:
    python Phase0_Setup\phase0_smoke.py

Expected output: seven '✅' lines, one for each imported symbol.
If you see ModuleNotFoundError, your virtual environment is not active.
"""

from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
    TurnState,
    MemoryStorage,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.activity import Activity, ActivityTypes


def main() -> None:
    print("✅ Imports succeeded")
    print(" - AgentApplication:", AgentApplication)
    print(" - TurnContext:     ", TurnContext)
    print(" - TurnState:       ", TurnState)
    print(" - MemoryStorage:   ", MemoryStorage)
    print(" - CloudAdapter:    ", CloudAdapter)
    print(" - Activity:        ", Activity)
    print(" - ActivityTypes:   ", ActivityTypes)


if __name__ == "__main__":
    main()
