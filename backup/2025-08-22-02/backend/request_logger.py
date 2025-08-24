import logging
from datetime import datetime, timedelta
from flask import request, g
import json
from typing import Dict, Any, Optional
from firestore_config import firestore_manager
import time

logger = logging.getLogger(__name__)

class RequestLogger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_client_ip(self) -> str:
        """Extract real client IP considering proxies and load balancers"""
        # Check for forwarded headers (common with load balancers)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(',')[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
            
        # Fallback to remote address
        return request.remote_addr
    
    def get_request_fingerprint(self) -> Dict[str, Any]:
        """Create unique request fingerprint for abuse detection"""
        return {
            'ip': self.get_client_ip(),
            'user_agent': request.headers.get('User-Agent', ''),
            'domain': request.args.get('domain', ''),
            'endpoint': request.endpoint,
            'method': request.method,
            'timestamp': datetime.utcnow().isoformat(),
            'session_id': request.cookies.get('session_id', ''),
            'referer': request.headers.get('Referer', ''),
            'path': request.path,
            'query_string': request.query_string.decode('utf-8') if request.query_string else ''
        }
    
    def log_request(self, response_data: Optional[Dict] = None, error: Optional[str] = None):
        """Log comprehensive request information"""
        fingerprint = self.get_request_fingerprint()
        
        log_entry = {
            **fingerprint,
            'response_status': getattr(g, 'response_status', 200),
            'response_time_ms': getattr(g, 'response_time', 0),
            'error': error,
            'response_size': len(str(response_data)) if response_data else 0
        }
        
        # Store in Firestore for analytics
        firestore_manager.store_request_log(log_entry)
        
        # Log to application logs
        self.logger.info(f"Request: {json.dumps(log_entry, default=str)}")
        
        return log_entry
