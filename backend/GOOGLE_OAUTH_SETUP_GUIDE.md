# Google OAuth Setup Guide for AstraVerify Enhanced DKIM

## 🔐 **Complete Setup Instructions**

### **Step 1: Google Cloud Console Setup**

#### **1.1 Create/Select Project**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing project:
   - **Project Name**: `astraverify-admin`
   - **Project ID**: `astraverify-admin-20250821` (or similar)

#### **1.2 Enable Required APIs**
1. Go to **APIs & Services** > **Library**
2. Search for and enable these APIs:
   - **Google+ API** (for OAuth)
   - **Gmail API** (for future email analysis)

#### **1.3 Create OAuth 2.0 Credentials**
1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth 2.0 Client IDs**
3. Configure the OAuth consent screen:
   - **User Type**: External
   - **App name**: AstraVerify Admin
   - **User support email**: your-email@astraverify.com
   - **Developer contact information**: your-email@astraverify.com
   - **Scopes**: Add `https://www.googleapis.com/auth/userinfo.email` and `https://www.googleapis.com/auth/userinfo.profile`

4. Create OAuth 2.0 Client ID:
   - **Application type**: Web application
   - **Name**: AstraVerify Admin
   - **Authorized JavaScript origins**:
     ```
     http://localhost:5001
     http://127.0.0.1:5001
     ```
   - **Authorized redirect URIs**:
     ```
     http://localhost:5001/admin/auth/callback
     http://127.0.0.1:5001/admin/auth/callback
     ```

5. **Copy the credentials**:
   - **Client ID**: `123456789-abcdefghijklmnop.apps.googleusercontent.com`
   - **Client Secret**: `GOCSPX-abcdefghijklmnopqrstuvwxyz`

### **Step 2: Update Environment Configuration**

#### **2.1 Edit the .env file**
```bash
nano .env
```

#### **2.2 Replace the placeholder values**
```env
# AstraVerify Enhanced DKIM - Google OAuth Configuration

# Environment
ENVIRONMENT=local

# Google OAuth 2.0 Configuration
GOOGLE_OAUTH_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-google-oauth-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:5001/admin/auth/callback

# JWT Configuration
JWT_SECRET_KEY=astraverify-local-jwt-secret-key-2024-change-in-production

# Email Configuration
EMAIL_PASSWORD=your-email-password

# Firestore Configuration (optional for local testing)
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/service-account-key.json
```

### **Step 3: Test the Configuration**

#### **3.1 Run the OAuth test**
```bash
python test_oauth_config.py
```

Expected output:
```
🔐 Testing Google OAuth Configuration
========================================
✅ GOOGLE_OAUTH_CLIENT_ID: **********...usercontent.com
✅ GOOGLE_OAUTH_CLIENT_SECRET: **********...xyz
✅ GOOGLE_OAUTH_REDIRECT_URI: **********...callback
✅ JWT_SECRET_KEY: **********...production

🔍 Testing OAuth endpoints...
✅ Health endpoint: Working
✅ Admin auth endpoint: Working
✅ Admin home endpoint: Working

🎉 OAuth configuration test completed successfully!
```

#### **3.2 Test the OAuth flow**
```bash
curl "http://localhost:5001/admin/auth/google"
```

Expected response:
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&scope=...&response_type=code&access_type=offline"
}
```

### **Step 4: Start the Enhanced System**

#### **4.1 Start the server**
```bash
./run_enhanced_local.sh
```

#### **4.2 Access the admin interface**
1. Open your browser
2. Go to: `http://localhost:5001/admin/ui/login`
3. Click **"Sign in with Google"**
4. Complete the OAuth flow
5. Access the admin dashboard

### **Step 5: Admin Access Control**

#### **5.1 Authorized Domains**
The system is configured to allow access only from:
- `astraverify.com`
- `cloudgofer.com`

#### **5.2 Admin Roles**
- **Super Admin**: Full system access
- **Domain Admin**: Domain and selector management
- **Limited Admin**: Selector management only

#### **5.3 Test with your email**
Make sure your Google account email is from an authorized domain:
- `your-name@astraverify.com`
- `your-name@cloudgofer.com`

### **Step 6: Troubleshooting**

#### **6.1 Common Issues**

**Issue**: "Invalid redirect URI"
- **Solution**: Make sure the redirect URI in Google Cloud Console matches exactly: `http://localhost:5001/admin/auth/callback`

**Issue**: "Access denied"
- **Solution**: Ensure your email domain is in the authorized domains list

**Issue**: "OAuth consent screen not configured"
- **Solution**: Complete the OAuth consent screen configuration in Google Cloud Console

**Issue**: "Invalid client ID"
- **Solution**: Double-check the Client ID and Client Secret in the .env file

#### **6.2 Debug Mode**
Enable debug logging:
```bash
export FLASK_DEBUG=1
python app_enhanced_dkim.py
```

#### **6.3 Check OAuth Flow**
```bash
# Test auth URL generation
curl "http://localhost:5001/admin/auth/google"

# Test callback (will fail with invalid code, but should return 400)
curl "http://localhost:5001/admin/auth/callback?code=invalid_code"
```

### **Step 7: Production Considerations**

#### **7.1 Security**
- Change `JWT_SECRET_KEY` to a strong, random value
- Use HTTPS in production
- Restrict authorized domains to production domains only

#### **7.2 Environment Variables**
For production, set these environment variables:
```bash
export ENVIRONMENT=production
export GOOGLE_OAUTH_CLIENT_ID=your-production-client-id
export GOOGLE_OAUTH_CLIENT_SECRET=your-production-client-secret
export JWT_SECRET_KEY=your-production-jwt-secret
```

#### **7.3 Firestore Setup**
For full functionality, set up Firestore:
1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Set `GOOGLE_APPLICATION_CREDENTIALS` to the path of the key file

## 🎯 **Quick Start Checklist**

- [ ] Created Google Cloud project
- [ ] Enabled Google+ API
- [ ] Created OAuth 2.0 credentials
- [ ] Added authorized redirect URIs
- [ ] Updated .env file with real credentials
- [ ] Tested OAuth configuration
- [ ] Started enhanced system
- [ ] Accessed admin interface
- [ ] Completed OAuth flow
- [ ] Verified admin access

## 🔗 **Useful Links**

- **Google Cloud Console**: https://console.cloud.google.com/
- **OAuth 2.0 Documentation**: https://developers.google.com/identity/protocols/oauth2
- **Admin Interface**: http://localhost:5001/admin/ui/login
- **Health Check**: http://localhost:5001/api/health

## 📞 **Support**

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all environment variables are set correctly
3. Ensure the server is running on port 5001
4. Check browser console for JavaScript errors
5. Review server logs for detailed error messages

---

**Status**: ✅ Ready for OAuth Configuration  
**Next Step**: Follow the Google Cloud Console setup instructions above
