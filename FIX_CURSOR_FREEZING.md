# Fix Cursor Freezing Issues

## Current Issues Found:

1. **Memory Pressure**: 10GB/15GB used, swap is full (511MB)
2. **Large Files**: 
   - `playlist_contacts.txt` (564KB, 32,959 lines)
   - `campaign.log` (79KB, 1,500 lines)
   - Large image files and PDFs
3. **Files Being Indexed**: Cursor may be trying to index large files

## Immediate Fixes:

### 1. Close Large Files
If you have these files open, **CLOSE THEM**:
- `playlist_contacts.txt` (32K lines!)
- `campaign.log` (1.5K lines)
- Any `.jpg`, `.png`, `.pdf` files
- `campaign_progress.json`

### 2. Restart Cursor
```bash
# Kill Cursor completely
pkill -f cursor

# Wait 5 seconds, then reopen
```

### 3. Clear Log Files (Optional)
```bash
# Truncate large log files (keeps last 100 lines)
tail -100 campaign.log > campaign.log.tmp && mv campaign.log.tmp campaign.log
tail -100 instagram_follow.log > instagram_follow.log.tmp && mv instagram_follow.log.tmp instagram_follow.log
```

### 4. Free Up Memory
```bash
# Check what's using memory
ps aux --sort=-%mem | head -10

# Kill unnecessary processes if needed
```

## Updated .cursorignore

I've updated `.cursorignore` to exclude:
- All image files (*.jpg, *.jpeg, *.png)
- PDF files (*.pdf)
- All log files (*.log)
- All CSV files (*.csv)
- Progress JSON files
- Session files

**Restart Cursor** after the .cursorignore update for it to take effect.

## Prevention:

1. **Don't open large files** - Use `head` or `tail` in terminal instead
2. **Close unused tabs** - Keep only files you're actively editing open
3. **Use terminal for logs** - `tail -f campaign.log` instead of opening in editor
4. **Rotate logs** - Clear old log files periodically

## If Still Freezing:

1. **Check Cursor logs**:
   - Look for error messages in Cursor's developer console
   - Check system logs: `journalctl -u cursor` (if systemd)

2. **Reduce workspace scope**:
   - Open only the specific folder you need
   - Don't open the entire project root

3. **Update Cursor**:
   - Make sure you're on the latest version
   - Check for updates

4. **System resources**:
   - Close other applications
   - Free up RAM
   - Consider increasing swap space if needed

## Quick Commands:

```bash
# View large files
find . -type f -size +100k -not -path "./.git/*" | head -20

# Check memory
free -h

# Check disk space
df -h

# View Cursor processes
ps aux | grep cursor
```
