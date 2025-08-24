const config = {
  // Backend API URL - DEFAULT environment (fallback)
  API_BASE_URL: 'http://localhost:8080',

  // API endpoints
  ENDPOINTS: {
    CHECK_DOMAIN: '/api/check'
  },

  // Application settings
  APP_NAME: 'AstraVerify (Default)',
  APP_DESCRIPTION: 'Email Domain Verification Tool - Default Environment'
};

export default config;
// Default config - should be overridden by environment-specific configs
