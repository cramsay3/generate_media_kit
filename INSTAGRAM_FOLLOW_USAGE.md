# Instagram Following Campaign Guide

This script extracts Instagram handles from your playlist contacts and follows them as part of your campaign outreach.

## ⚠️ Important Warnings

1. **Instagram Terms of Service**: Automated following may violate Instagram's Terms of Service. Use at your own risk.
2. **Account Security**: Your account may be flagged or temporarily restricted if you follow too many accounts too quickly.
3. **Rate Limits**: Instagram has strict rate limits (approximately 20-30 follows/hour, 100-150/day). The script respects these limits.
4. **Two-Factor Authentication**: If you have 2FA enabled, you may need to disable it temporarily or use an app-specific password.

## Installation

Install the required library:

```bash
pip install instagrapi
```

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install instagrapi
   ```

2. **Create `.env` file** (if not already created):
   ```bash
   echo "IG_USERNAME=your_instagram_username" >> .env
   echo "IG_PASSWORD=your_instagram_password" >> .env
   ```
   
   Or edit `.env` directly:
   ```
   IG_USERNAME=cramsay3@gmail.com
   IG_PASSWORD=your_password_here
   ```

## Usage

### Basic Usage (using .env file)

```bash
python3 follow_instagram.py
```

The script will automatically load credentials from `.env` file.

### Options

- `--username`: Override Instagram username from .env (optional)
- `--password`: Override Instagram password from .env (optional)
- `--dry-run`: Preview what would be followed without actually following (recommended first)
- `--resume`: Resume from previous progress (uses `instagram_progress.json`)
- `--limit N`: Limit to first N accounts (useful for testing)
- `--config PATH`: Path to config file (default: `config.yaml`)

### Examples

**Dry run (recommended first):**
```bash
python3 follow_instagram.py --dry-run --limit 5
```

**Follow first 10 accounts:**
```bash
python3 follow_instagram.py --limit 10
```

**Resume from previous run:**
```bash
python3 follow_instagram.py --resume
```

**Run in background:**
```bash
nohup python3 follow_instagram.py > instagram_output.log 2>&1 &
```

**Override credentials (if needed):**
```bash
python3 follow_instagram.py --username other_account --password other_password
```

## Configuration

Throttling settings are in `config.yaml` under the `instagram` section:

```yaml
instagram:
  min_delay_seconds: 60      # Minimum delay between follows
  max_delay_seconds: 180     # Maximum delay (randomized)
  max_per_hour: 20           # Maximum follows per hour
  max_per_day: 100           # Maximum follows per day
```

The script automatically applies the same genre filtering as your email campaign (from `email.genre_keywords` and `email.exclude_genres`).

## Progress Tracking

The script saves progress to `instagram_progress.json`:
- `followed`: List of successfully followed usernames
- `failed`: List of failed usernames with errors
- `skipped`: List of skipped usernames (already following, etc.)
- Rate limit counters

## Logging

All activity is logged to `instagram_follow.log` with timestamps.

## How It Works

1. **Extract Instagram Handles**: Parses contacts and extracts Instagram usernames from URLs
2. **Genre Filtering**: Applies the same genre filters as your email campaign
3. **Rate Limiting**: Respects Instagram's rate limits with automatic delays
4. **Progress Tracking**: Saves progress so you can resume if interrupted
5. **Error Handling**: Handles rate limits, challenges, and other errors gracefully

## Troubleshooting

### "Challenge Required" Error
Instagram may require additional verification. Try:
1. Logging into Instagram manually in a browser
2. Completing any verification steps
3. Running the script again

### Rate Limiting
If you hit rate limits:
1. The script will automatically wait and retry
2. You can resume later with `--resume`
3. Consider reducing `max_per_hour` in config.yaml

### Login Failures

**IP Blacklisted Error:**
If you see "IP address is added to the blacklist":
1. **Wait 24-48 hours** - Instagram will unblock your IP automatically
2. **Use a VPN** - Change your IP address
3. **Log in manually first** - Open Instagram in a browser and complete any security checks
4. **Complete challenges** - Instagram may require email verification or other checks

**Invalid Credentials:**
- Verify username/password in `.env` file
- Make sure you can log in manually in a browser
- **Disable 2FA** - Instagram automation requires 2FA to be disabled
- Check for typos in credentials

**Challenge Required:**
- Log into Instagram manually in a browser
- Complete any security verification steps
- Wait a few hours before trying again

**Session Saved:**
The script saves your session to `instagram_session.json` to avoid repeated logins. If you get login errors, delete this file and try again.

## Safety Tips

1. **Start Small**: Use `--limit 5` or `--dry-run` first
2. **Monitor Your Account**: Check Instagram regularly for any warnings
3. **Respect Limits**: Don't modify the config to exceed Instagram's limits
4. **Use Separate Account**: Consider using a separate Instagram account for campaigns
5. **Space Out Campaigns**: Don't run multiple campaigns back-to-back

## Integration with Email Campaign

This script works alongside your email campaign:
- Uses the same contact list (`playlist_contacts.txt`)
- Applies the same genre filtering
- Can be run before, during, or after sending emails
- Progress is tracked separately from email campaign progress
