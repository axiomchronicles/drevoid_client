#!/usr/bin/env python3
"""
install.py

Detects the host OS (Linux, macOS, Windows) and installs a small wrapper so that
`drevoid` becomes available in the user's PATH and runs your `client.py` from
anywhere.

Usage:
    python install.py [--source /path/to/client.py] [--name drevoid]

Behavior summary:
 - On Linux/macOS: creates an executable wrapper script named `drevoid` in a
   suitable bin directory (prefers ~/.local/bin if available). The wrapper
   executes the system python to run your client script.
 - On Windows: copies the client script to the chosen PATH directory as
   `drevoid.py` and creates a `drevoid.bat` wrapper that calls Python.

The installer will not overwrite an existing installation without prompting.
"""

from __future__ import annotations
import argparse
import os
import platform
import shutil
import stat
import sys
from pathlib import Path


def find_writable_path_dir(preferred_candidates=None):
    """Return first writable dir from PATH or preferred candidates, else None."""
    path_env = os.environ.get("PATH", "")
    sep = ";" if os.name == "nt" else ":"
    path_dirs = [Path(p).expanduser() for p in path_env.split(sep) if p]

    if preferred_candidates:
        for p in preferred_candidates:
            p = Path(p).expanduser()
            if p.exists() and os.access(p, os.W_OK | os.X_OK):
                return p

    for d in path_dirs:
        if d.exists() and os.access(d, os.W_OK | os.X_OK):
            return d

    return None


def ensure_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)


def install_posix(source: Path, name: str) -> Path:
    candidates = [Path("~/.local/bin").expanduser(), Path("~/bin").expanduser()]
    target_dir = find_writable_path_dir(preferred_candidates=candidates)

    if target_dir is None:
        target_dir = Path("~/.local/bin").expanduser()
        try:
            ensure_dir(target_dir)
        except Exception:
            if Path("/usr/local/bin").exists() and os.access("/usr/local/bin", os.W_OK):
                target_dir = Path("/usr/local/bin")
            else:
                raise RuntimeError(
                    "No writable bin directory found. Please create ~/.local/bin and add it to PATH."
                )

    wrapper_path = target_dir / name
    if wrapper_path.exists():
        raise FileExistsError(f"Target {wrapper_path} already exists. Remove it or choose a different name.")

    wrapper_contents = f"""#!/usr/bin/env bash
# Auto-generated wrapper to run your client.py as `{name}`
exec "$(command -v python3 || command -v python)" "{str(source)}" "$@"
"""

    wrapper_path.write_text(wrapper_contents)
    # Make executable
    st = wrapper_path.stat().st_mode
    wrapper_path.chmod(st | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return wrapper_path


def install_windows(source: Path, name: str) -> Path:
    # Find writable PATH dir
    path_dirs = [Path(p).expanduser() for p in os.environ.get("PATH", "").split(";") if p]
    target_dir = None
    for d in path_dirs:
        try:
            d = d.expanduser()
            if d.exists() and os.access(d, os.W_OK):
                target_dir = d
                break
        except Exception:
            continue

    if target_dir is None:
        up = Path.home() / "bin"
        ensure_dir(up)
        target_dir = up

    target_py = target_dir / f"{name}.py"
    if target_py.exists():
        raise FileExistsError(f"Target {target_py} already exists. Remove it or choose a different name.")

    shutil.copy2(source, target_py)

    wrapper_bat = target_dir / f"{name}.bat"
    bat_contents = (
        "@echo off\r\n"
        f"python \"%~dp0\\{name}.py\" %*\r\n"
    )

    wrapper_bat.write_text(bat_contents)

    return wrapper_bat


def main(argv=None):
    parser = argparse.ArgumentParser(description="Install client.py as a global 'drevoid' command")
    parser.add_argument("--source", "-s", default="client.py", help="Path to client.py (default: ./client.py)")
    parser.add_argument("--name", "-n", default="drevoid", help="Command name to create (default: drevoid)")
    args = parser.parse_args(argv)

    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        print(f"Error: source script not found: {source}")
        sys.exit(2)

    name = args.name

    system = platform.system().lower()

    try:
        if system == "windows":
            installed = install_windows(source, name)
        elif system in ("linux", "darwin"):
            installed = install_posix(source, name)
        else:
            raise RuntimeError(f"Unsupported OS: {system}")
    except FileExistsError as e:
        print(str(e))
        print("If you want to overwrite, remove the existing file and run again.")
        sys.exit(3)
    except Exception as e:
        print(f"Installation failed: {e}")
        sys.exit(4)

    print(f"Installed wrapper: {installed}")
    print("If that directory is not on your PATH, add it to run '" + name + "' from anywhere.")


if __name__ == "__main__":
    main()
