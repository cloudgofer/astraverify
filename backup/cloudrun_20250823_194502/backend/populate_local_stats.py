#!/usr/bin/env python3
"""
Script to populate local statistics with sample data for development
"""

import os
import sys
import json
from datetime import datetime, timedelta
import random

# Set environment to local
os.environ['ENVIRONMENT'] = 'local'

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from firestore_config import FirestoreManager

def create_sample_data():
    """Create sample domain analysis data for local development"""
    
    # Sample domains with realistic data
    sample_domains = [
        {
            'domain': 'google.com',
            'security_score': 95,
            'email_provider': 'Google',
            'timestamp': datetime.utcnow() - timedelta(hours=2)
        },
        {
            'domain': 'microsoft.com',
            'security_score': 92,
            'email_provider': 'Microsoft',
            'timestamp': datetime.utcnow() - timedelta(hours=4)
        },
        {
            'domain': 'yahoo.com',
            'security_score': 88,
            'email_provider': 'Yahoo',
            'timestamp': datetime.utcnow() - timedelta(hours=6)
        },
        {
            'domain': 'example.com',
            'security_score': 75,
            'email_provider': 'Unknown',
            'timestamp': datetime.utcnow() - timedelta(hours=8)
        },
        {
            'domain': 'github.com',
            'security_score': 96,
            'email_provider': 'GitHub',
            'timestamp': datetime.utcnow() - timedelta(hours=10)
        },
        {
            'domain': 'stackoverflow.com',
            'security_score': 89,
            'email_provider': 'Stack Overflow',
            'timestamp': datetime.utcnow() - timedelta(hours=12)
        },
        {
            'domain': 'reddit.com',
            'security_score': 82,
            'email_provider': 'Reddit',
            'timestamp': datetime.utcnow() - timedelta(hours=14)
        },
        {
            'domain': 'amazon.com',
            'security_score': 94,
            'email_provider': 'Amazon',
            'timestamp': datetime.utcnow() - timedelta(hours=16)
        },
        {
            'domain': 'netflix.com',
            'security_score': 91,
            'email_provider': 'Netflix',
            'timestamp': datetime.utcnow() - timedelta(hours=18)
        },
        {
            'domain': 'spotify.com',
            'security_score': 87,
            'email_provider': 'Spotify',
            'timestamp': datetime.utcnow() - timedelta(hours=20)
        }
    ]
    
    # Create some duplicate analyses for the same domains (to test unique domains count)
    additional_analyses = []
    for domain_data in sample_domains[:5]:  # Add 2 more analyses for first 5 domains
        for i in range(2):
            additional_analyses.append({
                'domain': domain_data['domain'],
                'security_score': domain_data['security_score'] + random.randint(-5, 5),
                'email_provider': domain_data['email_provider'],
                'timestamp': domain_data['timestamp'] - timedelta(hours=random.randint(1, 24))
            })
    
    all_analyses = sample_domains + additional_analyses
    
    return all_analyses

def populate_firestore():
    """Populate Firestore with sample data"""
    
    print("🚀 Populating local Firestore with sample data...")
    
    try:
        # Initialize Firestore manager
        firestore_manager = FirestoreManager()
        
        # Create sample data
        sample_data = create_sample_data()
        
        # Store each analysis
        stored_count = 0
        for analysis in sample_data:
            try:
                # Create analysis data structure similar to what the app stores
                analysis_data = {
                    'security_score': {
                        'score': analysis['security_score'],
                        'grade': 'A' if analysis['security_score'] >= 90 else 'B' if analysis['security_score'] >= 80 else 'C',
                        'status': 'Excellent' if analysis['security_score'] >= 90 else 'Good' if analysis['security_score'] >= 80 else 'Fair'
                    },
                    'email_provider': analysis['email_provider'],
                    'domain': analysis['domain'],
                    'timestamp': analysis['timestamp'].isoformat(),
                    'analysis_results': {
                        'domain': analysis['domain'],
                        'security_score': analysis['security_score'],
                        'email_provider': analysis['email_provider']
                    }
                }
                
                # Store in Firestore
                success = firestore_manager.store_analysis(analysis['domain'], analysis_data)
                if success:
                    stored_count += 1
                    print(f"✅ Stored analysis for {analysis['domain']} (Score: {analysis['security_score']})")
                else:
                    print(f"❌ Failed to store analysis for {analysis['domain']}")
                    
            except Exception as e:
                print(f"❌ Error storing analysis for {analysis['domain']}: {e}")
        
        print(f"\n📊 Successfully stored {stored_count} out of {len(sample_data)} analyses")
        
        # Test statistics
        print("\n🔍 Testing statistics...")
        stats = firestore_manager.get_statistics()
        
        print(f"📈 Statistics Results:")
        print(f"   Total Analyses: {stats.get('total_analyses', 0)}")
        print(f"   Unique Domains: {stats.get('unique_domains', 0)}")
        print(f"   Average Score: {stats.get('average_security_score', 0)}")
        print(f"   Email Providers: {stats.get('email_provider_distribution', {})}")
        
        return stored_count > 0
        
    except Exception as e:
        print(f"❌ Error populating Firestore: {e}")
        return False

def create_mock_statistics():
    """Create mock statistics for local development without Firestore"""
    
    print("🎭 Creating mock statistics for local development...")
    
    # Create a mock statistics file
    mock_stats = {
        "total_analyses": 25,
        "unique_domains": 10,
        "average_security_score": 89.2,
        "email_provider_distribution": {
            "Google": 8,
            "Microsoft": 6,
            "Yahoo": 4,
            "GitHub": 3,
            "Amazon": 2,
            "Netflix": 1,
            "Unknown": 1
        }
    }
    
    # Save to a JSON file
    stats_file = os.path.join(os.path.dirname(__file__), 'mock_statistics.json')
    with open(stats_file, 'w') as f:
        json.dump(mock_stats, f, indent=2)
    
    print(f"✅ Mock statistics saved to {stats_file}")
    print(f"📊 Mock Data:")
    print(f"   Total Analyses: {mock_stats['total_analyses']}")
    print(f"   Unique Domains: {mock_stats['unique_domains']}")
    print(f"   Average Score: {mock_stats['average_security_score']}")
    print(f"   Email Providers: {mock_stats['email_provider_distribution']}")
    
    return mock_stats

if __name__ == "__main__":
    print("🎯 AstraVerify Local Statistics Populator")
    print("=" * 50)
    
    # Try to populate Firestore first
    firestore_success = populate_firestore()
    if firestore_success:
        print("\n✅ Successfully populated Firestore with sample data!")
    else:
        print("\n⚠️  Firestore population failed, creating mock statistics...")
        create_mock_statistics()
        print("\n✅ Created mock statistics for local development!")
    
    print("\n🎉 Local development environment is ready!")
    print("📱 You can now test the frontend with realistic statistics data.")
