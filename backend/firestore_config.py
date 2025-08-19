import os
from google.cloud import firestore
from datetime import datetime
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class FirestoreManager:
    def __init__(self):
        """Initialize Firestore client"""
        self.db = None
        self.environment = os.environ.get('ENVIRONMENT', 'production')
        
        # Use environment-specific collection names
        if self.environment == 'staging':
            self.collection_name = 'domain_analyses_staging'
        elif self.environment == 'local':
            self.collection_name = 'domain_analyses_local'
        else:
            self.collection_name = 'domain_analyses'
            
        logger.info(f"Firestore manager initialized for {self.environment.upper()} environment")
        logger.info(f"Collection name: {self.collection_name}")

    def _get_client(self):
        """Get or initialize Firestore client"""
        if self.db is None:
            try:
                self.db = firestore.Client()
                logger.info("Firestore client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Firestore: {e}")
                return None
        return self.db

    def store_analysis(self, domain, analysis_data):
        """Store domain analysis results in Firestore"""
        db = self._get_client()
        if not db:
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
            doc_ref = db.collection(self.collection_name).document()
            doc_ref.set(doc_data)
            
            logger.info(f"Stored analysis for domain: {domain}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store analysis for {domain}: {e}")
            return False

    def get_recent_analyses(self, limit=10):
        """Get recent domain analyses"""
        db = self._get_client()
        if not db:
            return []
        
        try:
            # Query recent analyses
            docs = db.collection(self.collection_name)\
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
        db = self._get_client()
        if not db:
            return []
        
        try:
            # Query analyses for specific domain
            docs = db.collection(self.collection_name)\
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
        db = self._get_client()
        if not db:
            return {}
        
        try:
            # Get total analyses count
            total_docs = db.collection(self.collection_name).stream()
            total_count = sum(1 for _ in total_docs)
            
            # Get unique domains count
            unique_domains = set()
            docs = db.collection(self.collection_name).stream()
            for doc in docs:
                data = doc.to_dict()
                unique_domains.add(data.get('domain', ''))
            
            # Get average security score
            docs = db.collection(self.collection_name).stream()
            scores = []
            for doc in docs:
                data = doc.to_dict()
                score = data.get('security_score', 0)
                if score > 0:
                    scores.append(score)
            
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Get email provider distribution
            provider_counts = {}
            docs = db.collection(self.collection_name).stream()
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
        db = self._get_client()
        if not db:
            logger.warning("Firestore not available, skipping email report storage")
            return False
        
        try:
            # Use environment-specific email reports collection
            email_collection = 'email_reports'
            if self.environment == 'staging':
                email_collection = 'email_reports_staging'
            elif self.environment == 'local':
                email_collection = 'email_reports_local'
            
            doc_data = {
                'email': email,
                'domain': domain,
                'analysis_result': analysis_result,
                'opt_in_marketing': opt_in_marketing,
                'timestamp': timestamp,
                'status': 'pending',
                'created_at': firestore.SERVER_TIMESTAMP
            }
            doc_ref = db.collection(email_collection).document()
            doc_ref.set(doc_data)
            logger.info(f"Stored email report for domain: {domain} to email: {email} in {self.environment} environment")
            return True
        except Exception as e:
            logger.error(f"Failed to store email report for {domain}: {e}")
            return False

    def store_request_log(self, log_entry: Dict[str, Any]):
        """Store request log in Firestore"""
        db = self._get_client()
        if not db:
            logger.warning("Firestore not available, skipping request log storage")
            return False
        
        try:
            # Use environment-specific collection
            collection_name = 'request_logs'
            if self.environment == 'staging':
                collection_name = 'request_logs_staging'
            elif self.environment == 'local':
                collection_name = 'request_logs_local'
            
            # Add TTL for automatic cleanup (30 days)
            from datetime import datetime, timedelta
            log_entry['expires_at'] = datetime.utcnow() + timedelta(days=30)
            log_entry['created_at'] = firestore.SERVER_TIMESTAMP
            
            doc_ref = db.collection(collection_name).document()
            doc_ref.set(log_entry)
            
            return True
        except Exception as e:
            logger.error(f"Failed to store request log: {e}")
            return False

    def get_ip_analytics(self, ip_address: str, hours: int = 24) -> Dict[str, Any]:
        """Get analytics for specific IP address"""
        db = self._get_client()
        if not db:
            return {}
        
        try:
            from datetime import datetime, timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Use environment-specific collection
            collection_name = 'request_logs'
            if self.environment == 'staging':
                collection_name = 'request_logs_staging'
            elif self.environment == 'local':
                collection_name = 'request_logs_local'
            
            # Query recent requests for this IP
            docs = db.collection(collection_name)\
                .where('ip', '==', ip_address)\
                .where('timestamp', '>=', cutoff_time.isoformat())\
                .stream()
            
            requests = list(docs)
            
            return {
                'total_requests': len(requests),
                'unique_domains': len(set(doc.to_dict().get('domain', '') for doc in requests)),
                'error_count': len([doc for doc in requests if doc.to_dict().get('error')]),
                'avg_response_time': sum(doc.to_dict().get('response_time_ms', 0) for doc in requests) / len(requests) if requests else 0,
                'last_request': max(doc.to_dict().get('timestamp') for doc in requests) if requests else None
            }
        except Exception as e:
            logger.error(f"Failed to get IP analytics: {e}")
            return {}

    def get_daily_request_count(self) -> int:
        """Get total requests for today"""
        db = self._get_client()
        if not db:
            return 0
        
        try:
            from datetime import datetime, timedelta
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            collection_name = 'request_logs'
            if self.environment == 'staging':
                collection_name = 'request_logs_staging'
            elif self.environment == 'local':
                collection_name = 'request_logs_local'
            
            docs = db.collection(collection_name)\
                .where('timestamp', '>=', today_start.isoformat())\
                .stream()
            
            return sum(1 for _ in docs)
        except Exception as e:
            logger.error(f"Failed to get daily request count: {e}")
            return 0

    def get_rate_limited_count(self) -> int:
        """Get count of rate-limited requests today"""
        db = self._get_client()
        if not db:
            return 0
        
        try:
            from datetime import datetime, timedelta
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            collection_name = 'request_logs'
            if self.environment == 'staging':
                collection_name = 'request_logs_staging'
            elif self.environment == 'local':
                collection_name = 'request_logs_local'
            
            docs = db.collection(collection_name)\
                .where('timestamp', '>=', today_start.isoformat())\
                .where('error', '==', 'Rate limit exceeded')\
                .stream()
            
            return sum(1 for _ in docs)
        except Exception as e:
            logger.error(f"Failed to get rate limited count: {e}")
            return 0

    def get_top_requesting_ips(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top requesting IPs"""
        db = self._get_client()
        if not db:
            return []
        
        try:
            from datetime import datetime, timedelta
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            collection_name = 'request_logs'
            if self.environment == 'staging':
                collection_name = 'request_logs_staging'
            elif self.environment == 'local':
                collection_name = 'request_logs_local'
            
            docs = db.collection(collection_name)\
                .where('timestamp', '>=', today_start.isoformat())\
                .stream()
            
            ip_counts = {}
            for doc in docs:
                ip = doc.to_dict().get('ip', '')
                ip_counts[ip] = ip_counts.get(ip, 0) + 1
            
            # Sort by count and return top IPs
            sorted_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)
            return [{'ip': ip, 'count': count} for ip, count in sorted_ips[:limit]]
        except Exception as e:
            logger.error(f"Failed to get top requesting IPs: {e}")
            return []

# Global Firestore manager instance
firestore_manager = FirestoreManager()
