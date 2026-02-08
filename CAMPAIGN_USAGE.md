# Email Campaign Script Usage

## Overview

The `send_campaign.py` script sends emails with intelligent throttling to avoid spam detection. It's designed to run with `nohup` so it can run in the background.

## Features

- **Throttling**: 30-90 seconds randomized delay between emails
- **Rate Limits**: Max 50 emails/hour, 200 emails/day
- **Progress Tracking**: Saves progress to `campaign_progress.json`
- **Resume Capability**: Can resume from where it left off
- **Logging**: All output logged to file (default: `campaign.log`)
- **CC Support**: Automatically CCs `charley@ramsays.us` on all emails

## Usage

### Basic Usage (Send All Remaining Emails)

```bash
nohup python3 send_campaign.py > campaign_output.txt 2>&1 &
```

### Preview First (Dry Run)

```bash
python3 send_campaign.py --dry-run --limit 10
```

### Send Limited Number

```bash
nohup python3 send_campaign.py --limit 50 > campaign_output.txt 2>&1 &
```

### Resume Previous Run

```bash
nohup python3 send_campaign.py --resume > campaign_output.txt 2>&1 &
```

### Custom Log File

```bash
nohup python3 send_campaign.py --log-file my_campaign.log > campaign_output.txt 2>&1 &
```

## Rate Limiting

The script uses conservative rate limiting to avoid spam detection:

- **30-90 seconds** randomized delay between emails
- **50 emails per hour** maximum
- **200 emails per day** maximum

If limits are reached, the script will automatically wait until the next hour/day before continuing.

## Progress Tracking

The script saves progress to `campaign_progress.json`:
- Tracks which emails have been sent
- Tracks failed emails
- Tracks daily/hourly counts
- Allows resuming from where you left off

## Monitoring

### Check Progress

```bash
# View the log file
tail -f campaign.log

# Check progress file
cat campaign_progress.json

# Check if process is running
ps aux | grep send_campaign
```

### Stop the Campaign

```bash
# Find the process ID
ps aux | grep send_campaign

# Kill the process (replace PID with actual process ID)
kill PID
```

## Time Estimates

Based on rate limits:
- **1 email**: ~30-90 seconds
- **10 emails**: ~5-15 minutes
- **50 emails**: ~25-75 minutes
- **200 emails**: ~1.7-5 hours

## Example Workflow

1. **Test first** (dry run):
   ```bash
   python3 send_campaign.py --dry-run --limit 5
   ```

2. **Start small** (send 10 emails):
   ```bash
   nohup python3 send_campaign.py --limit 10 > campaign_output.txt 2>&1 &
   ```

3. **Monitor progress**:
   ```bash
   tail -f campaign.log
   ```

4. **Send remaining** (if everything looks good):
   ```bash
   nohup python3 send_campaign.py --resume > campaign_output.txt 2>&1 &
   ```

## Files Created

- `campaign.log` - Detailed log of all activity
- `campaign_progress.json` - Progress tracking (for resume)
- `campaign_output.txt` - Standard output/error (if using nohup)

## Troubleshooting

### Script stops unexpectedly
- Check `campaign.log` for errors
- Check Gmail API quota limits
- Verify internet connection

### Want to start fresh
- Delete `campaign_progress.json` to reset progress
- The script will start from the beginning

### Need to change rate limits
- Edit the constants at the top of `send_campaign.py`:
  - `MIN_SECONDS_BETWEEN_EMAILS`
  - `MAX_SECONDS_BETWEEN_EMAILS`
  - `MAX_EMAILS_PER_HOUR`
  - `MAX_EMAILS_PER_DAY`
