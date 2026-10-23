import difflib
from datetime import datetime
from pathlib import Path

import yaml
from netmiko import ConnectHandler

BASE_DIR = Path(__file__).resolve().parent
BACKUP_DIR = BASE_DIR / "backups"
DIFF_DIR = BASE_DIR / "diffs"

# Lines that change on their own and are not real configuration changes.
# Any line starting with one of these is skipped when comparing.
IGNORE_PREFIXES = (
    "Building configuration",
    "Current configuration",
    "! Last configuration change",
    "! NVRAM config last updated",
    "! No configuration change since last restart",
    "ntp clock-period",
)


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


def find_previous_backup(name, current_path):
    """Return the newest backup of this device older than current_path, or None."""
    all_backups = sorted(BACKUP_DIR.glob(f"{name}_*.cfg"))
    older = [p for p in all_backups if p.name < current_path.name]
    return older[-1] if older else None


def clean_lines(text):
    """Split config text into lines, dropping the noisy ones we ignore."""
    return [line for line in text.splitlines() if not line.startswith(IGNORE_PREFIXES)]


def write_diff(name, old_path, new_path):
    """Compare two backups. If they differ, save a .diff file and return its path."""
    old_lines = clean_lines(old_path.read_text(encoding="utf-8"))
    new_lines = clean_lines(new_path.read_text(encoding="utf-8"))

    diff = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=old_path.name,
            tofile=new_path.name,
            lineterm="",
        )
    )
    if not diff:
        return None

    DIFF_DIR.mkdir(exist_ok=True)
    diff_path = DIFF_DIR / f"{new_path.stem}.diff"
    header = [
        f"# CONFIG CHANGE DETECTED on {name}",
        f"# Previous backup: {old_path.name}",
        f"# Current backup:  {new_path.name}",
        "# Review: was this change authorized?",
        "",
    ]
    diff_path.write_text("\n".join(header + diff) + "\n", encoding="utf-8")
    return diff_path


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

        previous = find_previous_backup(name, filepath)
        if previous is None:
            print("  First backup for this device - nothing to compare yet.")
        else:
            diff_path = write_diff(name, previous, filepath)
            if diff_path is None:
                print("  No changes since previous backup.")
            else:
                print(f"  ALERT: {name} config CHANGED! Diff saved to {diff_path.name}")


if __name__ == "__main__":
    main()