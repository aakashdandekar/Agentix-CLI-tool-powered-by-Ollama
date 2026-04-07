# Agentix — CLI tool powered by Minimax-m2 / Gemma 4 via Ollama

A lightweight, agentic command-line AI assistant that uses **minimax-m2:cloud** / **Gemma 4** (via Ollama) with real tool-use: run shell commands, read/write files, browse the web, and list directories. All file and shell operations are safely sandboxed in the `agent-files/` directory.

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

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Pull the default model (e.g. minimax-m2:cloud or gemma)
ollama pull minimax-m2:cloud

# 5. Make agent.py and launch.sh executable (optional)
chmod +x agent.py launch.sh

# 6. (Optional) install as a CLI tool
pip install -e .
```

---

## Usage

### Interactive REPL

```bash
# Using the launch script (automatically activates .venv and opens in a new terminal)
./launch.sh

# Or directly:
python agent.py
# or, after pip install -e .
aiagent
```

### One-shot (pipe-friendly)

```bash
python agent.py "List all Python files in the agent-files directory"
python agent.py --model minimax-m2:cloud "Summarise agent-files/example.txt"
```

### Flags

| Flag | Description |
|---|---|
| `--model / -m` | Override model (e.g. `minimax-m2:cloud`) |
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
| `run_shell` | Execute a bash command (restricted to `agent-files/` directory) |
| `read_file` | Read a file's content (restricted to `agent-files/`, up to 32 KB by default) |
| `write_file` | Write or append to a file (restricted to `agent-files/`) |
| `browse_web` | Fetch a URL and return readable plain text |
| `list_directory` | List directory contents inside `agent-files/`, optionally recursive |

---

## Configuration

Configuration is stored at `~/.aiagent/config.yaml`.  
The tool log is at `~/.aiagent/tool.log` (JSONL, one entry per tool call).

### Default config

```yaml
model: minimax-m2:cloud
safe_mode: true
ollama_url: http://localhost:11434
max_iterations: 20
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
├── agent-files/    # Sandboxed directory for all file & shell operations
├── agent.py        # Entry point · CLI args · REPL loop · agentic tool loop
├── tools.py        # run_shell · read_file · write_file · browse_web · list_directory
├── config.py       # load/save config.yaml · defaults · CLI flag overrides
├── logger.py       # log_tool_call() · timestamped JSONL to ~/.aiagent/tool.log
├── safety.py       # dangerous command blocklist · confirmation prompts · safe-mode
├── pyproject.toml  # package metadata · dependencies · [project.scripts] entry point
├── requirements.txt
├── launch.sh       # bash script to activate virtual environment and launch main.py
├── main.py         # python script to spawn agent.py inside a new ptyxis terminal
└── README.md

~/.aiagent/         # auto-created at runtime
├── config.yaml     # model · safe_mode · log_path · default system prompt
└── tool.log        # JSONL audit log · one entry per tool call · timestamps
```
