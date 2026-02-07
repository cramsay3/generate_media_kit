#!/usr/bin/env python3
"""
Generate email templates for playlist contacts.
Supports markdown template files with <<field_name>> placeholders.
"""

import re
from pathlib import Path
from typing import Optional
from pdf_parser import PlaylistContact


class EmailTemplate:
    """Generate email content from playlist contact data."""
    
    @staticmethod
    def load_template(template_file: str = 'email_template.md') -> Optional[str]:
        """Load email template from markdown file."""
        template_path = Path(template_file)
        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
        return None
    
    @staticmethod
    def render_template(template_text: str, contact: PlaylistContact,
                       artist_name: Optional[str] = None,
                       custom_message: Optional[str] = None,
                       custom_subject: Optional[str] = None) -> str:
        """
        Render template with placeholders.
        
        Placeholders:
        - <<artist_name>>
        - <<curator_name>>
        - <<playlist_name>>
        - <<genres>>
        - <<followers>>
        - <<spotify_url>>
        - <<instagram>>
        - <<custom_message>>
        - <<subject>>
        """
        # Extract just the email body (skip documentation sections)
        lines = template_text.split('\n')
        body_lines = []
        skip_sections = False
        
        for line in lines:
            # Skip markdown headers and documentation
            if line.strip().startswith('#') or line.strip().startswith('##'):
                skip_sections = True
                continue
            if '---' in line and skip_sections:
                skip_sections = False
                continue
            if skip_sections:
                continue
            # Skip "Available Fields" and "Notes" sections
            if 'Available Fields' in line or 'Notes' in line or 'Email Template' in line:
                skip_sections = True
                continue
            
            body_lines.append(line)
        
        template_text = '\n'.join(body_lines).strip()
        
        # Replace placeholders
        replacements = {
            '<<artist_name>>': artist_name or '[Your Name]',
            '<<curator_name>>': contact.curator or 'there',
            '<<playlist_name>>': contact.playlist_name or 'your playlist',
            '<<genres>>': contact.genres or 'various genres',
            '<<followers>>': contact.followers or 'many',
            '<<spotify_url>>': contact.spotify_url or '[Spotify URL]',
            '<<instagram>>': f"Instagram: {contact.instagram}" if contact.instagram else '',
            '<<custom_message>>': custom_message or "I hope this email finds you well. I'm reaching out to submit my music for consideration for your playlist."
        }
        
        result = template_text
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, str(value))
        
        # Clean up empty lines
        lines = result.split('\n')
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append('')
                prev_empty = True
        
        return '\n'.join(cleaned_lines).strip()
    
    @staticmethod
    def generate_subject(contact: PlaylistContact, custom_subject: Optional[str] = None) -> str:
        """Generate email subject line."""
        if custom_subject:
            return custom_subject
        
        if contact.playlist_name:
            return f"Music Submission for {contact.playlist_name}"
        elif contact.curator:
            return f"Music Submission - {contact.curator}"
        else:
            return "Music Submission"
    
    @staticmethod
    def generate_body(contact: PlaylistContact, 
                     artist_name: Optional[str] = None,
                     custom_message: Optional[str] = None,
                     template_file: Optional[str] = None) -> str:
        """
        Generate email body with all available playlist information.
        
        Args:
            contact: PlaylistContact object with playlist data
            artist_name: Name of the artist submitting music
            custom_message: Custom message to include (optional)
            template_file: Path to markdown template file (optional)
        """
        # Try to load custom template
        if template_file:
            template_text = EmailTemplate.load_template(template_file)
            if template_text:
                # Extract body (everything after Subject line)
                lines = template_text.split('\n')
                body_start = 0
                for i, line in enumerate(lines):
                    if '**Subject:**' in line or 'Subject:' in line:
                        body_start = i + 1
                        break
                
                body_template = '\n'.join(lines[body_start:])
                return EmailTemplate.render_template(
                    body_template, contact, artist_name, custom_message
                )
        
        # Fallback to default template
        parts = []
        
        # Greeting
        if contact.curator:
            parts.append(f"Hello {contact.curator},")
        else:
            parts.append("Hello,")
        
        parts.append("")
        
        # Custom message or default
        if custom_message:
            parts.append(custom_message)
        else:
            parts.append("I hope this email finds you well. I'm reaching out to submit my music for consideration for your playlist.")
        
        parts.append("")
        
        # Playlist information
        if contact.playlist_name:
            parts.append(f"Playlist: {contact.playlist_name}")
        
        if contact.genres:
            parts.append(f"Genres: {contact.genres}")
        
        if contact.followers:
            parts.append(f"Followers: {contact.followers}")
        
        if contact.spotify_url:
            parts.append(f"Spotify Link: {contact.spotify_url}")
        
        parts.append("")
        
        # Artist information
        if artist_name:
            parts.append(f"Artist Name: {artist_name}")
        
        parts.append("")
        
        # Closing
        parts.append("Thank you for your time and consideration.")
        parts.append("")
        parts.append("Best regards,")
        if artist_name:
            parts.append(artist_name)
        else:
            parts.append("[Your Name]")
        
        # Additional links
        if contact.instagram:
            parts.append("")
            parts.append(f"Instagram: {contact.instagram}")
        
        if contact.other_links:
            parts.append("")
            parts.append("Additional Links:")
            for link in contact.other_links:
                parts.append(f"  - {link}")
        
        return "\n".join(parts)
    
    @staticmethod
    def generate_html_body(contact: PlaylistContact,
                          artist_name: Optional[str] = None,
                          custom_message: Optional[str] = None) -> str:
        """Generate HTML email body."""
        html_parts = []
        html_parts.append("<html><body>")
        
        # Greeting
        if contact.curator:
            html_parts.append(f"<p>Hello {contact.curator},</p>")
        else:
            html_parts.append("<p>Hello,</p>")
        
        # Custom message or default
        if custom_message:
            html_parts.append(f"<p>{custom_message.replace(chr(10), '<br>')}</p>")
        else:
            html_parts.append("<p>I hope this email finds you well. I'm reaching out to submit my music for consideration for your playlist.</p>")
        
        # Playlist information
        html_parts.append("<p><strong>Playlist Information:</strong></p>")
        html_parts.append("<ul>")
        
        if contact.playlist_name:
            html_parts.append(f"<li><strong>Playlist:</strong> {contact.playlist_name}</li>")
        
        if contact.genres:
            html_parts.append(f"<li><strong>Genres:</strong> {contact.genres}</li>")
        
        if contact.followers:
            html_parts.append(f"<li><strong>Followers:</strong> {contact.followers}</li>")
        
        if contact.spotify_url:
            html_parts.append(f"<li><strong>Spotify Link:</strong> <a href='{contact.spotify_url}'>{contact.spotify_url}</a></li>")
        
        html_parts.append("</ul>")
        
        # Artist information
        if artist_name:
            html_parts.append(f"<p><strong>Artist Name:</strong> {artist_name}</p>")
        
        # Closing
        html_parts.append("<p>Thank you for your time and consideration.</p>")
        html_parts.append("<p>Best regards,<br>")
        if artist_name:
            html_parts.append(artist_name)
        else:
            html_parts.append("[Your Name]")
        html_parts.append("</p>")
        
        # Additional links
        if contact.instagram:
            html_parts.append(f"<p><a href='{contact.instagram}'>Instagram</a></p>")
        
        if contact.other_links:
            html_parts.append("<p><strong>Additional Links:</strong></p><ul>")
            for link in contact.other_links:
                html_parts.append(f"<li><a href='{link}'>{link}</a></li>")
            html_parts.append("</ul>")
        
        html_parts.append("</body></html>")
        
        return "\n".join(html_parts)


if __name__ == '__main__':
    # Test template generation
    from pdf_parser import PlaylistContact
    
    test_contact = PlaylistContact(
        playlist_name="#1 Gaming Playlist",
        curator="Felix Krissmayr",
        genres="RAP, ROCK, HIP HOP, POST-GRUNGE, EDM, POP",
        spotify_url="https://open.spotify.com/playlist/1DRpqg3Vlub1gKMWN14gCg",
        followers="8,350",
        email="felix@pro-gamer-gear.de"
    )
    
    subject = EmailTemplate.generate_subject(test_contact)
    body = EmailTemplate.generate_body(test_contact, artist_name="Test Artist")
    
    print("Subject:", subject)
    print("\nBody:")
    print(body)
