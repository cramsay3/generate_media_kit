#!/usr/bin/env python3
"""
Send emails from CSV using Gmail API with proper rate limiting.
"""

import argparse
import sys
from pathlib import Path
from pdf_parser import PDFParser
from csv_reader import CSVReader
from email_template import EmailTemplate
from gmail_sender import GmailSender


def main():
    parser = argparse.ArgumentParser(
        description='Send emails from CSV using Gmail API with rate limiting'
    )
    parser.add_argument('csv_file', help='Path to CSV file with email addresses')
    parser.add_argument('--pdf-text', default='playlist_contacts.txt',
                       help='Path to extracted PDF text file')
    parser.add_argument('--email-column', default=None,
                       help='CSV column name containing emails')
    parser.add_argument('--artist-name', default=None,
                       help='Artist name to include in emails')
    parser.add_argument('--custom-message', default=None,
                       help='Custom message to include in email body')
    parser.add_argument('--custom-subject', default=None,
                       help='Custom email subject')
    parser.add_argument('--credentials', default='credentials.json',
                       help='Gmail API credentials file')
    parser.add_argument('--token', default='token.json',
                       help='Gmail API token file')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of emails to send')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be sent without actually sending')
    parser.add_argument('--confirm', action='store_true',
                       help='Skip confirmation prompt')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Gmail Email Sender with Rate Limiting")
    print("=" * 60)
    print()
    
    # Parse PDF
    print(f"Step 1: Parsing PDF text file: {args.pdf_text}")
    if not Path(args.pdf_text).exists():
        print(f"ERROR: PDF text file not found: {args.pdf_text}")
        sys.exit(1)
    
    pdf_parser = PDFParser(args.pdf_text)
    contacts = pdf_parser.parse()
    print(f"  ✓ Parsed {len(contacts)} playlist contacts")
    print()
    
    # Read CSV
    print(f"Step 2: Reading CSV file: {args.csv_file}")
    csv_reader = CSVReader(args.csv_file)
    try:
        rows = csv_reader.read()
        email_column = args.email_column or csv_reader.get_email_column()
        if not email_column:
            print("  ERROR: Could not determine email column")
            sys.exit(1)
        emails = csv_reader.get_emails(email_column)
        print(f"  ✓ Found {len(emails)} email addresses")
        print()
    except Exception as e:
        print(f"  ERROR: {e}")
        sys.exit(1)
    
    # Match emails
    print("Step 3: Matching emails to contacts")
    matched = []
    for email in emails:
        contact = pdf_parser.get_contact_by_email(email)
        if contact:
            matched.append({'email': email, 'contact': contact})
    
    print(f"  ✓ Matched {len(matched)} emails")
    print()
    
    if not matched:
        print("ERROR: No emails matched")
        sys.exit(1)
    
    # Generate messages
    print("Step 4: Generating email content")
    messages = []
    for match in matched[:args.limit] if args.limit else matched:
        contact = match['contact']
        email = match['email']
        
        subject = EmailTemplate.generate_subject(contact, args.custom_subject)
        body = EmailTemplate.generate_body(
            contact,
            artist_name=args.artist_name,
            custom_message=args.custom_message
        )
        
        messages.append({
            'to_email': email,
            'subject': subject,
            'body': body
        })
    
    print(f"  ✓ Generated {len(messages)} messages")
    print()
    
    # Show preview
    if messages:
        print("Preview of first message:")
        print("-" * 60)
        first = messages[0]
        print(f"To: {first['to_email']}")
        print(f"Subject: {first['subject']}")
        print(f"Body preview: {first['body'][:150]}...")
        print("-" * 60)
        print()
    
    # Dry run
    if args.dry_run:
        print("DRY RUN: Would send the following messages:")
        for i, msg in enumerate(messages[:10], 1):
            print(f"\n  Message {i}:")
            print(f"    To: {msg['to_email']}")
            print(f"    Subject: {msg['subject']}")
        if len(messages) > 10:
            print(f"\n  ... and {len(messages) - 10} more messages")
        print("\nRun without --dry-run to actually send.")
        return
    
    # Confirmation
    if not args.confirm:
        print(f"WARNING: This will send {len(messages)} emails!")
        print(f"Rate limiting: ~30-90 seconds between emails")
        print(f"Estimated time: ~{int(len(messages) * 60 / 60)} minutes")
        response = input("\nType 'yes' to continue: ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
    
    # Send messages
    print("Step 5: Sending emails with rate limiting")
    try:
        sender = GmailSender(args.credentials, args.token)
        sender.authenticate()
        
        results = sender.send_messages(messages)
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"\n{'='*60}")
        print(f"SUCCESS!")
        print(f"Sent {len(successful)}/{len(messages)} emails")
        if failed:
            print(f"Failed: {len(failed)}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
