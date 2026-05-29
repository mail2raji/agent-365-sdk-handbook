# 📖 Glossary — Plain-English Definitions

Every weird word in the curriculum, explained simply.

---

### Activity
A small JSON message that says *"something happened"*. Example: "the user typed hello", "a new person joined the chat", "a button was clicked". Everything that moves through the agent is an **Activity**.

> 👶 Like a sticky note. Each note has a type ("message", "membersAdded", …) and some text on it.

### Adaptive Card
A small UI form (buttons, text, images) sent as a chat message and rendered by the channel (Teams, web chat, etc.). Defined in JSON.

> 👶 Like a paper form the bot hands the user. The user fills it in and hands it back.

### Agent
A program that *receives messages, reasons about them (often with an LLM), and sends responses*. May call tools, remember things, and run for many turns.

### Agent 365 SDK (Microsoft Agent 365 SDK)
The **enterprise** layer that adds **identity, observability, notifications, and governed tool access** to an agent you've already built with *any* framework (M365 Agents SDK, Semantic Kernel, LangChain, OpenAI SDK…).

### Agent Application (`AgentApplication`)
The Python object that ties everything together. It owns the handlers (`@app.message`, `@app.activity`, …) and the state.

### A365 CLI
A command-line tool for managing Agent 365 things: agent blueprints, MCP server registration, publishing, deployment.

### Bot Framework
The **old name** for what is now the Microsoft 365 Agents SDK. The Python packages used to start with `botbuilder-`. They start with `microsoft-agents-` now.

### Channel
A place where users talk to the agent: Microsoft Teams, Microsoft 365 Copilot, web chat, Slack, Facebook Messenger, etc. The SDK hides the differences between channels.

### `CloudAdapter`
The piece that translates between the channel's HTTP request format and the SDK's internal `Activity` format. You almost never call its methods directly.

### Conversation
A single back-and-forth thread between a user (or a group of users) and the agent. Each conversation has a unique `conversation.id`.

### Conversation State
Data that lives **for the whole conversation**. Example: the items in a user's shopping cart. Cleared when the conversation ends.

### Custom Engine Agent
An agent you build yourself with code (vs. a no-code "declarative agent" built in Copilot Studio). Everything in this curriculum is a custom engine agent.

### Declarative Agent
A no-code agent you describe in YAML/JSON and host inside Microsoft 365 Copilot. **Not** what we're building here.

### Function Calling / Tool Use
When the LLM decides "to answer this I need to call a function" — for example `get_weather(city)`. The SDK + Agent framework executes the function, gives the result back to the model, and the model writes the final reply.

### Handler
A function you write that runs when a specific kind of activity arrives. Registered via decorators like `@AGENT_APP.message("/help")`.

### LLM (Large Language Model)
The AI brain (e.g. GPT-4o, Llama, Claude) that turns text into text. The SDK is "AI-agnostic" — it doesn't care which LLM you plug in.

### MCP (Model Context Protocol)
An open protocol for exposing tools to LLMs. An **MCP server** offers tools (e.g. read mail, search SharePoint) that any compatible agent can call. Agent 365 uses *governed* MCP servers for Microsoft 365 data.

### Memory / Long-term memory
Data your agent remembers across many conversations (e.g. a user's preferences). Usually stored in a database (Cosmos DB, blob storage).

### `MemoryStorage`
Built-in **in-RAM** storage. Loses everything on restart. Use only for local testing.

### Notifications (A365)
Inbound events the agent receives like a human teammate would: a new email, a Teams message, a Word comment. Handled by the Agent 365 SDK's notification package.

### Observability
The ability to see what your agent did and why: traces, logs, metrics. Agent 365 provides this via **OpenTelemetry**.

### OpenTelemetry (OTel)
An open standard for emitting traces, metrics, and logs. Agent 365's observability SDK is built on it and sends data to Azure Monitor (or any OTel-compatible backend).

### `pip`
Python's package installer. `pip install something` downloads and installs `something`.

### Playground / Test Tool / Emulator
Local apps that pretend to be a chat channel so you can test the agent on your laptop before deploying anywhere.

### Streaming
The model sends its answer **a few words at a time** instead of all at once. Feels much faster to the user.

### `TurnContext`
The object passed to every handler. Holds the current `Activity`, has `send_activity(...)` to reply, and exposes user/conversation IDs.

### `TurnState`
The object that gives you scoped places to put data: `state.conversation`, `state.user`, `state.temp`.

### Turn
One round of "user says something → agent processes it → agent replies". A whole conversation is a sequence of turns.

### Venv (Virtual Environment)
A folder (`.venv/`) that contains an isolated Python installation for one project. Activated with `.\.venv\Scripts\Activate.ps1`.

### Web Chat
A JavaScript widget you embed in any website to talk to your agent.
