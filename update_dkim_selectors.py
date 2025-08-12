#!/usr/bin/env python3
"""
DKIM Selectors Update Script

This script helps maintain an up-to-date list of DKIM selectors by:
1. Checking for new selectors from user submissions
2. Validating selectors against known domains
3. Updating the selectors list file
"""

import os
import json
import requests
from datetime import datetime

def load_current_selectors():
    """Load current DKIM selectors from file"""
    try:
        with open('backend/resources/dkim_selectors.txt', 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def save_selectors(selectors):
    """Save selectors to file"""
    os.makedirs('backend/resources', exist_ok=True)
    with open('backend/resources/dkim_selectors.txt', 'w') as f:
        for selector in sorted(set(selectors)):
            f.write(f"{selector}\n")

def validate_selector(selector, test_domain="example.com"):
    """Validate a selector by checking if it follows DKIM naming conventions"""
    # Basic validation rules
    if not selector or len(selector) > 63:
        return False
    
    # Check for valid characters (DNS label rules)
    import re
    if not re.match(r'^[a-zA-Z0-9-]+$', selector):
        return False
    
    return True

def add_new_selector(selector, source="manual"):
    """Add a new selector to the list"""
    current = load_current_selectors()
    
    if validate_selector(selector):
        if selector not in current:
            current.append(selector)
            save_selectors(current)
            print(f"✅ Added selector '{selector}' (source: {source})")
            return True
        else:
            print(f"⚠️  Selector '{selector}' already exists")
            return False
    else:
        print(f"❌ Invalid selector '{selector}'")
        return False

def bulk_add_selectors(selectors, source="bulk"):
    """Add multiple selectors at once"""
    added = 0
    for selector in selectors:
        if add_new_selector(selector, source):
            added += 1
    
    print(f"📊 Added {added} new selectors from {source}")
    return added

if __name__ == "__main__":
    print("🔧 DKIM Selectors Update Tool")
    print("=" * 40)
    
    # Example usage
    current_count = len(load_current_selectors())
    print(f"Current selectors: {current_count}")
    
    # Add some common missing selectors
    new_selectors = [
        "dreamhost",  # Already in our list
        "mailgun",
        "sendgrid", 
        "zoho",
        "yahoo"
    ]
    
    bulk_add_selectors(new_selectors, "common_providers")
    
    final_count = len(load_current_selectors())
    print(f"Final selectors: {final_count}")
    print("✅ Update complete!")
