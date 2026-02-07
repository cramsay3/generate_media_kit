#!/usr/bin/env python3
"""
Create a sample CSV file from the PDF contacts for testing.
"""

from pdf_parser import PDFParser
import csv

# Parse PDF
parser = PDFParser('playlist_contacts.txt')
contacts = parser.parse()

# Get contacts with emails
contacts_with_emails = [c for c in contacts if c.email]

print(f"Found {len(contacts_with_emails)} contacts with email addresses")

# Create sample CSV with first 10 contacts
output_file = 'sample_contacts.csv'
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['email', 'playlist_name', 'curator', 'spotify_url', 'followers'])
    writer.writeheader()
    
    for contact in contacts_with_emails[:10]:
        writer.writerow({
            'email': contact.email,
            'playlist_name': contact.playlist_name or '',
            'curator': contact.curator or '',
            'spotify_url': contact.spotify_url or '',
            'followers': contact.followers or ''
        })

print(f"Created {output_file} with {min(10, len(contacts_with_emails))} sample contacts")
print(f"\nYou can now run:")
print(f"  python3 create_email_drafts.py {output_file} --artist-name \"Your Name\" --custom-message \"Your message\"")
