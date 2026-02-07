# Troubleshooting: "Access blocked: This app's request is invalid"

This error occurs when Google OAuth is not properly configured. Here's how to fix it:

## Step 1: Enable Gmail API

1. Go to https://console.cloud.google.com/
2. Select project: **ramz-ai-home**
3. Navigate to **APIs & Services** > **Library**
4. Search for **"Gmail API"**
5. Click **"Enable"**

## Step 2: Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **"External"** (unless you have a Google Workspace account)
3. Fill in required fields:
   - **App name**: Gmail Draft Creator (or any name)
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Click **"Save and Continue"**
5. On **Scopes** page:
   - Click **"Add or Remove Scopes"**
   - Search for and add: `https://www.googleapis.com/auth/gmail.compose`
   - Click **"Update"** then **"Save and Continue"**
6. On **Test users** page (if app is in Testing mode):
   - Click **"Add Users"**
   - Add your Gmail address
   - Click **"Save and Continue"**
7. Click **"Back to Dashboard"**

## Step 3: Verify Credentials

1. Go to **APIs & Services** > **Credentials**
2. Find your OAuth 2.0 Client ID
3. Make sure it's set to **"Desktop app"** type
4. The **Authorized redirect URIs** should include: `http://localhost:*`

## Step 4: Test Again

Run the script again:
```bash
python3 create_email_drafts.py sample_contacts.csv \
    --artist-name "Test" \
    --custom-message "Test" \
    --limit 1
```

## Common Issues

### Issue: "App is in testing mode"
**Solution**: Add your email as a test user in OAuth consent screen, OR publish the app (requires verification for external users)

### Issue: "Gmail API not enabled"
**Solution**: Enable Gmail API in API Library (Step 1 above)

### Issue: "Invalid scope"
**Solution**: Make sure scope `https://www.googleapis.com/auth/gmail.compose` is added in OAuth consent screen

### Issue: "Redirect URI mismatch"
**Solution**: The script uses `http://localhost:0` which should work automatically. If not, check credentials configuration.

## Alternative: Use Existing Token

If you have a `token.json` from another project, you can copy it:
```bash
cp /path/to/other/project/token.json .
```

But make sure it was created with Gmail API scopes.
