import sys
from pathlib import Path

from crudapp.cli import ContactCLI
from crudapp.store import ContactStore


def _ensure_utf8() -> None:
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stdin.encoding and sys.stdin.encoding.lower() != "utf-8":
        sys.stdin.reconfigure(encoding="utf-8")


def main() -> None:
    _ensure_utf8()
    data_path = Path(__file__).parent / "data" / "contacts.json"
    store = ContactStore(data_path)
    ContactCLI(store).run()


if __name__ == "__main__":
    main()
