# Instagram Browser Automation (Selenium)

## Why Browser Automation?

**The Problem:** `instagrapi` (API-based) is being detected and blocked by Instagram.

**The Solution:** Use Selenium to automate a real browser - much harder to detect!

## Installation

```bash
# Install Selenium
pip install selenium

# Install ChromeDriver
# Option 1: Using apt (Ubuntu/Debian)
sudo apt-get install chromium-chromedriver

# Option 2: Download manually
# Visit: https://chromedriver.chromium.org/downloads
# Download version matching your Chrome version
# Extract and place in PATH
```

## Usage

```bash
# Basic usage
python3 follow_instagram_browser.py --limit 10

# With 2FA code
python3 follow_instagram_browser.py --limit 10 --twofa 123456

# Headless mode (no browser window)
python3 follow_instagram_browser.py --limit 10 --headless
```

## Advantages Over instagrapi

1. **Harder to detect** - Uses real browser, looks like human
2. **Handles 2FA better** - Can see and interact with 2FA prompts
3. **More reliable** - Less likely to be blocked
4. **Visual feedback** - You can see what's happening

## Disadvantages

1. **Slower** - Browser automation is slower than API
2. **More resource intensive** - Uses more CPU/memory
3. **Requires ChromeDriver** - Additional dependency

## Tips

- **Don't run headless** - Instagram may detect headless browsers easier
- **Add delays** - Random delays between actions (already built in)
- **Use sparingly** - Don't follow too many accounts at once
- **Monitor** - Watch the browser to see if anything goes wrong

## If Still Getting Blocked

1. **Login manually first** - Open Instagram in browser, login, then run script
2. **Use different IP** - Try VPN
3. **Reduce limits** - Follow fewer accounts per session
4. **Wait between sessions** - Don't run multiple times per day
