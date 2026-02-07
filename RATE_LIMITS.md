# Gmail API Rate Limits & Best Practices

## Official Gmail API Limits

### Quota Limits
- **250 quota units per user per second**
- **Sending email costs 100 quota units**
- **Effective maximum: ~2.5 emails/second** (theoretical)
- **Daily limits:**
  - Free Gmail: ~500 emails/day
  - Google Workspace: Higher limits (varies by plan)

### Why These Limits Matter
- Exceeding limits causes API errors
- Sending too fast triggers spam detection
- Account can be temporarily suspended
- Your domain/IP reputation matters

## Recommended Sending Strategy

### Conservative Approach (Implemented)
- **30-90 seconds between emails** (randomized)
- **Maximum 50 emails per hour**
- **Maximum 200 emails per day**
- **Randomized delays** to appear more natural

### Why This Works
1. **Avoids spam detection**: Natural sending pattern
2. **Stays under API limits**: Well below 500/day
3. **Protects account**: Reduces risk of suspension
4. **Better deliverability**: Gradual sending improves inbox placement

## Implementation Details

### Current Settings (`gmail_sender.py`)
```python
MIN_SECONDS_BETWEEN_EMAILS = 30  # Minimum spacing
MAX_SECONDS_BETWEEN_EMAILS = 90  # Maximum spacing (randomized)
MAX_EMAILS_PER_HOUR = 50         # Hourly limit
MAX_EMAILS_PER_DAY = 200         # Daily limit
```

### Time Estimates
- **1 email**: ~30-90 seconds
- **10 emails**: ~5-15 minutes
- **50 emails**: ~25-75 minutes
- **200 emails**: ~1.7-5 hours

## Usage

### Create Drafts (Safe - No Sending)
```bash
python3 create_email_drafts.py sample_contacts.csv \
    --artist-name "Your Name" \
    --limit 10
```
Review drafts in Gmail before sending.

### Send Emails (With Rate Limiting)
```bash
python3 send_emails.py sample_contacts.csv \
    --artist-name "Your Name" \
    --custom-message "Your message" \
    --limit 10 \
    --confirm
```

### Dry Run (Preview)
```bash
python3 send_emails.py sample_contacts.csv --dry-run
```

## Best Practices

1. **Start Small**: Test with 5-10 emails first
2. **Monitor Results**: Check bounce rates, spam complaints
3. **Warm Up**: If sending to new list, start with 10-20/day
4. **Personalize**: Use custom messages (reduces spam risk)
5. **Respect Recipients**: Only send to people who expect emails
6. **Monitor Account**: Check Gmail for any warnings

## Adjusting Limits

If you need different limits, edit `gmail_sender.py`:

```python
# More aggressive (not recommended)
MIN_SECONDS_BETWEEN_EMAILS = 15
MAX_EMAILS_PER_HOUR = 100

# More conservative (safer)
MIN_SECONDS_BETWEEN_EMAILS = 60
MAX_EMAILS_PER_HOUR = 30
```

## Troubleshooting

### "Daily limit reached"
- Wait 24 hours or reduce daily limit
- Check Google Cloud Console for actual quota

### "Rate limit exceeded"
- Script automatically waits
- Reduce `MAX_EMAILS_PER_HOUR` if persistent

### Emails going to spam
- Reduce sending rate further
- Improve email content (less promotional)
- Warm up account gradually

## Monitoring

Check your sending in:
- Gmail Sent folder
- Google Cloud Console > APIs & Services > Dashboard
- Monitor bounce/complaint rates
