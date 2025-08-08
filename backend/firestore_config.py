import os
from google.cloud import firestore
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FirestoreManager:
    def __init__(self):
        """Initialize Firestore client"""
        try:
            # Initialize Firestore client
            self.db = firestore.Client()
            self.collection_name = 'domain_analyses'
            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}")
            self.db = None

    def store_analysis(self, domain, analysis_data):
        """Store domain analysis results in Firestore"""
        if not self.db:
            logger.warning("Firestore not available, skipping storage")
            return False
        
        try:
            # Create document data
            doc_data = {
                'domain': domain,
                'timestamp': datetime.utcnow(),
                'security_score': analysis_data.get('security_score', {}).get('score', 0),
                'email_provider': analysis_data.get('email_provider', 'Unknown'),
                'analysis_results': analysis_data,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            
            # Add to Firestore collection
            doc_ref = self.db.collection(self.collection_name).document()
            doc_ref.set(doc_data)
            
            logger.info(f"Stored analysis for domain: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store analysis for {domain}: {e}")
            return False

    def get_recent_analyses(self, limit=10):
        """Get recent domain analyses"""
        if not self.db:
            return []
        
        try:
            # Query recent analyses
            docs = self.db.collection(self.collection_name)\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()
            
            analyses = []
            for doc in docs:
                data = doc.to_dict()
                analyses.append({
                    'id': doc.id,
                    'domain': data.get('domain'),
                    'timestamp': data.get('timestamp'),
                    'security_score': data.get('security_score'),
                    'email_provider': data.get('email_provider')
                })
            
            return analyses
            
        except Exception as e:
            logger.error(f"Failed to retrieve recent analyses: {e}")
            return []

    def get_domain_history(self, domain, limit=20):
        """Get analysis history for a specific domain"""
        if not self.db:
            return []
        
        try:
            # Query analyses for specific domain
            docs = self.db.collection(self.collection_name)\
                .where('domain', '==', domain)\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)\
                .stream()
            
            history = []
            for doc in docs:
                data = doc.to_dict()
                history.append({
                    'id': doc.id,
                    'timestamp': data.get('timestamp'),
                    'security_score': data.get('security_score'),
                    'email_provider': data.get('email_provider'),
                    'analysis_results': data.get('analysis_results')
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to retrieve history for {domain}: {e}")
            return []

    def get_statistics(self):
        """Get analytics statistics"""
        if not self.db:
            return {}
        
        try:
            # Get total analyses count
            total_docs = self.db.collection(self.collection_name).stream()
            total_count = sum(1 for _ in total_docs)
            
            # Get unique domains count
            unique_domains = set()
            docs = self.db.collection(self.collection_name).stream()
            for doc in docs:
                data = doc.to_dict()
                unique_domains.add(data.get('domain', ''))
            
            # Get average security score
            docs = self.db.collection(self.collection_name).stream()
            scores = []
            for doc in docs:
                data = doc.to_dict()
                score = data.get('security_score', 0)
                if score > 0:
                    scores.append(score)
            
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Get email provider distribution
            provider_counts = {}
            docs = self.db.collection(self.collection_name).stream()
            for doc in docs:
                data = doc.to_dict()
                provider = data.get('email_provider', 'Unknown')
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
            
            return {
                'total_analyses': total_count,
                'unique_domains': len(unique_domains),
                'average_security_score': round(avg_score, 1),
                'email_provider_distribution': provider_counts
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def store_email_report(self, email, domain, analysis_result, opt_in_marketing, timestamp):
        """Store email report request in Firestore"""
        if not self.db:
            logger.warning("Firestore not available, skipping email report storage")
            return False
        
        try:
            doc_data = {
                'email': email,
                'domain': domain,
                'analysis_result': analysis_result,
                'opt_in_marketing': opt_in_marketing,
                'timestamp': timestamp,
                'status': 'pending',
                'created_at': firestore.SERVER_TIMESTAMP
            }
            doc_ref = self.db.collection('email_reports').document()
            doc_ref.set(doc_data)
            logger.info(f"Stored email report for domain: {domain} to email: {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to store email report for {domain}: {e}")
            return False

# Global Firestore manager instance
firestore_manager = FirestoreManager()
