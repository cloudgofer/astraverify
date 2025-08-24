#!/usr/bin/env python3
"""
Demo script to show where IP logged data is stored in AstraVerify
"""

import requests
import json
import time
from datetime import datetime

def demo_ip_logging():
    """Demonstrate IP logging functionality"""
    
    print("🔒 AstraVerify IP Logging Demo")
    print("=" * 50)
    
    # Configuration
    BASE_URL = "http://localhost:8080"
    ADMIN_API_KEY = "astraverify-admin-2024"
    
    print("\n📊 Where IP Logged Data is Stored:")
    print("=" * 50)
    
    print("1. 🔥 Firestore Database (Primary Storage)")
    print("   - Collection: request_logs_local (local environment)")
    print("   - Collection: request_logs_staging (staging environment)")
    print("   - Collection: request_logs (production environment)")
    print("   - Data includes: IP, user agent, domain, timestamp, response time, errors")
    print("   - Retention: 30 days (automatic cleanup)")
    
    print("\n2. 🧠 In-Memory Storage (Runtime)")
    print("   - Rate limiter counters")
    print("   - Abuse detector history")
    print("   - IP blocker lists")
    print("   - Retention: 24 hours for history, permanent for blocks")
    
    print("\n3. 📝 Application Logs")
    print("   - Console output during development")
    print("   - Log files in production")
    print("   - Includes detailed request information")
    
    print("\n4. 📡 Admin API Endpoints")
    print("   - /api/admin/security-dashboard")
    print("   - /api/admin/blocked-ips")
    print("   - /api/admin/ip-analytics/{ip}")
    
    print("\n🚀 Testing IP Logging:")
    print("=" * 50)
    
    # Test if backend is running
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            
            # Make some test requests to generate logs
            print("\n📝 Making test requests to generate IP logs...")
            
            test_domains = ["example.com", "google.com", "microsoft.com"]
            for i, domain in enumerate(test_domains):
                try:
                    response = requests.get(f"{BASE_URL}/api/check?domain={domain}")
                    print(f"   Request {i+1}: {domain} - Status: {response.status_code}")
                    
                    # Show rate limit headers
                    if 'X-RateLimit-Remaining' in response.headers:
                        print(f"      Rate Limit Remaining: {response.headers['X-RateLimit-Remaining']}")
                    
                    time.sleep(0.5)  # Small delay
                    
                except Exception as e:
                    print(f"   Request {i+1}: {domain} - Error: {e}")
            
            print("\n📊 How to Access IP Logged Data:")
            print("=" * 50)
            
            print("1. 🔥 Firestore Console:")
            print("   - Go to: https://console.firebase.google.com/")
            print("   - Select your AstraVerify project")
            print("   - Navigate to Firestore Database")
            print("   - Look for 'request_logs_local' collection")
            print("   - Each document contains:")
            print("     * ip: Client IP address")
            print("     * user_agent: Browser/client info")
            print("     * domain: Requested domain")
            print("     * timestamp: Request time")
            print("     * response_time_ms: Processing time")
            print("     * error: Any errors encountered")
            
            print("\n2. 📡 Admin API (when backend is running):")
            print("   # Get security dashboard")
            print(f"   curl -H 'X-Admin-API-Key: {ADMIN_API_KEY}' \\")
            print(f"        {BASE_URL}/api/admin/security-dashboard")
            
            print("\n   # Get blocked IPs")
            print(f"   curl -H 'X-Admin-API-Key: {ADMIN_API_KEY}' \\")
            print(f"        {BASE_URL}/api/admin/blocked-ips")
            
            print("\n   # Get analytics for specific IP")
            print(f"   curl -H 'X-Admin-API-Key: {ADMIN_API_KEY}' \\")
            print(f"        {BASE_URL}/api/admin/ip-analytics/127.0.0.1")
            
            print("\n3. 🧠 In-Memory Data (Runtime):")
            print("   - Rate limiter: Tracks requests per IP per time window")
            print("   - Abuse detector: Maintains IP history and scores")
            print("   - IP blocker: Stores blocked IPs with reasons and expiration")
            
            print("\n4. 📝 Application Logs:")
            print("   - Check console output for detailed request logs")
            print("   - Look for lines starting with 'INFO:__main__:Request:'")
            print("   - Contains full request fingerprint and response data")
            
            print("\n🔧 Sample IP Log Entry Structure:")
            print("=" * 50)
            
            sample_log = {
                "ip": "127.0.0.1",
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "domain": "example.com",
                "endpoint": "check_domain",
                "method": "GET",
                "timestamp": datetime.now().isoformat(),
                "path": "/api/check",
                "query_string": "domain=example.com",
                "response_status": 200,
                "response_time_ms": 150,
                "error": None,
                "response_size": 1024
            }
            
            print(json.dumps(sample_log, indent=2))
            
        else:
            print("❌ Backend is not responding correctly")
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running")
        print("\n💡 To start the backend:")
        print("   cd backend")
        print("   source venv/bin/activate")
        print("   python app_with_security.py")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    demo_ip_logging()
