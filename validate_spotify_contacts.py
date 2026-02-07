#!/usr/bin/env python3
"""
Validate all emails from Spotify Playlist Contacts PDF and generate results report.
"""

import argparse
import csv
from pathlib import Path
from pdf_parser import PDFParser
from email_validator import EmailValidator
from collections import Counter


def main():
    parser = argparse.ArgumentParser(
        description='Validate all emails from Spotify Playlist Contacts PDF'
    )
    parser.add_argument('--pdf-text', default='playlist_contacts.txt',
                       help='Path to extracted PDF text file')
    parser.add_argument('--output', default='spotify_contacts_validation.csv',
                       help='Output CSV file with validation results')
    parser.add_argument('--summary', default='spotify_contacts_summary.txt',
                       help='Summary text file')
    parser.add_argument('--check-mx', action='store_true', default=True,
                       help='Check MX records')
    parser.add_argument('--check-disposable', action='store_true', default=True,
                       help='Check for disposable emails')
    parser.add_argument('--check-role', action='store_true',
                       help='Check for role accounts')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Spotify Playlist Contacts Email Validation")
    print("=" * 70)
    print()
    
    # Parse PDF
    print(f"Step 1: Parsing PDF: {args.pdf_text}")
    if not Path(args.pdf_text).exists():
        print(f"ERROR: PDF text file not found: {args.pdf_text}")
        return
    
    pdf_parser = PDFParser(args.pdf_text)
    contacts = pdf_parser.parse()
    print(f"  ✓ Parsed {len(contacts)} contacts")
    
    # Extract emails
    emails_with_contacts = []
    seen_emails = set()
    
    for contact in contacts:
        if contact.email:
            email_lower = contact.email.lower().strip()
            if email_lower and email_lower not in seen_emails:
                seen_emails.add(email_lower)
                emails_with_contacts.append({
                    'email': contact.email,
                    'contact': contact
                })
    
    unique_emails = len(emails_with_contacts)
    print(f"  ✓ Found {unique_emails} unique email addresses")
    print()
    
    # Validate emails
    print("Step 2: Validating emails...")
    print("  (This may take a few minutes for large lists)")
    print("  (No emails will be sent)")
    print()
    
    validator = EmailValidator()
    results = []
    
    for i, item in enumerate(emails_with_contacts, 1):
        email = item['email']
        contact = item['contact']
        
        if i % 100 == 0:
            print(f"  Validated {i}/{unique_emails}...", end='\r', flush=True)
        
        validation = validator.validate_email(
            email,
            check_mx=args.check_mx,
            check_disposable=args.check_disposable,
            check_role=args.check_role
        )
        
        # Add contact info
        validation['playlist_name'] = contact.playlist_name or ''
        validation['curator'] = contact.curator or ''
        validation['spotify_url'] = contact.spotify_url or ''
        validation['followers'] = contact.followers or ''
        validation['genres'] = contact.genres or ''
        
        results.append(validation)
    
    print(f"  ✓ Validated {unique_emails} emails")
    print()
    
    # Calculate statistics
    valid_count = sum(1 for r in results if r['valid'])
    invalid_count = unique_emails - valid_count
    syntax_valid = sum(1 for r in results if r['syntax_valid'])
    domain_exists = sum(1 for r in results if r['domain_exists'])
    has_mx = sum(1 for r in results if r['has_mx'])
    disposable_count = sum(1 for r in results if r['is_disposable'])
    role_count = sum(1 for r in results if r['is_role_account'])
    
    # Domain analysis
    domains = [r['email'].split('@')[1].lower() for r in results if r['email']]
    domain_counts = Counter(domains)
    top_domains = domain_counts.most_common(10)
    
    # Write detailed CSV
    print(f"Step 3: Writing results to {args.output}...")
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'email', 'valid', 'syntax_valid', 'domain_exists', 'has_mx',
            'is_disposable', 'is_role_account', 'playlist_name', 'curator',
            'spotify_url', 'followers', 'genres', 'warnings', 'errors'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for r in results:
            row = {
                'email': r['email'],
                'valid': r['valid'],
                'syntax_valid': r['syntax_valid'],
                'domain_exists': r['domain_exists'],
                'has_mx': r['has_mx'],
                'is_disposable': r['is_disposable'],
                'is_role_account': r['is_role_account'],
                'playlist_name': r.get('playlist_name', ''),
                'curator': r.get('curator', ''),
                'spotify_url': r.get('spotify_url', ''),
                'followers': r.get('followers', ''),
                'genres': r.get('genres', ''),
                'warnings': '; '.join(r['warnings']),
                'errors': '; '.join(r['errors'])
            }
            writer.writerow(row)
    
    print(f"  ✓ Results saved to {args.output}")
    print()
    
    # Write summary
    print(f"Step 4: Writing summary to {args.summary}...")
    with open(args.summary, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("Spotify Playlist Contacts - Email Validation Report\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("OVERALL STATISTICS\n")
        f.write("-" * 70 + "\n")
        f.write(f"Total contacts parsed: {len(contacts):,}\n")
        f.write(f"Unique email addresses: {unique_emails:,}\n")
        f.write(f"Valid emails: {valid_count:,} ({valid_count/unique_emails*100:.1f}%)\n")
        f.write(f"Invalid emails: {invalid_count:,} ({invalid_count/unique_emails*100:.1f}%)\n")
        f.write("\n")
        
        f.write("VALIDATION BREAKDOWN\n")
        f.write("-" * 70 + "\n")
        f.write(f"Syntax valid: {syntax_valid:,} ({syntax_valid/unique_emails*100:.1f}%)\n")
        f.write(f"Domain exists: {domain_exists:,} ({domain_exists/unique_emails*100:.1f}%)\n")
        f.write(f"Has MX records: {has_mx:,} ({has_mx/unique_emails*100:.1f}%)\n")
        f.write(f"Disposable emails: {disposable_count:,} ({disposable_count/unique_emails*100:.1f}%)\n")
        if args.check_role:
            f.write(f"Role accounts: {role_count:,} ({role_count/unique_emails*100:.1f}%)\n")
        f.write("\n")
        
        f.write("TOP 10 EMAIL DOMAINS\n")
        f.write("-" * 70 + "\n")
        for domain, count in top_domains:
            f.write(f"{domain:40s} {count:6,} emails ({count/unique_emails*100:.1f}%)\n")
        f.write("\n")
        
        # Invalid emails
        invalid_emails = [r for r in results if not r['valid']]
        if invalid_emails:
            f.write("INVALID EMAILS\n")
            f.write("-" * 70 + "\n")
            for r in invalid_emails[:50]:
                f.write(f"{r['email']}\n")
                if r['errors']:
                    f.write(f"  Errors: {', '.join(r['errors'])}\n")
            if len(invalid_emails) > 50:
                f.write(f"\n... and {len(invalid_emails) - 50} more invalid emails\n")
            f.write("\n")
        
        # Disposable emails
        if disposable_count > 0:
            disposable_emails = [r for r in results if r['is_disposable']]
            f.write("DISPOSABLE EMAIL ADDRESSES\n")
            f.write("-" * 70 + "\n")
            for r in disposable_emails[:20]:
                f.write(f"{r['email']}\n")
            if len(disposable_emails) > 20:
                f.write(f"\n... and {len(disposable_emails) - 20} more\n")
            f.write("\n")
        
        f.write("=" * 70 + "\n")
        f.write("Report generated successfully\n")
        f.write("=" * 70 + "\n")
    
    print(f"  ✓ Summary saved to {args.summary}")
    print()
    
    # Print summary to console
    print("=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    print(f"Total contacts parsed: {len(contacts):,}")
    print(f"Unique email addresses: {unique_emails:,}")
    print()
    print(f"✓ Valid emails: {valid_count:,} ({valid_count/unique_emails*100:.1f}%)")
    print(f"✗ Invalid emails: {invalid_count:,} ({invalid_count/unique_emails*100:.1f}%)")
    print()
    print("Breakdown:")
    print(f"  Syntax valid: {syntax_valid:,}")
    print(f"  Domain exists: {domain_exists:,}")
    print(f"  Has MX records: {has_mx:,}")
    print(f"  Disposable: {disposable_count:,}")
    if args.check_role:
        print(f"  Role accounts: {role_count:,}")
    print()
    print("Top domains:")
    for domain, count in top_domains[:5]:
        print(f"  {domain}: {count:,} emails")
    print()
    print("=" * 70)
    print(f"Detailed results: {args.output}")
    print(f"Summary report: {args.summary}")
    print("=" * 70)


if __name__ == '__main__':
    main()
