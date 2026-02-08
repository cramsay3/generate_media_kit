#!/usr/bin/env python3
"""
Update campaign progress with failed emails from bounce report.
This will prevent re-sending to addresses that have bounced.
"""

import json
import csv
from pathlib import Path


def load_progress(progress_file='campaign_progress.json'):
    """Load campaign progress."""
    progress_path = Path(progress_file)
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
            return json.load(f)
    except Exception as e:
        print(f"Error loading progress: {e}")
        return {
            'sent_emails': [],
            'failed_emails': [],
            'last_sent_time': None,
            'daily_count': 0,
            'hourly_count': 0,
            'hour_start': None
        }


def save_progress(progress, progress_file='campaign_progress.json'):
    """Save campaign progress."""
    try:
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving progress: {e}")
        return False


def load_failures_from_csv(csv_file='email_failures.csv'):
    """Load failed emails from CSV report."""
    failures_path = Path(csv_file)
    if not failures_path.exists():
        print(f"CSV file not found: {csv_file}")
        return []
    
    failed_emails = []
    try:
        with open(failures_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row.get('email', '').strip().lower()
                if email:
                    failed_emails.append(email)
        return failed_emails
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return []


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Update campaign progress with failed emails')
    parser.add_argument('--csv', default='email_failures.csv', help='CSV file with failures (default: email_failures.csv)')
    parser.add_argument('--progress', default='campaign_progress.json', help='Progress file (default: campaign_progress.json)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("UPDATING CAMPAIGN PROGRESS WITH FAILED EMAILS")
    print("=" * 60)
    print()
    
    # Load failures from CSV
    print(f"Loading failures from {args.csv}...")
    failed_emails = load_failures_from_csv(args.csv)
    print(f"✓ Found {len(failed_emails)} failed emails")
    print()
    
    if not failed_emails:
        print("No failures to add.")
        return
    
    # Load current progress
    print(f"Loading progress from {args.progress}...")
    progress = load_progress(args.progress)
    existing_failed = set(progress.get('failed_emails', []))
    print(f"✓ Current failed emails in progress: {len(existing_failed)}")
    print()
    
    # Add new failures
    new_failures = []
    for email in failed_emails:
        if email not in existing_failed:
            new_failures.append(email)
            existing_failed.add(email)
    
    progress['failed_emails'] = list(existing_failed)
    
    # Save updated progress
    print(f"Adding {len(new_failures)} new failed emails to progress...")
    if save_progress(progress, args.progress):
        print(f"✓ Updated progress file with {len(new_failures)} new failures")
        print(f"  Total failed emails: {len(existing_failed)}")
        print()
        
        if new_failures:
            print("New failures added:")
            for email in sorted(new_failures):
                print(f"  - {email}")
    else:
        print("✗ Failed to save progress")


if __name__ == '__main__':
    main()
