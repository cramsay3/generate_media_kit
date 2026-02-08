#!/usr/bin/env python3
"""
Send a test email for #Partäy playlist using the updated template.
"""

import sys
from pdf_parser import PDFParser, PlaylistContact
from template_processor import TemplateProcessor
from gmail_drafts import GmailDraftCreator
import yaml
from pathlib import Path


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


def main():
    # Get recipient emails from command line or use default test emails
    if len(sys.argv) >= 2:
        recipient_emails = sys.argv[1].split(',')
    else:
        recipient_emails = ['laura.b.ramsay@gmail.com', 'cramsay3@gmail.com']
    
    print("=" * 60)
    print("Sending Test Email for #Partäy Playlist")
    print("=" * 60)
    print()
    
    # Load config
    config = load_config()
    artist_name = config.get('artist', {}).get('name', 'Charley Ramsay')
    artist_spotify = config.get('artist', {}).get('spotify_link', 'https://open.spotify.com/artist/2s51Onhpd29JvOji1yuCKy?si=TVLfaQxOSz-qw6UQRraMkA')
    artist_instagram = config.get('artist', {}).get('instagram', 'cramsay3')
    artist_website = config.get('artist', {}).get('website', 'https://charleyramsay.com')
    cc_email = config.get('email_settings', {}).get('cc_email', 'charley@ramsays.us')
    # custom_message and additional_info removed - should be in template itself
    custom_message = None
    additional_info = None
    
    # Parse PDF to find #Partäy contact
    print("Step 1: Parsing playlist contacts...")
    pdf_parser = PDFParser('playlist_contacts.txt')
    contacts = pdf_parser.parse()
    
    # Find #Partäy contact
    party_contact = None
    for contact in contacts:
        if contact.playlist_name and '#Partäy' in contact.playlist_name:
            party_contact = contact
            break
    
    if not party_contact:
        print("ERROR: Could not find #Partäy playlist contact")
        sys.exit(1)
    
    print(f"  ✓ Found playlist: {party_contact.playlist_name}")
    print(f"  ✓ Curator: {party_contact.curator}")
    print(f"  ✓ Email: {party_contact.email}")
    print()
    
    # Generate email using template processor
    print("Step 2: Generating email content...")
    processor = TemplateProcessor('email_template.md')
    result = processor.process(
        party_contact,
        artist_name=artist_name,
        custom_message=custom_message,
        artist_spotify_link=artist_spotify,
        artist_instagram=artist_instagram,
        artist_website=artist_website,
        additional_info=additional_info
    )
    
    print(f"  ✓ Subject: {result['subject']}")
    print(f"  ✓ Body length: {len(result['body'])} characters")
    print()
    
    # Show preview
    print("Email Preview:")
    print("-" * 60)
    print(f"To: {', '.join(recipient_emails)}")
    print(f"CC: {cc_email}")
    print(f"Subject: {result['subject']}")
    print(f"Body preview (first 500 chars):")
    print(result['body'][:500] + "..." if len(result['body']) > 500 else result['body'])
    print("-" * 60)
    print()
    
    # Send emails to all recipients
    print("Step 3: Sending emails...")
    try:
        gmail = GmailDraftCreator()
        gmail.authenticate()
        print("  ✓ Authenticated with Gmail API")
        print(f"  ✓ CC on all emails: {cc_email}")
        print()
        
        successful = []
        failed = []
        
        for recipient_email in recipient_emails:
            recipient_email = recipient_email.strip()
            print(f"  Sending to: {recipient_email}...")
            
            message_id = gmail.send_email(
                to_email=recipient_email,
                subject=result['subject'],
                body=result['body'],
                cc_email=cc_email
            )
            
            if message_id:
                print(f"    ✓ Sent! Message ID: {message_id}")
                successful.append({'email': recipient_email, 'message_id': message_id})
            else:
                print(f"    ✗ Failed to send")
                failed.append({'email': recipient_email})
        
        print()
        print("=" * 60)
        print("SUCCESS!")
        print(f"Sent {len(successful)} test emails")
        print(f"CC'd on all: {cc_email}")
        print()
        print("Recipients:")
        for s in successful:
            print(f"  ✓ {s['email']}")
        if failed:
            print("\nFailed:")
            for f in failed:
                print(f"  ✗ {f['email']}")
        print("=" * 60)
            
    except Exception as e:
        print(f"  ✗ Error sending email: {e}")
        print()
        print("Troubleshooting:")
        print("1. Make sure you have credentials.json from Google Cloud Console")
        print("2. Enable Gmail API in your Google Cloud project")
        print("3. Check that you have internet connection")
        print("4. Install dependencies: pip3 install -r requirements.txt")
        sys.exit(1)


if __name__ == '__main__':
    main()
