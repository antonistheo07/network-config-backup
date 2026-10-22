
import yaml
from netmiko import ConnectHandler


def load_inventory(path="devices.yaml"):
    """Read the YAML inventory file and return the list of devices."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["devices"]


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

        line_count = len(output.splitlines())
        print(f"  OK: {name} returned {line_count} lines of config")


if __name__ == "__main__":
    main()
