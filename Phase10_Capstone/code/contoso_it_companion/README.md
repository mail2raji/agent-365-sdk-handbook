# Contoso IT Companion — Capstone Starter

This is the **scaffold** for your Phase 10 capstone. Files marked `TODO` are
intentionally left for you to complete using everything from Phases 1-9.

## Files in the scaffold

| File | What goes here |
|---|---|
| [`start_server.py`](start_server.py) | aiohttp launcher (provided). |
| [`app.py`](app.py) | Handlers — wire up commands. |
| [`llm.py`](llm.py) | Azure OpenAI chat-with-tools loop (Phase 5 + 6). |
| [`rag.py`](rag.py) | In-memory vector store (Phase 6). |
| [`tools.py`](tools.py) | `lookup_policy`, `create_ticket`, `get_my_profile`. |
| [`cards/ticket_form.py`](cards/ticket_form.py) | Adaptive Card form (Phase 4). |
| [`cards/ticket_confirm.py`](cards/ticket_confirm.py) | Adaptive Card confirmation. |
| [`docs/`](docs/) | Markdown policy docs the RAG index uses. |
| [`.env.example`](.env.example) | Template for the secrets you'll need. |

## Run

```powershell
Copy-Item .env.example .env       # fill in your keys
python app.py
```

Then open the Emulator at `http://localhost:3978/api/messages`.

## Suggested order

1. Get the scaffold running (it already replies).
2. Implement TODOs in `tools.py`.
3. Implement TODOs in `cards/`.
4. Wire those into `app.py` handlers.
5. Add Blob storage.
6. Add MSAL auth.
7. Add OTel.
8. Write tests in `tests/`.
9. Containerize + deploy with `azd`.

Good luck 🚀
