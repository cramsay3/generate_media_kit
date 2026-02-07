#!/usr/bin/env python3
"""
Send Gmail messages with rate limiting and proper spacing to avoid spam detection.
"""

import time
import random
from typing import Optional, List, Dict
from googleapiclient.errors import HttpError
from gmail_drafts import GmailDraftCreator


class GmailSender(GmailDraftCreator):
    """
    Send Gmail messages with rate limiting.
    
    Gmail API Limits (Official):
    - 250 quota units per user per second
    - Sending email costs 100 quota units
    - Effective rate: ~2.5 emails/second maximum
    - Daily limits: ~500 emails/day (free Gmail), higher for Workspace
    
    Best Practices:
    - Space emails 30-60 seconds apart for safety
    - Start with small batches (10-20 emails)
    - Monitor bounce/complaint rates
    - Never exceed 100 emails/hour
    """
    
    # Conservative limits to avoid spam detection
    MIN_SECONDS_BETWEEN_EMAILS = 30  # Minimum 30 seconds between emails
    MAX_SECONDS_BETWEEN_EMAILS = 90  # Maximum 90 seconds (randomized)
    MAX_EMAILS_PER_HOUR = 50  # Conservative: 50/hour = ~1 per minute
    MAX_EMAILS_PER_DAY = 200  # Conservative: 200/day (well under 500 limit)
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        super().__init__(credentials_file, token_file)
        self.sent_count_today = 0
        self.sent_count_hour = 0
        self.last_send_time = 0
        self.hour_start_time = time.time()
    
    def send_message(self, to_email: str, subject: str, body: str, 
                    from_email: Optional[str] = None) -> Optional[str]:
        """
        Send a Gmail message (not draft).
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            from_email: Sender email (optional)
        
        Returns:
            Message ID if successful, None otherwise
        """
        if not self.service:
            self.authenticate()
        
        try:
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            import base64
            
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['subject'] = subject
            if from_email:
                message['from'] = from_email
            
            # Add body
            if '<html>' in body.lower() or '<body>' in body.lower() or '<br>' in body.lower():
                msg_text = MIMEText(body, 'html')
            else:
                msg_text = MIMEText(body, 'plain')
            
            message.attach(msg_text)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return sent_message.get('id')
        
        except HttpError as error:
            print(f"Error sending to {to_email}: {error}")
            return None
    
    def _wait_for_rate_limit(self):
        """Wait appropriate time between emails to respect rate limits."""
        current_time = time.time()
        
        # Reset hourly counter if hour has passed
        if current_time - self.hour_start_time >= 3600:
            self.sent_count_hour = 0
            self.hour_start_time = current_time
        
        # Check daily limit
        if self.sent_count_today >= self.MAX_EMAILS_PER_DAY:
            raise Exception(f"Daily limit reached ({self.MAX_EMAILS_PER_DAY} emails/day)")
        
        # Check hourly limit
        if self.sent_count_hour >= self.MAX_EMAILS_PER_HOUR:
            wait_time = 3600 - (current_time - self.hour_start_time)
            if wait_time > 0:
                print(f"Hourly limit reached. Waiting {int(wait_time/60)} minutes...")
                time.sleep(wait_time)
                self.sent_count_hour = 0
                self.hour_start_time = time.time()
        
        # Wait between emails (randomized to appear more natural)
        if self.last_send_time > 0:
            elapsed = current_time - self.last_send_time
            if elapsed < self.MIN_SECONDS_BETWEEN_EMAILS:
                wait_time = self.MIN_SECONDS_BETWEEN_EMAILS - elapsed
                # Add random variation
                wait_time += random.uniform(0, self.MAX_SECONDS_BETWEEN_EMAILS - self.MIN_SECONDS_BETWEEN_EMAILS)
                print(f"Waiting {int(wait_time)} seconds before next email...")
                time.sleep(wait_time)
        
        self.last_send_time = time.time()
    
    def send_messages(self, messages: List[Dict], progress_callback=None) -> List[Dict]:
        """
        Send multiple messages with rate limiting.
        
        Args:
            messages: List of dicts with keys: to_email, subject, body, from_email (optional)
            progress_callback: Optional function called after each send (email, success, message_id)
        
        Returns:
            List of results with 'success', 'message_id', 'to_email', 'error' keys
        """
        results = []
        total = len(messages)
        
        print(f"\nSending {total} emails with rate limiting:")
        print(f"  - Minimum {self.MIN_SECONDS_BETWEEN_EMAILS}s between emails")
        print(f"  - Maximum {self.MAX_EMAILS_PER_HOUR} emails per hour")
        print(f"  - Maximum {self.MAX_EMAILS_PER_DAY} emails per day")
        print(f"  - Estimated time: ~{int(total * (self.MIN_SECONDS_BETWEEN_EMAILS + 30) / 60)} minutes\n")
        
        for i, msg_info in enumerate(messages, 1):
            to_email = msg_info.get('to_email')
            subject = msg_info.get('subject', '')
            body = msg_info.get('body', '')
            from_email = msg_info.get('from_email')
            
            try:
                # Wait for rate limit
                self._wait_for_rate_limit()
                
                # Send message
                print(f"[{i}/{total}] Sending to {to_email}...", end=' ', flush=True)
                message_id = self.send_message(to_email, subject, body, from_email)
                
                if message_id:
                    self.sent_count_today += 1
                    self.sent_count_hour += 1
                    results.append({
                        'success': True,
                        'message_id': message_id,
                        'to_email': to_email,
                        'error': None
                    })
                    print(f"✓ Sent (ID: {message_id[:20]}...)")
                    
                    if progress_callback:
                        progress_callback(to_email, True, message_id)
                else:
                    results.append({
                        'success': False,
                        'message_id': None,
                        'to_email': to_email,
                        'error': 'Failed to send'
                    })
                    print("✗ Failed")
                    
                    if progress_callback:
                        progress_callback(to_email, False, None)
            
            except Exception as e:
                error_msg = str(e)
                results.append({
                    'success': False,
                    'message_id': None,
                    'to_email': to_email,
                    'error': error_msg
                })
                print(f"✗ Error: {error_msg}")
                
                # If daily limit reached, stop
                if 'Daily limit' in error_msg:
                    print(f"\nStopped: {error_msg}")
                    break
        
        successful = sum(1 for r in results if r['success'])
        print(f"\n{'='*60}")
        print(f"Sent {successful}/{total} emails successfully")
        print(f"Remaining daily quota: {self.MAX_EMAILS_PER_DAY - self.sent_count_today}")
        print(f"{'='*60}")
        
        return results


if __name__ == '__main__':
    # Test
    sender = GmailSender()
    sender.authenticate()
    print("Gmail Sender initialized successfully")
