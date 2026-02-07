#!/usr/bin/env python3
"""
Main script to create Gmail drafts from CSV emails using Spotify Playlist Contacts PDF data.
"""

import argparse
import sys
from pathlib import Path
from pdf_parser import PDFParser, PlaylistContact
from csv_reader import CSVReader
from email_template import EmailTemplate
from template_processor import TemplateProcessor

# Gmail imports - only needed if not dry-run
try:
    from gmail_drafts import GmailDraftCreator
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    GmailDraftCreator = None

# Config file support
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def load_config(config_file='config.yaml'):
    """Load configuration from YAML file."""
    config = {}
    config_path = Path(config_file)
    
    if not config_path.exists():
        return config
    
    if not YAML_AVAILABLE:
        print(f"  ⚠ config.yaml found but PyYAML not installed. Install with: pip3 install pyyaml")
        return config
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"  ⚠ Failed to load config.yaml: {e}")
    
    return config


def get_config_value(config, *keys, default=None):
    """Get nested config value, e.g. get_config_value(config, 'artist', 'name')"""
    value = config
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
        if value is None:
            return default
    return value if value is not None else default


def main():
    parser = argparse.ArgumentParser(
        description='Create Gmail drafts from CSV emails using Spotify Playlist Contacts PDF data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple usage - uses config.yaml for defaults
  python3 create_email_drafts.py your_contacts.csv
  
  # Override specific values
  python3 create_email_drafts.py your_contacts.csv --artist-name "Different Name"
  
  # Preview without creating drafts
  python3 create_email_drafts.py your_contacts.csv --dry-run --limit 5
        """
    )
    parser.add_argument('csv_file', help='Path to CSV file with email addresses')
    parser.add_argument('--config', default='config.yaml',
                       help='Path to config file (default: config.yaml)')
    parser.add_argument('--pdf-text', default=None,
                       help='Path to extracted PDF text file (overrides config)')
    parser.add_argument('--email-column', default=None,
                       help='CSV column name containing emails (auto-detected if not specified)')
    parser.add_argument('--artist-name', default=None,
                       help='Artist name (overrides config)')
    parser.add_argument('--custom-message', default=None,
                       help='Custom message (overrides config)')
    parser.add_argument('--custom-subject', default=None,
                       help='Custom email subject (overrides config)')
    parser.add_argument('--template', default=None,
                       help='Path to markdown template file (overrides config)')
    parser.add_argument('--artist-spotify', default=None,
                       help='Spotify artist link (overrides config)')
    parser.add_argument('--artist-instagram', default=None,
                       help='Instagram handle/link (overrides config)')
    parser.add_argument('--artist-website', default=None,
                       help='Website URL (overrides config)')
    parser.add_argument('--additional-info', default=None,
                       help='Additional info (overrides config)')
    parser.add_argument('--credentials', default=None,
                       help='Gmail API credentials file (overrides config)')
    parser.add_argument('--token', default=None,
                       help='Gmail API token file (overrides config)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Parse and show what would be created without actually creating drafts')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of drafts to create (for testing)')
    
    args = parser.parse_args()
    
    # Load config file
    config = load_config(args.config)
    
    # Merge config with command-line args (CLI args take precedence)
    pdf_text = args.pdf_text or get_config_value(config, 'files', 'pdf_text', default='playlist_contacts.txt')
    template_file = args.template or get_config_value(config, 'files', 'template', default='email_template.md')
    credentials = args.credentials or get_config_value(config, 'files', 'credentials', default='credentials.json')
    token = args.token or get_config_value(config, 'files', 'token', default='token.json')
    
    artist_name = args.artist_name or get_config_value(config, 'artist', 'name')
    artist_spotify = args.artist_spotify or get_config_value(config, 'artist', 'spotify_link')
    artist_instagram = args.artist_instagram or get_config_value(config, 'artist', 'instagram')
    artist_website = args.artist_website or get_config_value(config, 'artist', 'website')
    
    custom_message = args.custom_message or get_config_value(config, 'email', 'custom_message')
    additional_info = args.additional_info or get_config_value(config, 'email', 'additional_info')
    custom_subject = args.custom_subject or get_config_value(config, 'email', 'custom_subject')
    
    print("=" * 60)
    print("Gmail Draft Creator for Spotify Playlist Contacts")
    print("=" * 60)
    print()
    
    if config:
        print(f"  ✓ Loaded config from: {args.config}")
    print()
    
    # Step 1: Parse PDF
    print(f"Step 1: Parsing PDF text file: {pdf_text}")
    if not Path(pdf_text).exists():
        print(f"ERROR: PDF text file not found: {pdf_text}")
        print("Please extract the PDF first using: pdftotext Spotify_Playlist_Contacts_3000.pdf playlist_contacts.txt")
        sys.exit(1)
    
    pdf_parser = PDFParser(pdf_text)
    contacts = pdf_parser.parse()
    print(f"  ✓ Parsed {len(contacts)} playlist contacts")
    print(f"  ✓ Found {len([c for c in contacts if c.email])} contacts with email addresses")
    print()
    
    # Step 2: Read CSV
    print(f"Step 2: Reading CSV file: {args.csv_file}")
    csv_reader = CSVReader(args.csv_file)
    try:
        rows = csv_reader.read()
        print(f"  ✓ Read {len(rows)} rows from CSV")
        
        email_column = args.email_column or csv_reader.get_email_column()
        if not email_column:
            print("  ERROR: Could not determine email column")
            print(f"  Available columns: {list(rows[0].keys()) if rows else 'No rows'}")
            sys.exit(1)
        
        print(f"  ✓ Using email column: {email_column}")
        emails = csv_reader.get_emails(email_column)
        print(f"  ✓ Found {len(emails)} email addresses in CSV")
        print()
    except Exception as e:
        print(f"  ERROR: Failed to read CSV: {e}")
        sys.exit(1)
    
    # Step 3: Match emails to contacts
    print("Step 3: Matching CSV emails to PDF contacts")
    matched = []
    unmatched = []
    
    for email in emails:
        contact = pdf_parser.get_contact_by_email(email)
        csv_row = csv_reader.get_row_by_email(email)
        
        if contact:
            matched.append({
                'email': email,
                'contact': contact,
                'csv_data': csv_row
            })
        else:
            unmatched.append({
                'email': email,
                'csv_data': csv_row
            })
    
    print(f"  ✓ Matched {len(matched)} emails to playlist contacts")
    print(f"  ⚠ {len(unmatched)} emails not found in PDF")
    print()
    
    if not matched:
        print("ERROR: No emails matched to playlist contacts. Cannot create drafts.")
        sys.exit(1)
    
    # Step 4: Generate email content
    print("Step 4: Generating email content")
    drafts_data = []
    
    # Check if using markdown template
    use_template = Path(template_file).exists()
    
    if use_template:
        print(f"  Using template: {template_file}")
        try:
            processor = TemplateProcessor(template_file)
        except FileNotFoundError:
            print(f"  ⚠ Template file not found, using default template")
            use_template = False
    else:
        print(f"  ⚠ Template file not found: {template_file}")
        print(f"  Using default template")
    
    for match in matched[:args.limit] if args.limit else matched:
        contact = match['contact']
        email = match['email']
        
        if use_template:
            # Use markdown template with placeholders
            result = processor.process(
                contact,
                artist_name=artist_name,
                custom_message=custom_message,
                artist_spotify_link=artist_spotify,
                artist_instagram=artist_instagram,
                artist_website=artist_website,
                additional_info=additional_info,
                custom_subject=custom_subject
            )
            subject = result['subject']
            body = result['body']
        else:
            # Use default template
            subject = EmailTemplate.generate_subject(contact, custom_subject)
            body = EmailTemplate.generate_body(
                contact,
                artist_name=artist_name,
                custom_message=custom_message
            )
        
        drafts_data.append({
            'to_email': email,
            'subject': subject,
            'body': body,
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
        print(f"Body preview:")
        print(first['body'][:200] + "..." if len(first['body']) > 200 else first['body'])
        print("-" * 60)
        print()
    
    # Step 5: Create Gmail drafts
    if args.dry_run:
        print("DRY RUN: Would create the following drafts:")
        for i, draft in enumerate(drafts_data[:10], 1):
            print(f"\n  Draft {i}:")
            print(f"    To: {draft['to_email']}")
            print(f"    Subject: {draft['subject']}")
            print(f"    Playlist: {draft['contact'].playlist_name or 'N/A'}")
            print(f"    Spotify: {draft['contact'].spotify_url or 'N/A'}")
            print(f"    Followers: {draft['contact'].followers or 'N/A'}")
        if len(drafts_data) > 10:
            print(f"\n  ... and {len(drafts_data) - 10} more drafts")
        print("\nRun without --dry-run to actually create the drafts.")
        print("\nTo create drafts, you'll need:")
        print("1. Install dependencies: pip3 install -r requirements.txt")
        print("2. Set up Gmail API credentials (see README_EMAILER.md)")
        return
    
    if not GMAIL_AVAILABLE:
        print("ERROR: Gmail API dependencies not installed.")
        print("Install with: pip3 install -r requirements.txt")
        sys.exit(1)
    
    print("Step 5: Creating Gmail drafts")
    print("  Note: You will need to authenticate with Google if this is the first run.")
    print()
    
    try:
        gmail_creator = GmailDraftCreator(credentials, token)
        gmail_creator.authenticate()
        print("  ✓ Authenticated with Gmail API")
        
        results = gmail_creator.create_drafts_batch(drafts_data)
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"  ✓ Successfully created {len(successful)} drafts")
        if failed:
            print(f"  ⚠ Failed to create {len(failed)} drafts:")
            for fail in failed[:5]:
                print(f"    - {fail['to_email']}: {fail['error']}")
        
        print()
        print("=" * 60)
        print("SUCCESS!")
        print(f"Created {len(successful)} Gmail drafts")
        print("You can now review and send them from Gmail.")
        print("=" * 60)
        
    except Exception as e:
        print(f"  ERROR: Failed to create drafts: {e}")
        print()
        print("Troubleshooting:")
        print("1. Make sure you have credentials.json from Google Cloud Console")
        print("2. Enable Gmail API in your Google Cloud project")
        print("3. Check that you have internet connection")
        print("4. Install dependencies: pip3 install -r requirements.txt")
        sys.exit(1)


if __name__ == '__main__':
    main()
