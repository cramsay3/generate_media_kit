#!/usr/bin/env python3
"""
Create random Gmail drafts from PDF contacts with genre filtering and email validation.
"""

import sys
import random
from pathlib import Path
from pdf_parser import PDFParser
from template_processor import TemplateProcessor
from gmail_drafts import GmailDraftCreator
from email_validator import EmailValidator
from csv_reader import CSVReader
import yaml


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


def filter_by_genres(contact, genre_keywords, exclude_keywords=None):
    """Check if contact genres match any of the specified keywords and don't match exclusions."""
    if not contact.genres or not genre_keywords:
        return False
    
    genres_lower = contact.genres.lower()
    
    # First check exclusions - if any excluded genre is present, exclude this contact
    if exclude_keywords:
        for exclude in exclude_keywords:
            if exclude.lower() in genres_lower:
                return False
    
    # Then check if it matches any of the included keywords
    for keyword in genre_keywords:
        if keyword.lower() in genres_lower:
            return True
    return False


def main():
    if len(sys.argv) > 1:
        num_drafts = int(sys.argv[1])
    else:
        num_drafts = 10
    
    print("=" * 60)
    print(f"Creating {num_drafts} Random Gmail Drafts")
    print("(Filtered by genre and validated emails)")
    print("=" * 60)
    print()
    
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
    
    # Get genre keywords and validation settings from config
    genre_keywords = config.get('email', {}).get('genre_keywords', [
        'indie pop', 'singer/songwriter', 'rock', 'folk-pop', 'acoustic', 'indie', 'chillwave'
    ])
    exclude_genres = config.get('email', {}).get('exclude_genres', [
        'hip hop', 'rap', 'edm', 'electronic', 'house', 'techno', 'trance', 'dubstep', 'brostep',
        'metal', 'punk', 'hardcore', 'reggae', 'reggaeton', 'trap'
    ])
    validate_emails = config.get('email', {}).get('validate_emails', True)
    validation_csv = config.get('email', {}).get('validation_csv')
    
    # Parse PDF to get all contacts with emails
    print(f"Step 1: Parsing PDF text file: {pdf_text}")
    if not Path(pdf_text).exists():
        print(f"ERROR: PDF text file not found: {pdf_text}")
        sys.exit(1)
    
    pdf_parser = PDFParser(pdf_text)
    contacts = pdf_parser.parse()
    contacts_with_email = [c for c in contacts if c.email]
    
    print(f"  ✓ Parsed {len(contacts)} playlist contacts")
    print(f"  ✓ Found {len(contacts_with_email)} contacts with email addresses")
    print()
    
    # Step 2: Filter by genres
    print(f"Step 2: Filtering by genres...")
    print(f"  Include: {', '.join(genre_keywords)}")
    if exclude_genres:
        print(f"  Exclude: {', '.join(exclude_genres[:5])}...")
    genre_filtered = [c for c in contacts_with_email if filter_by_genres(c, genre_keywords, exclude_genres)]
    print(f"  ✓ Found {len(genre_filtered)} contacts matching genre criteria")
    print()
    
    if len(genre_filtered) == 0:
        print("ERROR: No contacts match the genre criteria!")
        sys.exit(1)
    
    # Step 3: Validate emails (if enabled)
    validated_contacts = genre_filtered
    if validate_emails:
        print("Step 3: Validating emails...")
        
        # If CSV provided, use validated emails from CSV
        if validation_csv and Path(validation_csv).exists():
            print(f"  Using validated emails from CSV: {validation_csv}")
            csv_reader = CSVReader(validation_csv)
            validated_emails = set(csv_reader.get_emails())
            validated_contacts = [c for c in genre_filtered if c.email.lower() in validated_emails]
            print(f"  ✓ Found {len(validated_contacts)} contacts with validated emails from CSV")
        else:
            # Validate emails directly
            validator = EmailValidator()
            validated_contacts = []
            for i, contact in enumerate(genre_filtered, 1):
                if i % 50 == 0:
                    print(f"  Validating... {i}/{len(genre_filtered)}")
                result = validator.validate_email(contact.email, check_mx=True, check_disposable=True)
                if result['valid']:
                    validated_contacts.append(contact)
            print(f"  ✓ Found {len(validated_contacts)} contacts with valid emails")
        print()
    
    if len(validated_contacts) < num_drafts:
        print(f"  ⚠ Only {len(validated_contacts)} contacts available, creating {len(validated_contacts)} drafts")
        num_drafts = len(validated_contacts)
    
    # Step 4: Randomly select contacts
    print(f"Step 4: Randomly selecting {num_drafts} contacts...")
    selected_contacts = random.sample(validated_contacts, num_drafts)
    
    for i, contact in enumerate(selected_contacts, 1):
        print(f"  {i}. {contact.playlist_name or 'N/A'} - {contact.curator or 'N/A'} ({contact.email})")
    print()
    
    # Generate email content
    print("Step 5: Generating email content...")
    processor = TemplateProcessor(template_file)
    drafts_data = []
    
    for contact in selected_contacts:
        result = processor.process(
            contact,
            artist_name=artist_name,
            artist_spotify_link=artist_spotify,
            artist_instagram=artist_instagram,
            artist_website=artist_website
        )
        
        drafts_data.append({
            'to_email': contact.email,
            'subject': result['subject'],
            'body': result['body'],
            'contact': contact
        })
    
    print(f"  ✓ Generated {len(drafts_data)} email drafts")
    print()
    
    # Show preview
    print("Preview of first draft:")
    print("-" * 60)
    if drafts_data:
        first = drafts_data[0]
        print(f"To: {first['to_email']}")
        print(f"Subject: {first['subject']}")
        print(f"Playlist: {first['contact'].playlist_name or 'N/A'}")
        print(f"Curator: {first['contact'].curator or 'N/A'}")
        print("-" * 60)
        print()
    
    # Send emails (not drafts) so we can test HTML formatting
    print("Step 6: Sending emails...")
    try:
        gmail_creator = GmailDraftCreator(credentials, token)
        gmail_creator.authenticate()
        print("  ✓ Authenticated with Gmail API")
        
        # Get authenticated user's email to send test emails to
        profile = gmail_creator.service.users().getProfile(userId='me').execute()
        test_email = profile.get('emailAddress')
        print(f"  ✓ Sending test emails to: {test_email}")
        print()
        
        results = []
        for draft_info in drafts_data:
            # Send to test email instead of actual recipient for testing
            message_id = gmail_creator.send_email(
                to_email=test_email,
                subject=f"[TEST] {draft_info['subject']}",
                body=draft_info['body'],
                cc_email=cc_email
            )
            
            if message_id:
                results.append({
                    'success': True,
                    'message_id': message_id,
                    'to_email': test_email,
                    'original_recipient': draft_info['to_email'],
                    'contact': draft_info['contact'],
                    'error': None
                })
            else:
                results.append({
                    'success': False,
                    'message_id': None,
                    'to_email': test_email,
                    'original_recipient': draft_info['to_email'],
                    'error': 'Failed to send email'
                })
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"  ✓ Successfully sent {len(successful)} test emails")
        if failed:
            print(f"  ⚠ Failed to send {len(failed)} emails:")
            for fail in failed[:5]:
                print(f"    - {fail['original_recipient']}: {fail['error']}")
        
        print()
        print("=" * 60)
        print("SUCCESS!")
        print(f"Sent {len(successful)} test emails to {test_email}")
        print("Check your inbox to verify HTML formatting!")
        print()
        print("Contacts tested:")
        for i, result in enumerate(successful[:10], 1):
            contact = result['contact']
            print(f"  {i}. {contact.playlist_name or 'N/A'} - {contact.curator or 'N/A'} ({result['original_recipient']})")
        print("=" * 60)
        
    except Exception as e:
        print(f"  ERROR: Failed to create drafts: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
