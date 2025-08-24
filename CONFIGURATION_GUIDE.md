# Configuration Guide

## Overview

This document explains the environment-specific configuration system for AstraVerify.

## Configuration Files

### Environment-Specific Configs

| File | Environment | Backend URL | App Name |
|------|-------------|-------------|----------|
| `config.local.js` | Local Development | `http://localhost:8080` | `AstraVerify (Local)` |
| `config.staging.js` | Staging | `https://astraverify-backend-1098627686587.us-central1.run.app` | `AstraVerify (Staging)` |
| `config.production.js` | Production | `https://astraverify-backend-ml2mhibdvq-uc.a.run.app` | `AstraVerify` |
| `config.js` | Default/Fallback | `http://localhost:8080` | `AstraVerify (Default)` |

### Configuration Structure

Each config file follows this structure:

```javascript
const config = {
  // Backend API URL
  API_BASE_URL: 'https://backend-url.com',
  
  // API endpoints
  ENDPOINTS: {
    CHECK_DOMAIN: '/api/check'
  },
  
  // Application settings
  APP_NAME: 'AstraVerify (Environment)',
  APP_DESCRIPTION: 'Email Domain Verification Tool - Environment'
};

export default config;
```

## Dynamic Configuration Loading

The application automatically loads the correct configuration based on environment variables:

### Environment Detection Logic

```javascript
// In App.js
let config;
try {
  if (process.env.NODE_ENV === 'production') {
    config = require('./config.production').default;
  } else if (process.env.NODE_ENV === 'staging') {
    config = require('./config.staging').default;
  } else if (process.env.REACT_APP_ENV === 'local') {
    config = require('./config.local').default;
  } else {
    config = require('./config').default;
  }
} catch (error) {
  config = require('./config').default;
}
```

## Build Scripts

### Environment-Specific Build

Use the `build-env.sh` script to build for specific environments:

```bash
# Build for local development
./frontend/build-env.sh local

# Build for staging
./frontend/build-env.sh staging

# Build for production
./frontend/build-env.sh production
```

### Environment Variables Set

| Environment | NODE_ENV | REACT_APP_ENV |
|-------------|----------|---------------|
| local | `development` | `local` |
| staging | `staging` | `staging` |
| production | `production` | `production` |

## Deployment Scripts

### Staging Deployment

```bash
./deploy/deploy_staging.sh
```

- Uses `build-env.sh staging`
- Deploys to staging Cloud Run services
- Uses `config.staging.js`

### Production Deployment

```bash
./deploy/deploy_frontend_cloudrun.sh
```

- Uses `build-env.sh production`
- Deploys to production Cloud Run services
- Uses `config.production.js`

### Local Development

```bash
./run_local.sh
```

- Uses `build-env.sh local`
- Starts local development server
- Uses `config.local.js`

## Best Practices

### 1. Environment Isolation

- Each environment has its own configuration file
- No hardcoded URLs in the application code
- Environment variables control which config is loaded

### 2. Configuration Management

- Keep all environment-specific settings in config files
- Use descriptive app names to identify environments
- Maintain consistent structure across all config files

### 3. Deployment Process

- Always use environment-specific build scripts
- Verify configuration before deployment
- Test each environment independently

### 4. Development Workflow

- Use `run_local.sh` for local development
- Test with staging before production deployment
- Use environment-specific URLs for testing

## Troubleshooting

### Common Issues

1. **Wrong Backend URL**: Check that the correct config file is being loaded
2. **Build Failures**: Ensure environment variables are set correctly
3. **Deployment Issues**: Verify the build script is using the right environment

### Debugging Configuration

Add this to your component to debug which config is loaded:

```javascript
console.log('Current config:', config);
console.log('NODE_ENV:', process.env.NODE_ENV);
console.log('REACT_APP_ENV:', process.env.REACT_APP_ENV);
```

## Migration from Old System

The old system used hardcoded imports like:
```javascript
import config from './config.local';
```

The new system uses dynamic loading based on environment variables, making it more flexible and maintainable.
