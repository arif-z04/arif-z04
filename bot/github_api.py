"""
bot.github_api
~~~~~~~~~~~~~~
GitHub REST API client module. Fetches user profile metrics, repository statistics,
top programming languages, and total commits with optional OAuth token authorization.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import requests

from bot.config import Config

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.github.com"


@dataclass
class GitHubStats:
    """Dataclass holding normalized GitHub stats for SVG generation."""

    login: str
    name: str
    avatar_url: str
    created_at: str
    location: str | None
    company: str | None
    blog: str | None
    email: str | None
    twitter: str | None
    followers: int
    public_repos: int
    stars: int
    languages: list[str]
    commits: int | None


class GitHubAPIError(Exception):
    """Base exception for GitHub API errors."""
    pass


class GitHubUserNotFound(GitHubAPIError):
    """Raised when the specified GitHub user does not exist."""
    pass


def get_headers(token: str | None = None) -> dict[str, str]:
    """Builds standard headers for GitHub REST API requests."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": Config.USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def parse_iso_datetime(date_str: str) -> datetime:
    """Parses an ISO 8601 UTC timestamp string (e.g. '2022-05-10T14:20:00Z')."""
    # Replace Z with +00:00 for compatibility across Python versions
    clean_str = date_str.replace("Z", "+00:00")
    return datetime.fromisoformat(clean_str)


def account_uptime(created_at_str: str, now: datetime | None = None) -> str:
    """
    Calculates exact account uptime duration in years, months, and days
    from the GitHub account creation timestamp.
    """
    created = parse_iso_datetime(created_at_str)
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    years = now.year - created.year
    months = now.month - created.month
    days = now.day - created.day

    if days < 0:
        months -= 1
        # Get days in previous month
        prev_month_year = now.year if now.month > 1 else now.year - 1
        prev_month = now.month - 1 if now.month > 1 else 12
        # Use simple days per month lookup or calculation
        if prev_month in (1, 3, 5, 7, 8, 10, 12):
            prev_days = 31
        elif prev_month in (4, 6, 9, 11):
            prev_days = 30
        else:
            # Leap year check for Feb
            prev_days = 29 if (prev_month_year % 4 == 0 and (prev_month_year % 100 != 0 or prev_month_year % 400 == 0)) else 28
        days += prev_days

    if months < 0:
        years -= 1
        months += 12

    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    parts.append(f"{days} day{'s' if days != 1 else ''}")

    return ", ".join(parts)


def fetch_commit_count(username: str, headers: dict[str, str]) -> int | None:
    """
    Fetches total author commits count using GitHub Commit Search API.
    Returns None if search limit is exceeded or API request fails.
    """
    search_url = f"{API_BASE_URL}/search/commits"
    params = {"q": f"author:{username}", "per_page": 1}
    try:
        res = requests.get(search_url, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get("total_count", 0)
        else:
            logger.warning(
                "Commit search API returned status %d (Token may be required for commit metrics)",
                res.status_code,
            )
            return None
    except Exception as e:
        logger.warning("Failed to fetch commit count: %s", e)
        return None


def fetch_stats(username: str | None = None, token: str | None = None) -> GitHubStats:
    """
    Fetches comprehensive stats for the specified user from GitHub REST API.
    """
    target_user = username or Config.GITHUB_USERNAME
    auth_token = token or Config.GITHUB_TOKEN
    headers = get_headers(auth_token)

    logger.info("Fetching profile stats for user '%s'...", target_user)

    # 1. Fetch User Base Profile
    user_url = f"{API_BASE_URL}/users/{target_user}"
    res = requests.get(user_url, headers=headers, timeout=10)
    if res.status_code == 404:
        raise GitHubUserNotFound(f"User '{target_user}' not found on GitHub.")
    elif res.status_code != 200:
        raise GitHubAPIError(f"GitHub API Error [{res.status_code}]: {res.text}")

    user = res.json()

    # 2. Fetch User Repositories
    repos_url = f"{API_BASE_URL}/users/{target_user}/repos"
    params = {"per_page": 100, "sort": "pushed"}
    repos_res = requests.get(repos_url, headers=headers, params=params, timeout=10)
    repos = repos_res.json() if repos_res.status_code == 200 else []

    # Calculate total stargazers and language distribution
    stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    
    lang_counts: dict[str, int] = {}
    for repo in repos:
        # Ignore forks for primary language metrics
        if repo.get("fork", False):
            continue
        lang = repo.get("language")
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

    # Top 5 programming languages
    sorted_langs = sorted(lang_counts.items(), key=lambda item: item[1], reverse=True)
    top_languages = [lang for lang, _ in sorted_langs[:5]]

    # 3. Fetch Commit Count (best effort)
    commits = fetch_commit_count(target_user, headers)

    stats = GitHubStats(
        login=user["login"],
        name=user.get("name") or user["login"],
        avatar_url=user["avatar_url"],
        created_at=user["created_at"],
        location=user.get("location"),
        company=user.get("company"),
        blog=user.get("blog"),
        email=user.get("email"),
        twitter=user.get("twitter_username"),
        followers=user.get("followers", 0),
        public_repos=user.get("public_repos", 0),
        stars=stars,
        languages=top_languages,
        commits=commits,
    )

    logger.info("Successfully retrieved profile stats for '%s'", stats.login)
    return stats
