import json
import os
import pathlib
import datetime


LOG_DIR = pathlib.Path.home() / ".aiagent"
LOG_FILE = LOG_DIR / "tool.log"


def ensure_log_folder() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def log_tool_call(tool_name: str, arguments: dict, result: str, error: bool = False) -> None:
    ensure_log_folder()
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "tool": tool_name,
        "arguments": arguments,
        "result": result[:500] if isinstance(result, str) else str(result)[:500],
        "error": error,
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_log_path() -> str:
    return str(LOG_FILE)
