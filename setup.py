import os
import subprocess
import sys
from pathlib import Path

VENV_DIR = Path("venv")
PYTHON_EXEC = VENV_DIR / "bin" / "python" if os.name != "nt" else VENV_DIR / "Scripts" / "python.exe"
REQUIREMENTS = "req.txt"
MAIN_SCRIPT = "main.py"

def create_venv():
    print("[+] Creating virtual environment...")
    subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])

def install_requirements():
    if not Path(REQUIREMENTS).exists():
        print(f"[!] {REQUIREMENTS} not found.")
        sys.exit(1)
    print("[+] Installing dependencies...")
    subprocess.check_call([str(PYTHON_EXEC), "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([str(PYTHON_EXEC), "-m", "pip", "install", "-r", REQUIREMENTS])

def run_app():
    print("[+] Starting app...")
    subprocess.check_call([str(PYTHON_EXEC), MAIN_SCRIPT])

def main():
    if not VENV_DIR.exists():
        create_venv()
        install_requirements()
    else:
        # Ensure dependencies are installed even if venv already exists
        install_requirements()

    run_app()

if __name__ == "__main__":
    main()
