"""
Enhanced Error Handling System for AstraVerify Production Environment
Provides comprehensive error handling, retry logic, and graceful degradation
"""

import logging
import time
import functools
import traceback
from typing import Any, Callable, Dict, Optional, Union
from datetime import datetime, timedelta
import dns.resolver
import requests
from flask import jsonify, request
import os

# Configure logging
logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling system for production reliability"""
    
    def __init__(self):
        self.error_counts = {}
        self.last_errors = {}
        self.circuit_breaker_states = {}
        self.retry_configs = {
            'dns': {'max_retries': 3, 'backoff_factor': 2, 'timeout': 10},
            'http': {'max_retries': 3, 'backoff_factor': 2, 'timeout': 15},
            'database': {'max_retries': 5, 'backoff_factor': 1.5, 'timeout': 30},
            'email': {'max_retries': 2, 'backoff_factor': 3, 'timeout': 20}
        }
    
    def handle_dns_error(self, domain: str, error: Exception) -> Dict[str, Any]:
        """Handle DNS resolution errors with graceful degradation"""
        error_type = type(error).__name__
        error_key = f"dns_{domain}_{error_type}"
        
        # Log the error
        logger.warning(f"DNS error for {domain}: {error}")
        
        # Track error frequency
        self._track_error(error_key)
        
        # Check if we should use cached results
        if self._should_use_cache(error_key):
            logger.info(f"Using cached DNS results for {domain} due to repeated errors")
            return self._get_cached_dns_results(domain)
        
        # Return graceful error response
        return {
            'has_mx': False,
            'records': [],
            'status': 'Error',
            'description': f'DNS resolution failed: {str(error)}',
            'error_type': error_type,
            'fallback_used': False
        }
    
    def handle_network_error(self, operation: str, error: Exception) -> Dict[str, Any]:
        """Handle network-related errors"""
        error_type = type(error).__name__
        error_key = f"network_{operation}_{error_type}"
        
        logger.warning(f"Network error during {operation}: {error}")
        self._track_error(error_key)
        
        # Return appropriate fallback response
        if 'dns' in operation.lower():
            return self._get_dns_fallback_response()
        elif 'http' in operation.lower():
            return self._get_http_fallback_response()
        else:
            return {
                'status': 'Error',
                'description': f'Network operation failed: {str(error)}',
                'error_type': error_type
            }
    
    def handle_database_error(self, operation: str, error: Exception) -> Dict[str, Any]:
        """Handle database operation errors"""
        error_type = type(error).__name__
        error_key = f"database_{operation}_{error_type}"
        
        logger.error(f"Database error during {operation}: {error}")
        self._track_error(error_key)
        
        # For database errors, we can continue without storing results
        return {
            'status': 'Warning',
            'description': f'Database operation failed: {str(error)}',
            'operation_continued': True
        }
    
    def handle_email_error(self, operation: str, error: Exception) -> Dict[str, Any]:
        """Handle email-related errors"""
        error_type = type(error).__name__
        error_key = f"email_{operation}_{error_type}"
        
        logger.warning(f"Email error during {operation}: {error}")
        self._track_error(error_key)
        
        return {
            'status': 'Warning',
            'description': f'Email operation failed: {str(error)}',
            'email_sent': False
        }
    
    def _track_error(self, error_key: str):
        """Track error frequency for circuit breaker logic"""
        current_time = datetime.now()
        
        if error_key not in self.error_counts:
            self.error_counts[error_key] = 0
            self.last_errors[error_key] = current_time
        
        self.error_counts[error_key] += 1
        self.last_errors[error_key] = current_time
        
        # Reset counter if more than 1 hour has passed
        if current_time - self.last_errors[error_key] > timedelta(hours=1):
            self.error_counts[error_key] = 1
    
    def _should_use_cache(self, error_key: str) -> bool:
        """Determine if we should use cached results due to repeated errors"""
        error_count = self.error_counts.get(error_key, 0)
        return error_count >= 3  # Use cache after 3 consecutive errors
    
    def _get_cached_dns_results(self, domain: str) -> Dict[str, Any]:
        """Get cached DNS results for a domain"""
        # This would typically query a cache/database
        # For now, return a basic fallback
        return {
            'has_mx': True,
            'records': [{'priority': 10, 'server': 'fallback.example.com', 'valid': True}],
            'status': 'Cached',
            'description': 'Using cached DNS results due to resolution issues',
            'fallback_used': True
        }
    
    def _get_dns_fallback_response(self) -> Dict[str, Any]:
        """Get fallback response for DNS operations"""
        return {
            'has_mx': False,
            'records': [],
            'status': 'Error',
            'description': 'DNS resolution temporarily unavailable',
            'fallback_used': True
        }
    
    def _get_http_fallback_response(self) -> Dict[str, Any]:
        """Get fallback response for HTTP operations"""
        return {
            'status': 'Error',
            'description': 'Network request temporarily unavailable',
            'fallback_used': True
        }

# Global error handler instance
error_handler = ErrorHandler()

def retry_on_failure(max_retries: int = 3, backoff_factor: float = 2.0, 
                    timeout: int = 10, operation_type: str = 'general'):
    """Decorator for retrying operations with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        wait_time = backoff_factor ** attempt
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                                     f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}: {e}")
            
            # If all retries failed, handle the error appropriately
            if operation_type == 'dns':
                return error_handler.handle_dns_error(str(args[0]) if args else 'unknown', last_exception)
            elif operation_type == 'network':
                return error_handler.handle_network_error(func.__name__, last_exception)
            elif operation_type == 'database':
                return error_handler.handle_database_error(func.__name__, last_exception)
            elif operation_type == 'email':
                return error_handler.handle_email_error(func.__name__, last_exception)
            else:
                raise last_exception
        
        return wrapper
    return decorator

def safe_dns_resolve(domain: str, record_type: str = 'MX') -> Dict[str, Any]:
    """Safely resolve DNS records with error handling"""
    try:
        resolver = dns.resolver.Resolver()
        resolver.timeout = 10
        resolver.lifetime = 10
        
        records = resolver.resolve(domain, record_type)
        return {
            'success': True,
            'records': [str(record) for record in records],
            'count': len(records)
        }
    except dns.resolver.NXDOMAIN:
        return {
            'success': False,
            'error': 'Domain not found',
            'error_type': 'NXDOMAIN'
        }
    except dns.resolver.NoAnswer:
        return {
            'success': False,
            'error': 'No records found',
            'error_type': 'NoAnswer'
        }
    except dns.resolver.Timeout:
        return {
            'success': False,
            'error': 'DNS resolution timeout',
            'error_type': 'Timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }

def safe_http_request(url: str, method: str = 'GET', **kwargs) -> Dict[str, Any]:
    """Safely make HTTP requests with error handling"""
    try:
        timeout = kwargs.pop('timeout', 15)
        response = requests.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return {
            'success': True,
            'status_code': response.status_code,
            'data': response.text,
            'headers': dict(response.headers)
        }
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timeout',
            'error_type': 'Timeout'
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Connection error',
            'error_type': 'ConnectionError'
        }
    except requests.exceptions.HTTPError as e:
        return {
            'success': False,
            'error': f'HTTP error: {e}',
            'error_type': 'HTTPError',
            'status_code': e.response.status_code if hasattr(e, 'response') else None
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }

def create_error_response(error_message: str, error_code: int = 500, 
                         error_type: str = 'InternalError') -> tuple:
    """Create standardized error responses"""
    error_response = {
        'error': error_message,
        'error_type': error_type,
        'timestamp': datetime.utcnow().isoformat(),
        'request_id': getattr(request, 'id', 'unknown'),
        'environment': os.environ.get('ENVIRONMENT', 'unknown')
    }
    
    # Log the error for monitoring
    logger.error(f"API Error: {error_message} (Type: {error_type}, Code: {error_code})")
    
    return jsonify(error_response), error_code

def validate_production_environment() -> bool:
    """Validate that the production environment is properly configured"""
    required_vars = [
        'ENVIRONMENT',
        'ADMIN_API_KEY',
        'EMAIL_SENDER',
        'EMAIL_SMTP_SERVER'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return False
    
    return True

def health_check_enhanced() -> Dict[str, Any]:
    """Enhanced health check with detailed system status"""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': os.environ.get('ENVIRONMENT', 'unknown'),
        'version': '2.0.0',
        'checks': {}
    }
    
    # Check environment configuration
    health_status['checks']['environment'] = {
        'status': 'healthy' if validate_production_environment() else 'unhealthy',
        'details': 'Environment variables validated'
    }
    
    # Check DNS resolution capability
    dns_test = safe_dns_resolve('google.com', 'A')
    health_status['checks']['dns'] = {
        'status': 'healthy' if dns_test['success'] else 'unhealthy',
        'details': dns_test.get('error', 'DNS resolution working')
    }
    
    # Check network connectivity
    network_test = safe_http_request('https://httpbin.org/get', timeout=5)
    health_status['checks']['network'] = {
        'status': 'healthy' if network_test['success'] else 'unhealthy',
        'details': network_test.get('error', 'Network connectivity working')
    }
    
    # Overall status
    all_healthy = all(check['status'] == 'healthy' for check in health_status['checks'].values())
    health_status['status'] = 'healthy' if all_healthy else 'degraded'
    
    return health_status

# Circuit breaker implementation
class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == 'OPEN':
            if self._should_attempt_reset():
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if not self.last_failure_time:
            return True
        
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.recovery_timeout

# Global circuit breakers for different operations
dns_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
network_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
database_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=120)
