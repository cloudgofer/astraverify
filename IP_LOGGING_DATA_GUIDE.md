# AstraVerify IP Logging Data Guide

## 📍 Where to Find IP Logged Data

The AstraVerify IP abuse prevention system stores IP logged data in multiple locations for different purposes:

## 1. 🔥 **Firestore Database (Primary Storage)**

### **Location**: Firebase Console
- **URL**: https://console.firebase.google.com/
- **Project**: Your AstraVerify project
- **Database**: Firestore Database

### **Collections**:
- **Local Environment**: `request_logs_local`
- **Staging Environment**: `request_logs_staging`  
- **Production Environment**: `request_logs`

### **Data Structure**:
Each document in the collection contains:
```json
{
  "ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
  "domain": "example.com",
  "endpoint": "check_domain",
  "method": "GET",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "path": "/api/check",
  "query_string": "domain=example.com",
  "response_status": 200,
  "response_time_ms": 150,
  "error": null,
  "response_size": 1024,
  "created_at": "2024-01-15T10:30:00.000Z",
  "expires_at": "2024-02-14T10:30:00.000Z"
}
```

### **Access Method**:
1. Go to Firebase Console
2. Select your AstraVerify project
3. Click "Firestore Database"
4. Navigate to the appropriate collection
5. Browse or query the documents

## 2. 📡 **Admin API Endpoints**

### **Security Dashboard**
```bash
curl -H "X-Admin-API-Key: astraverify-admin-2024" \
     http://localhost:8080/api/admin/security-dashboard
```

**Returns**:
- Total requests today
- Rate-limited requests count
- Top requesting IPs
- Blocked IPs count
- System health information

### **Blocked IPs List**
```bash
curl -H "X-Admin-API-Key: astraverify-admin-2024" \
     http://localhost:8080/api/admin/blocked-ips
```

**Returns**:
```json
{
  "blocked_ips": {
    "192.168.1.100": {
      "reason": "High abuse detected: ['rapid_requests']",
      "blocked_until": "2024-01-15T11:00:00.000Z",
      "level": "temporary",
      "blocked_at": "2024-01-15T10:30:00.000Z"
    }
  },
  "total_blocked": 1,
  "statistics": {
    "total_blocked": 1,
    "by_level": {"temporary": 1},
    "permanent_blocks": 0,
    "temporary_blocks": 1,
    "extended_blocks": 0
  }
}
```

### **IP Analytics**
```bash
curl -H "X-Admin-API-Key: astraverify-admin-2024" \
     http://localhost:8080/api/admin/ip-analytics/192.168.1.100
```

**Returns**:
```json
{
  "ip": "192.168.1.100",
  "analytics": {
    "total_requests": 25,
    "unique_domains": 5,
    "error_count": 2,
    "avg_response_time": 120.5,
    "last_request": "2024-01-15T10:30:00.000Z"
  },
  "abuse_score": 15,
  "risk_level": "medium",
  "is_blocked": false,
  "block_info": null
}
```

## 3. 🧠 **In-Memory Storage (Runtime)**

### **Rate Limiter Data**
- **Location**: `rate_limiter.py` - `request_counts` dictionary
- **Format**: `{ip_timestamp_key: count}`
- **Retention**: 24 hours (automatic cleanup)

### **Abuse Detector Data**
- **Location**: `abuse_detector.py` - `ip_scores` and `ip_history`
- **Format**: 
  - `ip_scores`: `{ip: total_score}`
  - `ip_history`: `{ip: [request_history_list]}`
- **Retention**: 24 hours for history

### **IP Blocker Data**
- **Location**: `ip_blocker.py` - `blocked_ips` dictionary
- **Format**: `{ip: block_info}`
- **Retention**: Until manually unblocked or expired

## 4. 📝 **Application Logs**

### **Console Output (Development)**
When running the backend, you'll see logs like:
```
INFO:__main__:Request: {"ip": "127.0.0.1", "user_agent": "curl/7.68.0", "domain": "example.com", "timestamp": "2024-01-15T10:30:00.000Z", "response_status": 200, "response_time_ms": 150}
```

### **Log Files (Production)**
- **Location**: Application log files
- **Format**: JSON or structured logs
- **Retention**: Based on log rotation policy

## 5. 🔍 **Real-Time Monitoring**

### **Rate Limit Headers**
Every API response includes:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1705312200
```

### **Error Responses**
When rate limited or blocked:
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

## 6. 🛠️ **Development Tools**

### **Test Script**
Run the test script to generate sample data:
```bash
cd backend
python test_security_system.py
```

### **Demo Script**
Run the demo script to see data locations:
```bash
cd backend
python demo_ip_logging.py
```

## 7. 📊 **Data Retention Policies**

| Data Type | Storage | Retention | Cleanup |
|-----------|---------|-----------|---------|
| Request Logs | Firestore | 30 days | Automatic |
| Rate Limit Counters | Memory/Redis | 24 hours | Automatic |
| Abuse History | Memory | 24 hours | Automatic |
| Blocked IPs | Memory | Until unblocked | Manual |
| Application Logs | Files | Configurable | Log rotation |

## 8. 🔧 **Querying Examples**

### **Firestore Queries**
```javascript
// Get all requests from a specific IP
db.collection('request_logs_local')
  .where('ip', '==', '192.168.1.100')
  .orderBy('timestamp', 'desc')
  .limit(10)

// Get requests from last 24 hours
db.collection('request_logs_local')
  .where('timestamp', '>=', '2024-01-14T10:30:00.000Z')
  .orderBy('timestamp', 'desc')

// Get rate-limited requests
db.collection('request_logs_local')
  .where('error', '==', 'Rate limit exceeded')
  .orderBy('timestamp', 'desc')
```

### **Admin API Queries**
```bash
# Get analytics for specific time period
curl -H "X-Admin-API-Key: astraverify-admin-2024" \
     "http://localhost:8080/api/admin/ip-analytics/192.168.1.100?hours=48"

# Get top requesting IPs
curl -H "X-Admin-API-Key: astraverify-admin-2024" \
     "http://localhost:8080/api/admin/security-dashboard"
```

## 9. 🚨 **Security Considerations**

### **Data Privacy**
- IP addresses are logged for security purposes
- Data is automatically cleaned up after retention period
- Admin access is required to view detailed analytics

### **Access Control**
- Admin endpoints require `X-Admin-API-Key` header
- Firestore access requires proper authentication
- In-memory data is only accessible during runtime

### **Compliance**
- GDPR: Right to be forgotten (manual IP unblocking)
- Data minimization: Only necessary data is logged
- Retention limits: Automatic cleanup prevents data hoarding

## 10. 📈 **Analytics Use Cases**

### **Security Monitoring**
- Identify suspicious IP patterns
- Monitor rate limiting effectiveness
- Track abuse detection accuracy

### **Performance Analysis**
- Response time trends
- Error rate monitoring
- Usage pattern analysis

### **Capacity Planning**
- Request volume trends
- Peak usage identification
- Resource allocation optimization

---

**Note**: The IP logging system is designed to be transparent and secure. All data is automatically managed with appropriate retention policies, and access is controlled through proper authentication mechanisms.
