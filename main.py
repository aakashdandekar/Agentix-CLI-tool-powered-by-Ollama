import subprocess

subprocess.Popen([
    "ptyxis",
    "--",
    "bash", "-c",
    "python3 agent.py --model llama3:latest"
])