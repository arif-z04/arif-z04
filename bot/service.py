"""
bot.service
~~~~~~~~~~~
Linux Systemd user service management module.
Installs, configures, and controls the background system boot service
(`github-profile-bot.service`).
"""

import logging
from pathlib import Path
import shutil
import subprocess
import sys

from bot.config import Config

logger = logging.getLogger(__name__)

SERVICE_NAME = "github-profile-bot.service"
USER_SYSTEMD_DIR = Path.home() / ".config" / "systemd" / "user"
SERVICE_FILE_PATH = USER_SYSTEMD_DIR / SERVICE_NAME


def get_service_unit_content() -> str:
    """Generates Systemd unit file content with current paths."""
    python_bin = sys.executable
    repo_dir = Config.REPO_DIR

    return f"""[Unit]
Description=GitHub Profile SVG Generator Bot
Documentation=https://github.com/arif-z04/arif-z04
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={repo_dir}
ExecStart={python_bin} -m bot.main --daemon
Restart=always
RestartSec=60
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""


def run_systemctl(args: list[str]) -> subprocess.CompletedProcess:
    """Executes a systemctl user command."""
    cmd = ["systemctl", "--user"] + args
    return subprocess.run(cmd, capture_output=True, text=True)


def install_service() -> bool:
    """
    Installs and enables the Systemd user service for automatic boot execution.
    """
    if not shutil.which("systemctl"):
        logger.error("systemctl command not found. Systemd service installation requires Linux with Systemd.")
        return False

    USER_SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)
    unit_content = get_service_unit_content()

    logger.info("Writing Systemd user service to %s...", SERVICE_FILE_PATH)
    with open(SERVICE_FILE_PATH, "w", encoding="utf-8") as f:
        f.write(unit_content)

    # Reload Systemd daemon
    logger.info("Reloading Systemd user daemon...")
    reload_res = run_systemctl(["daemon-reload"])
    if reload_res.returncode != 0:
        logger.error("Failed to reload systemd daemon: %s", reload_res.stderr)
        return False

    # Enable and start service
    logger.info("Enabling and starting '%s'...", SERVICE_NAME)
    enable_res = run_systemctl(["enable", "--now", SERVICE_NAME])

    if enable_res.returncode == 0:
        print("\n" + "=" * 60)
        print(" SUCCESS: GitHub Profile SVG Bot systemd service installed!")
        print("=" * 60)
        print(f" Service Unit File : {SERVICE_FILE_PATH}")
        print(f" Status Command    : systemctl --user status {SERVICE_NAME}")
        print(f" Logs Command      : journalctl --user -u {SERVICE_NAME} -f")
        print("-" * 60)
        print(" TIP: To ensure the bot runs on boot even before user login, run:")
        print(f"      loginctl enable-linger {Path.home().owner() if hasattr(Path.home(), 'owner') else 'USERNAME'}")
        print("=" * 60 + "\n")
        return True
    else:
        logger.error("Failed to enable systemd service: %s", enable_res.stderr)
        return False


def uninstall_service() -> bool:
    """Stops, disables, and removes the Systemd user service."""
    if not SERVICE_FILE_PATH.exists():
        logger.info("Service unit file %s does not exist.", SERVICE_FILE_PATH)
        return True

    logger.info("Stopping and disabling service '%s'...", SERVICE_NAME)
    run_systemctl(["stop", SERVICE_NAME])
    run_systemctl(["disable", SERVICE_NAME])

    logger.info("Removing service file %s...", SERVICE_FILE_PATH)
    SERVICE_FILE_PATH.unlink()

    run_systemctl(["daemon-reload"])
    logger.info("Service '%s' successfully uninstalled.", SERVICE_NAME)
    return True


def service_status() -> None:
    """Prints the current Systemd user service status."""
    if not SERVICE_FILE_PATH.exists():
        print(f"Service '{SERVICE_NAME}' is NOT installed.")
        return

    res = run_systemctl(["status", SERVICE_NAME])
    print(res.stdout or res.stderr)


def start_service() -> None:
    """Starts the Systemd service."""
    res = run_systemctl(["start", SERVICE_NAME])
    if res.returncode == 0:
        print(f"Service '{SERVICE_NAME}' started.")
    else:
        print(f"Failed to start service: {res.stderr}")


def stop_service() -> None:
    """Stops the Systemd service."""
    res = run_systemctl(["stop", SERVICE_NAME])
    if res.returncode == 0:
        print(f"Service '{SERVICE_NAME}' stopped.")
    else:
        print(f"Failed to stop service: {res.stderr}")


def restart_service() -> None:
    """Restarts the Systemd service."""
    res = run_systemctl(["restart", SERVICE_NAME])
    if res.returncode == 0:
        print(f"Service '{SERVICE_NAME}' restarted.")
    else:
        print(f"Failed to restart service: {res.stderr}")
