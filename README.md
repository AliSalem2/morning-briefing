# Morning Briefing Agent

A local AI-powered morning briefing that tells you the weather, your calendar events, and top news — running on your own machine with no cloud dependency.

Built with Ollama, LiteLLM, and FastMCP.

---

## What it does

Every time you run it, the agent:
1. Fetches current weather for your city
2. Pulls today's events from your Google Calendar
3. Gets top headlines from NewsAPI
4. Passes everything to a local LLM to write a clean 3-sentence briefing

---

## Requirements

- Windows with WSL2 (Ubuntu) or native Linux/Mac
- Python 3.12+
- Ollama installed
- A free NewsAPI key
- A Google Cloud project with Calendar API enabled

---

## Pick your model based on your machine

| Your RAM | Recommended model | Command |
|---|---|---|
| 8GB | TinyLlama | `ollama pull tinyllama` |
| 16GB | Phi-3 Mini | `ollama pull phi3:mini` |
| 32GB+ | Llama 3.1 8B | `ollama pull llama3.1:8b` |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/morning-briefing.git
cd morning-briefing
```

### 2. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Set up your API keys

```bash
cp config/api_keys.example.env config/.env
```

Open `config/.env` and fill in:
- `NEWS_API_KEY` — free at https://newsapi.org/register
- `ANTHROPIC_API_KEY` — only needed if switching to Claude
- `MODEL_PROVIDER` — set to `ollama/tinyllama` for 8GB machines

### 4. Set up Google Calendar

- Go to https://console.cloud.google.com
- Create a project, enable Google Calendar API
- Create OAuth credentials (Desktop app), download as `gc_client.json`
- Move it to `config/gc_client.json`
- Add your Gmail as a test user under OAuth consent screen

### 5. Pull your model

```bash
ollama pull tinyllama
```

### 6. Run

```bash
# Terminal 1 — keep this running
ollama serve

# Terminal 2
python agent/briefing_agent.py
```

First run will open a browser for Google Calendar authentication. After that it runs silently.

---

## Switching to Claude (cloud fallback)

In `config/.env` change:
MODEL_PROVIDER=anthropic/claude-haiku-4-5

And make sure your `ANTHROPIC_API_KEY` is filled in. No other code changes needed.

---

## Project structure

morning-briefing/
├── servers/
│   ├── weather_mcp.py      # Open-Meteo API
│   ├── calendar_mcp.py     # Google Calendar
│   └── news_mcp.py         # NewsAPI
├── agent/
│   ├── briefing_agent.py   # Main agent
│   └── prompts.py          # System prompts
├── config/
│   ├── .env                # Your secrets (never committed)
│   └── api_keys.example.env
├── requirements.txt
└── README.md

## Credits

Built by [@AliSalem2](https://github.com/AliSalem2) as a learning project for local LLM stacks and MCP server architecture.

## Local model performance note

Local models require CPU-only generation on machines without a dedicated GPU.
Expected generation times on CPU:
- TinyLlama: 1-2 minutes
- Phi-3 Mini: 5-10 minutes
- Llama 3.1 8B: not recommended under 32GB RAM

For daily use on low-spec machines, the Claude Haiku API is recommended.
It costs roughly $0.001 per briefing — essentially free.
