#!/usr/bin/env python3
"""
Instagram Following Script
Extracts Instagram handles from contacts and follows them as part of the campaign.
"""

import re
import time
import json
import random
import argparse
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import yaml

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use command line args

from pdf_parser import PDFParser
from email_validator import EmailValidator


def extract_instagram_username(instagram_url: str) -> Optional[str]:
    """Extract username from Instagram URL."""
    if not instagram_url:
        return None
    
    # Clean up the URL
    instagram_url = instagram_url.strip()
    
    # Pattern 1: Full URL with https://www.instagram.com/username
    match = re.search(r'https?://(?:www\.)?instagram\.com/([^/?\s]+)', instagram_url, re.IGNORECASE)
    if match:
        username = match.group(1)
        if username and len(username) > 0 and len(username) < 31:
            return username
    
    # Pattern 2: instagram.com/username (without http)
    match = re.search(r'instagram\.com/([^/?\s]+)', instagram_url, re.IGNORECASE)
    if match:
        username = match.group(1)
        if username and len(username) > 0 and len(username) < 31:
            return username
    
    # Pattern 3: @username or just username
    match = re.search(r'@?([a-zA-Z0-9._]{1,30})', instagram_url)
    if match:
        username = match.group(1)
        # Make sure it's not part of an email or other URL
        if '@' not in instagram_url[:match.start()] and 'http' not in instagram_url.lower():
            if username and len(username) > 0 and len(username) < 31:
                return username
    
    return None


def filter_by_genres(contact, genre_keywords, exclude_keywords=None):
    """Filter contacts by genre keywords."""
    if not contact.genres or not genre_keywords:
        return False
    genres_lower = contact.genres.lower()
    matches = any(keyword.lower() in genres_lower for keyword in genre_keywords)
    if not matches:
        return False
    if exclude_keywords:
        excluded = any(excl.lower() in genres_lower for excl in exclude_keywords)
        if excluded:
            return False
    return True


def load_progress(progress_file: str) -> Dict:
    """Load progress from JSON file."""
    if Path(progress_file).exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {
        'followed': [],
        'failed': [],
        'skipped': [],
        'hourly_count': 0,
        'daily_count': 0,
        'hour_start': None,
        'last_follow_time': None
    }


def save_progress(progress: Dict, progress_file: str):
    """Save progress to JSON file."""
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)


def calculate_delay(progress: Dict, min_delay: int, max_delay: int, 
                    max_per_hour: int, max_per_day: int) -> tuple:
    """Calculate delay and check rate limits."""
    now = datetime.now()
    
    # Check daily limit
    if progress.get('daily_count', 0) >= max_per_day:
        # Check if 24 hours have passed
        last_follow = progress.get('last_follow_time')
        if last_follow:
            last_time = datetime.fromisoformat(last_follow)
            if (now - last_time).total_seconds() < 86400:  # 24 hours
                wait_seconds = 86400 - (now - last_time).total_seconds()
                return wait_seconds, "daily limit reached"
            else:
                # Reset daily count
                progress['daily_count'] = 0
    
    # Check hourly limit
    hour_start = progress.get('hour_start')
    if hour_start:
        start_time = datetime.fromisoformat(hour_start)
        if (now - start_time).total_seconds() < 3600:  # 1 hour
            if progress.get('hourly_count', 0) >= max_per_hour:
                wait_seconds = 3600 - (now - start_time).total_seconds()
                return wait_seconds, "hourly limit reached"
        else:
            # Reset hourly count
            progress['hourly_count'] = 0
            progress['hour_start'] = now.isoformat()
    else:
        progress['hour_start'] = now.isoformat()
    
    # Random delay between min and max
    delay = random.randint(min_delay, max_delay)
    return delay, None


def log_message(message: str, log_file: Optional[str] = None):
    """Log message to console and optionally to file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    if log_file:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')


def main():
    parser = argparse.ArgumentParser(description='Follow Instagram accounts from playlist contacts')
    parser.add_argument('--username', default=None, help='Instagram username (or set IG_USERNAME in .env)')
    parser.add_argument('--password', default=None, help='Instagram password (or set IG_PASSWORD in .env)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no actual follows)')
    parser.add_argument('--resume', action='store_true', help='Resume from previous progress')
    parser.add_argument('--limit', type=int, help='Limit number of follows (for testing)')
    parser.add_argument('--config', default='config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    # Get credentials from args, .env, or error
    username = args.username or os.getenv('IG_USERNAME')
    password = args.password or os.getenv('IG_PASSWORD')
    
    if not username or not password:
        print("ERROR: Instagram credentials required!")
        print("Set IG_USERNAME and IG_PASSWORD in .env file, or use --username and --password arguments")
        return
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        log_message(f"ERROR: Config file not found: {config_path}")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
    
    # Get Instagram settings from config (with defaults)
    instagram_config = config.get('instagram', {})
    min_delay = instagram_config.get('min_delay_seconds', 60)
    max_delay = instagram_config.get('max_delay_seconds', 180)
    max_per_hour = instagram_config.get('max_per_hour', 20)
    max_per_day = instagram_config.get('max_per_day', 100)
    
    # Get genre filtering settings
    genre_keywords = config.get('email', {}).get('genre_keywords', [])
    exclude_genres = config.get('email', {}).get('exclude_genres', [])
    
    # Progress tracking
    progress_file = 'instagram_progress.json'
    log_file = 'instagram_follow.log'
    
    progress = load_progress(progress_file) if args.resume else {
        'followed': [],
        'failed': [],
        'skipped': [],
        'hourly_count': 0,
        'daily_count': 0,
        'hour_start': None,
        'last_follow_time': None
    }
    
    log_message("=" * 60, log_file)
    log_message("INSTAGRAM FOLLOWING CAMPAIGN", log_file)
    log_message("=" * 60, log_file)
    if args.dry_run:
        log_message("DRY RUN MODE - No actual follows will be performed", log_file)
    log_message("", log_file)
    
    # Parse contacts
    pdf_text_file = config.get('files', {}).get('pdf_text', 'playlist_contacts.txt')
    parser = PDFParser(pdf_text_file)
    all_contacts = parser.parse()
    
    # Filter contacts with Instagram
    contacts_with_instagram = [c for c in all_contacts if c.instagram]
    
    # Apply genre filtering if configured
    if genre_keywords:
        contacts_with_instagram = [c for c in contacts_with_instagram 
                                  if filter_by_genres(c, genre_keywords, exclude_genres)]
    
    log_message(f"Total contacts with Instagram: {len(contacts_with_instagram)}", log_file)
    
    # Extract Instagram usernames
    instagram_data = []
    for contact in contacts_with_instagram:
        username = extract_instagram_username(contact.instagram)
        if username:
            # Skip if already followed or failed
            if username.lower() in [u.lower() for u in progress['followed']]:
                continue
            if username.lower() in [u.lower() for u in progress['failed']]:
                continue
            
            instagram_data.append({
                'username': username,
                'contact': contact
            })
    
    log_message(f"Unique Instagram accounts to follow: {len(instagram_data)}", log_file)
    
    if args.limit:
        instagram_data = instagram_data[:args.limit]
        log_message(f"Limited to first {args.limit} accounts", log_file)
    
    log_message("", log_file)
    
    # Initialize Instagram client
    if not args.dry_run:
        try:
            from instagrapi import Client
            from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes, ChallengeRequired, BadCredentials
        except ImportError:
            log_message("ERROR: instagrapi library not installed.", log_file)
            log_message("Install it with: pip install instagrapi", log_file)
            return
        
        cl = Client()
        session_file = 'instagram_session.json'
        
        # Try to load existing session first
        if Path(session_file).exists():
            try:
                log_message("Loading existing Instagram session...", log_file)
                cl.load_settings(session_file)
                # Try to login with saved session
                try:
                    cl.get_timeline_feed()  # Test if session is still valid
                    log_message("✓ Using existing session", log_file)
                except:
                    log_message("Session expired, logging in again...", log_file)
                    raise LoginRequired("Session expired")
            except:
                # Session invalid, need to login
                pass
        
        # Login (either new or after failed session)
        try:
            log_message("Logging into Instagram...", log_file)
            cl.login(username, password)
            # Save session for next time
            cl.dump_settings(session_file)
            log_message("✓ Successfully logged in and session saved", log_file)
        except ChallengeRequired as e:
            log_message(f"2FA Challenge Required: {e}", log_file)
            log_message("", log_file)
            log_message("Instagram requires 2FA verification code.", log_file)
            log_message("Check your email or authenticator app for the code.", log_file)
            
            # Try to handle 2FA challenge
            try:
                # Try to resolve challenge (sends code to email/SMS)
                log_message("Attempting to resolve challenge...", log_file)
                try:
                    challenge = cl.challenge_resolve()
                    if challenge:
                        log_message("Challenge code sent. Check your email or SMS.", log_file)
                except:
                    log_message("Challenge already initiated or alternative method needed.", log_file)
                
                challenge_code = input("Enter your 2FA code: ").strip()
                if challenge_code:
                    log_message("Submitting 2FA code...", log_file)
                    cl.challenge_code_handler(username, challenge_code)
                    cl.dump_settings(session_file)
                    log_message("✓ Successfully logged in with 2FA and session saved", log_file)
                else:
                    log_message("No code provided. Exiting.", log_file)
                    return
            except Exception as challenge_error:
                log_message(f"Failed to complete 2FA challenge: {challenge_error}", log_file)
                log_message("", log_file)
                log_message("ALTERNATIVE SOLUTIONS:", log_file)
                log_message("1. Temporarily disable 2FA in Instagram settings (Security → Two-Factor Authentication)", log_file)
                log_message("2. Use an app-specific password if available", log_file)
                log_message("3. Log in manually in browser first, complete 2FA, then try script", log_file)
                log_message("4. Wait 24 hours if IP is blacklisted, then try again", log_file)
                return
        except BadCredentials as e:
            log_message(f"ERROR: Invalid credentials: {e}", log_file)
            log_message("Check your username and password in .env file", log_file)
            return
        except PleaseWaitFewMinutes as e:
            log_message(f"ERROR: Rate limited by Instagram: {e}", log_file)
            log_message("Wait a few minutes and try again", log_file)
            return
        except Exception as e:
            error_msg = str(e)
            log_message(f"ERROR: Failed to login to Instagram: {error_msg}", log_file)
            
            if "blacklist" in error_msg.lower() or "ip" in error_msg.lower():
                log_message("", log_file)
                log_message("IP ADDRESS BLOCKED BY INSTAGRAM", log_file)
                log_message("SOLUTIONS:", log_file)
                log_message("1. Wait 24-48 hours for IP to be unblocked", log_file)
                log_message("2. Use a VPN to change your IP address", log_file)
                log_message("3. Log into Instagram manually in a browser first", log_file)
                log_message("4. Complete any security challenges", log_file)
                log_message("5. Try again after waiting", log_file)
            elif "password" in error_msg.lower() or "credentials" in error_msg.lower():
                log_message("", log_file)
                log_message("Check your credentials in .env file:", log_file)
                log_message(f"  IG_USERNAME={username}", log_file)
                log_message("  IG_PASSWORD=***", log_file)
                log_message("", log_file)
                log_message("Also ensure:", log_file)
                log_message("- 2FA is disabled on your Instagram account", log_file)
                log_message("- You can log in manually in a browser", log_file)
            else:
                log_message("", log_file)
                log_message("TROUBLESHOOTING:", log_file)
                log_message("1. Verify credentials work in browser", log_file)
                log_message("2. Disable 2FA on Instagram account", log_file)
                log_message("3. Wait and try again later", log_file)
            return
    
    # Follow accounts
    successful = []
    failed = []
    skipped = []
    
    for i, data in enumerate(instagram_data, 1):
        username = data['username']
        contact = data['contact']
        
        # Check rate limits
        delay, reason = calculate_delay(progress, min_delay, max_delay, max_per_hour, max_per_day)
        
        if reason:
            if reason == "daily limit reached":
                log_message(f"[{i}/{len(instagram_data)}] Daily limit reached. Stopping.", log_file)
                break
            elif reason == "hourly limit reached":
                log_message(f"[{i}/{len(instagram_data)}] Hourly limit reached. Waiting {delay/60:.1f} minutes...", log_file)
                time.sleep(delay)
                progress['hourly_count'] = 0
                progress['hour_start'] = datetime.now().isoformat()
        
        # Wait before following (except for first account)
        if i > 1:
            log_message(f"[{i}/{len(instagram_data)}] Waiting {delay:.1f} seconds before next follow...", log_file)
            time.sleep(delay)
        
        log_message(f"[{i}/{len(instagram_data)}] Following: @{username}", log_file)
        log_message(f"  Playlist: {contact.playlist_name or 'N/A'}", log_file)
        log_message(f"  Email: {contact.email or 'N/A'}", log_file)
        
        if args.dry_run:
            log_message(f"  [DRY RUN] Would follow @{username}", log_file)
            successful.append({
                'username': username,
                'contact': contact
            })
            progress['followed'].append(username.lower())
            progress['daily_count'] += 1
            progress['hourly_count'] += 1
            progress['last_follow_time'] = datetime.now().isoformat()
            if not progress.get('hour_start'):
                progress['hour_start'] = datetime.now().isoformat()
        else:
            try:
                from instagrapi.exceptions import PleaseWaitFewMinutes, ChallengeRequired
                
                # Get user ID from username
                user_id = cl.user_id_from_username(username)
                
                # Check if already following
                following = cl.user_following(cl.user_id)
                if user_id in following:
                    log_message(f"  ⚠ Already following @{username}", log_file)
                    skipped.append({
                        'username': username,
                        'contact': contact,
                        'reason': 'already_following'
                    })
                    progress['skipped'].append(username.lower())
                else:
                    # Follow the user
                    cl.user_follow(user_id)
                    log_message(f"  ✓ Successfully followed @{username}", log_file)
                    successful.append({
                        'username': username,
                        'contact': contact
                    })
                    progress['followed'].append(username.lower())
                    progress['daily_count'] += 1
                    progress['hourly_count'] += 1
                    progress['last_follow_time'] = datetime.now().isoformat()
                    if not progress.get('hour_start'):
                        progress['hour_start'] = datetime.now().isoformat()
                
                # Save progress after each follow
                save_progress(progress, progress_file)
                
            except PleaseWaitFewMinutes as e:
                log_message(f"  ✗ Rate limited: {e}. Waiting 5 minutes...", log_file)
                time.sleep(300)  # Wait 5 minutes
                failed.append({
                    'username': username,
                    'contact': contact,
                    'error': f'Rate limited: {e}'
                })
                progress['failed'].append(username.lower())
                save_progress(progress, progress_file)
                
            except ChallengeRequired as e:
                log_message(f"  ✗ Challenge required: {e}", log_file)
                log_message("  Instagram requires additional verification. Please login manually and try again.", log_file)
                failed.append({
                    'username': username,
                    'contact': contact,
                    'error': 'Challenge required'
                })
                progress['failed'].append(username.lower())
                save_progress(progress, progress_file)
                break  # Stop if challenge required
                
            except Exception as e:
                log_message(f"  ✗ Error: {e}", log_file)
                failed.append({
                    'username': username,
                    'contact': contact,
                    'error': str(e)
                })
                progress['failed'].append(username.lower())
                save_progress(progress, progress_file)
        
        log_message("", log_file)
    
    # Final summary
    log_message("=" * 60, log_file)
    log_message("CAMPAIGN SUMMARY", log_file)
    log_message("=" * 60, log_file)
    log_message(f"Successfully followed: {len(successful)}", log_file)
    log_message(f"Failed: {len(failed)}", log_file)
    log_message(f"Skipped: {len(skipped)}", log_file)
    log_message("", log_file)
    
    if failed:
        log_message("Failed accounts:", log_file)
        for fail in failed[:10]:  # Show first 10
            log_message(f"  @{fail['username']}: {fail.get('error', 'Unknown error')}", log_file)
        if len(failed) > 10:
            log_message(f"  ... and {len(failed) - 10} more", log_file)
    
    log_message("", log_file)
    log_message(f"Progress saved to: {progress_file}", log_file)
    log_message(f"Full log saved to: {log_file}", log_file)


if __name__ == '__main__':
    main()
