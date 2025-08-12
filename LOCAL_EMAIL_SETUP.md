# Local Email Configuration Guide

## Overview
The AstraVerify application now supports email sending in the local development environment using the same credentials as production.

## Email Configuration

### SMTP Settings
- **Server**: `smtp.dreamhost.com`
- **Port**: `587`
- **Username**: `hi@astraverify.com`
- **Sender**: `AstraVerify <hi@astraverify.com>`
- **Authentication**: TLS

### Environment Variable
The email password is configured via environment variable:
```bash
export EMAIL_PASSWORD="your-email-password"
```

## Testing Email Functionality

### 1. Test Email Configuration
```bash
curl -s "http://localhost:8080/api/test-email" | python3 -m json.tool
```

### 2. Test Email Report Sending
```bash
# First, get analysis results
curl -s "http://localhost:8080/api/check?domain=cloudgofer.com" > analysis.json

# Then send email report
curl -X POST "http://localhost:8080/api/email-report" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "domain": "cloudgofer.com",
    "analysis_result": '"$(cat analysis.json)"',
    "opt_in_marketing": false
  }'
```

## Local Development Setup

### 1. Start Backend
```bash
cd backend
source venv/bin/activate
python app.py
```

### 2. Start Frontend
```bash
cd frontend
npm start
```

### 3. Access Application
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8080

## Email Features Available Locally

1. **Email Report Modal**: Users can request email reports from the UI
2. **SMTP Authentication**: Uses the same DreamHost SMTP as production
3. **Formatted Reports**: HTML emails with security analysis details
4. **Error Handling**: Proper error messages for failed email attempts

## Troubleshooting

### Email Password Not Set
If you see "Email password not configured" error:
```bash
export EMAIL_PASSWORD="your-actual-password"
```

### SMTP Authentication Issues
- Verify the password is correct
- Check that `smtp.dreamhost.com` is accessible
- Ensure TLS is enabled on port 587

### Local vs Production
- **Local**: Uses environment variable for password
- **Production**: Uses GCP Secret Manager or environment variable
- **Staging**: Uses GCP Secret Manager or environment variable

## Security Notes
- Email password should be kept secure
- Never commit passwords to version control
- Use environment variables for local development
- Production uses GCP Secret Manager for enhanced security
