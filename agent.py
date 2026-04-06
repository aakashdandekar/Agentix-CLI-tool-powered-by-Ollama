import argparse
import json
import re
import sys
import time
import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.theme import Theme
import config
import logger
import tools


# Rich console setup
THEME = Theme({
    "agent": "bold cyan",
    "tool": "bold yellow",
    "error": "bold red",
    "system": "dim white",
    "user": "bold green",
})

console = Console(theme=THEME)


def show_status_banner(cfg: dict) -> None:
    console.print(Panel(
        f"[bold cyan]Agentix[/bold cyan]\n"
        f"Model: [bold]{cfg['model']}[/bold]  |  "
        f"Safe mode: [bold]{'ON' if cfg['safe_mode'] else 'OFF'}[/bold]  |  "
        f"Type [bold]/help[/bold] for commands, [bold]/exit[/bold] to quit.",
        border_style="cyan",
    ))


# Per-model tool-support cache  (True = supported, False = not supported)
_model_tools_support: dict[str, bool] = {}


def _normalize_tool_calls(payload) -> list[dict]:
    if isinstance(payload, list):
        calls = []
        for item in payload:
            calls.extend(_normalize_tool_calls(item))
        return calls

    if not isinstance(payload, dict):
        return []

    if "tool_calls" in payload:
        return _normalize_tool_calls(payload["tool_calls"])

    if "function" in payload and isinstance(payload["function"], dict):
        payload = payload["function"]

    name = payload.get("name")
    arguments = payload.get("arguments", {})

    if not isinstance(name, str) or name not in tools.TOOL_NAMES:
        return []

    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            arguments = {}

    if not isinstance(arguments, dict):
        arguments = {}

    return [{"function": {"name": name, "arguments": arguments}}]


def _extract_json_snippets(text: str):
    decoder = json.JSONDecoder()
    for idx, char in enumerate(text):
        if char not in "[{":
            continue
        try:
            _, end = decoder.raw_decode(text[idx:])
        except json.JSONDecodeError:
            continue
        yield text[idx:idx + end]


def parse_tool_calls_from_content(content: str) -> list[dict]:
    if not content or not content.strip():
        return []

    candidates = [content.strip()]
    fenced_blocks = re.findall(r"```(?:json)?\s*(.*?)```", content, flags=re.DOTALL | re.IGNORECASE)
    candidates.extend(block.strip() for block in fenced_blocks if block.strip())

    seen = set()
    for candidate in candidates:
        snippets = [candidate, *_extract_json_snippets(candidate)]
        for snippet in snippets:
            snippet = snippet.strip()
            if not snippet or snippet in seen:
                continue
            seen.add(snippet)

            try:
                payload = json.loads(snippet)
            except json.JSONDecodeError:
                continue

            tool_calls = _normalize_tool_calls(payload)
            if tool_calls:
                return tool_calls

    return []


def _tool_call_signature(tool_name: str, arguments: dict) -> str:
    return json.dumps(
        {
            "name": tool_name,
            "arguments": arguments or {},
        },
        sort_keys=True,
        ensure_ascii=False,
    )


# Ollama client
def ollama_chat(messages: list, model: str, ollama_url: str, tool_list: list) -> dict:
    url = f"{ollama_url}/api/chat"

    # Skip tools field if we already know this model doesn't support it
    use_tools = _model_tools_support.get(model, True) and bool(tool_list)

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if use_tools:
        payload["tools"] = tool_list

    try:
        resp = requests.post(url, json=payload, timeout=600)

        # Graceful fallback: model doesn't support the tools API
        if resp.status_code == 400 and "does not support tools" in resp.text:
            _model_tools_support[model] = False
            console.print(
                f"[system]⚠  {model} does not support the tools API — "
                "falling back to prompt-based mode.[/system]"
            )
            payload.pop("tools", None)
            resp = requests.post(url, json=payload, timeout=600)
        else:
            _model_tools_support[model] = True

        resp.raise_for_status()
        return resp.json()

    except requests.exceptions.ConnectionError:
        console.print(
            f"\n[error] Cannot connect to Ollama at {ollama_url}[/error]\n"
            f"Make sure Ollama is running: [bold]ollama serve[/bold]\n"
            f"And the model is pulled: [bold]ollama pull {model}[/bold]"
        )
        time.sleep(360)
        sys.exit(1)

    except Exception as e:
        console.print(f"[error]Ollama error: {e}[/error]")
        time.sleep(360)
        sys.exit(1)



# Agentic tool loop
def run_agent_turn(user_input: str, history: list, cfg: dict) -> str:
    history.append({"role": "user", "content": user_input})
    last_tool_signature: str | None = None
    last_tool_result: str | None = None

    for iteration in range(cfg["max_iterations"]):
        response = ollama_chat(
            messages=history,
            model=cfg["model"],
            ollama_url=cfg["ollama_url"],
            tool_list=tools.TOOL_SCHEMAS,
        )

        message = response.get("message", {})
        content = message.get("content", "")
        tool_calls = message.get("tool_calls", []) or parse_tool_calls_from_content(content)

        if not tool_calls:
            history.append({"role": "assistant", "content": content})
            return content

        history.append(message)

        for tc in tool_calls:
            fn = tc.get("function", {})
            tool_name = fn.get("name", "")
            raw_args = fn.get("arguments", {})

            if isinstance(raw_args, str):
                try:
                    raw_args = json.loads(raw_args)
                except json.JSONDecodeError:
                    raw_args = {}

            signature = _tool_call_signature(tool_name, raw_args)

            if signature == last_tool_signature:
                previous_result = last_tool_result or ""
                result = (
                    f"Duplicate tool call skipped: {tool_name} was already executed "
                    "immediately before this with the same arguments.\n"
                    f"Previous result:\n{previous_result}\n\n"
                    "Do not repeat the same tool call back to back unless something changed "
                    "or the user explicitly asked for a retry. Use the previous result to continue."
                )
                console.print(
                    f"\n[tool] Duplicate skipped:[/tool] [bold]{tool_name}[/bold] "
                    + (f"({json.dumps(raw_args, ensure_ascii=False)[:120]})" if raw_args else "")
                )
                display_result = result if len(result) <= 500 else result[:500] + "…"
                console.print(f"[system]  → {display_result}[/system]")
                history.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": result,
                })
                continue

            console.print(
                f"\n[tool] Tool call:[/tool] [bold]{tool_name}[/bold] "
                + (f"({json.dumps(raw_args, ensure_ascii=False)[:120]})" if raw_args else "")
            )

            try:
                result = tools.dispatch(tool_name, raw_args, safe_mode=cfg["safe_mode"])
            except Exception as e:
                result = f"Error calling tool {tool_name}: {e}"

            last_tool_signature = signature
            last_tool_result = result
            display_result = result if len(result) <= 500 else result[:500] + "…"
            console.print(f"[system]  → {display_result}[/system]")

            history.append({
                "role": "tool",
                "name": tool_name,
                "content": result,
            })

    return "Max iterations reached without a final answer."



# Slash commands
def handle_slash(cmd: str, cfg: dict, history: list) -> bool:
    cmd = cmd.strip()
    if cmd in ("/exit", "/quit", "/q"):
        console.print("[agent] Goodbye![/agent]")
        sys.exit(0)
    elif cmd == "/help":
        console.print(Panel(
            "[bold]/help[/bold]       - show this help\n"
            "[bold]/clear[/bold]      - clear conversation history\n"
            "[bold]/config[/bold]     - show current configuration\n"
            "[bold]/model <name>[/bold] - switch model on the fly\n"
            "[bold]/safe[/bold]       - toggle safe mode\n"
            "[bold]/log[/bold]        - show log file path\n"
            "[bold]/history[/bold]    - show message count\n"
            "[bold]/exit[/bold]       - quit",
            title="Commands", border_style="cyan"
        ))
    elif cmd == "/clear":
        history.clear()
        history.append({"role": "system", "content": cfg["system_prompt"]})
        console.print("[system]  History cleared.[/system]")

    elif cmd == "/config":
        config.show_config(cfg)
    
    elif cmd.startswith("/model "):
        new_model = cmd[7:].strip()
        cfg["model"] = new_model
        console.print(f"[system]Model switched to: [bold]{new_model}[/bold][/system]")
        show_status_banner(cfg)
    
    elif cmd == "/safe":
        cfg["safe_mode"] = not cfg["safe_mode"]
        state = "ON" if cfg["safe_mode"] else "OFF"
        console.print(f"[system]Safe mode: [bold]{state}[/bold][/system]")
        show_status_banner(cfg)
    
    elif cmd == "/log":
        console.print(f"[system]Log file: {logger.get_log_path()}[/system]")
    
    elif cmd == "/history":
        console.print(f"[system]Messages in history: {len(history)}[/system]")
    
    else:
        console.print(f"[error]Unknown command: {cmd}  (type /help)[/error]")
    
    return True



# REPL
def repl(cfg: dict) -> None:
    history = [{"role": "system", "content": cfg["system_prompt"]}]
    show_status_banner(cfg)

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[agent]Goodbye![/agent]")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            handle_slash(user_input, cfg, history)
            continue

        console.print()
        with console.status("[agent]Thinking…[/agent]", spinner="dots"):
            answer = run_agent_turn(user_input, history, cfg)

        console.print(Panel(
            Markdown(answer),
            title="[agent]Agent[/agent]",
            border_style="cyan",
        ))



# One-shot mode (non-interactive)
def one_shot(prompt: str, cfg: dict) -> None:
    history = [{"role": "system", "content": cfg["system_prompt"]}]
    with console.status("[agent]Thinking…[/agent]", spinner="dots"):
        answer = run_agent_turn(prompt, history, cfg)
    console.print(Markdown(answer))



# CLI entry point
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="aiagent",
        description="CLI AI agent powered by Gemma 4 via Ollama",
    )
    parser.add_argument("prompt", nargs="*", help="One-shot prompt (omit for interactive REPL)")
    parser.add_argument("--model", "-m", default=None, help="Model name (overrides config)")
    parser.add_argument("--ollama-url", "-u", default=None, help="Ollama base URL")
    parser.add_argument("--no-safe-mode", action="store_true", help="Disable safe mode")
    parser.add_argument("--show-config", action="store_true", help="Print config and exit")
    args = parser.parse_args()

    overrides = {
        "model": args.model,
        "ollama_url": args.ollama_url,
    }
    if args.no_safe_mode:
        overrides["safe_mode"] = False

    cfg = config.load_config(overrides)

    if args.show_config:
        config.show_config(cfg)
        return

    if args.prompt:
        one_shot(" ".join(args.prompt), cfg)
    else:
        repl(cfg)


if __name__ == "__main__":
    main()
