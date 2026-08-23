"""
bot.config
~~~~~~~~~~
Configuration manager for the GitHub Profile SVG Bot. Loads environment
variables from `.env` and provides validated settings across all modules.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the repository (parent of the 'bot' folder)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file in project root if present
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


class Config:
    """Central configuration class."""

    # Root repository directory path
    REPO_DIR: Path = Path(os.getenv("REPO_DIR", str(BASE_DIR))).resolve()

    # Target GitHub Username
    GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "arif-z04").strip()

    # GitHub Personal Access Token (PAT)
    GITHUB_TOKEN: str | None = (
        os.getenv("GITHUB_TOKEN").strip() if os.getenv("GITHUB_TOKEN") else None
    )

    # Update frequency in hours (default: 1 hour = 3600 seconds)
    UPDATE_INTERVAL_HOURS: float = float(os.getenv("UPDATE_INTERVAL_HOURS", "1"))

    # Remote git branch
    GIT_BRANCH: str = os.getenv("GIT_BRANCH", "main").strip()

    # User Personal Metrics & Custom Information
    BIRTHDAY: str = os.getenv("BIRTHDAY", "2004-05-04").strip()  # May 4, 2004
    OS_INFO: str = os.getenv("OS_INFO", "Linux, Android 16").strip()
    HOBBY_MAIN: str = os.getenv("HOBBY_MAIN", "Sing").strip()
    HOBBY_SOFTWARE: str = os.getenv("HOBBY_SOFTWARE", "Making bots").strip()
    HOBBY_HARDWARE: str = os.getenv("HOBBY_HARDWARE", "Networking modules, Raspberry PI").strip()
    DISCORD_HANDLE: str = os.getenv("DISCORD_HANDLE", "arif.noir").strip()

    # SVG Output File Paths
    LIGHT_SVG_PATH: Path = REPO_DIR / "light_mode.svg"
    DARK_SVG_PATH: Path = REPO_DIR / "dark_mode.svg"

    # User Agent for HTTP API requests
    USER_AGENT: str = f"GitHub-Profile-SVG-Bot/{GITHUB_USERNAME}"

    @classmethod
    def update_interval_seconds(cls) -> float:
        """Returns the update interval in seconds."""
        return max(60.0, cls.UPDATE_INTERVAL_HOURS * 3600.0)

    @classmethod
    def print_summary(cls) -> None:
        """Prints a summary of the active configuration."""
        print("=" * 60)
        print(" GitHub Profile SVG Generator Bot Configuration")
        print("=" * 60)
        print(f" Target Username     : {cls.GITHUB_USERNAME}")
        print(f" Repository Directory: {cls.REPO_DIR}")
        print(f" Birthday (Age Calc) : {cls.BIRTHDAY}")
        print(f" OS / System         : {cls.OS_INFO}")
        print(f" Discord Handle      : {cls.DISCORD_HANDLE}")
        print(f" Light SVG Path      : {cls.LIGHT_SVG_PATH.name}")
        print(f" Dark SVG Path       : {cls.DARK_SVG_PATH.name}")
        print(f" Update Interval     : {cls.UPDATE_INTERVAL_HOURS} hour(s)")
        print(f" Git Branch          : {cls.GIT_BRANCH}")
        print(f" API Token Configured: {'YES' if cls.GITHUB_TOKEN else 'NO (Unauthenticated Mode)'}")
        print("=" * 60)
