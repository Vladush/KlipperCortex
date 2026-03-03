#!/usr/bin/env python3
import json
import os
import subprocess
import argparse
import sys


def load_connections(config_path):
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
        print(
            "Please copy 'connections.json.example' to 'connections.json' and configure your devices."
        )
        sys.exit(1)

    with open(config_path, "r") as f:
        return json.load(f)


def run_command(cmd, shell=False):
    try:
        if shell:
            subprocess.check_call(cmd, shell=True)
        else:
            subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        sys.exit(1)


def deploy(device, model_path, inference_script):
    user = device.get("user", "pi")
    host = device.get("host")
    port = device.get("port", 22)
    key_file = device.get("id_file")
    target_dir = device.get("target_dir", "/home/pi")
    service_name = device.get("service_name", "klipper-cortex")

    if not host:
        print(f"Skipping device '{device.get('name', 'unnamed')}': No host specified.")
        return

    print(f"Deploying to {device.get('name')} ({host})...")

    ssh_opts = ["-p", str(port), "-o", "StrictHostKeyChecking=no"]
    if key_file:
        ssh_opts.extend(["-i", key_file])

    # 1. Transfer Model
    print("  Transferring model...")
    scp_cmd = ["scp"] + ssh_opts + [model_path, f"{user}@{host}:{target_dir}/"]
    run_command(scp_cmd)

    # 2. Transfer Inference Script
    print("  Transferring inference script...")
    scp_cmd = (
        ["scp"]
        + ssh_opts
        + [inference_script, f"{user}@{host}:{target_dir}/inference_loop.py"]
    )
    run_command(scp_cmd)

    # 3. Create/Update Environment File (Optional, but good practice)
    # We could write an .env file on the remote host, or rely on systemd env vars.
    # For now, we'll assume systemd is handled separately or we restart the service.

    # 4. Restart Service
    print("  Restarting service...")
    ssh_cmd = (
        ["ssh"]
        + ssh_opts
        + [f"{user}@{host}", f"sudo systemctl restart {service_name}"]
    )
    # We use 'run_command' but catch errors in case sudo needs a password or service doesn't exist yet
    try:
        subprocess.check_call(ssh_cmd)
        print("  Service restarted successfully.")
    except subprocess.CalledProcessError:
        print(
            "  Warning: Failed to restart service. It might not be installed or requires sudo password."
        )

    print(f"Deployment to {device.get('name')} complete.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Deploy KlipperCortex to remote printers."
    )
    parser.add_argument(
        "--config",
        default="connections.json",
        help="Path to connections configuration file.",
    )
    parser.add_argument(
        "--model",
        default="models/spaghetti_v2.vmfb",
        help="Path to compiled .vmfb model.",
    )
    parser.add_argument(
        "--script", default="src/inference_loop.py", help="Path to inference script."
    )
    args = parser.parse_args()

    devices = load_connections(args.config)

    if not os.path.exists(args.model):
        print(f"Error: Model file '{args.model}' not found. Did you compile it?")
        sys.exit(1)

    for device in devices:
        deploy(device, args.model, args.script)


if __name__ == "__main__":
    main()
