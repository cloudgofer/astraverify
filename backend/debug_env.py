#!/usr/bin/env python3
"""
Debug script to check environment variable loading
"""

import os
from dotenv import load_dotenv

print("🔍 Debugging Environment Variable Loading")
print("=" * 50)

# Check current directory
print(f"Current directory: {os.getcwd()}")

# Check if .env file exists
env_file = ".env"
if os.path.exists(env_file):
    print(f"✅ .env file exists: {env_file}")
    print(f"   Size: {os.path.getsize(env_file)} bytes")
else:
    print(f"❌ .env file not found: {env_file}")

# Load .env file
print("\n📋 Loading .env file...")
load_dotenv()

# Check environment variables
print("\n🔐 Environment Variables:")
print(f"GOOGLE_OAUTH_CLIENT_ID: {os.environ.get('GOOGLE_OAUTH_CLIENT_ID', 'NOT SET')}")
print(f"GOOGLE_OAUTH_CLIENT_SECRET: {os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', 'NOT SET')}")
print(f"GOOGLE_OAUTH_REDIRECT_URI: {os.environ.get('GOOGLE_OAUTH_REDIRECT_URI', 'NOT SET')}")
print(f"JWT_SECRET_KEY: {os.environ.get('JWT_SECRET_KEY', 'NOT SET')}")

# Check if values are the real ones or placeholders
client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
if 'your-google-oauth-client-id' in client_id:
    print("\n❌ Still using placeholder values!")
else:
    print("\n✅ Using real OAuth credentials!")

print("\n" + "=" * 50)
