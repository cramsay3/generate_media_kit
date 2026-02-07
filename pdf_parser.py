#!/usr/bin/env python3
"""
Parse Spotify Playlist Contacts PDF and extract structured contact information.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PlaylistContact:
    """Represents a playlist contact entry."""
    playlist_name: str = ""
    curator: str = ""
    genres: str = ""
    spotify_url: str = ""
    followers: str = ""
    email: str = ""
    instagram: str = ""
    other_links: List[str] = None
    
    def __post_init__(self):
        if self.other_links is None:
            self.other_links = []


class PDFParser:
    """Parse extracted PDF text into structured playlist contact data."""
    
    def __init__(self, pdf_text_file: str):
        self.pdf_text_file = pdf_text_file
        self.contacts: List[PlaylistContact] = []
    
    def parse(self) -> List[PlaylistContact]:
        """Parse the PDF text file and return list of PlaylistContact objects."""
        with open(self.pdf_text_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [line.strip() for line in f.readlines()]
        
        contacts = []
        current_contact = PlaylistContact()
        pending_data = {}  # Store data before we find the email
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Skip header lines
            if line in ['Playlist Name', 'Curator', 'Genres', 'Followers', 'Best Way To Contact']:
                i += 1
                continue
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Detect email addresses - this is our key anchor point
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line)
            if email_match:
                # Save previous contact if it has data
                if current_contact.email or current_contact.spotify_url:
                    contacts.append(current_contact)
                
                # Start new contact
                current_contact = PlaylistContact()
                email = email_match.group(0)
                current_contact.email = email
                
                # Apply any pending data we collected
                if 'playlist_name' in pending_data:
                    current_contact.playlist_name = pending_data['playlist_name']
                if 'curator' in pending_data:
                    current_contact.curator = pending_data['curator']
                if 'spotify_url' in pending_data:
                    current_contact.spotify_url = pending_data['spotify_url']
                if 'followers' in pending_data:
                    current_contact.followers = pending_data['followers']
                if 'genres' in pending_data:
                    current_contact.genres = pending_data['genres']
                
                pending_data = {}
                
                # Remove email from line to get remaining text (might be genres)
                remaining = line.replace(email, '').strip()
                if remaining and not re.match(r'^\d+[,\d]*$', remaining.replace(',', '').replace(' ', '')):
                    if current_contact.genres:
                        current_contact.genres += ", " + remaining
                    else:
                        current_contact.genres = remaining
            
            # Detect Spotify URLs
            elif 'spotify.com' in line.lower():
                if current_contact.email:
                    # We have a contact, add to it
                    if not current_contact.spotify_url:
                        current_contact.spotify_url = line
                    else:
                        if not current_contact.other_links:
                            current_contact.other_links = []
                        current_contact.other_links.append(line)
                else:
                    # Store for when we find the email
                    pending_data['spotify_url'] = line
            
            # Detect Instagram URLs
            elif 'instagram.com' in line.lower():
                if current_contact.email:
                    if not current_contact.instagram:
                        current_contact.instagram = line
                    else:
                        if not current_contact.other_links:
                            current_contact.other_links = []
                        current_contact.other_links.append(line)
            
            # Detect follower counts (numbers with optional commas, usually standalone)
            elif re.match(r'^\d+[,\d]*\s*$', line.replace(',', '').replace(' ', '')):
                followers = line.strip()
                if current_contact.email:
                    if not current_contact.followers:
                        current_contact.followers = followers
                else:
                    pending_data['followers'] = followers
            
            # Detect URLs (other than Spotify/Instagram)
            elif line.startswith('http://') or line.startswith('https://'):
                if current_contact.email:
                    if not current_contact.other_links:
                        current_contact.other_links = []
                    current_contact.other_links.append(line)
            
            # Look backwards and forwards to find playlist name and curator
            # Playlist name is usually before Spotify URL, curator is often between them
            elif current_contact.email or 'spotify_url' in pending_data:
                # We're in a contact block, look for playlist name and curator
                # Genres are usually uppercase, comma-separated
                genre_indicators = ['ROCK', 'POP', 'HIP', 'HOP', 'EDM', 'INDIE', 'ELECTRONIC', 
                                   'FOLK', 'SOUL', 'R&B', 'JAZZ', 'BLUES', 'PUNK', 'METAL',
                                   'ALTERNATIVE', 'ACOUSTIC', 'DANCE', 'TRIPHOP', 'CHILLWAVE']
                
                # Check if this looks like genres
                if any(indicator in line.upper() for indicator in genre_indicators) and len(line) > 5:
                    if current_contact.email:
                        if current_contact.genres:
                            current_contact.genres += ", " + line
                        else:
                            current_contact.genres = line
                    else:
                        if 'genres' in pending_data:
                            pending_data['genres'] += ", " + line
                        else:
                            pending_data['genres'] = line
                
                # Look backwards for playlist name (before Spotify URL)
                elif not current_contact.playlist_name and i > 0:
                    # Check previous lines for playlist name
                    for j in range(max(0, i-10), i):
                        prev_line = lines[j]
                        if (prev_line and 
                            len(prev_line) < 100 and 
                            '@' not in prev_line and 
                            'spotify' not in prev_line.lower() and
                            not prev_line.startswith('http') and
                            not re.match(r'^\d+[,\d]*\s*$', prev_line.replace(',', '').replace(' ', '')) and
                            prev_line not in ['Playlist Name', 'Curator', 'Genres']):
                            
                            # Check if next line after this is Spotify URL
                            if j + 1 < len(lines) and 'spotify' in lines[j+1].lower():
                                if current_contact.email:
                                    current_contact.playlist_name = prev_line
                                else:
                                    pending_data['playlist_name'] = prev_line
                                break
                
                # Look for curator (usually a name, not genres, between playlist and Spotify)
                elif (current_contact.playlist_name or 'playlist_name' in pending_data) and not current_contact.curator:
                    if (len(line) < 80 and 
                        '@' not in line and 
                        'spotify' not in line.lower() and
                        not line.startswith('http') and
                        not re.match(r'^\d+[,\d]*\s*$', line.replace(',', '').replace(' ', '')) and
                        not any(indicator in line.upper() for indicator in genre_indicators)):
                        
                        # Check if next line is Spotify URL
                        if i + 1 < len(lines) and 'spotify' in lines[i+1].lower():
                            if current_contact.email:
                                current_contact.curator = line
                            else:
                                pending_data['curator'] = line
            
            i += 1
        
        # Add last contact if it has data
        if current_contact.email or current_contact.spotify_url:
            contacts.append(current_contact)
        
        # Clean up contacts
        cleaned_contacts = []
        for contact in contacts:
            # Only include contacts with at least an email or Spotify URL
            if contact.email or contact.spotify_url:
                # Clean up genres
                if contact.genres:
                    contact.genres = re.sub(r'\s+', ' ', contact.genres).strip()
                    contact.genres = re.sub(r',+', ',', contact.genres)
                    # Remove any trailing numbers that got mixed in
                    contact.genres = re.sub(r',\s*\d+[,\d]*\s*$', '', contact.genres)
                cleaned_contacts.append(contact)
        
        self.contacts = cleaned_contacts
        return cleaned_contacts
    
    def get_contact_by_email(self, email: str) -> Optional[PlaylistContact]:
        """Find a contact by email address (case-insensitive)."""
        email_lower = email.lower().strip()
        for contact in self.contacts:
            if contact.email.lower().strip() == email_lower:
                return contact
        return None
    
    def get_all_emails(self) -> List[str]:
        """Get all email addresses from parsed contacts."""
        return [c.email for c in self.contacts if c.email]


if __name__ == '__main__':
    # Test parsing
    parser = PDFParser('playlist_contacts.txt')
    contacts = parser.parse()
    print(f"Parsed {len(contacts)} contacts")
    
    # Show first few
    for i, contact in enumerate(contacts[:5]):
        print(f"\n--- Contact {i+1} ---")
        print(f"Playlist: {contact.playlist_name}")
        print(f"Curator: {contact.curator}")
        print(f"Email: {contact.email}")
        print(f"Spotify: {contact.spotify_url}")
        print(f"Followers: {contact.followers}")
        print(f"Genres: {contact.genres[:100]}...")
