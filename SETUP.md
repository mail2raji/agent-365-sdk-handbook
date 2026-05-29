# 🛠️ Setup Guide

This page gets your computer ready in **~10 minutes**.

> Think of it like setting up the kitchen *before* you start cooking. We're installing the stove (Python), the recipe book (the SDK), and a tasting spoon (the test tool).

---

## 1. Install Python 3.10 or 3.11

The Microsoft 365 Agents SDK officially supports **Python 3.9 – 3.11**. Use **3.10 or 3.11** for best results.

### Windows

1. Download from <https://www.python.org/downloads/>.
2. During install, **tick "Add Python to PATH"** (very important).
3. Open PowerShell and check:

   ```powershell
   python --version
   ```

   You should see something like `Python 3.11.9`.

### macOS / Linux

```bash
# macOS (with Homebrew)
brew install python@3.11

# Linux (Debian/Ubuntu)
sudo apt update && sudo apt install python3.11 python3.11-venv
```

Verify:

```bash
python3 --version
```

---

## 2. Install VS Code + Python extension

1. Download VS Code: <https://code.visualstudio.com/>.
2. Open VS Code → Extensions panel (`Ctrl+Shift+X`) → search and install:
   - **Python** (by Microsoft)
   - **Pylance** (auto-included with Python)

---

## 3. Open the curriculum folder

Open this `Agent365_SDK_Learning/` folder in VS Code:

```powershell
cd C:\Scripts\Send-escalationEmail\Agent365_SDK_Learning
code .
```

---

## 4. Create a virtual environment

A **virtual environment** is a private sandbox where Python packages live. It keeps each project's packages from fighting with each other.

> 👶 Picture: every project gets its own toy box so toys don't get mixed up.

In VS Code:

1. Press `F1` → type `Python: Create environment` → press `Enter`.
2. Choose **Venv**.
3. Choose **Python 3.11** (or 3.10).
4. When asked to pick a `requirements.txt`, tick the one at the root of this folder.
5. Wait while it installs.

**Or** do it from the terminal:

```powershell
# from Agent365_SDK_Learning/
python -m venv .venv

# activate it
.\.venv\Scripts\Activate.ps1     # Windows PowerShell
# source .venv/bin/activate     # macOS / Linux

pip install --upgrade pip
pip install -r requirements.txt
```

You'll know the venv is active because your prompt now starts with `(.venv)`.

---

## 5. Copy `.env.example` → `.env`

We store secrets (API keys, etc.) in a file called `.env` that is **never** committed to git.

```powershell
Copy-Item .env.example .env
```

Open `.env`. For Phase 0–4 you don't need any keys yet. We'll fill it in as we go.

---

## 6. (Phase 9+) Install the Test Tool / Emulator

You have **two** choices for testing your agent locally without deploying it anywhere:

### Option A — Microsoft 365 Agents Toolkit (recommended)

VS Code extension. Includes "Agents Playground".

1. VS Code Extensions → search **Microsoft 365 Agents Toolkit** → Install.
2. The toolkit icon appears in the left sidebar.

### Option B — Bot Framework Emulator (classic)

Old but still works for the Agents SDK.

- Download: <https://github.com/Microsoft/BotFramework-Emulator/releases/latest>

We'll use these in Phase 9.

---

## 7. (Phase 8+) Install the Agent 365 CLI and `uv`

For the **enterprise** Agent 365 SDK (Phase 8 onward) you'll also need:

```powershell
pip install uv                       # fast Python package manager used by the A365 samples
```

The **Agent 365 CLI** (`a365`) installation steps depend on platform and tenant — we'll do it in Phase 8 when you actually need it.

---

## 8. Quick smoke test

Let's make sure your install works. Create a file `_smoke_test.py` at the root:

```python
from microsoft_agents.hosting.core import AgentApplication, MemoryStorage
print("✅ SDK imported OK")
print("AgentApplication:", AgentApplication)
print("MemoryStorage:", MemoryStorage)
```

Run it:

```powershell
python _smoke_test.py
```

You should see `✅ SDK imported OK` and two class names.
If you see `ModuleNotFoundError`, your venv probably isn't activated. Repeat step 4.

---

## ✅ You're ready!

Next → [Phase0_Setup/README.md](Phase0_Setup/README.md)
