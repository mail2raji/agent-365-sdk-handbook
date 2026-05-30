# 🧪 Phase 0 — Hands-On Lab: First Light

> A step-by-step lab you can finish even if you have **never** opened a terminal before. Follow each instruction in order. Don't skip steps. If you get stuck, scroll to the **🆘 If something goes wrong** section at the bottom.

---

## 🎯 What you'll build today

By the end of this lab you will have:

1. **A working Python workspace** for the whole curriculum (used by every later phase).
2. **All M365 Agents SDK packages installed** in a virtual environment.
3. **A tiny Python file** (`hello_sdk.py`) that proves the SDK works by importing every class you'll meet in Phase 1.
4. **Confidence** that you can read a Python error and fix it.

> 👶 Imagine you're setting up a brand-new kitchen. We'll buy the pots and pans (install Python), put them in a cabinet (the virtual environment), and cook one tiny meal (`hello_sdk.py`) to make sure the stove works. We are **not** cooking dinner yet — that's Phase 1.

⏱️ **About 30–45 minutes** if you take your time.

---

## ✅ Before you start (checklist)

- [ ] You are on Windows 10/11, macOS, or Linux.
- [ ] You have internet (you'll download Python packages).
- [ ] You have **VS Code** installed. If not, install from <https://code.visualstudio.com/>.
- [ ] You have **Python 3.10 or 3.11** installed. If not, install from <https://python.org/downloads>. **When the installer asks, tick the box that says "Add Python to PATH".**
- [ ] You have **at least 1 GB free disk space**.

If anything above is "no", fix that first and come back.

---

## 🧰 Tools you'll touch

| Tool | What it is (in one sentence) |
|---|---|
| **VS Code** | The text editor where you'll write code. |
| **Terminal** | A black box inside VS Code where you type commands. |
| **PowerShell** | The language the terminal speaks on Windows. (Mac/Linux use *bash* — same commands work for this lab.) |
| **Python** | The programming language we write the agent in. |
| **pip** | The command that downloads Python packages. |
| **Virtual environment** | A private cupboard for *this* project's packages — so they don't fight with other projects on your computer. |

---

## 🗺️ Today's roadmap

```
Lab 1 → Open the workspace
Lab 2 → Build the virtual environment
Lab 3 → Install the SDK
Lab 4 → Write & run hello_sdk.py
Lab 5 → Read an error on purpose (and survive it)
```

---

## Lab 1 — Open the workspace in VS Code (~5 min)

**You will:** open the curriculum folder in VS Code and open a terminal inside it.

### Step 1.1 — Open VS Code

1. Click the **VS Code** icon (looks like a blue ribbon).
2. If a **Welcome** tab opens, ignore it for now.

### Step 1.2 — Open the curriculum folder

1. In VS Code, press **`Ctrl+K`** then **`Ctrl+O`** (Windows/Linux) or **`Cmd+K`** then **`Cmd+O`** (Mac). A file picker opens.
2. Navigate to the folder that contains this `Agent365_SDK_Learning` directory.
3. Click on **`Agent365_SDK_Learning`** once to select it, then click **Select Folder**.
4. On the **left side** of VS Code you'll see a file tree starting with `Phase0_Setup/`, `Phase1_Foundations/`, … That's the curriculum.

> 🛡️ If a popup asks "Do you trust the authors of the files…?" click **Yes, I trust the authors**.

### Step 1.3 — Open a terminal inside VS Code

1. Press **`Ctrl+\``** (the key just under `Esc` — it's a backtick) **or** click the menu **Terminal → New Terminal**.
2. A panel slides up from the bottom. The last line shows your folder name followed by `>`. That's the prompt.

   ```text
   PS C:\Scripts\Send-escalationEmail\Agent365_SDK_Learning>
   ```

3. Type your first command — just to check the terminal works:

   ```powershell
   pwd
   ```

   Press **Enter**. You should see the same folder path printed again.

**What just happened?** `pwd` = "print working directory" = "where am I?". You confirmed the terminal is *inside* the curriculum folder. From now on, every command in this lab is typed here.

### ✅ Checkpoint 1
You can see the `Phase0_Setup/`, `Phase1_Foundations/` … folders on the left, and a terminal at the bottom with the prompt ending in `Agent365_SDK_Learning>`.

---

## Lab 2 — Build the virtual environment (~5 min)

**You will:** create a private "cupboard" called `.venv` and "step into" it so every `pip install` lands in there.

### Step 2.1 — Check your Python version

In the terminal, type **exactly**:

```powershell
python --version
```

Press Enter. You should see something like:

```text
Python 3.11.9
```

**What you want:** a version that starts with `3.10` or `3.11`.

| If you see… | Do this |
|---|---|
| `Python 3.10.x` or `3.11.x` | ✅ Perfect. Continue. |
| `Python 3.12.x` | Mostly fine, but a few packages may complain. If something breaks, install 3.11 alongside. |
| `Python 3.9.x` or lower | Install a newer Python from <https://python.org/downloads> first. |
| `Python was not found` | Re-install Python and **tick "Add Python to PATH"**. Close & reopen VS Code. |

### Step 2.2 — Create the virtual environment

Type:

```powershell
python -m venv .venv
```

Press Enter. It runs for ~10 seconds with **no output**. That's normal — silence means success.

**What just happened?** Python made a hidden folder `.venv` containing a private copy of Python and pip. Everything we install next will live inside `.venv` and won't touch your system Python.

### Step 2.3 — Activate the virtual environment

Type this on **Windows PowerShell**:

```powershell
.\.venv\Scripts\Activate.ps1
```

On **macOS / Linux** instead:

```bash
source .venv/bin/activate
```

Press Enter. **Your prompt should now start with `(.venv)`** — like:

```text
(.venv) PS C:\Scripts\Send-escalationEmail\Agent365_SDK_Learning>
```

**What just happened?** You "stepped into" the cupboard. Every `python` or `pip` you type now will use the venv copy, not the system copy. If you ever close the terminal you must re-run this activate command.

#### 🚨 Error: "cannot be loaded because running scripts is disabled"

If PowerShell complains, run this once (this allows scripts signed for your account):

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Answer `Y`, then re-run the activate command.

### ✅ Checkpoint 2
Your prompt starts with `(.venv)`. If it doesn't, the activate step didn't work — see the error box above.

---

## Lab 3 — Install the SDK packages (~10 min)

**You will:** download all the Microsoft Agents SDK packages into your `.venv`.

### Step 3.1 — Upgrade pip first

Always start with a fresh pip — older pips sometimes pick the wrong package.

```powershell
python -m pip install --upgrade pip
```

You'll see a few lines like `Successfully installed pip-25.x.x`.

### Step 3.2 — Install everything from `requirements.txt`

The curriculum ships a list of every package. Install them all at once:

```powershell
pip install -r requirements.txt
```

This takes **about 1–3 minutes** depending on your internet. You'll see lots of `Downloading…` and `Installing…` lines. The very last line should be:

```text
Successfully installed aiohttp-... microsoft-agents-activity-... microsoft-agents-hosting-aiohttp-... microsoft-agents-hosting-core-... ...
```

**What just happened?** Pip downloaded every package listed in `requirements.txt` (look in the file tree if curious) and put them in `.venv\Lib\site-packages\`.

### Step 3.3 — Confirm the SDK packages are installed

```powershell
pip list | findstr microsoft-agents
```

(On macOS/Linux, replace `findstr` with `grep`.)

You should see at least these 4 lines (versions will differ):

```text
microsoft-agents-activity              1.x.x
microsoft-agents-authentication-msal   1.x.x
microsoft-agents-hosting-aiohttp       1.x.x
microsoft-agents-hosting-core          1.x.x
```

### ✅ Checkpoint 3
You see ≥ 4 lines starting with `microsoft-agents-…`.

---

## Lab 4 — Write & run `hello_sdk.py` (~5 min)

**You will:** create a tiny Python file that imports every SDK class you'll meet in Phase 1, and run it.

### Step 4.1 — Move into the Phase 0 folder

```powershell
cd Phase0_Setup
```

Your prompt should now end with `Phase0_Setup>`.

### Step 4.2 — Create the file

```powershell
New-Item hello_sdk.py -ItemType File
code hello_sdk.py
```

On macOS/Linux replace the first line with `touch hello_sdk.py`.

VS Code opens an **empty** file tab.

### Step 4.3 — Paste the code

Click inside the empty file tab. Copy the block below (**triple-click** any line to select that line, or click the **copy** icon in the top-right of the code block), then paste with **`Ctrl+V`**:

```python
"""hello_sdk.py — proves the M365 Agents SDK is installed correctly.

Run me with:    python hello_sdk.py
"""

# Step A: import the foundation classes
from microsoft_agents.hosting.core import (
    AgentApplication,
    TurnContext,
    TurnState,
    MemoryStorage,
)
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.activity import Activity, ActivityTypes

# Step B: print one line per class so you know they're all there
print("AgentApplication ->", AgentApplication.__name__)
print("TurnContext      ->", TurnContext.__name__)
print("TurnState        ->", TurnState.__name__)
print("MemoryStorage    ->", MemoryStorage.__name__)
print("CloudAdapter     ->", CloudAdapter.__name__)
print("Activity         ->", Activity.__name__)
print("ActivityTypes    ->", ActivityTypes.__name__)
print()
print("All SDK imports OK. You are ready for Phase 1!")
```

Save with **`Ctrl+S`**.

**What does this code do?** Two things, on purpose simple:

- **Step A** *imports* seven classes from three different SDK packages. If any package is missing, Python crashes with `ModuleNotFoundError` and you know exactly which one.
- **Step B** *prints* each class name so you visually confirm Python found it.

### Step 4.4 — Run it

In the terminal:

```powershell
python hello_sdk.py
```

**Expected output:**

```text
AgentApplication -> AgentApplication
TurnContext      -> TurnContext
TurnState        -> TurnState
MemoryStorage    -> MemoryStorage
CloudAdapter     -> CloudAdapter
Activity         -> Activity
ActivityTypes    -> ActivityTypes

All SDK imports OK. You are ready for Phase 1!
```

### ✅ Checkpoint 4
You see the 7 class names + the "All SDK imports OK" message.

If you see `ModuleNotFoundError`, go to **🆘 If something goes wrong** below.

---

## Lab 5 — Read an error on purpose (~5 min)

**You will:** break the file deliberately, learn to read the error, and fix it. This is the most important skill in the whole curriculum.

### Step 5.1 — Make the file break

Open `hello_sdk.py` again. Find this line:

```python
from microsoft_agents.hosting.core import (
    AgentApplication,
```

Change `AgentApplication` to a typo on purpose — say `AgentApp`:

```python
from microsoft_agents.hosting.core import (
    AgentApp,
```

Save with `Ctrl+S`.

### Step 5.2 — Run it and read the error

```powershell
python hello_sdk.py
```

You'll see something like:

```text
Traceback (most recent call last):
  File "C:\...\Phase0_Setup\hello_sdk.py", line 7, in <module>
    from microsoft_agents.hosting.core import (
ImportError: cannot import name 'AgentApp' from 'microsoft_agents.hosting.core' (C:\...\__init__.py)
```

**How to read a Python error (the rule):** start at the **bottom**.

- Bottom line: `ImportError: cannot import name 'AgentApp'` ← the problem.
- File and line: `hello_sdk.py", line 7` ← where to look.

**Translation:** "I tried to fetch a thing called `AgentApp` from the SDK, but it doesn't exist."

### Step 5.3 — Fix it

Change `AgentApp` back to `AgentApplication`. Save. Re-run:

```powershell
python hello_sdk.py
```

The 7 lines come back.

### ✅ Checkpoint 5
You broke the file, read the error, and fixed it. **Remember the rule: read the bottom line of an error first.**

---

## 🆘 If something goes wrong

| What you see | What it really means | How to fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'microsoft_agents'` | Either the venv is not active, or pip never installed the packages. | Run `.\.venv\Scripts\Activate.ps1` (prompt should show `(.venv)`), then `pip install -r requirements.txt`. |
| `python : The term 'python' is not recognized…` | Python isn't on your PATH. | Re-install Python with the "Add Python to PATH" box ticked, then close & reopen VS Code. |
| `Activate.ps1 cannot be loaded because running scripts is disabled` | Windows blocks unsigned scripts by default. | Run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`, answer `Y`, then activate again. |
| Pip prints `pip install` is "externally-managed-environment" | Your venv isn't active — you're hitting the OS Python. | Activate the venv. The prompt **must** start with `(.venv)`. |
| The download stalls or times out | Slow or filtered internet. | Try `pip install -r requirements.txt --proxy http://YOUR-PROXY:PORT` if behind a corporate proxy. |
| You closed the terminal and lost `(.venv)` | The venv only stays active in the terminal where you ran `Activate.ps1`. | Re-activate it in the new terminal. |

---

## 🎓 Self-check — what did you learn?

Answer these out loud (or write them in a notebook). The answer is hidden — only peek if you're stuck.

1. **Why do we use a virtual environment instead of installing packages globally?**

   <details><summary>Show answer</summary>
   So this project's packages can't break — or be broken by — other Python projects on your computer. Each project lives in its own `.venv` cupboard.
   </details>

2. **You closed VS Code. You open it again, open a terminal, and run `python hello_sdk.py`. You get `ModuleNotFoundError`. Why?**

   <details><summary>Show answer</summary>
   The new terminal is **not** in the venv yet. Run `.\.venv\Scripts\Activate.ps1` (Windows) or `source .venv/bin/activate` (macOS/Linux) first. Your prompt should start with `(.venv)`.
   </details>

3. **When you read a Python error, which line do you read first?**

   <details><summary>Show answer</summary>
   The **bottom** line. It tells you the actual error name and message. The lines above are the trail of *where* the error happened.
   </details>

4. **Which package contains `AgentApplication`?**

   <details><summary>Show answer</summary>
   `microsoft-agents-hosting-core` — note the **dashes** in the PyPI name but **underscores** in the Python import:

   ```python
   from microsoft_agents.hosting.core import AgentApplication
   ```
   </details>

5. **There are two "Agent 365" SDKs. Which one did we install today, and which one is for later?**

   <details><summary>Show answer</summary>
   We installed the **Microsoft 365 Agents SDK** (foundation — for *building* agents). The **Microsoft Agent 365 SDK** (enterprise governance — identity, observability, governed tools) comes in Phase 8.
   </details>

---

## 🚀 Bonus tasks (optional)

Try any of these now or come back later.

1. **Show every installed package, not just `microsoft-agents-*`:**

   ```powershell
   pip list
   ```

   You'll see ~50 lines including `aiohttp`, `cryptography`, `msal`, etc. — they are the SDK's dependencies.

2. **Find where `AgentApplication` lives on your disk** (this is genuinely useful when an error mentions a file deep inside the SDK):

   ```powershell
   pip show microsoft-agents-hosting-core | findstr Location
   ```

3. **Save a "snapshot" of every installed package** (helpful for sharing your environment with a colleague):

   ```powershell
   pip freeze > my-snapshot.txt
   ```

   Open `my-snapshot.txt` and you'll see every package pinned to an exact version.

4. **Deactivate the venv** (to see what *not* having `(.venv)` looks like):

   ```powershell
   deactivate
   ```

   The `(.venv)` prefix disappears. Re-activate with `.\.venv\Scripts\Activate.ps1`.

---

## 🏁 You're done!

You now have:

- A working Python 3.10/3.11 environment.
- A `.venv` with every package Phase 1–7 needs.
- A proven-good import file (`hello_sdk.py`).
- A reflex to read errors from the bottom up.

Next → [Phase 1 — Foundations (build the Echo Agent)](../Phase1_Foundations/README.md)
