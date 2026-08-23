"""
bot.main
~~~~~~~~
Main entry point for the GitHub Profile SVG Generator Bot.
Supports single-run update mode, background continuous daemon mode,
and Linux Systemd boot service management commands.
"""

import argparse
import logging
import sys
import time

from bot.ascii_generator import fetch_avatar_image, generate_ascii_art
from bot.config import Config
from bot.git_manager import commit_and_push_svgs
from bot.github_api import fetch_stats
from bot.service import (
    install_service,
    restart_service,
    service_status,
    start_service,
    stop_service,
    uninstall_service,
)
from bot.svg_renderer import render_svg_card


def setup_logging() -> None:
    """Configures application-wide logging format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def run_update_cycle() -> bool:
    """
    Executes a complete update cycle:
    1. Fetches metrics from GitHub API.
    2. Downloads avatar image.
    3. Generates high-detail Light and Dark ASCII art.
    4. Renders light_mode.svg and dark_mode.svg.
    5. Saves SVGs to repository root.
    6. Commits and pushes changes via Git/SSH.
    """
    logger = logging.getLogger("bot.main")
    logger.info("Starting profile SVG update cycle...")

    try:
        # 1. Fetch GitHub Statistics
        stats = fetch_stats()

        # 2. Fetch Avatar Image
        avatar_img = fetch_avatar_image(stats.avatar_url)

        # 3. Generate Detailed ASCII Art for Light & Dark themes
        logger.info("Generating light-theme ASCII art...")
        light_ascii = generate_ascii_art(avatar_img, theme="light", cols=100)

        logger.info("Generating dark-theme ASCII art...")
        dark_ascii = generate_ascii_art(avatar_img, theme="dark", cols=100)

        # 4. Render SVGs
        logger.info("Rendering light_mode.svg...")
        light_svg = render_svg_card(stats, light_ascii, theme="light")

        logger.info("Rendering dark_mode.svg...")
        dark_svg = render_svg_card(stats, dark_ascii, theme="dark")

        # 5. Write SVGs to disk
        Config.LIGHT_SVG_PATH.write_text(light_svg, encoding="utf-8")
        logger.info("Saved updated SVG -> %s", Config.LIGHT_SVG_PATH)

        Config.DARK_SVG_PATH.write_text(dark_svg, encoding="utf-8")
        logger.info("Saved updated SVG -> %s", Config.DARK_SVG_PATH)

        # 6. Commit and Push via Git
        commit_and_push_svgs()

        logger.info("Update cycle completed successfully!")
        return True

    except Exception as e:
        logger.error("An error occurred during update cycle: %s", e, exc_info=True)
        return False


def run_daemon_loop() -> None:
    """Runs the bot continuously in a background loop at configured interval."""
    logger = logging.getLogger("bot.main")
    Config.print_summary()

    interval_sec = Config.update_interval_seconds()
    logger.info("Starting background daemon loop (Interval: %s seconds)...", interval_sec)

    try:
        while True:
            start_time = time.time()
            run_update_cycle()
            elapsed = time.time() - start_time
            sleep_time = max(10.0, interval_sec - elapsed)

            logger.info("Sleeping for %.1f seconds until next update...", sleep_time)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("Daemon loop stopped by user (KeyboardInterrupt). Exiting clean.")
        sys.exit(0)


def main() -> None:
    """Main CLI entrypoint."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="GitHub Profile SVG Generator Bot - Automated stats monitoring and SVG generation."
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single update cycle immediately and exit.",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run continuously in background daemon loop every hour.",
    )
    parser.add_argument(
        "--install-service",
        action="store_true",
        help="Install and enable Linux Systemd user service to run on boot.",
    )
    parser.add_argument(
        "--uninstall-service",
        action="store_true",
        help="Uninstall Systemd user boot service.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Display status of the Systemd boot service.",
    )
    parser.add_argument(
        "--start-service",
        action="store_true",
        help="Start the Systemd service.",
    )
    parser.add_argument(
        "--stop-service",
        action="store_true",
        help="Stop the Systemd service.",
    )
    parser.add_argument(
        "--restart-service",
        action="store_true",
        help="Restart the Systemd service.",
    )

    args = parser.parse_args()

    if args.install_service:
        install_service()
    elif args.uninstall_service:
        uninstall_service()
    elif args.status:
        service_status()
    elif args.start_service:
        start_service()
    elif args.stop_service:
        stop_service()
    elif args.restart_service:
        restart_service()
    elif args.once:
        Config.print_summary()
        success = run_update_cycle()
        sys.exit(0 if success else 1)
    elif args.daemon:
        run_daemon_loop()
    else:
        # Default behavior if no flags passed: show help and run once
        Config.print_summary()
        print("\n[NOTE] No mode specified. Running a single update cycle. Use --daemon or --install-service for continuous background execution.\n")
        run_update_cycle()


if __name__ == "__main__":
    main()
