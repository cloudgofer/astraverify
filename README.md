# AstraVerify - Email Domain Verification Tool

AstraVerify is a web application that checks email domain configurations including MX, SPF, DKIM, and DMARC records.

## Features

- **MX Record Check**: Verifies mail exchange records
- **SPF Record Check**: Validates Sender Policy Framework records
- **DMARC Record Check**: Checks Domain-based Message Authentication, Reporting & Conformance
- **Modern UI**: Clean, responsive interface built with React
- **RESTful API**: Flask backend with CORS support
- **Cloud Ready**: Deployable to Google Cloud Platform

## Quick Start

### Prerequisites

- Node.js (v14 or higher)
- Python 3.7+
- npm or yarn

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd astraverify
   ```

2. **Run the setup script**
   ```bash
   ./setup.sh
   ```

3. **Start local development**
   ```bash
   ./run_local.sh
   ```

   This will start both frontend and backend services:
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8080

### Manual Local Setup

If you prefer to set up manually:

#### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## Deployment

### Google Cloud Platform Deployment

1. **Install Google Cloud SDK**
   ```bash
   # macOS
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   
   # Or download from: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate and set project**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Deploy to GCP**
   ```bash
   ./deploy/deploy_to_gcp.sh YOUR_PROJECT_ID
   ```

### Deployment Scripts

- `./deploy/deploy_to_gcp.sh` - Full deployment to GCP Cloud Run
- `./deploy/fix_frontend.sh` - Fix frontend and backend setup issues
- `./deploy/deploy_frontend_cloudrun.sh` - Deploy only frontend to Cloud Run

## API Endpoints

### Health Check
```
GET /api/health
```
Returns service health status.

### Domain Check
```
GET /api/check?domain=example.com
```
Returns domain verification results:
```json
{
  "domain": "example.com",
  "MX": true,
  "SPF": true,
  "DKIM": false,
  "DMARC": true,
  "status": "success"
}
```

## Project Structure

```
astraverify/
├── backend/
│   ├── app.py              # Flask backend API
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Container configuration
├── frontend/
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   ├── App.css        # Styles
│   │   └── config.js      # Configuration
│   ├── package.json       # Node.js dependencies
│   └── Dockerfile         # Container configuration
├── deploy/
│   ├── deploy_to_gcp.sh   # Main deployment script
│   ├── fix_frontend.sh    # Fix deployment issues
│   └── deploy_frontend_cloudrun.sh
├── setup.sh               # Initial setup script
├── run_local.sh           # Local development script
└── README.md
```

## Troubleshooting

### Common Issues

1. **gcloud not found**
   ```bash
   # Install Google Cloud SDK
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   ```

2. **Node.js/npm not found**
   ```bash
   # Install Node.js from https://nodejs.org/
   ```

3. **Python virtual environment issues**
   ```bash
   cd backend
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Frontend build errors**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

### Fix Deployment Issues

Run the fix script to resolve common deployment problems:
```bash
./deploy/fix_frontend.sh
```

## Development

### Adding New Features

1. **Backend**: Add new routes in `backend/app.py`
2. **Frontend**: Create new components in `frontend/src/`
3. **Testing**: Add tests for both frontend and backend

### Code Style

- Frontend: ESLint with React recommended rules
- Backend: Follow PEP 8 Python style guide
- Use meaningful commit messages

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the deployment logs
3. Create an issue in the repository