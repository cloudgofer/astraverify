// Configuration for the AstraVerify application
const config = {
  // Backend API URL - always use the production backend URL for GCP deployment
  API_BASE_URL: 'https://astraverify-backend-ml2mhibdvq-uc.a.run.app',
  
  // API endpoints
  ENDPOINTS: {
    CHECK_DOMAIN: '/api/check'
  },
  
  // Application settings
  APP_NAME: 'AstraVerify',
  APP_DESCRIPTION: 'Email Domain Verification Tool'
};

export default config;
