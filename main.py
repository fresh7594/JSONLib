from pathlib import Path

from crudapp.cli import ContactCLI
from crudapp.store import ContactStore


def main() -> None:
    data_path = Path(__file__).parent / "data" / "contacts.json"
    store = ContactStore(data_path)
    ContactCLI(store).run()


if __name__ == "__main__":
    main()
