# Frontend Rate Limiting & IP Blocking Error Handling

## Overview

The AstraVerify frontend now includes enhanced error handling for security responses from the backend, providing user-friendly messages for rate limiting and IP blocking scenarios.

## Enhanced Error Handling Features

### 1. Rate Limiting (HTTP 429)

**Backend Response:**
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

**Frontend Display:**
- **Icon:** ⏱️
- **Title:** "Rate Limit Exceeded"
- **Message:** "Rate limit exceeded. You can make 10 requests per minute. Please wait 60 seconds before trying again."
- **Style:** Orange background with warning colors

### 2. IP Blocking (HTTP 403)

**Backend Response:**
```json
{
  "error": "Access denied",
  "reason": "High abuse detected: ['suspicious_user_agent']",
  "blocked_until": "2024-01-15T10:30:00"
}
```

**Frontend Display:**
- **Icon:** 🚫
- **Title:** "Access Blocked"
- **Message:** "Access temporarily blocked due to suspicious activity. Block expires in 45 minutes. Reason: High abuse detected: ['suspicious_user_agent']"
- **Style:** Red background with security warning colors

### 3. General Errors

**Frontend Display:**
- **Icon:** ⚠️
- **Title:** "Error"
- **Message:** Generic error message
- **Style:** Red background with error colors

## Implementation Details

### Error Parsing

The frontend now properly parses JSON error responses from the backend:

```javascript
// Enhanced error handling for security responses
let errorMessage = error.message;

// Check for rate limiting (429)
if (error.status === 429 && error.data) {
  if (error.data.error === 'Rate limit exceeded') {
    errorMessage = `Rate limit exceeded. You can make ${error.data.limits?.requests_per_minute || 10} requests per minute. Please wait ${error.data.retry_after || 60} seconds before trying again.`;
  } else {
    errorMessage = 'Rate limit exceeded. Please wait a moment before trying again.';
  }
}

// Check for IP blocking (403)
if (error.status === 403 && error.data) {
  if (error.data.error === 'Access denied') {
    if (error.data.blocked_until) {
      const blockedUntil = new Date(error.data.blocked_until);
      const now = new Date();
      const timeRemaining = Math.ceil((blockedUntil - now) / 1000 / 60); // minutes
      errorMessage = `Access temporarily blocked due to suspicious activity. Block expires in ${timeRemaining} minutes. Reason: ${error.data.reason || 'Security violation'}`;
    } else {
      errorMessage = `Access denied: ${error.data.reason || 'Security violation detected'}`;
    }
  } else {
    errorMessage = 'Access denied due to security policy. Please try again later.';
  }
}
```

### Visual Styling

Different error types have distinct visual styles:

```css
.error-message.rate-limit-error {
  background: #fff3e0;
  color: #e65100;
  border-left-color: #e65100;
}

.error-message.security-error {
  background: #fce4ec;
  color: #ad1457;
  border-left-color: #ad1457;
}

.error-message.general-error {
  background: #ffebee;
  color: #c62828;
  border-left-color: #c62828;
}
```

### Error Display Structure

```jsx
{error && (
  <div className={`error-message ${error.includes('Rate limit') ? 'rate-limit-error' : error.includes('Access denied') || error.includes('blocked') ? 'security-error' : 'general-error'}`}>
    <div className="error-icon">
      {error.includes('Rate limit') ? '⏱️' : error.includes('Access denied') || error.includes('blocked') ? '🚫' : '⚠️'}
    </div>
    <div className="error-content">
      <h4>
        {error.includes('Rate limit') ? 'Rate Limit Exceeded' : 
         error.includes('Access denied') || error.includes('blocked') ? 'Access Blocked' : 
         'Error'}
      </h4>
      <p>{error}</p>
    </div>
  </div>
)}
```

## User Experience

### Rate Limiting Scenario

1. **User makes multiple rapid requests**
2. **Backend returns 429 with rate limit details**
3. **Frontend displays friendly message with:**
   - Clear explanation of the limit
   - Retry time information
   - Visual indicator (⏱️ icon)
   - Orange warning styling

### IP Blocking Scenario

1. **User triggers abuse detection (suspicious user agent, rapid requests, etc.)**
2. **Backend returns 403 with block details**
3. **Frontend displays security message with:**
   - Block reason explanation
   - Time remaining until unblock
   - Visual indicator (🚫 icon)
   - Red security styling

## Testing

### Test Page

A test page (`test_rate_limit_frontend.html`) is available to demonstrate the error handling:

1. **Rate Limiting Test:** Makes 15 rapid requests to trigger rate limiting
2. **IP Blocking Test:** Uses suspicious user agents to trigger IP blocking
3. **Normal Request Test:** Verifies normal functionality

### Manual Testing

To test manually:

1. **Rate Limiting:**
   ```bash
   # Make 11 rapid requests (exceeds 10/minute limit)
   for i in {1..11}; do curl "http://localhost:8080/api/check?domain=test$i.com"; done
   ```

2. **IP Blocking:**
   ```bash
   # Use suspicious user agent
   curl -H "User-Agent: python-requests/2.28.1" "http://localhost:8080/api/check?domain=test.com"
   ```

## Benefits

1. **User-Friendly Messages:** Clear, actionable error messages
2. **Visual Distinction:** Different styles for different error types
3. **Informative Content:** Includes retry times, limits, and reasons
4. **Accessibility:** Proper icons and color coding
5. **Consistent Experience:** Uniform error handling across the application

## Future Enhancements

1. **Retry Countdown:** Real-time countdown timer for rate limits
2. **Progressive Enhancement:** Graceful degradation for older browsers
3. **Internationalization:** Support for multiple languages
4. **Analytics:** Track error frequency and user behavior
5. **Custom Limits:** Display user-specific rate limits based on tier
