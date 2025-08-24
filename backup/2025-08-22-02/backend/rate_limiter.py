from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Any
import time
from collections import defaultdict
import threading
import redis
import os
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self):
        self.rate_limits = {
            'free': {
                'requests_per_minute': 10,
                'requests_per_hour': 100,
                'requests_per_day': 1000
            },
            'authenticated': {
                'requests_per_minute': 30,
                'requests_per_hour': 500,
                'requests_per_day': 5000
            },
            'premium': {
                'requests_per_minute': 100,
                'requests_per_hour': 2000,
                'requests_per_day': 20000
            }
        }
        
        # Try to connect to Redis, fallback to in-memory
        self.redis_client = None
        try:
            redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            logger.info("Connected to Redis for rate limiting")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory rate limiting: {e}")
            self.redis_client = None
        
        # In-memory storage for rate limiting (fallback)
        self.request_counts = defaultdict(int)
        self.last_reset = defaultdict(datetime.utcnow)
        self.lock = threading.Lock()
    
    def get_user_tier(self, api_key: Optional[str] = None, ip: str = None) -> str:
        """Determine user tier based on API key or IP reputation"""
        if api_key:
            # Check if API key exists and is valid
            if self._is_valid_api_key(api_key):
                return 'authenticated'
        
        # Check IP reputation
        if self._is_premium_ip(ip):
            return 'premium'
        
        return 'free'
    
    def _is_valid_api_key(self, api_key: str) -> bool:
        """Check if API key is valid"""
        # For now, check against environment variable
        valid_keys = os.environ.get('VALID_API_KEYS', '').split(',')
        return api_key in valid_keys
    
    def _is_premium_ip(self, ip: str) -> bool:
        """Check if IP is premium (trusted)"""
        # For now, check against environment variable
        premium_ips = os.environ.get('PREMIUM_IPS', '').split(',')
        return ip in premium_ips
    
    def check_rate_limit(self, identifier: str, tier: str = 'free') -> Tuple[bool, Dict[str, Any]]:
        """Check if request is within rate limits"""
        if self.redis_client:
            return self._check_rate_limit_redis(identifier, tier)
        else:
            return self._check_rate_limit_memory(identifier, tier)
    
    def _check_rate_limit_redis(self, identifier: str, tier: str) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limits using Redis"""
        try:
            limits = self.rate_limits[tier]
            now = datetime.utcnow()
            
            # Create keys for different time windows
            minute_key = f"rate_limit:{identifier}:{now.strftime('%Y%m%d%H%M')}"
            hour_key = f"rate_limit:{identifier}:{now.strftime('%Y%m%d%H')}"
            day_key = f"rate_limit:{identifier}:{now.strftime('%Y%m%d')}"
            
            # Get current counts
            minute_count = int(self.redis_client.get(minute_key) or 0)
            hour_count = int(self.redis_client.get(hour_key) or 0)
            day_count = int(self.redis_client.get(day_key) or 0)
            
            # Check if any limit is exceeded
            if (minute_count >= limits['requests_per_minute'] or
                hour_count >= limits['requests_per_hour'] or
                day_count >= limits['requests_per_day']):
                
                return False, {
                    'limit_exceeded': True,
                    'retry_after': self._get_retry_after_redis(identifier, limits),
                    'limits': limits,
                    'current_usage': {
                        'minute': minute_count,
                        'hour': hour_count,
                        'day': day_count
                    }
                }
            
            # Increment counters with expiration
            pipe = self.redis_client.pipeline()
            pipe.incr(minute_key)
            pipe.expire(minute_key, 60)  # 1 minute
            pipe.incr(hour_key)
            pipe.expire(hour_key, 3600)  # 1 hour
            pipe.incr(day_key)
            pipe.expire(day_key, 86400)  # 1 day
            pipe.execute()
            
            return True, {
                'limit_exceeded': False,
                'limits': limits,
                'current_usage': {
                    'minute': minute_count + 1,
                    'hour': hour_count + 1,
                    'day': day_count + 1
                }
            }
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            # Fallback to memory-based rate limiting
            return self._check_rate_limit_memory(identifier, tier)
    
    def _check_rate_limit_memory(self, identifier: str, tier: str) -> Tuple[bool, Dict[str, Any]]:
        """Check rate limits using in-memory storage"""
        with self.lock:
            now = datetime.utcnow()
            limits = self.rate_limits[tier]
            
            # Reset counters if needed
            self._reset_counters_if_needed(identifier, now)
            
            # Check limits
            minute_key = f"{identifier}:{now.strftime('%Y%m%d%H%M')}"
            hour_key = f"{identifier}:{now.strftime('%Y%m%d%H')}"
            day_key = f"{identifier}:{now.strftime('%Y%m%d')}"
            
            minute_count = self.request_counts[minute_key]
            hour_count = self.request_counts[hour_key]
            day_count = self.request_counts[day_key]
            
            # Check if any limit is exceeded
            if (minute_count >= limits['requests_per_minute'] or
                hour_count >= limits['requests_per_hour'] or
                day_count >= limits['requests_per_day']):
                
                return False, {
                    'limit_exceeded': True,
                    'retry_after': self._get_retry_after_memory(identifier, limits),
                    'limits': limits,
                    'current_usage': {
                        'minute': minute_count,
                        'hour': hour_count,
                        'day': day_count
                    }
                }
            
            # Increment counters
            self.request_counts[minute_key] += 1
            self.request_counts[hour_key] += 1
            self.request_counts[day_key] += 1
            
            return True, {
                'limit_exceeded': False,
                'limits': limits,
                'current_usage': {
                    'minute': minute_count + 1,
                    'hour': hour_count + 1,
                    'day': day_count + 1
                }
            }
    
    def _get_retry_after_redis(self, identifier: str, limits: Dict) -> int:
        """Get retry after time for Redis-based rate limiting"""
        # Return 60 seconds for now (simplified)
        return 60
    
    def _get_retry_after_memory(self, identifier: str, limits: Dict) -> int:
        """Get retry after time for memory-based rate limiting"""
        # Return 60 seconds for now (simplified)
        return 60
    
    def _reset_counters_if_needed(self, identifier: str, now: datetime):
        """Reset counters for old time periods"""
        # Clean up old entries (older than 24 hours)
        cutoff = now - timedelta(hours=24)
        keys_to_remove = []
        
        for key in self.request_counts:
            if key.startswith(f"{identifier}:"):
                try:
                    # Extract timestamp from key and check if it's old
                    timestamp_str = key.split(':', 1)[1]
                    if len(timestamp_str) >= 8:  # YYYYMMDD format
                        key_date = datetime.strptime(timestamp_str[:8], '%Y%m%d')
                        if key_date < cutoff.date():
                            keys_to_remove.append(key)
                except:
                    pass
        
        for key in keys_to_remove:
            del self.request_counts[key]
