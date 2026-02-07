#!/usr/bin/env python3
"""
Process markdown email template with <<placeholders>> and generate emails.
Converts markdown to HTML for proper email rendering.
"""

import re
from pathlib import Path
from typing import Dict, Optional
from pdf_parser import PlaylistContact


class TemplateProcessor:
    """Process markdown templates with placeholders."""
    
    def __init__(self, template_file: str = 'email_template.md'):
        self.template_file = Path(template_file)
        self.template_content = None
        self.load_template()
    
    def load_template(self):
        """Load template from file."""
        if not self.template_file.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_file}")
        
        with open(self.template_file, 'r', encoding='utf-8') as f:
            self.template_content = f.read()
    
    def process(self, contact: PlaylistContact, 
                artist_name: Optional[str] = None,
                custom_message: Optional[str] = None,
                artist_spotify_link: Optional[str] = None,
                artist_instagram: Optional[str] = None,
                artist_website: Optional[str] = None,
                additional_info: Optional[str] = None,
                custom_subject: Optional[str] = None) -> Dict[str, str]:
        """
        Process template with contact data.
        
        Returns:
            Dictionary with 'subject' and 'body' keys
        """
        if not self.template_content:
            raise ValueError("Template not loaded")
        
        # Extract subject if it's in the template
        subject_match = re.search(r'\*\*Subject:\*\*\s*<<subject>>', self.template_content)
        if subject_match:
            # Subject is in template, extract it
            subject_line = re.search(r'\*\*Subject:\*\*\s*(.+?)(?:\n|$)', self.template_content)
            if subject_line:
                subject_template = subject_line.group(1).strip()
            else:
                subject_template = "<<subject>>"
        else:
            # Generate default subject
            if custom_subject:
                subject_template = custom_subject
            elif contact.playlist_name:
                subject_template = f"Music Submission for {contact.playlist_name}"
            elif contact.curator:
                subject_template = f"Music Submission - {contact.curator}"
            else:
                subject_template = "Music Submission"
        
        # Filter genres to only show relevant ones (POP, INDIE, Americana, etc.)
        # Exclude: RAP, EDM, ROCK, HIP HOP, METAL, PUNK, etc.
        relevant_genres = self._filter_relevant_genres(contact.genres)
        
        # Prepare replacement values
        replacements = {
            'subject': self._generate_subject(contact, custom_subject),
            'curator_name': contact.curator or 'there',
            'custom_message': custom_message or "I hope this email finds you well. I'm reaching out because I believe my music would be a great fit for your playlist.",
            'playlist_name': contact.playlist_name or 'your playlist',
            'genres': relevant_genres or 'various genres',
            'followers': contact.followers or 'N/A',
            'spotify_url': contact.spotify_url or 'N/A',
            'artist_name': artist_name or '[Your Name]',
            'additional_info': additional_info or '',
            'artist_spotify_link': artist_spotify_link or '[Your Spotify Link]',
            'artist_instagram': f"@{artist_instagram}" if artist_instagram and not artist_instagram.startswith('@') else (artist_instagram or '[Your Instagram]'),
            'artist_website': artist_website or '[Your Website]',
        }
        
        # Process template - extract just the email body
        body = self.template_content
        
        # Find the actual email content (between first --- and Available Placeholders section)
        lines = body.split('\n')
        body_lines = []
        in_email_body = False
        skip_until_dash = True
        
        for line in lines:
            # Skip until we find the first --- separator
            if skip_until_dash:
                if line.strip().startswith('---'):
                    skip_until_dash = False
                    in_email_body = True
                    continue
                continue
            
            # Stop at documentation sections (but keep credentials!)
            if 'Available Placeholders' in line or 'Example Usage' in line:
                break
            
            # Skip markdown headers (but keep content after them)
            if line.strip().startswith('#') and not in_email_body:
                continue
            
            if in_email_body:
                body_lines.append(line)
        
        body = '\n'.join(body_lines).strip()
        
        # Remove subject line if it's in the body
        body = re.sub(r'\*\*Subject:\*\*\s*.+?\n', '', body)
        
        # Replace all placeholders
        for key, value in replacements.items():
            placeholder = f'<<{key}>>'
            body = body.replace(placeholder, str(value))
        
        # Clean up empty sections
        body = re.sub(r'\*\*.*?:\*\*\s*N/A\n', '', body)
        body = re.sub(r'\*\*.*?:\*\*\s*\[.*?\]\n', '', body)
        
        # Convert markdown to HTML for email
        html_body = self._markdown_to_html(body)
        
        # Create proper plain text version (no markdown) from the processed body
        plain_text_lines = []
        prev_was_empty = False
        for line in body.split('\n'):
            stripped = line.strip()
            if not stripped:
                # Add spacing between sections
                if not prev_was_empty and plain_text_lines:
                    plain_text_lines.append('')
                prev_was_empty = True
                continue
            if stripped.startswith('---'):
                continue
            prev_was_empty = False
            # Remove markdown formatting
            plain = re.sub(r'\*\*(.+?)\*\*', r'\1', stripped)  # Remove bold
            plain = re.sub(r'##+\s*', '', plain)  # Remove headers
            plain = re.sub(r'^-\s+', '', plain)  # Remove list markers
            plain = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', plain)  # Remove link formatting
            if plain:
                plain_text_lines.append(plain)
        
        plain_text_body = '\n'.join(plain_text_lines)
        
        return {
            'subject': replacements['subject'],
            'body': html_body.strip(),
            'body_plain': plain_text_body.strip()  # Clean plain text version
        }
    
    def _markdown_to_html(self, markdown_text: str) -> str:
        """Convert markdown to HTML for email rendering - Gmail-compatible with tables."""
        lines = markdown_text.split('\n')
        html_lines = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines (spacing handled by paragraph margins)
            if not stripped:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                continue
            
            # Headers - use divs with strong tags and explicit styling (Gmail-friendly)
            if stripped.startswith('## '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                header_text = stripped[3:].strip()
                # Convert any markdown in header
                header_text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight: bold;">\1</strong>', header_text)
                html_lines.append(f'<div style="font-size: 20px; font-weight: bold; color: #2c3e50; margin-top: 25px; margin-bottom: 12px; padding-bottom: 8px; font-family: Arial, Helvetica, sans-serif;"><strong style="font-weight: bold; font-size: 20px; color: #2c3e50;">{header_text}</strong></div>')
                continue
            
            if stripped.startswith('### '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                header_text = stripped[4:].strip()
                # Convert any markdown in header
                header_text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight: bold;">\1</strong>', header_text)
                html_lines.append(f'<div style="font-size: 18px; font-weight: bold; color: #34495e; margin-top: 18px; margin-bottom: 10px; font-family: Arial, Helvetica, sans-serif;"><strong style="font-weight: bold; font-size: 18px; color: #34495e;">{header_text}</strong></div>')
                continue
            
            # List items
            if stripped.startswith('- '):
                if not in_list:
                    html_lines.append('<ul style="margin: 10px 0; padding-left: 25px;">')
                    in_list = True
                item_text = stripped[2:].strip()
                # Convert bold and links in list items with inline styles
                item_text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight: bold; color: #333333; font-family: Arial, Helvetica, sans-serif;">\1</strong>', item_text)
                item_text = re.sub(r'(https?://[^\s]+)', r'<a href="\1" style="color: #3498db; text-decoration: none;">\1</a>', item_text)
                html_lines.append(f'<li style="margin: 6px 0; line-height: 1.6; font-family: Arial, Helvetica, sans-serif;">{item_text}</li>')
                continue
            
            # Close list if needed
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            
            # Skip separator lines
            if stripped.startswith('---'):
                continue
            
            # Regular paragraph - convert markdown to HTML
            para_text = stripped
            
            # Handle bold labels followed by colons (like "**Label:** value") - keep on same line
            # Convert bold **text** to <strong> with explicit bold styling
            para_text = re.sub(r'\*\*(.+?)\*\*', r'<strong style="font-weight: bold; color: #2c3e50; font-family: Arial, Helvetica, sans-serif;">\1</strong>', para_text)
            
            # Convert URLs to links with inline styles
            para_text = re.sub(r'(https?://[^\s<>"{}|\\^`\[\]]+)', r'<a href="\1" style="color: #3498db; text-decoration: none;">\1</a>', para_text)
            
            # Convert markdown links [text](url) with inline styles
            para_text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2" style="color: #3498db; text-decoration: none;">\1</a>', para_text)
            
            html_lines.append(f'<p style="margin: 12px 0; line-height: 1.7; font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #333333;">{para_text}</p>')
        
        if in_list:
            html_lines.append('</ul>')
        
        html_content = '\n'.join(html_lines)
        
        # HTML wrapper with table-based layout for maximum Gmail compatibility
        html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f4;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f4f4f4;">
<tr>
<td align="center" style="padding: 20px;">
<table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 4px;">
<tr>
<td style="padding: 30px; font-family: Arial, Helvetica, sans-serif; font-size: 14px; line-height: 1.7; color: #333333;">
{html_content}
</td>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>"""
        
        return html_body
    
    def _filter_relevant_genres(self, genres: Optional[str]) -> Optional[str]:
        """
        Filter genres to only include relevant ones for indie pop/Americana music.
        Includes: POP, INDIE, Americana, FOLK, ACOUSTIC, SINGER/SONGWRITER, etc.
        Excludes: RAP, EDM, ROCK, HIP HOP, METAL, PUNK, etc.
        """
        if not genres:
            return None
        
        # Relevant genre keywords (case-insensitive)
        relevant_keywords = [
            'pop', 'indie', 'americana', 'folk', 'acoustic', 'singer', 'songwriter',
            'soft', 'alternative', 'country', 'roots', 'bluegrass', 'soul', 'r&b',
            'jazz', 'blues', 'ballad', 'melodic', 'chill', 'ambient'
        ]
        
        # Exclude these genres
        exclude_keywords = [
            'rap', 'hip hop', 'edm', 'electronic', 'rock', 'metal', 'punk', 'hardcore',
            'techno', 'house', 'dance', 'trance', 'dubstep', 'brostep', 'grunge',
            'hard rock', 'heavy metal', 'death metal', 'thrash'
        ]
        
        # Split genres by comma and filter
        genre_list = [g.strip() for g in genres.split(',')]
        filtered_genres = []
        
        for genre in genre_list:
            genre_lower = genre.lower()
            # Check if it should be excluded
            if any(exclude in genre_lower for exclude in exclude_keywords):
                continue
            # Check if it's relevant
            if any(relevant in genre_lower for relevant in relevant_keywords):
                filtered_genres.append(genre)
        
        if filtered_genres:
            return ', '.join(filtered_genres)
        else:
            # If no relevant genres found, return original but cleaned up
            return genres
    
    def _generate_subject(self, contact: PlaylistContact, custom_subject: Optional[str] = None) -> str:
        """Generate email subject."""
        if custom_subject:
            return custom_subject
        
        if contact.playlist_name:
            return f"Music Submission for {contact.playlist_name}"
        elif contact.curator:
            return f"Music Submission - {contact.curator}"
        else:
            return "Music Submission"


if __name__ == '__main__':
    # Test
    from pdf_parser import PlaylistContact
    
    test_contact = PlaylistContact(
        playlist_name="#1 Gaming Playlist",
        curator="Felix Krissmayr",
        genres="RAP, ROCK, HIP HOP",
        spotify_url="https://open.spotify.com/playlist/1DRpqg3Vlub1gKMWN14gCg",
        followers="8,350",
        email="felix@pro-gamer-gear.de"
    )
    
    processor = TemplateProcessor()
    result = processor.process(
        test_contact,
        artist_name="Test Artist",
        custom_message="I'm a huge fan of your playlist!",
        artist_spotify_link="https://open.spotify.com/artist/test"
    )
    
    print("Subject:", result['subject'])
    print("\nBody:")
    print(result['body'])
