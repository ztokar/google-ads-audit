"""Install the pinned official read-only server into a local environment."""
import os, subprocess, sys, venv
from pathlib import Path
if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required.")
root = Path(__file__).resolve().parent
venv.EnvBuilder(with_pip=True).create(root / ".venv")
python = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
subprocess.run([str(python), "-m", "pip", "install", "--no-compile", "-r", str(root / "requirements.txt")], check=True)
print("Installed. Next: configure.py, Google login, connection.py check --live.")
