# Cursor Freezing Troubleshooting

If Cursor keeps freezing or crashing, try these solutions:

## Quick Fixes

### 1. Exclude Large/Log Files
Large log files and data files can cause Cursor to freeze. They're already in `.cursorignore`:
- `*.log` - All log files
- `playlist_contacts.txt` - Large contact list
- `campaign_progress.json` - Progress tracking
- `campaign_output.txt` - Campaign output

### 2. Close Large Files
If you have `campaign.log` or `playlist_contacts.txt` open, close them. These files are large and can cause performance issues.

### 3. Restart Cursor
Sometimes a simple restart fixes temporary issues:
- Close Cursor completely
- Reopen the project

### 4. Check System Resources
```bash
# Check memory usage
free -h

# Check disk space
df -h

# Check if any Python processes are consuming resources
ps aux | grep python
```

### 5. Reduce File Watching
If you have many files, Cursor may be watching too many:
- Close unused file tabs
- Use `.cursorignore` to exclude unnecessary files
- Don't open the entire project root if you only need specific folders

## Common Causes

1. **Large Log Files**: `campaign.log` (79KB+) can slow down indexing
2. **Large Data Files**: `playlist_contacts.txt` (564KB) is excluded but may still cause issues if opened
3. **Too Many Open Files**: Having many file tabs open
4. **Background Processes**: Long-running Python scripts consuming resources
5. **Memory Issues**: System running low on RAM

## Prevention

1. **Use `.cursorignore`**: Already configured for large files
2. **Rotate Logs**: Consider rotating or truncating large log files periodically
3. **Close Unused Tabs**: Don't keep large files open unnecessarily
4. **Monitor Resources**: Keep an eye on system memory and CPU

## If Still Freezing

1. **Check Cursor Logs**: Look for error messages in Cursor's developer console
2. **Disable Extensions**: Some extensions can cause conflicts
3. **Update Cursor**: Make sure you're on the latest version
4. **Report Issue**: If persistent, report to Cursor support with:
   - System info (OS, RAM, CPU)
   - Cursor version
   - What you were doing when it froze
   - Any error messages

## Workaround: Use Terminal

If Cursor keeps freezing, you can run scripts directly in terminal:

```bash
# Run campaign in background
nohup python3 send_campaign.py --resume > campaign_output.txt 2>&1 &

# Monitor progress
tail -f campaign.log

# Check status
ps aux | grep send_campaign
```
