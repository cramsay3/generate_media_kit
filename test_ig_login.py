#!/usr/bin/env python3
"""Simple test script to debug Instagram login with 2FA"""

import os
import sys
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import TwoFactorRequired

load_dotenv()

username = os.getenv('IG_USERNAME')
password = os.getenv('IG_PASSWORD')

# Get code from command line or prompt
code = sys.argv[1] if len(sys.argv) > 1 else None

print(f"Testing login for: {username}")
print()

cl = Client()

try:
    print("Attempting login...")
    cl.login(username, password)
    print("✅ Login successful!")
    print(f"User ID: {cl.user_id}")
    
except TwoFactorRequired as e:
    print(f"❌ 2FA Required: {e}")
    print()
    
    if not code:
        print("Enter your 2FA code from authenticator app:")
        code = input("Code: ").strip()
    else:
        print(f"Using code from command line: {code}")
    
    if code:
        print(f"\nTrying login with code: {code}")
        try:
            # IMPORTANT: Use the SAME client instance and pass verification_code
            cl.login(username, password, verification_code=code)
            print("✅ Login successful with 2FA!")
            print(f"User ID: {cl.user_id}")
            
            # Save session
            cl.dump_settings('instagram_session.json')
            print("✅ Session saved!")
            
        except Exception as e2:
            print(f"❌ Login with 2FA failed: {type(e2).__name__}")
            print(f"Error: {e2}")
    else:
        print("No code provided")

except Exception as e:
    print(f"❌ Login failed: {type(e).__name__}")
    print(f"Error: {e}")
