from datetime import datetime, timedelta
from typing import Dict, List, Any
import re
from collections import defaultdict
import logging
import os

logger = logging.getLogger(__name__)

class AbuseDetector:
    def __init__(self):
        # Get environment to adjust sensitivity
        self.environment = os.environ.get('ENVIRONMENT', 'local')
        
        # Adjust thresholds based on environment
        if self.environment == 'production':
            # More lenient thresholds for production
            self.suspicious_patterns = {
                'rapid_requests': {
                    'threshold': 200,  # Increased from 50
                    'window': 60,     # seconds
                    'score': 5        # Reduced from 10
                },
                'repeated_domains': {
                    'threshold': 50,  # Increased from 20
                    'window': 3600,   # 1 hour
                    'score': 2        # Reduced from 5
                },
                'error_spam': {
                    'threshold': 20,  # Increased from 10
                    'window': 300,    # 5 minutes
                    'score': 4        # Reduced from 8
                },
                'suspicious_user_agents': {
                    'patterns': [
                        r'bot|crawler|spider|scraper',
                        # Removed python|curl|wget patterns for production
                        r'^\s*$'  # Empty user agent
                    ],
                    'score': 1        # Reduced from 3
                },
                'invalid_domains': {
                    'patterns': [
                        r'^[0-9.]+$',  # IP addresses
                        r'^[a-z0-9]{32}$',  # MD5 hashes
                        r'^test\d+\.com$',  # Test domains
                    ],
                    'score': 2        # Reduced from 5
                }
            }
        else:
            # Original thresholds for staging/local
            self.suspicious_patterns = {
                'rapid_requests': {
                    'threshold': 50,  # requests per minute
                    'window': 60,     # seconds
                    'score': 10
                },
                'repeated_domains': {
                    'threshold': 20,  # same domain requests
                    'window': 3600,   # 1 hour
                    'score': 5
                },
                'error_spam': {
                    'threshold': 10,  # consecutive errors
                    'window': 300,    # 5 minutes
                    'score': 8
                },
                'suspicious_user_agents': {
                    'patterns': [
                        r'bot|crawler|spider|scraper',
                        r'python|curl|wget',
                        r'^\s*$'  # Empty user agent
                    ],
                    'score': 3
                },
                'invalid_domains': {
                    'patterns': [
                        r'^[0-9.]+$',  # IP addresses
                        r'^[a-z0-9]{32}$',  # MD5 hashes
                        r'^test\d+\.com$',  # Test domains
                    ],
                    'score': 5
                }
            }
        
        self.ip_scores = defaultdict(int)
        self.ip_history = defaultdict(list)
    
    def clear_all_blocks(self):
        """Clear all IP scores and history - for production emergencies"""
        self.ip_scores.clear()
        self.ip_history.clear()
        logger.warning("All abuse detection data cleared - production emergency")
    
    def reset_ip_score(self, ip: str):
        """Reset score for a specific IP"""
        if ip in self.ip_scores:
            del self.ip_scores[ip]
        if ip in self.ip_history:
            del self.ip_history[ip]
        logger.info(f"Reset abuse detection data for IP {ip}")
    
    def analyze_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request for suspicious behavior"""
        ip = request_data['ip']
        score = 0
        flags = []
        
        # Check rapid requests
        if self._check_rapid_requests(ip, request_data['timestamp']):
            score += self.suspicious_patterns['rapid_requests']['score']
            flags.append('rapid_requests')
        
        # Check repeated domains
        if self._check_repeated_domains(ip, request_data['domain'], request_data['timestamp']):
            score += self.suspicious_patterns['repeated_domains']['score']
            flags.append('repeated_domains')
        
        # Check error spam
        if request_data.get('error') and self._check_error_spam(ip, request_data['timestamp']):
            score += self.suspicious_patterns['error_spam']['score']
            flags.append('error_spam')
        
        # Check suspicious user agent
        if self._check_suspicious_user_agent(request_data['user_agent']):
            score += self.suspicious_patterns['suspicious_user_agents']['score']
            flags.append('suspicious_user_agent')
        
        # Check invalid domains
        if self._check_invalid_domain(request_data['domain']):
            score += self.suspicious_patterns['invalid_domains']['score']
            flags.append('invalid_domain')
        
        # Update IP score
        self.ip_scores[ip] += score
        
        # Store request in history
        self.ip_history[ip].append({
            'timestamp': request_data['timestamp'],
            'domain': request_data['domain'],
            'score': score,
            'flags': flags,
            'error': request_data.get('error')
        })
        
        # Clean old history
        self._clean_old_history(ip)
        
        return {
            'score': score,
            'total_score': self.ip_scores[ip],
            'flags': flags,
            'risk_level': self._get_risk_level(self.ip_scores[ip]),
            'action_required': self._should_take_action(self.ip_scores[ip])
        }
    
    def _check_rapid_requests(self, ip: str, timestamp: str) -> bool:
        """Check for rapid request patterns"""
        window = self.suspicious_patterns['rapid_requests']['window']
        threshold = self.suspicious_patterns['rapid_requests']['threshold']
        
        cutoff = datetime.fromisoformat(timestamp) - timedelta(seconds=window)
        recent_requests = [
            req for req in self.ip_history[ip]
            if datetime.fromisoformat(req['timestamp']) > cutoff
        ]
        
        return len(recent_requests) > threshold
    
    def _check_repeated_domains(self, ip: str, domain: str, timestamp: str) -> bool:
        """Check for repeated domain requests"""
        window = self.suspicious_patterns['repeated_domains']['window']
        threshold = self.suspicious_patterns['repeated_domains']['threshold']
        
        cutoff = datetime.fromisoformat(timestamp) - timedelta(seconds=window)
        recent_requests = [
            req for req in self.ip_history[ip]
            if datetime.fromisoformat(req['timestamp']) > cutoff and req['domain'] == domain
        ]
        
        return len(recent_requests) > threshold
    
    def _check_error_spam(self, ip: str, timestamp: str) -> bool:
        """Check for consecutive error patterns"""
        window = self.suspicious_patterns['error_spam']['window']
        threshold = self.suspicious_patterns['error_spam']['threshold']
        
        cutoff = datetime.fromisoformat(timestamp) - timedelta(seconds=window)
        recent_errors = [
            req for req in self.ip_history[ip]
            if datetime.fromisoformat(req['timestamp']) > cutoff and req.get('error')
        ]
        
        return len(recent_errors) > threshold
    
    def _check_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check for suspicious user agent patterns"""
        for pattern in self.suspicious_patterns['suspicious_user_agents']['patterns']:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return True
        return False
    
    def _check_invalid_domain(self, domain: str) -> bool:
        """Check for invalid domain patterns"""
        for pattern in self.suspicious_patterns['invalid_domains']['patterns']:
            if re.search(pattern, domain, re.IGNORECASE):
                return True
        return False
    
    def _get_risk_level(self, score: int) -> str:
        """Get risk level based on score"""
        if score >= 50:
            return 'critical'
        elif score >= 30:
            return 'high'
        elif score >= 15:
            return 'medium'
        elif score >= 5:
            return 'low'
        else:
            return 'normal'
    
    def _should_take_action(self, score: int) -> bool:
        """Determine if action should be taken"""
        return score >= 30  # Take action for high/critical risk
    
    def _clean_old_history(self, ip: str):
        """Clean old request history"""
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.ip_history[ip] = [
            req for req in self.ip_history[ip]
            if datetime.fromisoformat(req['timestamp']) > cutoff
        ]
    
    def get_ip_analytics(self, ip: str) -> Dict[str, Any]:
        """Get analytics for a specific IP"""
        if ip not in self.ip_history:
            return {
                'total_requests': 0,
                'total_score': 0,
                'risk_level': 'normal',
                'recent_activity': []
            }
        
        history = self.ip_history[ip]
        total_score = self.ip_scores.get(ip, 0)
        
        # Get recent activity (last 10 requests)
        recent_activity = sorted(history, key=lambda x: x['timestamp'], reverse=True)[:10]
        
        return {
            'total_requests': len(history),
            'total_score': total_score,
            'risk_level': self._get_risk_level(total_score),
            'recent_activity': recent_activity
        }
