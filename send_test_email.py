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
    # Get recipient email from command line or use authenticated user's email
    if len(sys.argv) >= 2:
        recipient_email = sys.argv[1]
    else:
        recipient_email = None  # Will get from authenticated account
    
    print("=" * 60)
    print("Sending Test Email for #Partäy Playlist")
    print("=" * 60)
    print()
    
    # Load config
    config = load_config()
    artist_name = config.get('artist', {}).get('name', 'Charley Ramsay')
    artist_spotify = config.get('artist', {}).get('spotify_link', 'https://open.spotify.com/artist/charleyramsay')
    artist_instagram = config.get('artist', {}).get('instagram', 'cramsay3')
    artist_website = config.get('artist', {}).get('website', 'https://charleyramsay.com')
    custom_message = config.get('email', {}).get('custom_message')
    additional_info = config.get('email', {}).get('additional_info')
    
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
    print(f"To: {recipient_email}")
    print(f"Subject: {result['subject']}")
    print(f"Body preview (first 500 chars):")
    print(result['body'][:500] + "..." if len(result['body']) > 500 else result['body'])
    print("-" * 60)
    print()
    
    # Send email
    print("Step 3: Sending email...")
    try:
        gmail = GmailDraftCreator()
        gmail.authenticate()
        print("  ✓ Authenticated with Gmail API")
        
        # Get authenticated user's email if not provided
        if not recipient_email:
            profile = gmail.service.users().getProfile(userId='me').execute()
            recipient_email = profile.get('emailAddress')
            print(f"  ✓ Using authenticated account: {recipient_email}")
        
        message_id = gmail.send_email(
            to_email=recipient_email,
            subject=result['subject'],
            body=result['body']
        )
        
        if message_id:
            print(f"  ✓ Email sent successfully!")
            print(f"  ✓ Message ID: {message_id}")
            print()
            print("=" * 60)
            print("SUCCESS!")
            print(f"Test email sent to: {recipient_email}")
            print("Check your inbox (and spam folder) for the email.")
            print("=" * 60)
        else:
            print("  ✗ Failed to send email")
            sys.exit(1)
            
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
