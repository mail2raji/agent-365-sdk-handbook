# 🧪 Phase 7 — Hands-On Lab: Take Your Agent Into Teams (with SSO)

> A step-by-step lab. By the end your agent will live inside Microsoft Teams, sign you in with your real corporate account, and read your mailbox folders from Microsoft Graph.

---

## 🎯 What you'll build today

A **Profile Agent** that:

1. Runs locally and is reachable from the internet through a dev tunnel.
2. Is registered as an **Azure Bot** so Teams can talk to it.
3. Is side-loaded into Teams as an app you can chat with.
4. Prompts you to **sign in with your Microsoft account** via an OAuth card.
5. Calls **Microsoft Graph** to fetch your display name and mailbox folders.

You'll also learn:

- The difference between **agent identity** (who the bot is) and **user identity** (who you are).
- How to detect which **channel** you're on (`msteams`, `webchat`, `emulator`).
- The minimum Teams manifest needed to side-load.

> 👶 Today is more about **clicking around in the Azure portal and Teams admin centre** than writing Python. Take it slow — and check off each step before moving on.

⏱️ **About 120 minutes** (most of it portal clicking, not coding).

---

## ✅ Before you start

- [ ] Phase 6 finished — you understand tool calling.
- [ ] You have **admin access** to an Entra (Azure AD) tenant — OR an admin who can do the app registration for you.
- [ ] You have a **Microsoft 365** tenant where you can side-load custom Teams apps. (Free dev tenants from <https://developer.microsoft.com/microsoft-365/dev-program> work.)
- [ ] You have **Teams desktop or Teams web** open and signed in.
- [ ] Terminal prompt starts with **`(.venv)`**.

> 💡 If you don't have an Entra/Teams tenant today, you can still do **Lab 1** (dev tunnel) and **Lab 5** (channel-aware logic) — skip 2–4 for now.

---

## 🗺️ Today's roadmap

```
Lab 1 → Open a public dev tunnel (HTTPS) to your local agent
Lab 2 → Register the Bot in Azure (Bot Service)
Lab 3 → Register an Entra app for user SSO + configure OAuth in the Bot
Lab 4 → Build & side-load the Teams app manifest
Lab 5 → Code: login / logout / me / folders with channel-aware logic
```

---

## Lab 1 — Open a dev tunnel (~15 min)

**You will:** make your `localhost:3978` reachable from the internet over HTTPS.

> Teams/Azure Bot Service must reach your agent over **HTTPS on a public URL**. Two free options below.

### Option A — VS Code dev tunnels

```powershell
# In any terminal (does NOT need the venv)
code tunnel
```

Follow the device-code login (it opens a browser). After a minute you'll see something like:

```text
Open this link in your browser https://YOUR-TUNNEL-NAME.use.devtunnels.ms
```

> ⚠️ The tunnel must be **publicly accessible**. Run `devtunnel access list` to confirm. If not, `devtunnel access create --allow-anonymous` (or set "Anyone" in the VS Code Tunnels view).

### Option B — ngrok

Download from <https://ngrok.com/download>. Then:

```powershell
ngrok http 3978
```

You'll see something like `Forwarding https://abc-1-2-3-4.ngrok-free.app -> http://localhost:3978`.

### Step 1.1 — Note your public URL

Copy it. From now on we'll call it **`<PUBLIC_URL>`**. Example: `https://abc-1-2-3-4.ngrok-free.app`.

### Step 1.2 — Verify

In a browser, visit `<PUBLIC_URL>/api/messages`. You should get a `405 Method Not Allowed` (because that endpoint only accepts POST). That's good — it proves traffic reaches your laptop.

### ✅ Checkpoint 1
You have a public HTTPS URL that forwards to `localhost:3978`.

---

## Lab 2 — Register the Bot (~20 min)

**You will:** create an Azure Bot resource that brokers messages between channels (Teams) and your endpoint.

### Step 2.1 — Open the Azure portal

Browse to <https://portal.azure.com>. Sign in. Search the top bar for **"Azure Bot"** → click it → click **+ Create**.

### Step 2.2 — Fill in the form

| Field | Value |
|---|---|
| Bot handle | `profile-bot-yourname` (must be globally unique) |
| Subscription | (your sub) |
| Resource group | new — `rg-agent-labs` (or any) |
| Pricing tier | **F0 (Free)** |
| Microsoft App ID | **Type of App = Multi Tenant**, **Creation type = Create new Microsoft App ID** |

Click **Review + create → Create**. Wait ~1 min.

### Step 2.3 — Copy the App ID + secret

1. Go to the new Bot resource → **Settings → Configuration**.
2. Copy **Microsoft App ID** → save somewhere.
3. Click **Manage Password** → **+ New client secret** → **Add**. Copy the secret **value** (you'll never see it again).

Set them in your agent's `.env`:

```dotenv
MICROSOFT_APP_ID=<your app id>
MICROSOFT_APP_PASSWORD=<your secret>
MICROSOFT_APP_TYPE=MultiTenant
MICROSOFT_APP_TENANT_ID=<your tenant id (Bot Configuration page shows it too)>
```

### Step 2.4 — Set the messaging endpoint

Same **Configuration** page → **Messaging endpoint**: paste `<PUBLIC_URL>/api/messages`. **Apply**.

### Step 2.5 — Enable Teams channel

In the Bot resource → **Channels** → click the **Microsoft Teams** icon → accept terms → **Apply**.

### ✅ Checkpoint 2
Bot is created, has an App ID + secret, messaging endpoint points to your dev tunnel, and Teams channel is enabled.

---

## Lab 3 — Set up user SSO (~30 min)

**You will:** register an Entra (Azure AD) app for **user identity** (so the bot can act *as* the user when calling Graph), then attach it to the Bot as an OAuth connection.

### Step 3.1 — Create the Entra app

Portal → **Entra ID → App registrations → + New registration**.

| Field | Value |
|---|---|
| Name | `profile-agent-sso` |
| Supported account types | **Single tenant** (simplest) |
| Redirect URI | **Web** → `https://token.botframework.com/.auth/web/redirect` |

Click **Register**.

### Step 3.2 — Add API permissions

In the new app → **API permissions → + Add a permission → Microsoft Graph → Delegated permissions**:

- ✅ `User.Read`
- ✅ `Mail.Read`

Click **Add permissions**. Then click **Grant admin consent for <tenant>** (you need an admin).

### Step 3.3 — Create a client secret for this Entra app

**Certificates & secrets → + New client secret → Add**. Copy the **value**.

### Step 3.4 — Configure the OAuth Connection in the Bot

Back to your Bot resource → **Configuration → OAuth Connection Settings → + Add OAuth Connection Settings**.

| Field | Value |
|---|---|
| Name | `graph-sso` |
| Service Provider | **Azure Active Directory v2** |
| Client id | (Entra app's Application ID) |
| Client secret | (Entra app's secret value) |
| Tenant ID | `common` (multi-tenant) or your tenant id |
| Scopes | `User.Read Mail.Read` |

Save. Then **Test connection** → sign in with your user → you should get a token preview. 🎉

In `.env`:

```dotenv
OAUTH_CONNECTION_NAME=graph-sso
```

### ✅ Checkpoint 3
"Test connection" returned a token (not a red error).

---

## Lab 4 — Build the Teams app manifest (~15 min)

**You will:** zip three files into a `.zip` and upload it to Teams.

### Step 4.1 — Create lab folder

```powershell
cd Phase7_Channels_Teams_Auth
mkdir -Force lab_profile
cd lab_profile
Copy-Item ..\code\profile_agent\start_server.py .
mkdir -Force manifest
```

### Step 4.2 — Create the icons

You need two PNGs. For quick testing use any 192×192 (color) and 32×32 (outline).

```powershell
# Quick placeholders — use real images later
Add-Type -AssemblyName System.Drawing
$bmp = New-Object System.Drawing.Bitmap 192, 192
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::FromArgb(91,83,255))
$bmp.Save("manifest\color.png", [System.Drawing.Imaging.ImageFormat]::Png)

$bmp = New-Object System.Drawing.Bitmap 32, 32
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::White)
$bmp.Save("manifest\outline.png", [System.Drawing.Imaging.ImageFormat]::Png)
```

### Step 4.3 — Create `manifest/manifest.json`

```powershell
New-Item manifest\manifest.json -ItemType File
code manifest\manifest.json
```

Paste (replacing the two `REPLACE-…` placeholders):

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.17/MicrosoftTeams.schema.json",
  "manifestVersion": "1.17",
  "version": "1.0.0",
  "id": "REPLACE-WITH-A-NEW-GUID",
  "developer": {
    "name": "Lab Dev",
    "websiteUrl": "https://example.com",
    "privacyUrl": "https://example.com/privacy",
    "termsOfUseUrl": "https://example.com/terms"
  },
  "name": { "short": "Profile Bot", "full": "Profile Bot — Phase 7 Lab" },
  "description": {
    "short": "Greets you and shows your mailbox folders.",
    "full": "Demo bot for the Microsoft 365 Agents SDK Phase 7 lab."
  },
  "icons": { "color": "color.png", "outline": "outline.png" },
  "accentColor": "#5b53ff",
  "bots": [
    {
      "botId": "REPLACE-WITH-AZURE-BOT-APP-ID",
      "scopes": ["personal", "team", "groupchat"],
      "supportsFiles": false,
      "isNotificationOnly": false
    }
  ],
  "permissions": ["identity", "messageTeamMembers"],
  "validDomains": ["token.botframework.com"]
}
```

Generate a fresh GUID for the `id` field:

```powershell
[guid]::NewGuid().ToString()
```

Paste it into the manifest.

### Step 4.4 — Zip it

```powershell
Compress-Archive -Path manifest\manifest.json,manifest\color.png,manifest\outline.png `
    -DestinationPath manifest\profile-bot.zip -Force
```

### Step 4.5 — Side-load into Teams

In Teams → **Apps** (left sidebar) → **Manage your apps** → **Upload an app** → **Upload a custom app** → pick `profile-bot.zip`.

If "Upload a custom app" is missing, your tenant disables custom app upload — ask your admin or use a developer tenant.

### ✅ Checkpoint 4
Teams now lists "Profile Bot" under your apps. **Don't start chatting yet** — we need to add the code first.

---

## Lab 5 — Code the agent (~25 min)

### Step 5.1 — Create `app.py`

```powershell
New-Item app.py -ItemType File
code app.py
```

Paste:

```python
"""profile_agent — Phase 7 lab. Login → /me → folders."""
import os, httpx
from dotenv import load_dotenv

from microsoft_agents.hosting.core import (
    AgentApplication, MemoryStorage, TurnContext, TurnState,
)
# ⚠️ The exact import path for MSAL helper may vary between SDK versions.
# In recent builds:
from microsoft_agents.authentication.msal import MsalAuth

from start_server import start_server

load_dotenv()

auth = MsalAuth(connection_name=os.environ["OAUTH_CONNECTION_NAME"])
AGENT_APP = AgentApplication(storage=MemoryStorage(), auth=auth)


@AGENT_APP.conversation_update("membersAdded")
async def welcome(context: TurnContext, state: TurnState):
    for m in context.activity.members_added or []:
        if m.id != context.activity.recipient.id:
            channel = context.activity.channel_id
            await context.send_activity(
                f"👋 Hi! You're on **{channel}**.\n"
                "Commands: `login`, `me`, `folders`, `logout`."
            )


@AGENT_APP.message("login")
async def login(context: TurnContext, state: TurnState):
    token = await auth.get_token(context)
    if token:
        await context.send_activity("✅ Already signed in.")
    else:
        await auth.sign_in(context, state)


@AGENT_APP.message("logout")
async def logout(context: TurnContext, state: TurnState):
    await auth.sign_out(context, state)
    await context.send_activity("👋 Signed out.")


async def _graph_get(path: str, token: str) -> dict:
    async with httpx.AsyncClient(timeout=20) as http:
        r = await http.get(
            f"https://graph.microsoft.com/v1.0{path}",
            headers={"Authorization": f"Bearer {token}"},
        )
        r.raise_for_status()
        return r.json()


@AGENT_APP.message("me")
async def me(context: TurnContext, state: TurnState):
    token = await auth.get_token(context)
    if not token:
        await context.send_activity("Please type `login` first.")
        return
    profile = await _graph_get("/me", token)
    await context.send_activity(
        f"You are **{profile.get('displayName')}** ({profile.get('mail') or profile.get('userPrincipalName')})."
    )


@AGENT_APP.message("folders")
async def folders(context: TurnContext, state: TurnState):
    token = await auth.get_token(context)
    if not token:
        await context.send_activity("Please type `login` first.")
        return
    data = await _graph_get("/me/mailFolders", token)
    names = [f["displayName"] for f in data["value"]]
    await context.send_activity("📁 Your folders:\n- " + "\n- ".join(names))


@AGENT_APP.activity("message")
async def fallback(context: TurnContext, state: TurnState):
    channel = context.activity.channel_id
    extra = " (Teams supports tabs and mentions)" if channel == "msteams" else ""
    await context.send_activity(
        f"I don't know that command on **{channel}**.{extra}\n"
        "Try `login`, `me`, `folders`, `logout`."
    )


if __name__ == "__main__":
    start_server(AGENT_APP, None)
```

> 💡 If `from microsoft_agents.authentication.msal import MsalAuth` errors, run `pip show microsoft-agents-authentication-msal` to confirm it's installed, then check the package's `__init__.py` for the right export name in your SDK version. The shape (constructor `connection_name=`, methods `get_token / sign_in / sign_out`) is stable across versions even if the import path moves.

Save.

### Step 5.2 — Run it

```powershell
python app.py
```

Keep the dev tunnel from Lab 1 alive.

### Step 5.3 — Chat in Teams

Open Teams → **Profile Bot** → start a chat → type:

| You type | Expected |
|---|---|
| `hi` | "Hi! You're on **msteams**. Commands: …" |
| `me` | "Please type `login` first." |
| `login` | An **OAuth sign-in card** appears. Click it, sign in. |
| `me` | "You are **<Your Name>** (<your email>)." |
| `folders` | List of mailbox folders. |
| `logout` | "👋 Signed out." |

### ✅ Checkpoint 5
You signed in inside Teams and Graph returned your real name and folders. 🎉

---

## 🆘 If something goes wrong

| What you see | What it really means | How to fix |
|---|---|---|
| Bot doesn't respond at all in Teams | Messaging endpoint wrong or dev tunnel dead. | Confirm `<PUBLIC_URL>/api/messages` is reachable from a browser (must return 405). |
| `401 Unauthorized` in agent logs | App ID / secret mismatch. | Re-copy `MICROSOFT_APP_ID` / `MICROSOFT_APP_PASSWORD` into `.env`. Restart agent. |
| OAuth card appears but sign-in fails: "AADSTS50011 reply URL mismatch" | Redirect URI on the Entra app doesn't match. | Set it to **exactly** `https://token.botframework.com/.auth/web/redirect` (no trailing slash). |
| `403 Forbidden` from Graph | Missing permission or admin consent not granted. | Re-add the permission and click **Grant admin consent**. |
| Teams says "We can't upload this app" | Custom apps disabled in the tenant. | Use a developer tenant from <https://developer.microsoft.com/microsoft-365/dev-program>. |
| Manifest GUID error on upload | `id` is not a valid GUID. | Regenerate with `[guid]::NewGuid().ToString()` and re-zip. |
| `ImportError: MsalAuth` | Package missing or moved. | `pip install microsoft-agents-authentication-msal`; check the package's `__init__.py` for the actual export name. |

---

## 🎓 Self-check

1. **What's the difference between agent identity and user identity?**

   <details><summary>Show answer</summary>
   Agent identity = the bot's own credentials (App ID + secret) so it can talk to the Bot Service. User identity = the signed-in human, obtained via OAuth, used to call Graph on their behalf.
   </details>

2. **Why does Teams/Bot Service need a public HTTPS URL?**

   <details><summary>Show answer</summary>
   The Bot Service in Azure has to POST activities **to** your agent. It can't reach `localhost`. HTTPS is required for security.
   </details>

3. **What does `connection_name="graph-sso"` mean?**

   <details><summary>Show answer</summary>
   It's the name you gave the OAuth Connection Setting in the Bot resource. The SDK looks it up so it knows which Entra app to use for the sign-in card.
   </details>

4. **Which manifest field decides which Bot resource the manifest is for?**

   <details><summary>Show answer</summary>
   `bots[0].botId` — set it to the **Microsoft App ID** of your Azure Bot.
   </details>

5. **What does `context.activity.channel_id` give you, and why is it useful?**

   <details><summary>Show answer</summary>
   The channel name (`msteams`, `webchat`, `emulator`, `outlook`, etc.). Useful for channel-specific behavior — e.g. only show @mentions in Teams.
   </details>

---

## 🚀 Bonus tasks

1. **Calendar peek** — add a `today` command that calls `/me/calendarview` and lists today's meetings.
2. **Channel-only feature** — restrict `folders` to Teams only; reply "Folders only work in Teams" elsewhere.
3. **@mention me** — in Teams, send an Adaptive Card that mentions the user using `EntityMention`.
4. **Token cache** — add logging to see when `auth.get_token` hits the cache vs. when it round-trips to Entra.
5. **Multi-tenant** — change the Entra app to multi-tenant and try the bot in a second tenant.

---

## 🏁 You're done!

You can now:

- Expose a local agent over the internet with a dev tunnel.
- Register and configure an Azure Bot + Teams channel.
- Add user SSO via an Entra app + Bot OAuth Connection.
- Read Microsoft Graph using the signed-in user's token.
- Side-load a custom Teams app.

Next → [Phase 8 — Agent 365 Enterprise (identity, governance, OTel)](../Phase8_Agent365_Enterprise/README.md)
