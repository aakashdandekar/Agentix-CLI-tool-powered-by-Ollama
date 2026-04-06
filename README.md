# Agentix — CLI tool powered by Ollama

A lightweight, agentic command-line AI assistant that uses **Llama 3** (via Ollama) with real tool-use: run shell commands, read/write files, browse the web, and list directories.

---

## Requirements

- Linux (tested on Ubuntu 22.04+)
- Python 3.11+
- [Ollama](https://ollama.com) installed and running

---

## Install

```bash
# 1. Clone / copy the project folder
cd agentix

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Pull the Llama 3 model
ollama pull llama3:latest

# 4. Make agent.py executable (optional)
chmod +x agent.py

# 5. (Optional) install as a CLI tool
pip install -e .
```

---

## Usage

### Interactive REPL

```bash
python agent.py
# or, after pip install -e .
aiagent
```

### One-shot (pipe-friendly)

```bash
python agent.py "List all Python files in the current directory"
python agent.py --model llama3:latest "Summarise /etc/os-release"
```

### Flags

| Flag | Description |
|---|---|
| `--model / -m` | Override model (e.g. `llama3:latest`) |
| `--ollama-url / -u` | Override Ollama URL (default `http://localhost:11434`) |
| `--no-safe-mode` | Disable confirmation prompts for risky commands |
| `--show-config` | Print resolved config and exit |

---

## Slash commands (REPL only)

| Command | Description |
|---|---|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/config` | Show current configuration |
| `/model <name>` | Switch model on the fly |
| `/safe` | Toggle safe mode on/off |
| `/log` | Show path to the tool log file |
| `/history` | Show number of messages in context |
| `/exit` or `/quit` | Quit |

---

## Available Tools

| Tool | Description |
|---|---|
| `run_shell` | Execute any bash command; blocked patterns + confirmation prompts in safe mode |
| `read_file` | Read a file's content (up to 32 KB by default) |
| `write_file` | Write or append to a file |
| `browse_web` | Fetch a URL and return readable plain text |
| `list_directory` | List directory contents, optionally recursive |

---

## Configuration

Configuration is stored at `~/.aiagent/config.yaml`.  
The tool log is at `~/.aiagent/tool.log` (JSONL, one entry per tool call).

### Default config

```yaml
model: llama3:latest
safe_mode: true
ollama_url: http://localhost:11434
max_iterations: 10
log_path: ~/.aiagent/tool.log
system_prompt: "You are a helpful CLI assistant…"
```

Edit `~/.aiagent/config.yaml` to persist changes across sessions.

---

## Safe mode

When `safe_mode: true` (default), certain commands require confirmation before running, and a hard blocklist prevents obviously destructive operations (`rm -rf /`, `mkfs`, `dd if=…`, etc.) from ever executing.

Disable with `--no-safe-mode` flag or `/safe` in the REPL (temporary).

---

## File layout

```
agentix/
├── agent.py        # Entry point · CLI args · REPL loop · agentic tool loop
├── tools.py        # run_shell · read_file · write_file · browse_web · list_directory
├── config.py       # load/save config.yaml · defaults · CLI flag overrides
├── logger.py       # log_tool_call() · timestamped JSONL to ~/.aiagent/tool.log
├── safety.py       # dangerous command blocklist · confirmation prompts · safe-mode
├── pyproject.toml  # package metadata · dependencies · [project.scripts] entry point
├── requirements.txt
└── README.md

~/.aiagent/         # auto-created at runtime
├── config.yaml     # model · safe_mode · log_path · default system prompt
└── tool.log        # JSONL audit log · one entry per tool call · timestamps
```
