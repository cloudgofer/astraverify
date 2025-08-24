// Dynamic configuration loader
const getEnvironmentConfig = () => {
  // Check if we're in a browser environment
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    const href = window.location.href;
    
    // Production environment
    if (hostname === 'astraverify.com' || hostname === 'www.astraverify.com' || 
        href.includes('astraverify-frontend-ml2mhibdvq-uc.a.run.app')) {
      console.log('Loading PRODUCTION configuration');
      return require('./config.production').default;
    }
    
    // Staging environment
    if (hostname.includes('staging') || href.includes('staging') || 
        href.includes('astraverify-backend-staging')) {
      console.log('Loading STAGING configuration');
      return require('./config.staging').default;
    }
    
    // Local development environment
    if (hostname === 'localhost' || hostname === '127.0.0.1' || 
        hostname.includes('local') || process.env.NODE_ENV === 'development') {
      console.log('Loading LOCAL configuration');
      return require('./config.local').default;
    }
  }
  
  // Fallback to local config for development
  console.log('Loading LOCAL configuration (fallback)');
  return require('./config.local').default;
};

const config = getEnvironmentConfig();

export default config;
