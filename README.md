# PS99 + Roblox FFlags Discord Change Tracker

This starter project checks:
- Roblox public Windows desktop-client FastFlags.
- BIG Games PS99 public `Eggs` collection.
- BIG Games PS99 public `Pets` collection.

It compares each check with the last saved snapshot and sends Discord webhook embeds for additions, removals, and changes.

## Important limitations

- Roblox FastFlags are Roblox client settings, not PS99 hatch odds.
- The BIG Games public API documents the PS99 `Eggs` and `Pets` configuration collections, but it does not promise a complete live percentage-odds feed. This tracker reports changes to the public egg/pet configuration that the API actually returns. It must not be treated as proof of an exact Huge/Titanic hatch percentage.
- The first run only creates a baseline. Notifications begin when a later run detects a difference.
- GitHub Actions scheduled jobs are periodic, not instant. GitHub may delay scheduled runs.
- Use a public repository if you want standard GitHub-hosted Actions runs to be free. The repository contents are public, so never put secrets in files or commit them.

## Setup

1. Create a Discord webhook in a channel you control:
   - Open the channel settings.
   - Open **Integrations** → **Webhooks** → **New Webhook**.
   - Copy its webhook URL. Keep it private; anyone with it can post to that channel.
2. Create a **public** GitHub repository, for example `ps99-change-tracker`.
3. Upload all project files, keeping `.github/workflows/check.yml` in that exact folder.
4. In GitHub, open **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
   - Name: `DISCORD_WEBHOOK_URL`
   - Value: your Discord webhook URL
5. Optional role ping:
   - Enable Developer Mode in Discord and copy the notification role ID.
   - Add another repository secret named `DISCORD_ROLE_ID` with that ID.
   - Leave it unset if you do not want role pings.
6. Open the repository **Settings** → **Actions** → **General**. Under Workflow permissions, allow read and write permissions so the workflow can save its snapshot.
7. Open **Actions** and enable workflows if GitHub asks.
8. Run **PS99 + FFlags tracker** manually once using **Run workflow**. This saves the baseline. Later scheduled runs send changes.

## Check frequency

The workflow is scheduled every 15 minutes. You can change the cron expression in `.github/workflows/check.yml`.

## Run locally (optional)

```bash
python -m pip install -r requirements.txt
# Set DISCORD_WEBHOOK_URL in your terminal environment first.
python tracker.py
```

Never share your webhook URL, bot token, or repository secrets with anyone.
