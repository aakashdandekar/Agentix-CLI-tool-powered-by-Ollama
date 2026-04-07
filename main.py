import subprocess

subprocess.Popen([
    "ptyxis",
    "--",
    "bash", "-c",
    "python3 agent.py --model minimax-m2:cloud"
])