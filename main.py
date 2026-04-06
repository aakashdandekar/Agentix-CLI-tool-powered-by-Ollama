import subprocess

subprocess.Popen([
    "ptyxis",
    "--",
    "bash", "-c",
    "python3 agent.py --model qwen2.5-coder:1.5b"
])