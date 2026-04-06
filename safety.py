import re
import sys

BLOCKLIST = [
    r"\brm\s+-rf\b",
    r"\brm\s+--no-preserve-root\b",
    r"mkfs",
    r"dd\s+if=",
    r":(){:|:&};:",
    r"chmod\s+-R\s+777\s+/",
    r"wget\s+.*\|\s*sh",
    r"curl\s+.*\|\s*sh",
    r"curl\s+.*\|\s*bash",
    r">\s*/dev/sd[a-z]",
    r"shred\s+",
    r"fdisk\s+/dev/",
    r"parted\s+/dev/",
    r"shutdown",
    r"reboot",
    r"halt\b",
    r"poweroff",
    r"init\s+0",
    r"init\s+6",
    r"systemctl\s+(poweroff|reboot|halt)",
    r"passwd\s+root",
    r"userdel\s+-r\s+root",
    r"truncate\s+.*--size\s+0\s+/",
]

CONFIRM_PATTERNS = [
    r"\brm\b",
    r"\bmv\b",
    r"\bcp\b.*-f",
    r"sudo\b",
    r"chmod\b",
    r"chown\b",
    r"kill\b",
    r"pkill\b",
    r"killall\b",
    r"apt\s+(remove|purge|autoremove)",
    r"pip\s+uninstall",
    r"systemctl\s+(stop|disable|mask)",
    r"iptables",
    r"ufw\s+(delete|disable|reset)",
]


def is_blocked(command: str) -> tuple[bool, str]:
    for pattern in BLOCKLIST:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"Blocked pattern matched: {pattern}"
    return False, ""


def needs_confirmation(command: str) -> bool:
    for pattern in CONFIRM_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def confirm(prompt: str) -> bool:
    try:
        answer = input(f"\n{prompt}\nProceed? [y/N] ").strip().lower()
        return answer in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def check_command(command: str, safe_mode: bool) -> bool:
    blocked, reason = is_blocked(command)
    if blocked:
        print(f"Command blocked: {reason}", file=sys.stderr)
        return False

    if safe_mode and needs_confirmation(command):
        return confirm(f"Command requires confirmation:\n  $ {command}")

    return True
