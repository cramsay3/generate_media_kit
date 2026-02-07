#!/usr/bin/env python3
"""
Create Gmail drafts using Gmail API.
"""

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailDraftCreator:
    """Create Gmail drafts using the Gmail API."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.compose', 'https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
    
    def authenticate(self):
        """Authenticate with Gmail API."""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        "Please download credentials.json from Google Cloud Console:\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Create a project or select existing one\n"
                        "3. Enable Gmail API\n"
                        "4. Create OAuth 2.0 credentials\n"
                        "5. Download as credentials.json"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('gmail', 'v1', credentials=creds)
        return self.service
    
    def create_draft(self, to_email: str, subject: str, body: str, 
                    from_email: Optional[str] = None) -> Optional[str]:
        """
        Create a Gmail draft.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            from_email: Sender email (optional, uses authenticated account if not provided)
        
        Returns:
            Draft ID if successful, None otherwise
        """
        if not self.service:
            self.authenticate()
        
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['subject'] = subject
            if from_email:
                message['from'] = from_email
            
            # Detect if body is HTML
            is_html = '<html>' in body.lower() or '<body>' in body.lower() or '<p>' in body.lower() or '<strong>' in body.lower() or '<a href' in body.lower()
            
            if is_html:
                # IMPORTANT: HTML part must come FIRST in multipart/alternative
                # Gmail prefers HTML as the primary content type
                
                # Create HTML part with explicit headers - attach FIRST
                msg_html = MIMEText(body, 'html', 'utf-8')
                msg_html.set_charset('utf-8')
                # Remove any existing Content-Type and set explicitly
                if 'Content-Type' in msg_html:
                    del msg_html['Content-Type']
                msg_html.add_header('Content-Type', 'text/html; charset=utf-8')
                msg_html.add_header('Content-Transfer-Encoding', 'quoted-printable')
                
                # Create minimal plain text version (Gmail fallback)
                # Strip HTML tags but keep it minimal so Gmail prefers HTML
                import re
                plain_body = re.sub(r'<[^>]+>', '', body)
                plain_body = re.sub(r'\s+', ' ', plain_body).strip()
                plain_body = re.sub(r'\*\*', '', plain_body)  # Remove any remaining markdown
                
                msg_plain = MIMEText(plain_body, 'plain', 'utf-8')
                msg_plain.set_charset('utf-8')
                msg_plain.add_header('Content-Type', 'text/plain; charset=utf-8')
                
                # Attach HTML FIRST (Gmail will use this as primary)
                message.attach(msg_html)
                # Then attach plain text as fallback (minimal)
                message.attach(msg_plain)
            else:
                # Plain text only
                msg_text = MIMEText(body, 'plain', 'utf-8')
                msg_text.add_header('Content-Type', 'text/plain; charset=utf-8')
                message.attach(msg_text)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Debug: Check message structure
            if is_html:
                msg_bytes = message.as_bytes()
                msg_str = msg_bytes.decode('utf-8', errors='ignore')
                if 'Content-Type: text/html' not in msg_str:
                    print("WARNING: HTML Content-Type not found in message structure")
            
            # Create draft
            draft = self.service.users().drafts().create(
                userId='me',
                body={'message': {'raw': raw_message}}
            ).execute()
            
            return draft.get('id')
        
        except HttpError as error:
            print(f"An error occurred creating draft: {error}")
            return None
    
    def create_drafts_batch(self, drafts_data: List[dict]) -> List[dict]:
        """
        Create multiple drafts in batch.
        
        Args:
            drafts_data: List of dicts with keys: to_email, subject, body, from_email (optional)
        
        Returns:
            List of results with 'success', 'draft_id', 'to_email', 'error' keys
        """
        results = []
        
        for draft_info in drafts_data:
            to_email = draft_info.get('to_email')
            subject = draft_info.get('subject', '')
            body = draft_info.get('body', '')
            from_email = draft_info.get('from_email')
            
            draft_id = self.create_draft(to_email, subject, body, from_email)
            
            if draft_id:
                results.append({
                    'success': True,
                    'draft_id': draft_id,
                    'to_email': to_email,
                    'error': None
                })
            else:
                results.append({
                    'success': False,
                    'draft_id': None,
                    'to_email': to_email,
                    'error': 'Failed to create draft'
                })
        
        return results
    
    def send_email(self, to_email: str, subject: str, body: str, 
                   from_email: Optional[str] = None) -> Optional[str]:
        """
        Send an email directly (not a draft).
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            from_email: Sender email (optional, uses authenticated account if not provided)
        
        Returns:
            Message ID if successful, None otherwise
        """
        if not self.service:
            self.authenticate()
        
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['to'] = to_email
            message['subject'] = subject
            if from_email:
                message['from'] = from_email
            
            # Detect if body is HTML - check for DOCTYPE, html tags, or common HTML elements
            is_html = ('<!DOCTYPE' in body.upper() or 
                      '<html>' in body.lower() or 
                      '<body>' in body.lower() or 
                      '<p>' in body.lower() or 
                      '<strong>' in body.lower() or 
                      '<a href' in body.lower() or
                      '<div' in body.lower())
            
            if is_html:
                # Force HTML-only email - don't include plain text fallback
                # This ensures Gmail always displays HTML
                msg_html = MIMEText(body, 'html', 'utf-8')
                msg_html.set_charset('utf-8')
                # Remove any existing Content-Type and set explicitly
                if 'Content-Type' in msg_html:
                    del msg_html['Content-Type']
                msg_html.add_header('Content-Type', 'text/html; charset=utf-8')
                msg_html.add_header('Content-Transfer-Encoding', 'quoted-printable')
                
                # Attach HTML ONLY - no plain text fallback to force HTML rendering
                message.attach(msg_html)
            else:
                # Plain text only
                msg_text = MIMEText(body, 'plain', 'utf-8')
                msg_text.add_header('Content-Type', 'text/plain; charset=utf-8')
                message.attach(msg_text)
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send email
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return sent_message.get('id')
        
        except HttpError as error:
            print(f"An error occurred sending email: {error}")
            return None


if __name__ == '__main__':
    # Test authentication
    creator = GmailDraftCreator()
    try:
        service = creator.authenticate()
        print("Authentication successful!")
        print(f"Service: {service}")
    except Exception as e:
        print(f"Authentication failed: {e}")
