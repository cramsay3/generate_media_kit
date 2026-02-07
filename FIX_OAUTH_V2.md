# Fix OAuth - If Consent Screen Already Exists

If you see an "Overview" instead of the creation screen, the OAuth consent screen is already configured. Here's what to do:

## Step 1: Check Current Status

When you go to the OAuth consent screen, you should see:
- **Publishing status**: Testing / In production
- **App information**: Name, logo, etc.
- **Scopes**: List of scopes currently configured
- **Test users**: List of authorized test users

## Step 2: Add Gmail Compose Scope

1. On the OAuth consent screen page, look for **"EDIT APP"** button (top right)
2. Click **"EDIT APP"**
3. Go to **"Scopes"** tab (or click "SAVE AND CONTINUE" until you reach Scopes)
4. Click **"ADD OR REMOVE SCOPES"**
5. In the filter/search box, type: `gmail`
6. Check the box for: `https://www.googleapis.com/auth/gmail.compose`
   - Full name: "See, edit, compose, and send email from your Gmail account"
7. Click **"UPDATE"**
8. Click **"SAVE AND CONTINUE"** (or "BACK TO DASHBOARD")

## Step 3: Add Yourself as Test User (if in Testing mode)

1. Still in OAuth consent screen, look for **"Test users"** section
2. Click **"ADD USERS"** or **"EDIT"**
3. Add your Gmail address (the one you'll authenticate with)
4. Click **"ADD"** then **"SAVE"**

## Step 4: Enable Gmail API

1. Go to: https://console.cloud.google.com/apis/library/gmail.googleapis.com?project=ramz-ai-home
2. If you see **"ENABLE"** button, click it
3. If you see **"MANAGE"**, Gmail API is already enabled ✓

## Step 5: Verify Scopes

On the OAuth consent screen Overview, check:
- **Scopes** section should list: `.../auth/gmail.compose`
- If not there, go back to Step 2

## Step 6: Try Again

```bash
python3 create_email_drafts.py sample_contacts.csv \
    --artist-name "Test" \
    --custom-message "Test" \
    --limit 1
```

## If You See "Publishing Status: Testing"

This means the app is in testing mode. You MUST:
1. Add your email to "Test users" list
2. Wait a few minutes after adding
3. Try authentication again

## Alternative: Check What You Actually See

Take a screenshot or describe what you see on the OAuth consent screen page. Common sections:
- **App information** (name, logo, etc.)
- **Scopes** (list of permissions)
- **Test users** (if in testing mode)
- **Publishing status** (Testing/In production)

Let me know what sections you see and I can guide you more specifically!
