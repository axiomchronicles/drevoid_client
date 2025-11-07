#!/usr/bin/env python3
"""
install.py

Installer that adds a command alias (default: drevoid) for client.py.
Overwrites existing installations automatically.
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


def install_posix(source: Path, name: str, target_dir: Path | None, symlink: bool, verbose: bool) -> Path:
    if target_dir is None:
        candidates = [Path("~/.local/bin").expanduser(), Path("~/bin").expanduser()]
        target_dir = pick_target_dir(candidates) or Path("~/.local/bin").expanduser()
        ensure_dir(target_dir)

    wrapper_path = target_dir / name
    if wrapper_path.exists():
        try:
            wrapper_path.unlink()
        except Exception:
            pass

    if symlink:
        try:
            wrapper_path.symlink_to(source)
            if verbose:
                print(f"Symlinked {wrapper_path} → {source}")
            return wrapper_path
        except OSError:
            pass

    python_bin = Path(sys.executable).resolve()
    wrapper_contents = (
        f"#!{python_bin}\n"
        f'import runpy, sys\nsys.argv[0] = "{source}"\nrunpy.run_path("{source}", run_name="__main__")\n'
    )
    atomic_write(wrapper_path, wrapper_contents)
    if verbose:
        print(f"Installed {wrapper_path} using {python_bin}")
    return wrapper_path


def install_windows(source: Path, name: str, target_dir: Path | None, verbose: bool) -> Path:
    if target_dir is None:
        target_dir = next((d for d in path_dirs_from_env() if d.exists() and os.access(str(d), os.W_OK)), None)
        if target_dir is None:
            target_dir = Path.home() / "bin"
            ensure_dir(target_dir)

    target_py = target_dir / f"{name}.py"
    if target_py.exists():
        try:
            target_py.unlink()
        except Exception:
            pass
    shutil.copy2(source, target_py)
    target_py.chmod(target_py.stat().st_mode | stat.S_IEXEC)

    wrapper_bat = target_dir / f"{name}.bat"
    if wrapper_bat.exists():
        try:
            wrapper_bat.unlink()
        except Exception:
            pass
    bat_contents = "@echo off\r\n" f"\"{sys.executable}\" \"%~dp0\\{name}.py\" %*\r\n"
    atomic_write(wrapper_bat, bat_contents, 0o666)
    if verbose:
        print(f"Copied {source} to {target_py} and created {wrapper_bat}")
    return wrapper_bat


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="install.py")
    p.add_argument("--source", "-s", default=DEFAULT_SOURCE)
    p.add_argument("--name", "-n", default=DEFAULT_NAME)
    p.add_argument("--target-dir", "-t", type=Path, default=None)
    p.add_argument("--symlink", action="store_true")
    p.add_argument("--verbose", "-v", action="store_true")
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
            installed = install_posix(source, name, target_dir, args.symlink, args.verbose)
        else:
            print(f"Unsupported OS: {system}")
            return 4
    except Exception as e:
        print(f"Installation failed: {e}")
        return 5

    print(f"Installed: {installed}")
    if str(installed.parent) not in os.environ.get("PATH", ""):
        print(f"Note: {installed.parent} is not in your PATH.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
