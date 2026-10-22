from datetime import datetime
from pathlib import Path

import yaml
from netmiko import ConnectHandler

BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "backups"


def load_inventory(path=None):
    """Read the YAML inventory file and return the list of devices."""
    if path is None:
        path = BASE_DIR / "devices.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["devices"]


def save_backup(name, config_text):
    """Save a config to backups/<name>_<timestamp>.cfg and return the path."""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = BACKUP_DIR / f"{name}_{timestamp}.cfg"
    if not config_text.endswith("\n"):
        config_text += "\n"
    filepath.write_text(config_text, encoding="utf-8")
    return filepath


def main():
    devices = load_inventory()
    print(f"Loaded {len(devices)} devices from inventory.")

    for entry in devices:
        params = dict(entry)             # copy, so the original stays untouched
        name = params.pop("name")        # remove 'name' from the copy
        command = params.pop("command")  # remove 'command' from the copy

        print(f"Connecting to {name}...")
        with ConnectHandler(**params) as connection:
            output = connection.send_command(command)

        filepath = save_backup(name, output)
        line_count = len(output.splitlines())
        print(f"  OK: {name} returned {line_count} lines, saved to {filepath.name}")


if __name__ == "__main__":
    main()