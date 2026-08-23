# 🔑 How to Generate a GitHub Personal Access Token (PAT)

This guide provides step-by-step instructions for creating a GitHub Personal Access Token to configure your **GitHub Profile SVG Generator Bot**.

---

## 🎯 Why is a Token Recommended?

- **Higher API Rate Limits**: Increases API request quota from **60 requests/hour** (unauthenticated) to **5,000 requests/hour**.
- **Detailed Commit Metrics**: Enables full authorization for GitHub's Search API to query your total author commit counts.

---

## 🛠️ Step-by-Step Guide

### Method 1: Fine-Grained Personal Access Token (Recommended)

Fine-grained tokens provide precise permission control scoped to specific repositories.

1. **Log in to GitHub**: Navigate to [github.com](https://github.com) and log into your account (`arif-z04`).
2. **Open Developer Settings**:
   - Click your profile avatar in the upper-right corner -> **Settings**.
   - Scroll down the left sidebar and click **Developer settings** (at the very bottom).
3. **Navigate to Tokens**:
   - In the left sidebar, expand **Personal access tokens** -> Click **Fine-grained tokens**.
   - Click the **Generate new token** button.
4. **Configure Token Details**:
   - **Token name**: `Profile-SVG-Bot`
   - **Expiration**: Select your preferred expiration period (e.g., `90 days`, `1 year`, or custom).
   - **Description**: `Token for GitHub Profile SVG Generator background bot`.
5. **Set Repository Access**:
   - Under **Repository access**, choose **Only select repositories**.
   - Select your profile repository (`arif-z04`).
6. **Set Permissions**:
   - Expand **Repository permissions**:
     - `Contents`: Set to **Read-only**
     - `Metadata`: Set to **Read-only** (mandatory)
   - Expand **Account permissions**:
     - `User permissions`: Set to **Read-only**
7. **Generate and Copy**:
   - Click **Generate token** at the bottom.
   - ⚠️ **Important**: Copy your token string immediately (`github_pat_xxxxxxxxxxxx...`). It will only be shown once.

---

### Method 2: Personal Access Token (Classic)

Classic tokens are quick to set up and work across all public repositories.

1. Navigate to **GitHub Settings** -> **Developer settings** -> **Personal access tokens** -> **Tokens (classic)**.
2. Click **Generate new token** -> Select **Generate new token (classic)**.
3. Enter Note: `Profile-SVG-Bot`.
4. Choose Expiration: `90 days` or your preference.
5. Select Scopes:
   - ✅ `read:user` (Read all user profile data)
   - ✅ `public_repo` (Access public repositories)
6. Click **Generate token** at the bottom.
7. Copy the token string (`ghp_xxxxxxxxxxxxxxxxxxxx`).

---

## ⚙️ How to Add the Token to Your Bot

Once you have copied your token (`ghp_...` or `github_pat_...`):

### Step 1: Open `.env` File
Open the `.env` file in your repository root directory:
```bash
nano /home/noir/Documents/GITHUB_REPOS/arif-z04/arif-z04/.env
```

### Step 2: Paste Your Token
Update the `GITHUB_TOKEN` line:
```env
GITHUB_TOKEN=ghp_your_copied_token_here
```

### Step 3: Restart the Bot Service
Restart the background systemd service so it picks up the new token:
```bash
python3 -m bot.main --restart-service
```

### Step 4: Verify Token Activation
Check the bot service status or run a single update test:
```bash
python3 -m bot.main --once
```

Look for this line in the output:
```text
API Token Configured: YES
```

---

## 🔒 Security Best Practices

- **Never Commit `.env`**: Your `.env` file contains secret credentials and is automatically ignored by `.gitignore`.
- **Token Scope Minimization**: Only assign `Read-only` access permissions required by the bot.
- **Revocation**: If your token is ever compromised, revoke it immediately at [GitHub Developer Settings](https://github.com/settings/tokens).
