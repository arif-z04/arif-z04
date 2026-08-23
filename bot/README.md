# 🤖 GitHub Profile SVG Bot

A modular Python background bot that automatically monitors your GitHub profile stats, generates high-detail light & dark mode ASCII profile cards (`light_mode.svg` and `dark_mode.svg`), and pushes updated SVGs to your GitHub repository using SSH.

---

## 🛠️ Features

- **Continuous Background Execution**: Runs as a systemd user service starting automatically on Linux system boot.
- **Dual-Theme SVG Rendering**: Generates both GitHub Light mode (`light_mode.svg`) and Dark mode (`dark_mode.svg`) vector cards.
- **Detailed ASCII Generator**: Uses Pillow image sampling, Sobel edge detection (`|`, `\`, `-`, `/`), luminance normalization, and Floyd-Steinberg dithering for high-detail ASCII art.
- **Automated Git Push**: Stages updated SVGs, creates descriptive commits, and pushes to your remote GitHub repository via SSH.
- **Secured Environment Handling**: Supports optional GitHub Personal Access Token (PAT) via `.env` to elevate API limits (5,000 req/hr) and query author commits.

---

## 📦 Project Structure

```
arif-z04/
├── .env.example            # Environment configuration template
├── .env                    # Local environment config (token, username)
├── .gitignore              # Git ignore configuration
├── light_mode.svg          # Generated Light theme SVG profile card
├── dark_mode.svg           # Generated Dark theme SVG profile card
└── bot/
    ├── __init__.py         # Package initialization
    ├── config.py           # Config loader via python-dotenv
    ├── github_api.py       # GitHub REST API client & uptime calculator
    ├── ascii_generator.py  # High-detail image to ASCII art generator
    ├── svg_renderer.py     # Light and Dark SVG vector card renderer
    ├── git_manager.py      # Git diff monitoring, committing & SSH pushing
    ├── service.py          # Linux Systemd user service installer & manager
    └── main.py             # Main CLI and daemon loop entry point
```

---

## 🚀 Quick Setup & Usage

### 1. Add your GitHub API Token (Optional but Recommended)
Open the `.env` file in the repository root and paste your token:
```env
GITHUB_TOKEN=ghp_your_personal_access_token_here
GITHUB_USERNAME=arif-z04
UPDATE_INTERVAL_HOURS=1
GIT_BRANCH=main
```

### 2. Management Commands

#### Single Update Run (Testing)
Run a single update cycle to verify data fetching and SVG generation:
```bash
python3 -m bot.main --once
```

#### Run in Foreground Daemon Mode
Run the bot continuously in the current terminal window:
```bash
python3 -m bot.main --daemon
```

---

## ⚙️ System Boot Background Service (Systemd)

The bot comes with built-in systemd user service integration so it runs automatically in the background when your computer boots up.

### Install & Enable Service
```bash
python3 -m bot.main --install-service
```

### Check Service Status
```bash
python3 -m bot.main --status
```

### Control Service
```bash
python3 -m bot.main --start-service
python3 -m bot.main --stop-service
python3 -m bot.main --restart-service
```

### View Service Logs
```bash
journalctl --user -u github-profile-bot.service -f
```

### Uninstall Service
```bash
python3 -m bot.main --uninstall-service
```
