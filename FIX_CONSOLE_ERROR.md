# Fix: "Failed to load" Error in Google Cloud Console

This error usually indicates a temporary Google Cloud Console issue or browser problem.

## Quick Fixes

### 1. Try Different Browser/Incognito Mode
- Open an incognito/private window
- Try a different browser (Chrome, Firefox, Edge)
- Clear browser cache and cookies for console.cloud.google.com

### 2. Try Direct API Links Instead

**Enable Gmail API directly:**
```
https://console.cloud.google.com/apis/library/gmail.googleapis.com?project=ramz-ai-home
```

**OAuth Consent Screen (alternative):**
```
https://console.cloud.google.com/apis/credentials/consent?project=ramz-ai-home
```

**All APIs:**
```
https://console.cloud.google.com/apis/dashboard?project=ramz-ai-home
```

### 3. Check if Gmail API is Already Enabled

Run this to check:
```bash
python3 -c "
import subprocess
try:
    result = subprocess.run(['gcloud', 'services', 'list', '--enabled', '--project=ramz-ai-home'], 
                          capture_output=True, text=True, timeout=10)
    if 'gmail' in result.stdout.lower():
        print('Gmail API appears to be enabled')
    else:
        print('Gmail API may not be enabled')
except:
    print('Cannot check via gcloud CLI')
"
```

### 4. Wait and Retry

Sometimes Google Cloud Console has temporary issues. Wait 5-10 minutes and try again.

### 5. Alternative: Create New OAuth Credentials

If the existing credentials are causing issues:

1. Go to: https://console.cloud.google.com/apis/credentials?project=ramz-ai-home
2. Click **"CREATE CREDENTIALS"** > **"OAuth client ID"**
3. Choose **"Desktop app"**
4. Name it: `Gmail Draft Creator`
5. Click **"CREATE"**
6. Download the new credentials.json
7. Replace the current credentials.json

### 6. Check Project Permissions

Make sure you have the right permissions:
- Go to: https://console.cloud.google.com/iam-admin/iam?project=ramz-ai-home
- Verify you have "Owner" or "Editor" role

## Workaround: Use gcloud CLI (if installed)

If you have gcloud CLI installed:

```bash
# Enable Gmail API
gcloud services enable gmail.googleapis.com --project=ramz-ai-home

# List enabled APIs to verify
gcloud services list --enabled --project=ramz-ai-home | grep gmail
```

## Test Without Full Setup

You can test the script in dry-run mode without Gmail API:

```bash
python3 create_email_drafts.py sample_contacts.csv --dry-run --limit 3
```

This will show you what would be created without needing Gmail API setup.
