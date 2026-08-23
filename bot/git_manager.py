"""
bot.git_manager
~~~~~~~~~~~~~~~
Git repository manager. Monitors SVG file modifications, creates git commits,
and pushes updated SVGs to the GitHub remote repository using SSH authentication.
"""

from datetime import datetime
import hashlib
import logging
from pathlib import Path
import subprocess

from bot.config import Config

logger = logging.getLogger(__name__)


def compute_file_hash(filepath: Path) -> str | None:
    """Computes SHA-256 hash of a file to check for content modifications."""
    if not filepath.exists():
        return None
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_git_cmd(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    """Runs a git command in the repository directory and returns execution results."""
    cmd = ["git"] + args
    logger.debug("Executing git command: %s", " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def has_git_changes(repo_dir: Path, files: list[Path]) -> bool:
    """Checks if specified files have uncommitted changes or untracked state."""
    rel_paths = [str(f.relative_to(repo_dir)) for f in files if f.exists()]
    if not rel_paths:
        return False

    # Check status for modifications
    res = run_git_cmd(["status", "--porcelain"] + rel_paths, cwd=repo_dir)
    if res.returncode == 0 and res.stdout.strip():
        return True

    return False


def commit_and_push_svgs() -> bool:
    """
    Stages light_mode.svg and dark_mode.svg, commits changes if any exist,
    and pushes the update to the remote repository.

    Returns True if changes were successfully committed and pushed, False otherwise.
    """
    repo_dir = Config.REPO_DIR
    light_path = Config.LIGHT_SVG_PATH
    dark_path = Config.DARK_SVG_PATH
    branch = Config.GIT_BRANCH

    svg_files = [light_path, dark_path]

    if not has_git_changes(repo_dir, svg_files):
        logger.info("No SVG file changes detected. Skipping git commit and push.")
        return False

    logger.info("SVG updates detected! Staging files for git commit...")

    # Stage files
    rel_files = [str(f.relative_to(repo_dir)) for f in svg_files if f.exists()]
    add_res = run_git_cmd(["add"] + rel_files, cwd=repo_dir)
    if add_res.returncode != 0:
        logger.error("Failed to stage SVG files: %s", add_res.stderr)
        return False

    # Create Commit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"docs: update profile stats SVGs [auto] ({timestamp})"
    commit_res = run_git_cmd(["commit", "-m", commit_msg], cwd=repo_dir)

    if commit_res.returncode != 0:
        logger.warning("Git commit returned status %d: %s", commit_res.returncode, commit_res.stderr)
        return False

    logger.info("Created git commit: '%s'", commit_msg)

    # Push to remote using SSH key
    logger.info("Pushing committed SVGs to origin/%s...", branch)
    push_res = run_git_cmd(["push", "origin", branch], cwd=repo_dir)

    if push_res.returncode == 0:
        logger.info("Successfully pushed SVG updates to remote origin/%s!", branch)
        return True
    else:
        logger.error("Git push failed! Standard Error: %s", push_res.stderr)
        return False
