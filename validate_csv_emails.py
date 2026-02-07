#!/usr/bin/env python3
"""
Validate all emails in a CSV file without sending any emails.
"""

import argparse
import sys
from email_validator import EmailValidator
from csv_reader import CSVReader


def main():
    parser = argparse.ArgumentParser(
        description='Validate emails in CSV file without sending'
    )
    parser.add_argument('csv_file', help='CSV file with email addresses')
    parser.add_argument('--email-column', default=None,
                       help='Email column name (auto-detected if not specified)')
    parser.add_argument('--output', default=None,
                       help='Output CSV file with validation results')
    parser.add_argument('--check-mx', action='store_true', default=True,
                       help='Check MX records (default: True)')
    parser.add_argument('--check-disposable', action='store_true', default=True,
                       help='Check for disposable emails (default: True)')
    parser.add_argument('--check-role', action='store_true',
                       help='Check for role accounts (info@, support@, etc.)')
    parser.add_argument('--show-invalid-only', action='store_true',
                       help='Show only invalid emails')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Email Validation (Non-Invasive)")
    print("=" * 60)
    print()
    
    # Read CSV
    reader = CSVReader(args.csv_file)
    rows = reader.read()
    email_column = args.email_column or reader.get_email_column()
    
    if not email_column:
        print("ERROR: Could not determine email column")
        sys.exit(1)
    
    emails = reader.get_emails(email_column)
    print(f"Found {len(emails)} email addresses")
    print()
    
    # Validate
    validator = EmailValidator()
    print("Validating emails...")
    print("  (This checks syntax, domain existence, MX records)")
    print("  (No emails will be sent)")
    print()
    
    results = []
    for email in emails:
        result = validator.validate_email(
            email,
            check_mx=args.check_mx,
            check_disposable=args.check_disposable,
            check_role=args.check_role
        )
        results.append(result)
    
    # Summary
    valid_count = sum(1 for r in results if r['valid'])
    invalid_count = len(results) - valid_count
    disposable_count = sum(1 for r in results if r['is_disposable'])
    role_count = sum(1 for r in results if r['is_role_account'])
    no_mx_count = sum(1 for r in results if not r['has_mx'] and r['domain_exists'])
    
    print("=" * 60)
    print("Validation Results")
    print("=" * 60)
    print(f"Total emails: {len(results)}")
    print(f"Valid: {valid_count}")
    print(f"Invalid: {invalid_count}")
    if disposable_count > 0:
        print(f"Disposable emails: {disposable_count}")
    if role_count > 0:
        print(f"Role accounts: {role_count}")
    if no_mx_count > 0:
        print(f"No MX records: {no_mx_count}")
    print()
    
    # Show invalid emails
    invalid_emails = [r for r in results if not r['valid']]
    if invalid_emails:
        print("Invalid Emails:")
        print("-" * 60)
        for r in invalid_emails[:20]:
            print(f"{r['email']}")
            if r['errors']:
                print(f"  Errors: {', '.join(r['errors'])}")
            if r['warnings']:
                print(f"  Warnings: {', '.join(r['warnings'])}")
        if len(invalid_emails) > 20:
            print(f"\n... and {len(invalid_emails) - 20} more invalid emails")
        print()
    
    # Show warnings
    warned_emails = [r for r in results if r['warnings'] and r['valid']]
    if warned_emails and not args.show_invalid_only:
        print("Valid but with warnings:")
        print("-" * 60)
        for r in warned_emails[:10]:
            print(f"{r['email']}: {', '.join(r['warnings'])}")
        if len(warned_emails) > 10:
            print(f"\n... and {len(warned_emails) - 10} more")
        print()
    
    # Write output file
    if args.output:
        import csv
        with open(args.output, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'email', 'valid', 'syntax_valid', 'domain_exists',
                'has_mx', 'is_disposable', 'is_role_account',
                'warnings', 'errors'
            ])
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
                    'warnings': '; '.join(r['warnings']),
                    'errors': '; '.join(r['errors'])
                }
                writer.writerow(row)
        print(f"Results saved to: {args.output}")
    
    # Recommendations
    print("=" * 60)
    print("Recommendations:")
    print("=" * 60)
    if invalid_count > 0:
        print(f"- Remove {invalid_count} invalid emails before sending")
    if disposable_count > 0:
        print(f"- Consider removing {disposable_count} disposable email addresses")
    if role_count > 0:
        print(f"- {role_count} role accounts may have lower engagement")
    if no_mx_count > 0:
        print(f"- {no_mx_count} emails have no MX records (may bounce)")
    print()
    print(f"Ready to send: {valid_count} valid emails")
    print("=" * 60)


if __name__ == '__main__':
    main()
