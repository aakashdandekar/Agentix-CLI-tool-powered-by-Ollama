import subprocess
import sys
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
command_unix = "python3 agent.py --model gemma4:31b-cloud"
command_win = "python agent.py --model gemma4:31b-cloud"

if sys.platform == "win32":
    subprocess.Popen(["start", "cmd", "/k", f"cd /d {base_dir} && {command_win}"], shell=True)
elif sys.platform == "darwin":
    script = f'tell app "Terminal" to do script "cd {base_dir} && {command_unix}"'
    subprocess.Popen(["osascript", "-e", script])
else:
    subprocess.Popen([
        "ptyxis",
        "--",
        "bash", "-c",
        f"cd {base_dir} && {command_unix}"
    ])