#!/usr/bin/env python3
"""
Send email campaign with throttling to avoid spam detection.
Designed to run with nohup - logs all output to file.
"""

import sys
import random
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from pdf_parser import PDFParser
from template_processor import TemplateProcessor
from gmail_drafts import GmailDraftCreator
from email_validator import EmailValidator
from csv_reader import CSVReader
import yaml
import argparse


# Rate limiting settings (conservative to avoid spam detection)
MIN_SECONDS_BETWEEN_EMAILS = 30  # Minimum delay between emails
MAX_SECONDS_BETWEEN_EMAILS = 90  # Maximum delay (randomized)
MAX_EMAILS_PER_HOUR = 50         # Hourly limit
MAX_EMAILS_PER_DAY = 200         # Daily limit

# Progress file to track sent emails and resume capability
PROGRESS_FILE = 'campaign_progress.json'


def load_config(config_file='config.yaml'):
    """Load configuration from YAML file."""
    config = {}
    config_path = Path(config_file)
    
    if not config_path.exists():
        return config
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"  ⚠ Failed to load config.yaml: {e}")
    
    return config


def load_progress():
    """Load progress from previous run."""
    progress_path = Path(PROGRESS_FILE)
    if not progress_path.exists():
        return {
            'sent_emails': [],
            'failed_emails': [],
            'last_sent_time': None,
            'daily_count': 0,
            'hourly_count': 0,
            'hour_start': None
        }
    
    try:
        with open(progress_path, 'r', encoding='utf-8') as f:
            progress = json.load(f)
            # Reset daily/hourly counts if it's a new day/hour
            now = datetime.now()
            if progress.get('last_sent_time'):
                last_sent = datetime.fromisoformat(progress['last_sent_time'])
                if (now - last_sent).days >= 1:
                    progress['daily_count'] = 0
                if progress.get('hour_start'):
                    hour_start = datetime.fromisoformat(progress['hour_start'])
                    if (now - hour_start).total_seconds() >= 3600:  # 1 hour
                        progress['hourly_count'] = 0
                        progress['hour_start'] = now.isoformat()
            return progress
    except Exception as e:
        print(f"  ⚠ Failed to load progress: {e}")
        return {
            'sent_emails': [],
            'failed_emails': [],
            'last_sent_time': None,
            'daily_count': 0,
            'hourly_count': 0,
            'hour_start': None
        }


def save_progress(progress):
    """Save progress to file."""
    try:
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2)
    except Exception as e:
        print(f"  ⚠ Failed to save progress: {e}")


def filter_by_genres(contact, genre_keywords, exclude_keywords=None):
    """Check if contact genres match any of the specified keywords."""
    if not contact.genres or not genre_keywords:
        return False
    
    genres_lower = contact.genres.lower()
    
    if exclude_keywords:
        for exclude in exclude_keywords:
            if exclude.lower() in genres_lower:
                return False
    
    for keyword in genre_keywords:
        if keyword.lower() in genres_lower:
            return True
    
    return False


def log_message(message, log_file=None):
    """Print and optionally log to file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    if log_file:
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except:
            pass  # Don't fail if logging fails


def calculate_delay(progress):
    """Calculate delay before next email based on rate limits."""
    now = datetime.now()
    
    # Check if we've hit daily limit
    if progress['daily_count'] >= MAX_EMAILS_PER_DAY:
        # Calculate time until next day
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
        delay_seconds = (tomorrow - now).total_seconds()
        return delay_seconds, "daily limit reached"
    
    # Check if we've hit hourly limit
    if progress['hourly_count'] >= MAX_EMAILS_PER_HOUR:
        # Calculate time until next hour
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        delay_seconds = (next_hour - now).total_seconds()
        return delay_seconds, "hourly limit reached"
    
    # Random delay between emails
    delay_seconds = random.uniform(MIN_SECONDS_BETWEEN_EMAILS, MAX_SECONDS_BETWEEN_EMAILS)
    
    # If we just sent an email, ensure minimum delay
    if progress.get('last_sent_time'):
        last_sent = datetime.fromisoformat(progress['last_sent_time'])
        elapsed = (now - last_sent).total_seconds()
        if elapsed < MIN_SECONDS_BETWEEN_EMAILS:
            delay_seconds = MIN_SECONDS_BETWEEN_EMAILS - elapsed
    
    return delay_seconds, None


def main():
    parser = argparse.ArgumentParser(description='Send email campaign with throttling')
    parser.add_argument('--limit', type=int, help='Maximum number of emails to send (default: all)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without sending')
    parser.add_argument('--resume', action='store_true', help='Resume from previous run')
    parser.add_argument('--log-file', default='campaign.log', help='Log file path (default: campaign.log)')
    args = parser.parse_args()
    
    log_file = args.log_file
    
    log_message("=" * 60, log_file)
    log_message("EMAIL CAMPAIGN STARTED", log_file)
    log_message("=" * 60, log_file)
    log_message(f"Log file: {log_file}", log_file)
    log_message(f"Dry run: {args.dry_run}", log_file)
    log_message("", log_file)
    
    # Load config
    config = load_config()
    artist_name = config.get('artist', {}).get('name', 'Charley Ramsay')
    artist_spotify = config.get('artist', {}).get('spotify_link', 'https://open.spotify.com/artist/2s51Onhpd29JvOji1yuCKy?si=TVLfaQxOSz-qw6UQRraMkA')
    artist_instagram = config.get('artist', {}).get('instagram', 'cramsay3')
    artist_website = config.get('artist', {}).get('website', 'https://charleyramsay.com')
    template_file = config.get('files', {}).get('template', 'email_template.md')
    pdf_text = config.get('files', {}).get('pdf_text', 'playlist_contacts.txt')
    credentials = config.get('files', {}).get('credentials', 'credentials.json')
    token = config.get('files', {}).get('token', 'token.json')
    cc_email = config.get('email_settings', {}).get('cc_email', 'charley@ramsays.us')
    
    # Get genre keywords
    genre_keywords = config.get('email', {}).get('genre_keywords', [])
    exclude_genre_keywords = config.get('email', {}).get('exclude_genres', [])
    validate_emails = config.get('email', {}).get('validate_emails', True)
    validation_csv = config.get('email', {}).get('validation_csv')
    
    # Load progress
    progress = load_progress()
    if args.resume:
        log_message(f"Resuming from previous run...", log_file)
        log_message(f"  Already sent: {len(progress['sent_emails'])}", log_file)
        log_message(f"  Failed: {len(progress['failed_emails'])}", log_file)
    
    # Parse PDF contacts
    log_message("Step 1: Parsing playlist contacts...", log_file)
    pdf_parser = PDFParser(pdf_text)
    contacts = pdf_parser.parse()
    contacts_with_email = [c for c in contacts if c.email]
    log_message(f"  ✓ Found {len(contacts_with_email)} contacts with emails", log_file)
    
    # Filter by genres
    log_message("Step 2: Filtering by genres...", log_file)
    genre_filtered = [c for c in contacts_with_email if filter_by_genres(c, genre_keywords, exclude_genre_keywords)]
    log_message(f"  ✓ {len(genre_filtered)} contacts match genre criteria", log_file)
    
    # Validate emails
    validated_contacts = []
    if validate_emails:
        log_message("Step 3: Validating emails...", log_file)
        validator = EmailValidator()
        
        # Load CSV validation if provided
        if validation_csv and Path(validation_csv).exists():
            csv_reader = CSVReader(validation_csv)
            validated_emails = csv_reader.read_validated_emails()
            log_message(f"  ✓ Loaded {len(validated_emails)} validated emails from CSV", log_file)
        else:
            validated_emails = None
        
        for i, contact in enumerate(genre_filtered, 1):
            if i % 50 == 0:
                log_message(f"  Validated {i}/{len(genre_filtered)}...", log_file)
            
            # Check CSV first if available
            if validated_emails and contact.email.lower() in validated_emails:
                validated_contacts.append(contact)
            else:
                result = validator.validate_email(contact.email, check_mx=True, check_disposable=True)
                if result['valid']:
                    validated_contacts.append(contact)
        
        log_message(f"  ✓ {len(validated_contacts)} contacts have valid emails", log_file)
    else:
        validated_contacts = genre_filtered
    
    # Filter out already sent emails
    sent_emails_set = set(progress['sent_emails'])
    failed_emails_set = set(progress['failed_emails'])
    remaining_contacts = [c for c in validated_contacts 
                         if c.email.lower() not in sent_emails_set 
                         and c.email.lower() not in failed_emails_set]
    
    log_message(f"Step 4: Filtering already sent emails...", log_file)
    log_message(f"  ✓ {len(remaining_contacts)} contacts remaining to send", log_file)
    
    if not remaining_contacts:
        log_message("", log_file)
        log_message("No emails to send! All contacts have already been processed.", log_file)
        return
    
    # Apply limit if specified
    if args.limit:
        remaining_contacts = remaining_contacts[:args.limit]
        log_message(f"  ✓ Limited to {len(remaining_contacts)} contacts", log_file)
    
    # Generate email content
    log_message("Step 5: Generating email content...", log_file)
    processor = TemplateProcessor(template_file)
    email_data = []
    
    for contact in remaining_contacts:
        result = processor.process(
            contact,
            artist_name=artist_name,
            artist_spotify_link=artist_spotify,
            artist_instagram=artist_instagram,
            artist_website=artist_website
        )
        email_data.append({
            'contact': contact,
            'to_email': contact.email,
            'subject': result['subject'],
            'body': result['body']
        })
    
    log_message(f"  ✓ Generated {len(email_data)} email templates", log_file)
    log_message("", log_file)
    
    # Authenticate with Gmail
    if not args.dry_run:
        log_message("Step 6: Authenticating with Gmail API...", log_file)
        try:
            gmail_creator = GmailDraftCreator(credentials, token)
            gmail_creator.authenticate()
            log_message("  ✓ Authenticated successfully", log_file)
            log_message(f"  ✓ CC on all emails: {cc_email}", log_file)
        except Exception as e:
            log_message(f"  ✗ Authentication failed: {e}", log_file)
            sys.exit(1)
    else:
        log_message("Step 6: DRY RUN MODE - No authentication needed", log_file)
        gmail_creator = None
    
    log_message("", log_file)
    log_message("=" * 60, log_file)
    log_message("STARTING EMAIL SENDING", log_file)
    log_message(f"Rate limits: {MIN_SECONDS_BETWEEN_EMAILS}-{MAX_SECONDS_BETWEEN_EMAILS}s between emails", log_file)
    log_message(f"Max per hour: {MAX_EMAILS_PER_HOUR}", log_file)
    log_message(f"Max per day: {MAX_EMAILS_PER_DAY}", log_file)
    log_message("=" * 60, log_file)
    log_message("", log_file)
    
    # Send emails with throttling
    successful = []
    failed = []
    skipped = []
    
    for i, email_info in enumerate(email_data, 1):
        contact = email_info['contact']
        to_email = email_info['to_email']
        
        # Check rate limits
        delay, reason = calculate_delay(progress)
        
        if reason:
            if reason == "daily limit reached":
                log_message(f"[{i}/{len(email_data)}] Daily limit reached. Stopping.", log_file)
                break
            elif reason == "hourly limit reached":
                log_message(f"[{i}/{len(email_data)}] Hourly limit reached. Waiting {delay/60:.1f} minutes...", log_file)
                time.sleep(delay)
                progress['hourly_count'] = 0
                progress['hour_start'] = datetime.now().isoformat()
        
        # Wait before sending (except for first email)
        if i > 1:
            log_message(f"[{i}/{len(email_data)}] Waiting {delay:.1f} seconds before next email...", log_file)
            time.sleep(delay)
        
        # Send email
        playlist_name = contact.playlist_name or 'N/A'
        curator_name = contact.curator or 'N/A'
        
        log_message(f"[{i}/{len(email_data)}] Sending to: {to_email}", log_file)
        log_message(f"  Playlist: {playlist_name}", log_file)
        log_message(f"  Curator: {curator_name}", log_file)
        
        if args.dry_run:
            log_message(f"  [DRY RUN] Would send email", log_file)
            successful.append({
                'email': to_email,
                'contact': contact,
                'message_id': 'DRY_RUN'
            })
            progress['sent_emails'].append(to_email.lower())
            progress['daily_count'] += 1
            progress['hourly_count'] += 1
            progress['last_sent_time'] = datetime.now().isoformat()
            if not progress.get('hour_start'):
                progress['hour_start'] = datetime.now().isoformat()
        else:
            try:
                message_id = gmail_creator.send_email(
                    to_email=to_email,
                    subject=email_info['subject'],
                    body=email_info['body'],
                    cc_email=cc_email
                )
                
                if message_id:
                    log_message(f"  ✓ Sent! Message ID: {message_id}", log_file)
                    successful.append({
                        'email': to_email,
                        'contact': contact,
                        'message_id': message_id
                    })
                    progress['sent_emails'].append(to_email.lower())
                    progress['daily_count'] += 1
                    progress['hourly_count'] += 1
                    progress['last_sent_time'] = datetime.now().isoformat()
                    if not progress.get('hour_start'):
                        progress['hour_start'] = datetime.now().isoformat()
                else:
                    log_message(f"  ✗ Failed to send", log_file)
                    failed.append({
                        'email': to_email,
                        'contact': contact,
                        'error': 'No message ID returned'
                    })
                    progress['failed_emails'].append(to_email.lower())
                
                # Save progress after each email
                save_progress(progress)
                
            except Exception as e:
                log_message(f"  ✗ Error: {e}", log_file)
                failed.append({
                    'email': to_email,
                    'contact': contact,
                    'error': str(e)
                })
                progress['failed_emails'].append(to_email.lower())
                save_progress(progress)
        
        log_message("", log_file)
    
    # Final summary
    log_message("", log_file)
    log_message("=" * 60, log_file)
    log_message("CAMPAIGN SUMMARY", log_file)
    log_message("=" * 60, log_file)
    log_message(f"Total processed: {len(email_data)}", log_file)
    log_message(f"Successfully sent: {len(successful)}", log_file)
    log_message(f"Failed: {len(failed)}", log_file)
    log_message(f"Daily count: {progress['daily_count']}/{MAX_EMAILS_PER_DAY}", log_file)
    log_message(f"Hourly count: {progress['hourly_count']}/{MAX_EMAILS_PER_HOUR}", log_file)
    log_message("", log_file)
    
    if failed:
        log_message("Failed emails:", log_file)
        for f in failed[:10]:  # Show first 10 failures
            log_message(f"  - {f['email']}: {f.get('error', 'Unknown error')}", log_file)
        if len(failed) > 10:
            log_message(f"  ... and {len(failed) - 10} more", log_file)
    
    log_message("", log_file)
    log_message("Progress saved to: campaign_progress.json", log_file)
    log_message("Run with --resume to continue from where you left off", log_file)
    log_message("=" * 60, log_file)


if __name__ == '__main__':
    main()
