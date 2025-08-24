# IP Management Test Guide - 2025-08-22-02

## 🚀 Quick Start

### 1. Start the Backend Server
```bash
cd backend
python3 app_enhanced_dkim.py
```

### 2. Access the IP Management UI
Open your browser and navigate to:
```
http://localhost:5001/admin/ui/ip-management
```

## 🧪 Testing Scenarios

### Test 1: Basic IP Management Access
1. Navigate to the IP Management page
2. Verify the page loads with the admin interface
3. Check that the navigation shows "IP Management" as active
4. Verify the statistics cards are displayed

### Test 2: Block an IP Address
1. Click the "🚫 Block New IP" button
2. Fill in the modal form:
   - IP Address: `192.168.1.100`
   - Block Level: `Temporary`
   - Reason: `Test block for demonstration`
3. Click "Block IP"
4. Verify the IP appears in the blocked list
5. Check that the statistics update

### Test 3: View Block Details
1. Find the blocked IP in the list
2. Verify the following information is displayed:
   - IP address
   - Block level (Temporary/Extended/Permanent)
   - Reason for blocking
   - Blocked until timestamp
   - Time remaining
   - Blocked at timestamp

### Test 4: Extend Block Duration
1. Click the "Extend" button on a blocked IP
2. Enter additional hours (e.g., `2`)
3. Verify the block duration is extended
4. Check that the "Time remaining" updates

### Test 5: Unblock an IP
1. Click the "Unblock" button on a blocked IP
2. Confirm the action in the dialog
3. Verify the IP is removed from the blocked list
4. Check that the statistics update

### Test 6: Real-time Updates
1. Block an IP from another browser tab/window
2. Verify the blocked list updates automatically within 30 seconds
3. Check that statistics update in real-time

### Test 7: Different Block Levels
1. Block an IP with "Extended" level (6 hours)
2. Block another IP with "Permanent" level
3. Verify different visual indicators for each level
4. Check that permanent blocks show "Permanent" instead of time remaining

## 🔧 API Testing

### Test API Endpoints Directly
```bash
# Get all blocked IPs (requires authentication)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:5001/admin/ip-blocks

# Block an IP
curl -X POST -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"level": "temporary", "reason": "API test"}' \
     http://localhost:5001/admin/ip-blocks/10.0.0.100

# Unblock an IP
curl -X DELETE -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:5001/admin/ip-blocks/10.0.0.100

# Get block statistics
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:5001/admin/ip-blocks/statistics
```

## 📊 Expected Results

### Statistics Dashboard
- **Total Blocked**: Shows count of all currently blocked IPs
- **Temporary Blocks**: Shows count of temporary blocks
- **Permanent Blocks**: Shows count of permanent blocks
- **Premium IPs**: Shows count of premium IPs (if configured)

### Block Information Display
- **Temporary Blocks**: Orange border, shows time remaining
- **Extended Blocks**: Yellow border, shows time remaining
- **Permanent Blocks**: Red border, shows "Permanent" status

### Real-time Features
- Auto-refresh every 30 seconds
- Immediate updates when actions are performed
- Live countdown timers for temporary blocks

## 🐛 Troubleshooting

### Common Issues

1. **Server not starting**
   ```bash
   # Check if port is in use
   lsof -ti:5001
   # Kill existing processes
   kill -9 $(lsof -ti:5001)
   ```

2. **Authentication errors**
   - Ensure you're logged in with a valid Google account
   - Check that your email domain is authorized (`astraverify.com` or `cloudgofer.com`)

3. **IP not appearing in list**
   - Check browser console for JavaScript errors
   - Verify the API call was successful
   - Check server logs for errors

4. **Real-time updates not working**
   - Check browser console for JavaScript errors
   - Verify the auto-refresh interval is running
   - Check network connectivity

### Debug Mode
Enable debug logging by setting the environment variable:
```bash
export FLASK_DEBUG=1
python3 app_enhanced_dkim.py
```

## ✅ Success Criteria

The IP management system is working correctly if:

1. ✅ IP Management page loads without errors
2. ✅ You can block new IP addresses with different levels
3. ✅ Blocked IPs appear in the list with correct information
4. ✅ You can unblock IPs successfully
5. ✅ You can extend block durations
6. ✅ Statistics update in real-time
7. ✅ Auto-refresh works every 30 seconds
8. ✅ Different block levels show appropriate visual indicators
9. ✅ All actions require proper authentication
10. ✅ No JavaScript errors in browser console

## 📞 Support

If you encounter issues:
1. Check the server logs for error messages
2. Verify all dependencies are installed
3. Ensure the server is running on the correct port
4. Check browser console for JavaScript errors
5. Verify authentication is working properly

---

**Test Date**: 2025-08-22-02  
**Environment**: Local Development  
**Status**: Ready for Testing
