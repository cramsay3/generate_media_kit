#!/usr/bin/env python3
"""
Send a test HTML email to yourself to verify formatting works.
"""

import sys
from gmail_sender import GmailSender
from pdf_parser import PDFParser
from template_processor import TemplateProcessor

def main():
    print("=" * 70)
    print("HTML Email Test - Sending Test Email to Yourself")
    print("=" * 70)
    print()
    
    # Get your email address
    your_email = input("Enter your Gmail address to send test email to: ").strip()
    if not your_email or '@' not in your_email:
        print("ERROR: Invalid email address")
        sys.exit(1)
    
    print()
    print("Creating test email with HTML formatting...")
    
    # Get a sample contact
    parser = PDFParser('playlist_contacts.txt')
    contacts = parser.parse()
    contact = None
    for c in contacts:
        if 'felix@pro-gamer-gear.de' in c.email.lower():
            contact = c
            break
    
    if not contact:
        print("ERROR: Could not find sample contact")
        sys.exit(1)
    
    # Process template
    processor = TemplateProcessor('email_template.md')
    result = processor.process(
        contact,
        artist_name='Charley Ramsay',
        custom_message="I'm reaching out because I just released my latest single 'Bottle Rocket Sunsets' last week and I think it would be a perfect fit for your playlist.",
        artist_spotify_link='https://open.spotify.com/artist/charleyramsay',
        artist_instagram='@charleyramsay',
        artist_website='https://charleyramsay.com',
        additional_info="My latest single 'Bottle Rocket Sunsets' was released last week and captures that nostalgic summer vibe that I think would resonate with your listeners."
    )
    
    subject = f"TEST: {result['subject']}"
    body = result['body']
    
    print(f"  Subject: {subject}")
    print(f"  Body length: {len(body)} characters")
    print(f"  Contains HTML: {'<html>' in body}")
    print()
    
    # Send test email
    print("Sending test email...")
    try:
        sender = GmailSender()
        sender.authenticate()
        
        message_id = sender.send_message(
            to_email=your_email,
            subject=subject,
            body=body
        )
        
        if message_id:
            print()
            print("=" * 70)
            print("SUCCESS!")
            print("=" * 70)
            print(f"Test email sent to: {your_email}")
            print(f"Message ID: {message_id}")
            print()
            print("Check your inbox (and spam folder) to see the formatted email!")
            print("The email should have:")
            print("  ✓ Clickable links")
            print("  ✓ Bold text")
            print("  ✓ Proper formatting")
            print("  ✓ Professional appearance")
            print("=" * 70)
        else:
            print("ERROR: Failed to send email")
            sys.exit(1)
    
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
