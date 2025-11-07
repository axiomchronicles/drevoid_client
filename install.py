#!/usr/bin/env python3
"""
install.py

Cross-platform installer that creates a global alias (default: 'drevoid')
to run your Python client script (default: start_client.py) from anywhere.

✅ Overwrites existing installations automatically.
✅ Embeds the correct absolute path to the client script.
✅ Works on Linux, macOS, and Windows.
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

# Template for the installed launcher on POSIX and Windows (.py)
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


def is_executable_dir(path: Path) -> bool:
    try:
        return path.exists() and os.access(str(path), os.W_OK | os.X_OK)
    except Exception:
        return False


def path_dirs_from_env() -> list[Path]:
    sep = ";" if os.name == "nt" else ":"
    return [Path(p).expanduser() for p in os.environ.get("PATH", "").split(sep) if p]


def pick_target_dir(preferred: list[Path] | None = None) -> Path | None:
    if preferred:
        for p in preferred:
            if is_executable_dir(p.expanduser()):
                return p.expanduser()
    for d in path_dirs_from_env():
        if is_executable_dir(d):
            return d
    return None


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def atomic_write(path: Path, data: str, mode: int = 0o755) -> None:
    ensure_dir(path.parent)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def install_posix(source: Path, name: str, target_dir: Path | None, verbose: bool) -> Path:
    if target_dir is None:
        candidates = [Path("~/.local/bin").expanduser(), Path("~/bin").expanduser()]
        target_dir = pick_target_dir(candidates) or Path("~/.local/bin").expanduser()
        ensure_dir(target_dir)

    wrapper_path = target_dir / name
    if wrapper_path.exists():
        wrapper_path.unlink(missing_ok=True)

    launcher_code = LAUNCHER_TEMPLATE.replace("{CLIENT_PATH}", str(source))
    atomic_write(wrapper_path, launcher_code)
    if verbose:
        print(f"[POSIX] Installed {wrapper_path} → {source}")
    return wrapper_path


def install_windows(source: Path, name: str, target_dir: Path | None, verbose: bool) -> Path:
    if target_dir is None:
        target_dir = next((d for d in path_dirs_from_env() if d.exists() and os.access(str(d), os.W_OK)), None)
        if target_dir is None:
            target_dir = Path.home() / "bin"
            ensure_dir(target_dir)

    target_py = target_dir / f"{name}.py"
    target_bat = target_dir / f"{name}.bat"

    # Remove old ones if exist
    for f in (target_py, target_bat):
        try:
            f.unlink(missing_ok=True)
        except Exception:
            pass

    # Write the launcher with embedded client path
    launcher_code = LAUNCHER_TEMPLATE.replace("{CLIENT_PATH}", str(source))
    atomic_write(target_py, launcher_code)
    target_py.chmod(target_py.stat().st_mode | stat.S_IEXEC)

    # .bat file to run the Python launcher
    bat_contents = f'@echo off\r\n"{sys.executable}" "%~dp0\\{name}.py" %*\r\n'
    atomic_write(target_bat, bat_contents, 0o666)

    if verbose:
        print(f"[WIN] Installed {target_py} and {target_bat} → {source}")
    return target_bat


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="install.py", description="Installer for drevoid client launcher")
    p.add_argument("--source", "-s", default=DEFAULT_SOURCE, help="Path to the client launcher (default: start_client.py)")
    p.add_argument("--name", "-n", default=DEFAULT_NAME, help="Command name to install (default: drevoid)")
    p.add_argument("--target-dir", "-t", type=Path, default=None, help="Optional target directory")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        print(f"Error: source not found: {source}")
        return 2

    name = args.name
    target_dir = args.target_dir.expanduser().resolve() if args.target_dir else None
    system = platform.system().lower()

    try:
        if system == "windows":
            installed = install_windows(source, name, target_dir, args.verbose)
        elif system in ("linux", "darwin"):
            installed = install_posix(source, name, target_dir, args.verbose)
        else:
            print(f"Unsupported OS: {system}")
            return 4
    except Exception as e:
        print(f"Installation failed: {e}")
        return 5

    print(f"✅ Installed: {installed}")
    if str(installed.parent) not in os.environ.get("PATH", ""):
        print(f"⚠️  Note: {installed.parent} is not in your PATH.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
