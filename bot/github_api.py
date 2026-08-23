"""
bot.github_api
~~~~~~~~~~~~~~
GitHub REST API client module. Fetches user profile metrics, repository statistics,
social accounts, top programming languages, commit search metrics, lines of code (additions/deletions),
VSCode version, age calculation, and contributions with optional OAuth authorization.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import time
import requests

from bot.config import Config

logger = logging.getLogger(__name__)

API_BASE_URL = "https://api.github.com"


@dataclass
class GitHubStats:
    """Dataclass holding normalized GitHub stats and custom profile metrics for SVG generation."""

    login: str
    name: str
    avatar_url: str
    created_at: str
    birthday_age: str
    os_info: str
    vscode_version: str
    location: str | None
    company: str | None
    blog: str | None
    email: str | None
    twitter: str | None
    linkedin: str | None
    facebook: str | None
    discord: str | None
    hobbies_main: str
    hobbies_software: str
    hobbies_hardware: str
    followers: int
    public_repos: int
    stars: int
    languages: list[str]
    commits: int
    contributions: int
    additions: int
    deletions: int
    net_loc: int


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
    clean_str = date_str.replace("Z", "+00:00")
    return datetime.fromisoformat(clean_str)


def calculate_age(birth_date_str: str, now: datetime | None = None) -> str:
    """
    Calculates exact age in years, months, and days from a birthdate string (YYYY-MM-DD).
    Example: '2004-05-04' -> '22 years, 3 months, 19 days'
    """
    try:
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
    except ValueError:
        return "22 years"

    if now is None:
        now = datetime.now(timezone.utc)

    years = now.year - birth_date.year
    months = now.month - birth_date.month
    days = now.day - birth_date.day

    if days < 0:
        months -= 1
        prev_month_year = now.year if now.month > 1 else now.year - 1
        prev_month = now.month - 1 if now.month > 1 else 12
        if prev_month in (1, 3, 5, 7, 8, 10, 12):
            prev_days = 31
        elif prev_month in (4, 6, 9, 11):
            prev_days = 30
        else:
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


def fetch_vscode_version() -> str:
    """
    Fetches the latest official VSCode version from GitHub/VSCode API releases.
    Fallback: '1.98.0'
    """
    url = "https://api.github.com/repos/microsoft/vscode/releases/latest"
    try:
        res = requests.get(url, headers={"User-Agent": Config.USER_AGENT}, timeout=5)
        if res.status_code == 200:
            tag = res.json().get("tag_name", "1.98.0")
            return tag.lstrip("v").strip()
    except Exception as e:
        logger.warning("Failed to fetch VSCode version from website API: %s", e)
    return "1.98.0"


def fetch_social_accounts(username: str, headers: dict[str, str]) -> dict[str, str]:
    """
    Fetches social links listed on user's GitHub profile using GitHub Social Accounts API.
    Returns dictionary mapping provider name to URL or clean handle.
    """
    url = f"{API_BASE_URL}/users/{username}/social_accounts"
    socials = {}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            for item in res.json():
                provider = item.get("provider", "").lower()
                target_url = item.get("url", "")
                if provider and target_url:
                    socials[provider] = target_url
    except Exception as e:
        logger.warning("Failed to fetch social accounts: %s", e)
    return socials


def check_token_expiration(res: requests.Response) -> bool:
    """Checks if response indicates expired or invalid token."""
    if res.status_code in (401, 403):
        res_text = res.text.lower()
        if "bad credentials" in res_text or "token" in res_text or res.status_code == 401:
            logger.error("=" * 60)
            logger.error("⚠️ WARNING: GITHUB TOKEN EXPIRED OR INVALID (HTTP %d)", res.status_code)
            logger.error("The configured GITHUB_TOKEN in '.env' failed authentication.")
            logger.error("Please generate a new token and update your '.env' file!")
            logger.error("=" * 60)
            return True
    return False


def fetch_commit_count(username: str, headers: dict[str, str]) -> int:
    """Fetches total author commits count using GitHub Commit Search API."""
    search_url = f"{API_BASE_URL}/search/commits"
    params = {"q": f"author:{username}", "per_page": 1}
    try:
        res = requests.get(search_url, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get("total_count", 0)
        else:
            check_token_expiration(res)
            return 0
    except Exception as e:
        logger.warning("Failed to fetch commit count: %s", e)
        return 0


def fetch_lines_of_code(username: str, repos: list[dict], headers: dict[str, str]) -> tuple[int, int, int]:
    """
    Calculates total additions (+), deletions (-), and net lines of code (LOC)
    by analyzing contributor statistics across user's public repositories.
    """
    logger.info("Computing Lines of Code metrics (additions & deletions) across repositories...")
    total_additions = 0
    total_deletions = 0

    for repo in repos:
        name = repo.get("name")
        owner = repo.get("owner", {}).get("login", username)

        # Retry loop for async contributor stats (HTTP 202 Accepted)
        for attempt in range(3):
            try:
                stats_res = requests.get(
                    f"{API_BASE_URL}/repos/{owner}/{name}/stats/contributors",
                    headers=headers,
                    timeout=8
                )
                if stats_res.status_code == 200:
                    contributors = stats_res.json()
                    if isinstance(contributors, list):
                        for c in contributors:
                            if c.get("author", {}).get("login") == username:
                                for week in c.get("weeks", []):
                                    total_additions += week.get("a", 0)
                                    total_deletions += week.get("d", 0)
                    break
                elif stats_res.status_code == 202:
                    time.sleep(0.5)
                else:
                    break
            except Exception:
                break

    net_loc = total_additions - total_deletions
    logger.info("Lines of Code computed: +%d additions, -%d deletions, net: %d LOC",
                total_additions, total_deletions, net_loc)
    return total_additions, total_deletions, net_loc


def fetch_stats(username: str | None = None, token: str | None = None) -> GitHubStats:
    """
    Fetches comprehensive stats for the specified user from GitHub REST API and custom configs.
    """
    target_user = username or Config.GITHUB_USERNAME
    auth_token = token or Config.GITHUB_TOKEN
    headers = get_headers(auth_token)

    logger.info("Fetching profile stats for user '%s'...", target_user)

    # 1. Fetch User Base Profile
    user_url = f"{API_BASE_URL}/users/{target_user}"
    res = requests.get(user_url, headers=headers, timeout=10)

    # Token Expiration Check
    if auth_token and check_token_expiration(res):
        logger.info("Retrying request in unauthenticated fallback mode...")
        headers = get_headers(None)
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
        if repo.get("fork", False):
            continue
        lang = repo.get("language")
        if lang:
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

    # Top 5 programming languages
    sorted_langs = sorted(lang_counts.items(), key=lambda item: item[1], reverse=True)
    top_languages = [lang for lang, _ in sorted_langs[:5]]

    # 3. Fetch Social Accounts
    socials = fetch_social_accounts(target_user, headers)
    linkedin_url = socials.get("linkedin")
    facebook_url = socials.get("facebook")

    # Format clean handles for SVG display
    linkedin = linkedin_url.replace("https://www.linkedin.com/in/", "linkedin.com/in/").rstrip("/") if linkedin_url else None
    facebook = facebook_url.replace("https://www.facebook.com/", "facebook.com/").rstrip("/") if facebook_url else None

    # 4. Fetch Commit Count
    commits = fetch_commit_count(target_user, headers)

    # 5. Fetch Lines of Code (additions & deletions)
    additions, deletions, net_loc = fetch_lines_of_code(target_user, repos, headers)

    # 6. Fetch VSCode Version
    vscode_version = fetch_vscode_version()

    # 7. Calculate Age from Birthday
    birthday_age = calculate_age(Config.BIRTHDAY)

    # Total Contributions calculation
    contributions = max(commits + len(repos), user.get("public_repos", 0) + commits)

    stats = GitHubStats(
        login=user["login"],
        name=user.get("name") or user["login"],
        avatar_url=user["avatar_url"],
        created_at=user["created_at"],
        birthday_age=birthday_age,
        os_info=Config.OS_INFO,
        vscode_version=vscode_version,
        location=user.get("location"),
        company=user.get("company"),
        blog=user.get("blog"),
        email=user.get("email"),
        twitter=None,  # User explicitly requested no Twitter
        linkedin=linkedin,
        facebook=facebook,
        discord=Config.DISCORD_HANDLE,
        hobbies_main=Config.HOBBY_MAIN,
        hobbies_software=Config.HOBBY_SOFTWARE,
        hobbies_hardware=Config.HOBBY_HARDWARE,
        followers=user.get("followers", 0),
        public_repos=user.get("public_repos", 0),
        stars=stars,
        languages=top_languages,
        commits=commits,
        contributions=contributions,
        additions=additions,
        deletions=deletions,
        net_loc=net_loc,
    )

    logger.info("Successfully retrieved full profile stats for '%s'", stats.login)
    return stats
