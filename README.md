<picture>
  <source media="(prefers-color-scheme: dark)" srcset="dark_mode.svg" />
  <source media="(prefers-color-scheme: light)" srcset="light_mode.svg" />
  <img alt="arif-z04's GitHub profile" src="dark_mode.svg" />
</picture>

---

## 🤖 GitHub Profile SVG Generator Bot

This repository features an automated Python bot that continuously updates the light and dark ASCII profile card SVGs above.

### Features
- **Hourly Updates**: Automatically monitors GitHub profile stats, repository stars, language breakdown, and commits.
- **Dual Themes**: Generates both `<source srcset="dark_mode.svg">` and `<source srcset="light_mode.svg">`.
- **System Boot Service**: Runs in the background as a Linux `systemd --user` service.
- **SSH Auto-Push**: Automatically commits and pushes updated SVGs to GitHub.

### Quick Commands

```bash
# Run a single manual update cycle
python3 -m bot.main --once

# Check systemd background boot service status
python3 -m bot.main --status

# View background bot logs
journalctl --user -u github-profile-bot.service -f
```

For full documentation and token setup instructions, see [bot/README.md](file:///home/noir/Documents/GITHUB_REPOS/arif-z04/arif-z04/bot/README.md).