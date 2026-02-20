<div align="center">
  <img src="nanobot_logo.png" alt="nanobot" width="500">
  <h1>nanobot: Ultra-Lightweight Personal AI Assistant</h1>
  <p>
    <a href="https://pypi.org/project/nanobot-ai/"><img src="https://img.shields.io/pypi/v/nanobot-ai" alt="PyPI"></a>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</div>

**nanobot** is an **ultra-lightweight** personal AI assistant framework.

⚡️ Delivers core agent functionality in just **~2,000** lines of code.

## 🏗️ Architecture

nanobot uses a simple architecture:

1. **CLI Interface** - Interactive chat or single-message mode
2. **Agent Loop** - Processes messages, calls LLM, executes tools
3. **Tools** - File I/O, Shell, Web Search, Web Fetch
4. **Skills** - Extend capabilities with custom markdown files
5. **Memory** - Persistent conversation history and long-term memory

## ✨ Features

- **CLI Chat** - Interactive terminal-based chat with history
- **File Tools** - Read, write, edit files in workspace
- **Shell Execution** - Run commands safely with workspace restriction
- **Web Search** - Brave Search integration for real-time info
- **Web Fetch** - Fetch and parse web page content
- **Skills System** - Custom capabilities via SKILL.md files
- **Memory** - Automatic conversation consolidation

## 📦 Install

**From PyPI:**
```bash
pip install nanobot-ai
```

**From source:**
```bash
git clone https://github.com/HKUDS/nanobot.git
cd nanobot
pip install -e .
```

## 🚀 Quick Start

**1. Initialize**
```bash
nanobot onboard
```

**2. Configure** (`~/.nanobot/config.json`)

Add your OpenRouter API key:
```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    }
  }
}
```

Get API key: https://openrouter.ai/keys

**3. Chat**
```bash
# Interactive mode
nanobot agent

# Single message
nanobot agent -m "Hello!"
```

## ⚙️ Configuration

Config file: `~/.nanobot/config.json`

### Providers

| Provider | Purpose | Get API Key |
|----------|---------|-------------|
| `openrouter` | LLM (recommended, access to all models) | [openrouter.ai](https://openrouter.ai) |

### Agent Defaults

```json
{
  "agents": {
    "defaults": {
      "model": "openrouter/anthropic/claude-3-5-sonnet",
      "max_tokens": 8192,
      "temperature": 0.7,
      "max_tool_iterations": 20,
      "memory_window": 50
    }
  }
}
```

### Tools

```json
{
  "tools": {
    "web": {
      "search": {
        "api_key": "",  // Brave Search API key (optional)
        "max_results": 5
      }
    },
    "exec": {
      "timeout": 60
    },
    "restrict_to_workspace": false
  }
}
```

## 🛠️ Skills

Skills extend nanobot's capabilities. They are markdown files that teach the agent how to use specific tools or perform tasks.

### List Skills
```bash
nanobot skills list
```

### View Skill
```bash
nanobot skills show <skill-name>
```

### Create Custom Skills

Create a directory in `~/.nanobot/workspace/skills/<skill-name>/` with a `SKILL.md` file:

```markdown
---
name: My Skill
description: What this skill does
---

# Skill Instructions

Your custom instructions here...
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `nanobot onboard` | Initialize config & workspace |
| `nanobot agent` | Interactive chat mode |
| `nanobot agent -m "..."` | Send a single message |
| `nanobot agent --no-markdown` | Plain-text responses |
| `nanobot agent --logs` | Show runtime logs |
| `nanobot status` | Show status |
| `nanobot skills list` | List available skills |
| `nanobot skills show <name>` | Show skill content |

Interactive mode exits: `exit`, `quit`, `/exit`, `/quit`, `:q`, or `Ctrl+D`.

## 📁 Workspace Structure

```
~/.nanobot/
├── config.json          # Configuration file
└── workspace/
    ├── skills/          # Custom skills
    ├── sessions/        # Conversation history
    └── memory/
        ├── MEMORY.md    # Long-term memory
        └── HISTORY.md   # Consolidated history
```

## 🔒 Security

- **Workspace Restriction**: Set `"restrict_to_workspace": true` to sandbox file/shell access
- **No External Access**: CLI-only mode, no network exposure

## 🐛 Troubleshooting

**No API key configured:**
```
Error: No API key configured.
```
→ Add your API key to `~/.nanobot/config.json`

**Model not found:**
→ Check model name format: `openrouter/anthropic/claude-3-5-sonnet`

## License

MIT License
