#!/usr/bin/env python3
"""
Instagram Engagement Script
Automates liking and commenting on posts from target accounts to increase visibility.
⚠️ Use carefully - Instagram has strict limits!
"""

import time
import json
import random
import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import yaml

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from pdf_parser import PDFParser


def load_progress(progress_file: str) -> Dict:
    """Load progress from JSON file."""
    if Path(progress_file).exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {
        'liked_posts': [],
        'commented_posts': [],
        'hourly_likes': 0,
        'hourly_comments': 0,
        'daily_likes': 0,
        'daily_comments': 0,
        'hour_start': None,
        'last_action_time': None
    }


def save_progress(progress: Dict, progress_file: str):
    """Save progress to JSON file."""
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)


def log_message(message: str, log_file: Optional[str] = None):
    """Log message to console and optionally to file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    if log_file:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')


def get_comments() -> List[str]:
    """Get list of comments to use (customize these!)."""
    return [
        "Love this! 🎵",
        "Great vibes! ✨",
        "This is beautiful! 🎶",
        "Amazing! 🔥",
        "So good! 💫",
        "Love your taste! 🎸",
        "Perfect! 🎹",
        "This hits! 🎤",
        "Beautiful music! 🎵",
        "Great playlist! 🎧",
    ]


def main():
    parser = argparse.ArgumentParser(description='Engage with Instagram posts to increase visibility')
    parser.add_argument('--like-only', action='store_true', help='Only like posts, no comments')
    parser.add_argument('--comment-only', action='store_true', help='Only comment, no likes')
    parser.add_argument('--limit', type=int, default=20, help='Max actions per run (default: 20)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no actual actions)')
    parser.add_argument('--config', default='config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    # Get credentials
    username = os.getenv('IG_USERNAME')
    password = os.getenv('IG_PASSWORD')
    
    if not username or not password:
        print("ERROR: Instagram credentials required!")
        print("Set IG_USERNAME and IG_PASSWORD in .env file")
        return
    
    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}
    
    # Get engagement settings
    engagement_config = config.get('instagram_engagement', {})
    min_delay = engagement_config.get('min_delay_seconds', 30)
    max_delay = engagement_config.get('max_delay_seconds', 90)
    max_likes_per_hour = engagement_config.get('max_likes_per_hour', 30)
    max_comments_per_hour = engagement_config.get('max_comments_per_hour', 10)
    max_likes_per_day = engagement_config.get('max_likes_per_day', 150)
    max_comments_per_day = engagement_config.get('max_comments_per_day', 50)
    
    # Progress tracking
    progress_file = 'instagram_engagement_progress.json'
    log_file = 'instagram_engagement.log'
    
    progress = load_progress(progress_file)
    
    log_message("=" * 60, log_file)
    log_message("INSTAGRAM ENGAGEMENT CAMPAIGN", log_file)
    log_message("=" * 60, log_file)
    if args.dry_run:
        log_message("DRY RUN MODE - No actual actions will be performed", log_file)
    log_message("", log_file)
    
    # Initialize Instagram client
    if not args.dry_run:
        try:
            from instagrapi import Client
            from instagrapi.exceptions import PleaseWaitFewMinutes, ChallengeRequired
        except ImportError:
            log_message("ERROR: instagrapi library not installed.", log_file)
            log_message("Install it with: pip install instagrapi", log_file)
            return
        
        cl = Client()
        session_file = 'instagram_session.json'
        
        # Try to load existing session
        if Path(session_file).exists():
            try:
                cl.load_settings(session_file)
                try:
                    cl.get_timeline_feed()
                    log_message("✓ Using existing session", log_file)
                except:
                    log_message("Session expired, logging in...", log_file)
                    cl.login(username, password)
                    cl.dump_settings(session_file)
            except:
                cl.login(username, password)
                cl.dump_settings(session_file)
        else:
            log_message("Logging into Instagram...", log_file)
            cl.login(username, password)
            cl.dump_settings(session_file)
        
        log_message("✓ Successfully logged in", log_file)
    
    # Get target accounts from contacts
    pdf_text_file = config.get('files', {}).get('pdf_text', 'playlist_contacts.txt')
    parser = PDFParser(pdf_text_file)
    all_contacts = parser.parse()
    
    # Get genre filtering
    genre_keywords = config.get('email', {}).get('genre_keywords', [])
    exclude_genres = config.get('email', {}).get('exclude_genres', [])
    
    # Filter contacts with Instagram
    contacts_with_instagram = [c for c in all_contacts if c.instagram]
    
    # Apply genre filtering
    if genre_keywords:
        from follow_instagram import filter_by_genres, extract_instagram_username
        contacts_with_instagram = [c for c in contacts_with_instagram 
                                  if filter_by_genres(c, genre_keywords, exclude_genres)]
    
    # Extract usernames
    target_usernames = []
    for contact in contacts_with_instagram:
        username = extract_instagram_username(contact.instagram)
        if username:
            target_usernames.append(username)
    
    log_message(f"Target accounts: {len(target_usernames)}", log_file)
    log_message("", log_file)
    
    # Get comments
    comments = get_comments()
    
    # Track actions
    actions_taken = 0
    likes_count = 0
    comments_count = 0
    
    # Shuffle for randomness
    random.shuffle(target_usernames)
    
    for target_username in target_usernames[:args.limit * 2]:  # Get more accounts than needed
        if actions_taken >= args.limit:
            break
        
        # Check rate limits
        now = datetime.now()
        hour_start = progress.get('hour_start')
        if hour_start:
            start_time = datetime.fromisoformat(hour_start)
            if (now - start_time).total_seconds() >= 3600:
                progress['hourly_likes'] = 0
                progress['hourly_comments'] = 0
                progress['hour_start'] = now.isoformat()
        else:
            progress['hour_start'] = now.isoformat()
        
        # Check daily limits
        if progress.get('daily_likes', 0) >= max_likes_per_day:
            log_message("Daily like limit reached. Stopping.", log_file)
            break
        if progress.get('daily_comments', 0) >= max_comments_per_day:
            log_message("Daily comment limit reached. Stopping.", log_file)
            break
        
        # Check hourly limits
        if progress.get('hourly_likes', 0) >= max_likes_per_hour:
            log_message(f"Hourly like limit reached. Waiting...", log_file)
            time.sleep(3600 - (now - datetime.fromisoformat(progress['hour_start'])).total_seconds())
            progress['hourly_likes'] = 0
        
        if progress.get('hourly_comments', 0) >= max_comments_per_hour:
            log_message(f"Hourly comment limit reached. Waiting...", log_file)
            time.sleep(3600 - (now - datetime.fromisoformat(progress['hour_start'])).total_seconds())
            progress['hourly_comments'] = 0
        
        try:
            if args.dry_run:
                log_message(f"[DRY RUN] Would engage with @{target_username}", log_file)
                actions_taken += 1
                continue
            
            # Get user's recent posts
            user_id = cl.user_id_from_username(target_username)
            user_medias = cl.user_medias(user_id, amount=3)  # Get 3 most recent posts
            
            if not user_medias:
                continue
            
            # Pick a random post
            media = random.choice(user_medias)
            media_id = media.pk
            
            # Skip if already engaged
            if media_id in progress.get('liked_posts', []):
                continue
            
            # Like the post
            if not args.comment_only:
                try:
                    cl.media_like(media_id)
                    log_message(f"✓ Liked @{target_username}'s post", log_file)
                    progress['liked_posts'].append(media_id)
                    progress['hourly_likes'] += 1
                    progress['daily_likes'] += 1
                    likes_count += 1
                    actions_taken += 1
                except Exception as e:
                    log_message(f"✗ Failed to like @{target_username}: {e}", log_file)
            
            # Comment on the post
            if not args.like_only and random.random() < 0.3:  # 30% chance to comment
                try:
                    comment_text = random.choice(comments)
                    cl.media_comment(media_id, comment_text)
                    log_message(f"✓ Commented on @{target_username}'s post: {comment_text}", log_file)
                    progress['commented_posts'].append(media_id)
                    progress['hourly_comments'] += 1
                    progress['daily_comments'] += 1
                    comments_count += 1
                except Exception as e:
                    log_message(f"✗ Failed to comment on @{target_username}: {e}", log_file)
            
            # Save progress
            save_progress(progress, progress_file)
            
            # Random delay
            delay = random.randint(min_delay, max_delay)
            time.sleep(delay)
            
        except Exception as e:
            log_message(f"✗ Error with @{target_username}: {e}", log_file)
            continue
    
    # Summary
    log_message("", log_file)
    log_message("=" * 60, log_file)
    log_message("ENGAGEMENT SUMMARY", log_file)
    log_message("=" * 60, log_file)
    log_message(f"Likes: {likes_count}", log_file)
    log_message(f"Comments: {comments_count}", log_file)
    log_message(f"Total actions: {actions_taken}", log_file)
    log_message("", log_file)
    log_message(f"Progress saved to: {progress_file}", log_file)
    log_message(f"Full log saved to: {log_file}", log_file)


if __name__ == '__main__':
    main()
