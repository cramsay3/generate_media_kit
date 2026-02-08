#!/usr/bin/env python3
"""
Check Gmail inbox for bounce/failure messages and organize them.
Extracts failed email addresses and creates a report.
"""

import os
import re
import json
import base64
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import csv

# Use the same scopes as gmail_drafts.py to reuse existing token
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send'
]


class BounceChecker:
    """Check Gmail for bounce/failure messages."""
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json', gmail_service=None):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = gmail_service  # Can reuse existing service
    
    def authenticate(self):
        """Authenticate with Gmail API - reuse existing service or create new one."""
        if self.service:
            return self.service
        
        creds = None
        
        if os.path.exists(self.token_file):
            try:
                # Try loading with all scopes
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
            except Exception as e:
                # If that fails, try to load existing token and check scopes
                try:
                    with open(self.token_file, 'r') as f:
                        token_data = json.load(f)
                    existing_scopes = token_data.get('scopes', [])
                    # Use existing scopes if readonly is included
                    if 'https://www.googleapis.com/auth/gmail.readonly' in existing_scopes:
                        creds = Credentials.from_authorized_user_file(self.token_file, existing_scopes)
                    else:
                        # Need to add readonly scope - will require re-auth
                        print("  ⚠ Existing token missing readonly scope, will need to re-authenticate")
                        print("  This will update your token file but won't affect the running campaign.")
                        creds = None
                except:
                    creds = None
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"  ⚠ Token refresh failed: {e}")
                    creds = None
        
        if not creds or not creds.valid:
            if not os.path.exists(self.credentials_file):
                raise FileNotFoundError(f"Credentials file not found: {self.credentials_file}")
            
            print("  Requesting new authentication with required scopes...")
            print("  (This will add readonly scope to your token)")
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, SCOPES)
            creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def search_bounce_messages(self, days_back: int = 7) -> List[Dict]:
        """
        Search for bounce/failure messages in Gmail.
        
        Returns list of message metadata.
        """
        if not self.service:
            self.authenticate()
        
        # Search for bounce-related messages
        # Look for messages from mailer-daemon, postmaster, or containing bounce keywords
        query = (
            f'(from:mailer-daemon OR from:postmaster OR '
            f'subject:"delivery failure" OR subject:"undeliverable" OR '
            f'subject:"delivery status" OR subject:"mail delivery" OR '
            f'subject:"failure notice" OR subject:"returned mail" OR '
            f'subject:"couldn\'t be delivered" OR subject:"wasn\'t delivered" OR '
            f'subject:"address couldn\'t be found") '
            f'newer_than:{days_back}d'
        )
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=500
            ).execute()
            
            messages = results.get('messages', [])
            print(f"Found {len(messages)} potential bounce messages")
            
            return messages
        
        except HttpError as error:
            print(f"Error searching messages: {error}")
            return []
    
    def get_message_details(self, msg_id: str) -> Optional[Dict]:
        """Get full message details including body."""
        if not self.service:
            self.authenticate()
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            return message
        
        except HttpError as error:
            print(f"Error getting message {msg_id}: {error}")
            return None
    
    def extract_failed_email(self, message: Dict) -> Optional[str]:
        """Extract failed email address from bounce message."""
        # Get headers
        headers = message.get('payload', {}).get('headers', [])
        subject = ''
        for header in headers:
            if header['name'].lower() == 'subject':
                subject = header['value']
                break
        
        # Get body
        body_text = self._get_message_body(message)
        
        # Combine subject and body for extraction
        full_text = f"{subject}\n{body_text}"
        
        # Common patterns for failed email addresses
        patterns = [
            r'to[:\s]+<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?',
            r'recipient[:\s]+<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?',
            r'address[:\s]+<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?',
            r'<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?\s+couldn\'t be found',
            r'<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?\s+wasn\'t delivered',
            r'<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?\s+is unable to receive',
            r'<?([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})>?\s+does not exist',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                email = match.group(1).lower().strip()
                # Validate it looks like an email
                if '@' in email and '.' in email.split('@')[1]:
                    return email
        
        # Fallback: look for any email in the message that's not from mailer-daemon
        emails = re.findall(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', full_text)
        for email in emails:
            email_lower = email.lower()
            if 'mailer-daemon' not in email_lower and 'postmaster' not in email_lower:
                return email_lower
        
        return None
    
    def _get_message_body(self, message: Dict) -> str:
        """Extract text body from message."""
        payload = message.get('payload', {})
        body_text = ''
        
        def extract_part(part):
            text = ''
            if part.get('body', {}).get('data'):
                data = part['body']['data']
                try:
                    text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                except:
                    pass
            
            if part.get('parts'):
                for subpart in part['parts']:
                    text += extract_part(subpart)
            
            return text
        
        body_text = extract_part(payload)
        return body_text
    
    def extract_error_reason(self, message: Dict) -> str:
        """Extract error reason from bounce message."""
        body_text = self._get_message_body(message)
        subject = ''
        
        headers = message.get('payload', {}).get('headers', [])
        for header in headers:
            if header['name'].lower() == 'subject':
                subject = header['value']
                break
        
        full_text = f"{subject}\n{body_text}".lower()
        
        # Common error patterns
        if "couldn't be found" in full_text or "could not be found" in full_text:
            return "Address not found"
        elif "doesn't exist" in full_text or "does not exist" in full_text:
            return "Address does not exist"
        elif "unable to receive" in full_text:
            return "Unable to receive mail"
        elif "mailbox full" in full_text or "quota exceeded" in full_text:
            return "Mailbox full"
        elif "rejected" in full_text:
            return "Rejected by server"
        elif "blocked" in full_text:
            return "Blocked"
        elif "spam" in full_text:
            return "Marked as spam"
        else:
            return "Unknown error"
    
    def check_all_bounces(self, days_back: int = 7) -> List[Dict]:
        """Check all bounce messages and extract failed emails."""
        messages = self.search_bounce_messages(days_back)
        failures = []
        
        print(f"Processing {len(messages)} messages...")
        
        for i, msg_meta in enumerate(messages, 1):
            if i % 10 == 0:
                print(f"  Processed {i}/{len(messages)}...")
            
            msg_id = msg_meta['id']
            message = self.get_message_details(msg_id)
            
            if not message:
                continue
            
            failed_email = self.extract_failed_email(message)
            if failed_email:
                error_reason = self.extract_error_reason(message)
                
                # Get date
                headers = message.get('payload', {}).get('headers', [])
                date_str = ''
                for header in headers:
                    if header['name'].lower() == 'date':
                        date_str = header['value']
                        break
                
                failures.append({
                    'email': failed_email,
                    'error_reason': error_reason,
                    'date': date_str,
                    'message_id': msg_id
                })
        
        return failures


def load_campaign_failures() -> List[str]:
    """Load failed emails from campaign progress file."""
    progress_file = Path('campaign_progress.json')
    if not progress_file.exists():
        return []
    
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress = json.load(f)
            return progress.get('failed_emails', [])
    except:
        return []


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Check Gmail for bounce messages and create failure report')
    parser.add_argument('--days', type=int, default=7, help='Days back to search (default: 7)')
    parser.add_argument('--output', default='email_failures.csv', help='Output CSV file (default: email_failures.csv)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("CHECKING GMAIL FOR BOUNCE MESSAGES")
    print("=" * 60)
    print()
    
    # Check Gmail bounces
    checker = BounceChecker()
    print("Authenticating with Gmail...")
    checker.authenticate()
    print("✓ Authenticated")
    print()
    
    print(f"Searching for bounce messages from last {args.days} days...")
    gmail_failures = checker.check_all_bounces(days_back=args.days)
    print(f"✓ Found {len(gmail_failures)} failed email addresses in Gmail")
    print()
    
    # Load campaign failures
    print("Loading campaign progress failures...")
    campaign_failures = load_campaign_failures()
    print(f"✓ Found {len(campaign_failures)} failed emails in campaign progress")
    print()
    
    # Combine and deduplicate
    all_failures = {}
    
    # Add Gmail failures
    for failure in gmail_failures:
        email = failure['email'].lower()
        if email not in all_failures:
            all_failures[email] = {
                'email': email,
                'error_reason': failure['error_reason'],
                'date': failure['date'],
                'source': 'Gmail bounce'
            }
    
    # Add campaign failures
    for email in campaign_failures:
        email_lower = email.lower()
        if email_lower not in all_failures:
            all_failures[email_lower] = {
                'email': email_lower,
                'error_reason': 'Campaign failure',
                'date': '',
                'source': 'Campaign progress'
            }
    
    # Write to CSV
    output_file = Path(args.output)
    print(f"Writing results to {output_file}...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['email', 'error_reason', 'date', 'source'])
        writer.writeheader()
        for failure in sorted(all_failures.values(), key=lambda x: x['email']):
            writer.writerow(failure)
    
    print(f"✓ Wrote {len(all_failures)} unique failed emails to {output_file}")
    print()
    
    # Summary
    print("SUMMARY:")
    print(f"  Total unique failed emails: {len(all_failures)}")
    print(f"  From Gmail bounces: {len(gmail_failures)}")
    print(f"  From campaign progress: {len(campaign_failures)}")
    print()
    
    # Error reason breakdown
    error_counts = {}
    for failure in all_failures.values():
        reason = failure['error_reason']
        error_counts[reason] = error_counts.get(reason, 0) + 1
    
    print("Error breakdown:")
    for reason, count in sorted(error_counts.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")
    
    print()
    print(f"Full report saved to: {output_file}")


if __name__ == '__main__':
    main()
