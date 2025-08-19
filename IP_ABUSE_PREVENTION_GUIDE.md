# AstraVerify IP Abuse Prevention System

## Overview

This document describes the implementation of a comprehensive IP abuse prevention system for AstraVerify, designed to protect the service from overuse and malicious activities while maintaining good user experience for legitimate users.

## 🏗️ Architecture

### Core Components

1. **Request Logger** (`request_logger.py`)
   - Captures all incoming requests with IP addresses
   - Creates request fingerprints for abuse detection
   - Stores logs in Firestore for analytics

2. **Rate Limiter** (`rate_limiter.py`)
   - Multi-tier rate limiting (free, authenticated, premium)
   - Redis-based with in-memory fallback
   - Time-based limits (minute, hour, day)

3. **Abuse Detector** (`abuse_detector.py`)
   - Behavioral analysis of request patterns
   - Suspicious pattern detection
   - Risk scoring and automatic action triggers

4. **IP Blocker** (`ip_blocker.py`)
   - Multi-level IP blocking (temporary, extended, permanent)
   - Automatic block expiration
   - Admin management interface

5. **Enhanced Firestore** (`firestore_config.py`)
   - Request log storage
   - IP analytics and statistics
   - Environment-specific collections

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
./install_security_deps.sh
```

### 2. Start the Secure Backend

```bash
cd backend
./start_secure_backend.sh
```

### 3. Test the System

```bash
cd backend
python test_security_system.py
```

## 📊 Features

### Rate Limiting

- **Free Tier**: 10/min, 100/hour, 1000/day
- **Authenticated**: 30/min, 500/hour, 5000/day
- **Premium**: 100/min, 2000/hour, 20000/day

### Abuse Detection Patterns

- **Rapid Requests**: >50 requests per minute
- **Repeated Domains**: >20 same domain requests per hour
- **Error Spam**: >10 consecutive errors per 5 minutes
- **Suspicious User Agents**: Bot/crawler patterns
- **Invalid Domains**: IP addresses, hashes, test domains

### IP Blocking Levels

- **Temporary**: 30 minutes
- **Extended**: 6 hours
- **Permanent**: Until manually unblocked

## 🔧 Configuration

### Environment Variables

```bash
# Required
ENVIRONMENT=local
ADMIN_API_KEY=astraverify-admin-2024

# Optional
REDIS_URL=redis://localhost:6379
VALID_API_KEYS=key1,key2,key3
PREMIUM_IPS=127.0.0.1,::1
```

### Rate Limiting Configuration

```python
# In rate_limiter.py
rate_limits = {
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
```

## 📡 API Endpoints

### Public Endpoints

- `GET /api/health` - Health check
- `GET /api/check?domain=example.com` - Domain analysis

### Admin Endpoints

All admin endpoints require `X-Admin-API-Key` header.

- `GET /api/admin/security-dashboard` - Security overview
- `GET /api/admin/blocked-ips` - List blocked IPs
- `POST /api/admin/block-ip/{ip}` - Block an IP
- `POST /api/admin/unblock-ip/{ip}` - Unblock an IP
- `GET /api/admin/ip-analytics/{ip}` - IP analytics

### Rate Limit Headers

All responses include rate limit headers:
- `X-RateLimit-Limit`: Requests per minute
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp

## 🔍 Monitoring

### Security Dashboard

```bash
curl -H "X-Admin-API-Key: astraverify-admin-2024" \
     http://localhost:5000/api/admin/security-dashboard
```

Response includes:
- Rate limiting statistics
- Abuse detection metrics
- System health information

### IP Analytics

```bash
curl -H "X-Admin-API-Key: astraverify-admin-2024" \
     http://localhost:5000/api/admin/ip-analytics/192.168.1.1
```

Response includes:
- Request count and patterns
- Abuse score and risk level
- Block status and history

## 🛡️ Security Features

### Request Logging

Every request is logged with:
- Client IP address
- User agent
- Request details
- Response status and timing
- Error information

### Behavioral Analysis

The system analyzes:
- Request frequency patterns
- Domain repetition
- Error patterns
- User agent anomalies
- Geographic patterns

### Automatic Actions

Based on risk scores:
- **Score 5-14**: Low risk (monitoring)
- **Score 15-29**: Medium risk (monitoring)
- **Score 30-49**: High risk (temporary block)
- **Score 50+**: Critical risk (permanent block)

## 🔧 Admin Management

### Block an IP

```bash
curl -X POST \
     -H "X-Admin-API-Key: astraverify-admin-2024" \
     -H "Content-Type: application/json" \
     -d '{"reason": "Suspicious activity", "level": "temporary"}' \
     http://localhost:5000/api/admin/block-ip/192.168.1.100
```

### Unblock an IP

```bash
curl -X POST \
     -H "X-Admin-API-Key: astraverify-admin-2024" \
     http://localhost:5000/api/admin/unblock-ip/192.168.1.100
```

### View Blocked IPs

```bash
curl -H "X-Admin-API-Key: astraverify-admin-2024" \
     http://localhost:5000/api/admin/blocked-ips
```

## 📈 Analytics

### Firestore Collections

- `request_logs_local` - Request logs (local environment)
- `request_logs_staging` - Request logs (staging environment)
- `request_logs` - Request logs (production environment)

### Data Retention

- Request logs: 30 days (automatic cleanup)
- IP history: 24 hours (in-memory)
- Blocked IPs: Until manually unblocked

## 🧪 Testing

### Run All Tests

```bash
cd backend
python test_security_system.py
```

### Test Individual Components

```bash
# Test rate limiting
curl -X GET "http://localhost:5000/api/check?domain=test1.com"
curl -X GET "http://localhost:5000/api/check?domain=test2.com"
# ... repeat until rate limited

# Test abuse detection
curl -H "User-Agent: bot/crawler" \
     "http://localhost:5000/api/check?domain=test.com"

# Test admin endpoints
curl -H "X-Admin-API-Key: astraverify-admin-2024" \
     "http://localhost:5000/api/admin/security-dashboard"
```

## 🔄 Integration

### With Existing Frontend

The secure backend is compatible with the existing frontend. No changes needed to the frontend code.

### With Existing Backend

The secure backend (`app_with_security.py`) includes all functionality from the original backend (`app.py`) plus security features.

## 🚨 Error Handling

### Rate Limit Exceeded

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60,
  "limits": {
    "requests_per_minute": 10,
    "requests_per_hour": 100,
    "requests_per_day": 1000
  },
  "current_usage": {
    "minute": 10,
    "hour": 50,
    "day": 200
  }
}
```

### IP Blocked

```json
{
  "error": "Access denied",
  "reason": "High abuse detected: ['rapid_requests', 'suspicious_user_agent']",
  "blocked_until": "2024-01-15T10:30:00"
}
```

## 🔧 Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - System falls back to in-memory rate limiting
   - No functionality lost, just reduced performance

2. **Firestore Not Available**
   - Request logging is skipped
   - Analytics endpoints return empty data
   - Core functionality continues to work

3. **Rate Limiting Not Working**
   - Check if Redis is running
   - Verify environment variables
   - Check logs for errors

### Debug Mode

Enable debug logging by setting:
```bash
export FLASK_DEBUG=1
```

## 📋 Best Practices

### For Production

1. **Use Redis** for distributed rate limiting
2. **Monitor logs** regularly for abuse patterns
3. **Review blocked IPs** periodically
4. **Adjust thresholds** based on usage patterns
5. **Set up alerts** for security events

### For Development

1. **Use in-memory rate limiting** for simplicity
2. **Test with various user agents**
3. **Simulate abuse patterns** to verify detection
4. **Monitor admin dashboard** during testing

## 🔮 Future Enhancements

### Planned Features

1. **Machine Learning** integration for better pattern detection
2. **Geographic blocking** by country/region
3. **API key management** with usage quotas
4. **Real-time alerts** for security events
5. **Advanced analytics** dashboard

### Scalability Improvements

1. **Distributed rate limiting** across multiple instances
2. **Database optimization** for high-volume logging
3. **Caching strategies** for frequently accessed data
4. **Load balancing** integration

## 📞 Support

For issues or questions about the IP abuse prevention system:

1. Check the logs for error messages
2. Run the test suite to verify functionality
3. Review the configuration settings
4. Check the admin dashboard for system status

---

**Note**: This system is designed to be non-intrusive for legitimate users while providing robust protection against abuse. All thresholds and configurations can be adjusted based on your specific needs and usage patterns.
