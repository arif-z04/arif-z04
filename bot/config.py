"""
bot.config
~~~~~~~~~~
Configuration manager for the GitHub Profile SVG Bot. Loads environment
variables from `.env` and provides validated settings across all modules.
"""

import os
from pathlib import Path

# Base directory of the repository (parent of the 'bot' folder)
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file in project root if present
ENV_PATH = BASE_DIR / ".env"
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH)
except ImportError:
    # Fallback parser if python-dotenv is not installed
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                    v = v[1:-1]
                os.environ.setdefault(k, v)


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

    # Polling / Status Check interval in seconds (default: 120 seconds = 2 minutes)
    CHECK_INTERVAL_SECONDS: float = float(
        os.getenv(
            "CHECK_INTERVAL_SECONDS",
            os.getenv("POLL_INTERVAL_SECONDS", "120")
        )
    )

    # State file path for tracking last known GitHub record
    STATE_FILE_PATH: Path = REPO_DIR / ".bot_state.json"

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
    def check_interval(cls) -> float:
        """Returns the status check interval in seconds (minimum 10s)."""
        return max(10.0, cls.CHECK_INTERVAL_SECONDS)

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
        print(f" Check Interval      : {cls.check_interval()} seconds")
        print(f" State File          : {cls.STATE_FILE_PATH.name}")
        print(f" Git Branch          : {cls.GIT_BRANCH}")
        print(f" API Token Configured: {'YES' if cls.GITHUB_TOKEN else 'NO (Unauthenticated Mode)'}")
        print("=" * 60)
