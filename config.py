import os
import pathlib
import yaml


CONFIG_DIR = pathlib.Path.home() / ".aiagent"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULTS = {
    "model": "minimax-m2:cloud",
    "safe_mode": True,
    "log_path": str(pathlib.Path.home() / ".aiagent" / "tool.log"),
    "system_prompt": (
        "You are a helpful CLI assistant running on Linux. "
        "You have access to tools: run_shell, read_file, write_file, browse_web, list_directory. "
        "Use them to help the user accomplish tasks. "
        "All file and shell operations must stay inside the agent-files directory and its subdirectories. "
        "If the user asks you to do something in the terminal, prefer run_shell. "
        "Execute each requested tool action once, then answer the user with the result. "
        "Do not repeat the same tool call back to back unless something changed or the user explicitly asks you to retry. "
        "Always prefer safe, reversible actions. "
        "When running shell commands, explain what you are doing. "
        "CRITICAL: 'cd' commands DO NOT persist between tool calls. "
        "Always use absolute paths or full paths relative to the initial directory "
        "for write_file, read_file, and subsequent run_shell calls. "
        "If native tool calling is unavailable and you need a tool, respond with ONLY JSON in the form "
        "{\"name\":\"run_shell\",\"arguments\":{\"command\":\"pwd\"}} "
        "or a JSON array of the same objects."
        "If file not located in current directory then check in sub-directories."
        "Execute the command once and check result. if result is not what expected then redo else respond to user."
    ),
    "max_iterations": 50,
    "ollama_url": "http://localhost:11434",
}


def ensure_config_folder() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config(overrides: dict | None = None) -> dict:
    ensure_config_folder()
    config = dict(DEFAULTS)

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                file_cfg = yaml.safe_load(f) or {}
            config.update(file_cfg)
        except Exception as e:
            print(f"Could not read config file: {e}")

    if overrides:
        for key, val in overrides.items():
            if val is not None:
                config[key] = val

    return config


def save_config(config: dict) -> None:
    ensure_config_folder()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)


def show_config(config: dict) -> None:
    print("\ncurrent configuration:")
    for key, val in config.items():
        print(f"  {key}: {val}")
    print()
