# Export Instagram Session from Browser

Since instagrapi is being blocked, here's how to export your browser session:

## Method 1: Manual Session Export (Easiest)

1. **Login to Instagram in your browser** (Chrome/Firefox)
2. **Open Developer Tools** (F12)
3. **Go to Application/Storage tab**
4. **Find Cookies** → `instagram.com`
5. **Copy the `sessionid` cookie value**
6. **Save it** - we'll use it in the script

## Method 2: Use Browser Extension

Install a cookie exporter extension to get all Instagram cookies.

## Method 3: Use Browser Automation (Recommended)

Just use `follow_instagram_browser.py` - it logs in through a real browser, so Instagram can't detect it as easily.

## The Real Issue

Instagram is detecting `instagrapi` (the API library) and blocking it, even though:
- Your IP isn't blocked (you can access via browser)
- Your credentials are correct
- 2FA works fine in browser

**Solution:** Use browser automation instead of API calls.
