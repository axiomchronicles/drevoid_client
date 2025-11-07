import pathlib

print(pathlib.Path("./client.py").expanduser().resolve())