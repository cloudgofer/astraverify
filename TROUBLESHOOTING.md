# AstraVerify Troubleshooting Guide

## Common Issues and Solutions

### 1. "Error analyzing domain: Failed to fetch"

**Cause**: The backend server is not running or not accessible.

**Solutions**:

#### Option A: Use the Startup Script (Recommended)
```bash
./start_app.sh
```

#### Option B: Start Servers Manually

1. **Start Backend**:
   ```bash
   cd backend
   python app.py
   ```

2. **Start Frontend** (in a new terminal):
   ```bash
   cd frontend
   npm start
   ```

#### Option C: Check if Backend is Running
```bash
curl http://localhost:8080/api/check?domain=example.com
```

### 2. CORS Errors

**Cause**: Cross-origin requests are blocked.

**Solution**: The backend already has CORS enabled. If you're still getting CORS errors:

1. Check that the backend is running on `http://localhost:8080`
2. Check that the frontend is running on `http://localhost:3000`
3. Ensure you're accessing the frontend via `http://localhost:3000` (not `file://`)

### 3. Port Already in Use

**Solution**: Kill processes using the ports:

```bash
# Kill process on port 8080 (backend)
lsof -ti:8080 | xargs kill -9

# Kill process on port 3000 (frontend)
lsof -ti:3000 | xargs kill -9
```

### 4. Python Dependencies Missing

**Solution**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Node.js Dependencies Missing

**Solution**:
```bash
cd frontend
npm install
```

### 6. Network Connectivity Issues

**Diagnosis**:
```bash
# Test backend connectivity
curl -v http://localhost:8080/api/check?domain=example.com

# Test frontend connectivity
curl -v http://localhost:3000
```

### 7. Browser Console Errors

**To Debug**:
1. Open browser developer tools (F12)
2. Go to Console tab
3. Try the domain analysis
4. Look for error messages

### 8. Environment Configuration Issues

**Check Configuration**:
- Frontend config: `frontend/src/config.js`
- Backend config: `backend/app.py`

**Common Configurations**:
- **Local Development**: `API_BASE_URL: 'http://localhost:8080'`
- **Production**: `API_BASE_URL: 'https://astraverify-backend-ml2mhibdvq-uc.a.run.app'`
- **Staging**: `API_BASE_URL: 'https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app'`

### 9. Firewall or Antivirus Issues

**Solution**:
- Temporarily disable firewall/antivirus
- Add localhost to allowed hosts
- Check if any security software is blocking local connections

### 10. DNS Resolution Issues

**Solution**:
```bash
# Test DNS resolution
nslookup localhost
ping localhost
```

## Quick Diagnostic Commands

```bash
# Check if ports are in use
lsof -i :8080
lsof -i :3000

# Check if processes are running
ps aux | grep python
ps aux | grep node

# Test API endpoints
curl http://localhost:8080/api/check?domain=example.com
curl http://localhost:3000

# Check logs
tail -f backend/app.log  # if logging is enabled
```

## Environment Setup Checklist

- [ ] Python 3.7+ installed
- [ ] Node.js 14+ installed
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Backend server running on port 8080
- [ ] Frontend server running on port 3000
- [ ] No firewall blocking localhost connections
- [ ] Browser supports fetch API

## Getting Help

If you're still experiencing issues:

1. Check the browser console for detailed error messages
2. Run the diagnostic commands above
3. Check the backend logs for any Python errors
4. Ensure both servers are running simultaneously
5. Try accessing the API directly with curl to isolate the issue

## Common Error Messages and Solutions

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| "Failed to fetch" | Backend not running | Start backend server |
| "CORS error" | Cross-origin blocked | Check server URLs |
| "Port already in use" | Another process using port | Kill existing process |
| "Module not found" | Dependencies missing | Run npm install or pip install |
| "Connection refused" | Server not started | Start the appropriate server |
