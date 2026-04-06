import os
import pathlib
import yaml


CONFIG_DIR = pathlib.Path.home() / ".aiagent"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULTS = {
    "model": "gemma4:31b-cloud",
    "safe_mode": True,
    "log_path": str(pathlib.Path.home() / ".aiagent" / "tool.log"),
    "system_prompt": (
        "You are a helpful CLI assistant running on Linux. "
        "You have access to tools: run_shell, read_file, write_file, browse_web, list_directory. "
        "Use them to help the user accomplish tasks. "
        "Always prefer safe, reversible actions. "
        "When running shell commands, explain what you are doing."
    ),
    "max_iterations": 10,
    "ollama_url": "http://localhost:11434",
}


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config(overrides: dict | None = None) -> dict:
    _ensure_config_dir()
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
    _ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)


def show_config(config: dict) -> None:
    print("\ncurrent configuration:")
    for key, val in config.items():
        print(f"  {key}: {val}")
    print()
