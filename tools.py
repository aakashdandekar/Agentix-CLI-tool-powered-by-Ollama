import os
import subprocess
import pathlib
import requests
from bs4 import BeautifulSoup
import safety
import logger


# Tool schemas (passed to Ollama)
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": (
                "Execute a shell command on the Linux system and return stdout+stderr. "
                "Use for file operations, package management, git, compiling, running scripts, etc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The bash command to run.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds (default 30).",
                        "default": 30,
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file and return them as a string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative path to the file.",
                    },
                    "max_bytes": {
                        "type": "integer",
                        "description": "Maximum bytes to read (default 32768).",
                        "default": 32768,
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write (or overwrite) a file with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute or relative path to write to.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Text content to write.",
                    },
                    "append": {
                        "type": "boolean",
                        "description": "If true, append instead of overwrite (default false).",
                        "default": False,
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browse_web",
            "description": "Fetch a URL and return the page's readable text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch.",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Max characters to return (default 8000).",
                        "default": 8000,
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List the contents of a directory, with optional recursion.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory path to list (default '.').",
                        "default": ".",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Whether to recurse into subdirectories (default false).",
                        "default": False,
                    },
                    "show_hidden": {
                        "type": "boolean",
                        "description": "Include hidden files/dirs (default false).",
                        "default": False,
                    },
                },
                "required": [],
            },
        },
    },
]



# Tool implementations
def run_shell(command: str, timeout: int = 30, safe_mode: bool = True) -> str:
    if not safety.check_command(command, safe_mode):
        result = f"Command was blocked or rejected by safety check."
        logger.log_tool_call("run_shell", {"command": command}, result, error=True)
        return result

    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            executable="/bin/bash",
        )
        output = ""
        if proc.stdout:
            output += proc.stdout
        if proc.stderr:
            output += "\n[stderr]\n" + proc.stderr
        result = output.strip() or "(no output)"
        if proc.returncode != 0:
            result = f"[exit {proc.returncode}]\n{result}"
        logger.log_tool_call("run_shell", {"command": command}, result)
        return result
    except subprocess.TimeoutExpired:
        result = f"Command timed out after {timeout}s."
        logger.log_tool_call("run_shell", {"command": command}, result, error=True)
        return result
    except Exception as e:
        result = f"Error running command: {e}"
        logger.log_tool_call("run_shell", {"command": command}, result, error=True)
        return result


def read_file(path: str, max_bytes: int = 32768) -> str:
    try:
        p = pathlib.Path(path).expanduser().resolve()
        if not p.exists():
            result = f"File not found: {path}"
            logger.log_tool_call("read_file", {"path": path}, result, error=True)
            return result
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_bytes)
        if len(content) == max_bytes:
            content += f"\n... (truncated at {max_bytes} bytes)"
        logger.log_tool_call("read_file", {"path": path}, content)
        return content
    except Exception as e:
        result = f"Error reading file: {e}"
        logger.log_tool_call("read_file", {"path": path}, result, error=True)
        return result


def write_file(path: str, content: str, append: bool = False) -> str:
    try:
        p = pathlib.Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(p, mode, encoding="utf-8") as f:
            f.write(content)
        action = "Appended to" if append else "Wrote"
        result = f"{action} {p} ({len(content)} chars)."
        logger.log_tool_call("write_file", {"path": path, "append": append}, result)
        return result
    except Exception as e:
        result = f"Error writing file: {e}"
        logger.log_tool_call("write_file", {"path": path}, result, error=True)
        return result


def browse_web(url: str, max_chars: int = 8000) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) ai-agent/1.0"}
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [l for l in text.splitlines() if l.strip()]
        result = "\n".join(lines)[:max_chars]
        if len(result) == max_chars:
            result += "\n... (truncated)"
        logger.log_tool_call("browse_web", {"url": url}, result)
        return result
    except Exception as e:
        result = f"Error fetching URL: {e}"
        logger.log_tool_call("browse_web", {"url": url}, result, error=True)
        return result


def list_directory(path: str = ".", recursive: bool = False, show_hidden: bool = False) -> str:
    try:
        p = pathlib.Path(path).expanduser().resolve()
        if not p.exists():
            result = f"Path not found: {path}"
            logger.log_tool_call("list_directory", {"path": path}, result, error=True)
            return result
        entries = []
        if recursive:
            for root, dirs, files in os.walk(p):
                if not show_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith(".")]
                rel_root = pathlib.Path(root).relative_to(p)
                for d in sorted(dirs):
                    entries.append(f"  {'.' / rel_root / d}/")
                for f in sorted(files):
                    if show_hidden or not f.startswith("."):
                        entries.append(f"  ./{rel_root / f}")
        else:
            for item in sorted(p.iterdir()):
                if not show_hidden and item.name.startswith("."):
                    continue
                suffix = "/" if item.is_dir() else ""
                entries.append(f"  {item.name}{suffix}")
        result = f"{p}:\n" + ("\n".join(entries) if entries else "  (empty)")
        logger.log_tool_call("list_directory", {"path": path, "recursive": recursive}, result)
        return result
    except Exception as e:
        result = f"Error listing directory: {e}"
        logger.log_tool_call("list_directory", {"path": path}, result, error=True)
        return result



# Dispatcher
def dispatch(tool_name: str, args: dict, safe_mode: bool = True) -> str:
    if tool_name == "run_shell":
        return run_shell(safe_mode=safe_mode, **args)
    elif tool_name == "read_file":
        return read_file(**args)
    elif tool_name == "write_file":
        return write_file(**args)
    elif tool_name == "browse_web":
        return browse_web(**args)
    elif tool_name == "list_directory":
        return list_directory(**args)
    else:
        return f"Unknown tool: {tool_name}"
