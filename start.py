"""One command setup: check Python and Tk, build .venv, install, test, open the GUI."""
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"


def fail(message: str, hint: str) -> None:
    """Print an error with a fix hint and exit with code 1."""
    print(f"error: {message}")
    print(f"fix: {hint}")
    sys.exit(1)


def venv_python() -> str:
    """Return the path of the python program inside the venv."""
    if os.name == "nt":
        return str(VENV / "Scripts" / "python.exe")
    return str(VENV / "bin" / "python")


def check_python() -> None:
    """Step 1: Python must be 3.10 or newer."""
    print("[1/6] Python version")
    if sys.version_info < (3, 10):
        found = ".".join(str(n) for n in sys.version_info[:3])
        fail(f"found Python {found}", "install Python 3.10 or newer")
    print("ok")


def check_tk(no_gui: bool) -> None:
    """Step 2: tkinter must import in this interpreter, the venv inherits it."""
    print("[2/6] Tk for the GUI")
    result = subprocess.run([sys.executable, "-c", "import tkinter"], check=False)
    if result.returncode == 0:
        print("ok")
        return
    print("Tk is missing. Install it:")
    print("  Debian/Ubuntu: sudo apt install python3-tk")
    print("  Fedora: sudo dnf install python3-tkinter")
    print("  macOS: use the python.org installer, it includes Tk")
    print("  Windows: re-run the Python installer and tick tcl/tk")
    if not no_gui:
        sys.exit(1)
    print("warning: continuing because of --no-gui")


def make_venv() -> None:
    """Step 3: create .venv if it does not exist."""
    print("[3/6] Virtual environment")
    if Path(venv_python()).exists():
        print("exists, reused")
        return
    result = subprocess.run([sys.executable, "-m", "venv", ".venv"], check=False)
    if result.returncode != 0:
        fail("could not create .venv",
             "on Debian/Ubuntu run: sudo apt install python3-venv, "
             "then delete the .venv folder and run this script again")
    print("ok")


def install() -> None:
    """Step 4: install requirements.txt into the venv."""
    print("[4/6] Install requirements")
    cmd = [venv_python(), "-m", "pip", "install", "--disable-pip-version-check",
           "-r", "requirements.txt"]
    if subprocess.run(cmd, check=False).returncode != 0:
        fail("pip install failed",
             "check the network, or delete the .venv folder and run this script again")
    print("ok")


def verify(no_tests: bool) -> bool:
    """Step 5: import the packages, then run the tests. Return True if all is well."""
    print("[5/6] Verify")
    code = ("import numpy, matplotlib, pytest; "
            "print(numpy.__version__, matplotlib.__version__, pytest.__version__)")
    if subprocess.run([venv_python(), "-c", code], check=False).returncode != 0:
        fail("a package does not import", "delete .venv and run this script again")
    if no_tests:
        print("tests skipped")
        return True
    result = subprocess.run([venv_python(), "-m", "pytest", "-q"],
                            capture_output=True, text=True, check=False)
    lines = result.stdout.strip().splitlines()
    print(lines[-1] if lines else "no test output")
    if result.returncode != 0:
        print("tests failed, the GUI may still run")
        return False
    print("ok")
    return True


def launch(no_gui: bool) -> int:
    """Step 6: print the manual commands, then start the GUI and wait for it."""
    print("[6/6] Launch")
    if os.name == "nt":
        print("Later, activate with: .venv\\Scripts\\activate")
    else:
        print("Later, activate with: source .venv/bin/activate")
    print("Then run: python -m ballsim --gui")
    if no_gui:
        print("skipped (--no-gui)")
        return 0
    print("starting the GUI, close its window to finish")
    return subprocess.call([venv_python(), "-m", "ballsim", "--gui"])


def main() -> None:
    """Run the six steps in order."""
    parser = argparse.ArgumentParser(description="Set up the project and open the GUI.")
    parser.add_argument("--no-gui", action="store_true", help="set up and test only")
    parser.add_argument("--no-tests", action="store_true", help="skip the test run")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):  # absent in some IDE consoles
        sys.stdout.reconfigure(line_buffering=True)  # keep our lines in order with child output
    os.chdir(ROOT)
    check_python()
    check_tk(args.no_gui)
    make_venv()
    install()
    tests_ok = verify(args.no_tests)
    gui_code = launch(args.no_gui)
    sys.exit(0 if tests_ok and gui_code == 0 else 1)


if __name__ == "__main__":
    main()
