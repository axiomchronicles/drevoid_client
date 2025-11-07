#!/usr/bin/env python3
import sys
import os
import traceback
from pathlib import Path
import importlib.util

def main():
    try:
        client_path_str = os.environ.get("DREVOID_CLIENT_PATH", None)
        if not client_path_str:
            client_path_str = "{{CLIENT_PATH_PLACEHOLDER}}"

        if client_path_str == "{{CLIENT_PATH_PLACEHOLDER}}":
            project_root = Path(__file__).resolve().parent
            client_path = project_root / "client.py"
        else:
            client_path = Path(client_path_str).expanduser().resolve()

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
