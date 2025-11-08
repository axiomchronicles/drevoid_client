#!/usr/bin/env python3
"""
install.py

Cross-platform installer for the 'drevoid' launcher.

✅ Creates/updates a global alias (default: 'drevoid')
✅ Embeds the correct path to your Python client script (default: start_client.py)
✅ Works on Linux, macOS, and Windows
✅ Automatically fixes PATH issues (adds ~/.local/bin if needed)
"""

from __future__ import annotations
import argparse
import os
import platform
import shutil
import stat
import sys
import tempfile
from pathlib import Path

DEFAULT_NAME = "drevoid"
DEFAULT_SOURCE = "start_client.py"

LAUNCHER_TEMPLATE = r'''#!/usr/bin/env python3
import sys, os, traceback, importlib.util
from pathlib import Path

CLIENT_PATH = r"{CLIENT_PATH}"

def main():
    try:
        client_path = Path(CLIENT_PATH).expanduser().resolve()
        if not client_path.exists():
            raise FileNotFoundError(f"Missing required file: {client_path}")

        project_root = client_path.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        spec = importlib.util.spec_from_file_location("client", client_path)
        client = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(client)

        if hasattr(client, "main") and callable(client.main):
            client.main()
        else:
            print("[WARNING] client.py has no callable 'main()' function.")

    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        sys.exit(2)
    except SystemExit:
        raise
    except Exception:
        print(f"\n[CRITICAL] Unhandled error while launching client.py:\n")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    main()
'''


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def is_executable_dir(path: Path) -> bool:
    try:
        return path.exists() and os.access(str(path), os.W_OK | os.X_OK)
    except Exception:
        return False


def path_dirs_from_env() -> list[Path]:
    sep = ";" if os.name == "nt" else ":"
    return [Path(p).expanduser() for p in os.environ.get("PATH", "").split(sep) if p]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def atomic_write(path: Path, data: str, mode: int = 0o755) -> None:
    ensure_dir(path.parent)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def ensure_path_in_shell_profile(bin_dir: Path, verbose: bool = False):
    """Add bin_dir to PATH in shell config if missing."""
    home = Path.home()
    profiles = [home / ".bashrc", home / ".zshrc", home / ".profile"]
    export_line = f'\n# Added by drevoid installer\nexport PATH="$PATH:{bin_dir}"\n'
    path_env = os.environ.get("PATH", "")

    if str(bin_dir) in path_env:
        return

    for profile in profiles:
        try:
            if not profile.exists():
                continue
            content = profile.read_text(encoding="utf-8")
            if str(bin_dir) in content:
                return
            with profile.open("a", encoding="utf-8") as f:
                f.write(export_line)
            if verbose:
                print(f"🔧 Added {bin_dir} to PATH in {profile}")
            return
        except Exception:
            continue

    if verbose:
        print(f"⚠️ Could not auto-add {bin_dir} to PATH. Add manually:\n  export PATH=\"$PATH:{bin_dir}\"")


# ---------------------------------------------------------------------
# Installation logic
# ---------------------------------------------------------------------

def install_posix(source: Path, name: str, target_dir: Path | None, verbose: bool) -> Path:
    candidates = [Path("~/.local/bin").expanduser(), Path("~/bin").expanduser()]
    target_dir = target_dir or next((p for p in candidates if is_executable_dir(p)), candidates[0])
    ensure_dir(target_dir)

    wrapper_path = target_dir / name
    if wrapper_path.exists():
        wrapper_path.unlink(missing_ok=True)

    launcher_code = LAUNCHER_TEMPLATE.replace("{CLIENT_PATH}", str(source))
    atomic_write(wrapper_path, launcher_code)
    wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IEXEC)

    if verbose:
        print(f"[POSIX] Installed {wrapper_path} → {source}")
    return wrapper_path


def install_windows(source: Path, name: str, target_dir: Path | None, verbose: bool) -> Path:
    if target_dir is None:
        home_bin = Path.home() / "AppData" / "Local" / "Programs" / name
        ensure_dir(home_bin)
        target_dir = home_bin

    target_py = target_dir / f"{name}.py"
    target_bat = target_dir / f"{name}.bat"

    for f in (target_py, target_bat):
        try:
            f.unlink(missing_ok=True)
        except Exception:
            pass

    launcher_code = LAUNCHER_TEMPLATE.replace("{CLIENT_PATH}", str(source))
    atomic_write(target_py, launcher_code)
    target_py.chmod(target_py.stat().st_mode | stat.S_IEXEC)

    bat_contents = f'@echo off\r\n"{sys.executable}" "%~dp0\\{name}.py" %*\r\n'
    atomic_write(target_bat, bat_contents, 0o666)

    if verbose:
        print(f"[WIN] Installed {target_py} and {target_bat} → {source}")
    return target_bat


# ---------------------------------------------------------------------
# CLI + Entry point
# ---------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="install.py", description="Installer for drevoid client launcher")
    p.add_argument("--source", "-s", default=DEFAULT_SOURCE, help="Client launcher file (default: start_client.py)")
    p.add_argument("--name", "-n", default=DEFAULT_NAME, help="Command name to install (default: drevoid)")
    p.add_argument("--target-dir", "-t", type=Path, default=None, help="Optional custom install directory")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    source = Path(args.source).expanduser().resolve()

    if not source.exists():
        print(f"❌ Error: Source not found: {source}")
        return 2

    system = platform.system().lower()
    try:
        if system == "windows":
            installed = install_windows(source, args.name, args.target_dir, args.verbose)
        elif system in ("linux", "darwin"):
            installed = install_posix(source, args.name, args.target_dir, args.verbose)
        else:
            print(f"Unsupported OS: {system}")
            return 4
    except Exception as e:
        print(f"❌ Installation failed: {e}")
        return 5

    print(f"✅ Installed: {installed}")

    if str(installed.parent) not in os.environ.get("PATH", ""):
        print(f"⚠️  Note: {installed.parent} is not in your PATH.")
        if system in ("linux", "darwin"):
            ensure_path_in_shell_profile(installed.parent, args.verbose)
            print("👉 Restart your terminal or run: source ~/.bashrc")
        else:
            print(f"👉 Add it manually to your PATH: {installed.parent}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
