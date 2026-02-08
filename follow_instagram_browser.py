#!/usr/bin/env python3
"""
Instagram Following Script using Browser Automation (Selenium)
This avoids Instagram's bot detection by using a real browser.
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

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    print("ERROR: selenium not installed.")
    print("Install with: pip install selenium")
    print("Also need ChromeDriver: https://chromedriver.chromium.org/")
    exit(1)

from pdf_parser import PDFParser


def log_message(message: str, log_file: Optional[str] = None):
    """Log message to console and optionally to file."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    if log_file:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')


def setup_driver(headless=False):
    """Setup Chrome driver with options to avoid detection."""
    chrome_options = Options()
    
    if headless:
        chrome_options.add_argument('--headless')
    
    # Options to avoid detection
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def login_instagram(driver, username, password, twofa_code=None):
    """Login to Instagram via browser."""
    log_message("Opening Instagram login page...")
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(3)
    
    try:
        # Enter username
        username_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input.send_keys(username)
        time.sleep(1)
        
        # Enter password
        password_input = driver.find_element(By.NAME, "password")
        password_input.send_keys(password)
        time.sleep(1)
        
        # Click login
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        time.sleep(5)
        
        # Check for 2FA
        try:
            twofa_input = driver.find_element(By.NAME, "verificationCode")
            if twofa_code:
                log_message("Entering 2FA code...")
                twofa_input.send_keys(twofa_code)
                time.sleep(1)
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='button']")
                submit_button.click()
                time.sleep(5)
            else:
                twofa_code = input("Enter your 2FA code: ").strip()
                twofa_input.send_keys(twofa_code)
                time.sleep(1)
                submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='button']")
                submit_button.click()
                time.sleep(5)
        except NoSuchElementException:
            pass  # No 2FA required
        
        # Check if logged in
        if "instagram.com" in driver.current_url and "login" not in driver.current_url:
            log_message("✓ Successfully logged in!")
            return True
        else:
            log_message("✗ Login failed - check credentials or 2FA")
            return False
            
    except Exception as e:
        log_message(f"✗ Login error: {e}")
        return False


def follow_user(driver, username):
    """Follow a user by username."""
    try:
        log_message(f"Following @{username}...")
        driver.get(f"https://www.instagram.com/{username}/")
        time.sleep(3)
        
        # Find follow button
        follow_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Follow')]"))
        )
        follow_button.click()
        time.sleep(2)
        
        log_message(f"✓ Followed @{username}")
        return True
        
    except TimeoutException:
        log_message(f"✗ Could not find follow button for @{username} (may already be following)")
        return False
    except Exception as e:
        log_message(f"✗ Error following @{username}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Follow Instagram accounts using browser automation')
    parser.add_argument('--username', default=None, help='Instagram username (or set IG_USERNAME in .env)')
    parser.add_argument('--password', default=None, help='Instagram password (or set IG_PASSWORD in .env)')
    parser.add_argument('--twofa', default=None, help='2FA code (or will prompt)')
    parser.add_argument('--limit', type=int, default=10, help='Max accounts to follow')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--config', default='config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    # Get credentials
    username = args.username or os.getenv('IG_USERNAME')
    password = args.password or os.getenv('IG_PASSWORD')
    
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
    
    # Get Instagram settings
    instagram_config = config.get('instagram', {})
    min_delay = instagram_config.get('min_delay_seconds', 60)
    max_delay = instagram_config.get('max_delay_seconds', 180)
    
    log_file = 'instagram_browser_follow.log'
    
    log_message("=" * 60, log_file)
    log_message("INSTAGRAM FOLLOWING (Browser Automation)", log_file)
    log_message("=" * 60, log_file)
    log_message("", log_file)
    
    # Setup browser
    driver = setup_driver(headless=args.headless)
    
    try:
        # Login
        if not login_instagram(driver, username, password, args.twofa):
            log_message("Failed to login. Exiting.", log_file)
            return
        
        # Get target accounts
        pdf_text_file = config.get('files', {}).get('pdf_text', 'playlist_contacts.txt')
        parser = PDFParser(pdf_text_file)
        all_contacts = parser.parse()
        
        # Filter contacts with Instagram
        from follow_instagram import filter_by_genres, extract_instagram_username
        genre_keywords = config.get('email', {}).get('genre_keywords', [])
        exclude_genres = config.get('email', {}).get('exclude_genres', [])
        
        contacts_with_instagram = [c for c in all_contacts if c.instagram]
        if genre_keywords:
            contacts_with_instagram = [c for c in contacts_with_instagram 
                                      if filter_by_genres(c, genre_keywords, exclude_genres)]
        
        # Extract usernames
        target_usernames = []
        for contact in contacts_with_instagram[:args.limit * 2]:
            username_ig = extract_instagram_username(contact.instagram)
            if username_ig:
                target_usernames.append(username_ig)
        
        log_message(f"Target accounts: {len(target_usernames[:args.limit])}", log_file)
        log_message("", log_file)
        
        # Follow accounts
        successful = 0
        failed = 0
        
        for i, target_username in enumerate(target_usernames[:args.limit], 1):
            log_message(f"[{i}/{args.limit}] Processing @{target_username}", log_file)
            
            if follow_user(driver, target_username):
                successful += 1
            else:
                failed += 1
            
            # Random delay
            if i < args.limit:
                delay = random.randint(min_delay, max_delay)
                log_message(f"Waiting {delay} seconds...", log_file)
                time.sleep(delay)
        
        # Summary
        log_message("", log_file)
        log_message("=" * 60, log_file)
        log_message("SUMMARY", log_file)
        log_message("=" * 60, log_file)
        log_message(f"Successfully followed: {successful}", log_file)
        log_message(f"Failed: {failed}", log_file)
        
    finally:
        log_message("Closing browser...", log_file)
        driver.quit()


if __name__ == '__main__':
    main()
