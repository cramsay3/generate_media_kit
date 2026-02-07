# Fix "Access blocked: This app's request is invalid"

## Quick Fix Steps

### 1. Enable Gmail API
- Go to: https://console.cloud.google.com/apis/library/gmail.googleapis.com?project=ramz-ai-home
- Click **"ENABLE"**

### 2. Configure OAuth Consent Screen
- Go to: https://console.cloud.google.com/apis/credentials/consent?project=ramz-ai-home
- Click **"CONFIGURE CONSENT SCREEN"**
- Choose **"External"** → **"CREATE"**
- Fill required fields:
  - **App name**: `Gmail Draft Creator`
  - **User support email**: Your email
  - **Developer contact**: Your email
- Click **"SAVE AND CONTINUE"**

### 3. Add Scopes
- On Scopes page, click **"ADD OR REMOVE SCOPES"**
- Search for: `gmail.compose`
- Select: `https://www.googleapis.com/auth/gmail.compose`
- Click **"UPDATE"** → **"SAVE AND CONTINUE"**

### 4. Add Test Users (if app is in Testing mode)
- Click **"ADD USERS"**
- Add your Gmail address (the one you'll use)
- Click **"SAVE AND CONTINUE"**
- Click **"BACK TO DASHBOARD"**

### 5. Try Again
```bash
python3 create_email_drafts.py sample_contacts.csv \
    --artist-name "Test" \
    --custom-message "Test" \
    --limit 1
```

## Direct Links (for project: ramz-ai-home)

- **Enable Gmail API**: https://console.cloud.google.com/apis/library/gmail.googleapis.com?project=ramz-ai-home
- **OAuth Consent Screen**: https://console.cloud.google.com/apis/credentials/consent?project=ramz-ai-home
- **Credentials**: https://console.cloud.google.com/apis/credentials?project=ramz-ai-home

## If Still Not Working

1. **Check if Gmail API is enabled**: Look for "Gmail API" in Enabled APIs list
2. **Verify scope is added**: In OAuth consent screen → Scopes, make sure `gmail.compose` is listed
3. **Check test users**: If app is in "Testing" mode, your email must be in test users list
4. **Try incognito/private browser**: Sometimes browser cache causes issues

## Alternative: Use Different Credentials

If you have another Google Cloud project with Gmail API already set up:
1. Download new credentials.json from that project
2. Replace the current credentials.json
3. Run the script again
