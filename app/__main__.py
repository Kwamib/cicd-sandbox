import sys

from app.visits import clean_name

name = sys.argv[1] if len(sys.argv) > 1 else "  Home "
print(f"{name!r} is counted as {clean_name(name)!r}")
