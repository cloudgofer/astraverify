const config = {
  API_BASE_URL: 'http://localhost:8080',
  ENDPOINTS: {
    CHECK_DOMAIN: '/api/check'
  }
};

async function testFrontendAPI() {
  console.log('🧪 Testing Frontend API Connectivity...');
  
  const testDomain = 'example.com';
  const progressiveUrl = `${config.API_BASE_URL}${config.ENDPOINTS.CHECK_DOMAIN}?domain=${encodeURIComponent(testDomain)}&progressive=true`;
  
  console.log('📡 Testing URL:', progressiveUrl);
  
  try {
    console.log('🔄 Making fetch request...');
    const response = await fetch(progressiveUrl);
    
    console.log('📊 Response status:', response.status);
    console.log('📊 Response ok:', response.ok);
    console.log('📊 Response headers:', Object.fromEntries(response.headers.entries()));
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Response error:', response.status, errorText);
      throw new Error(`HTTP error! status: ${response.status} - ${errorText.substring(0, 100)}`);
    }
    
    const contentType = response.headers.get('content-type');
    console.log('📊 Content-Type:', contentType);
    
    if (!contentType || !contentType.includes('application/json')) {
      const text = await response.text();
      console.error('❌ Non-JSON response:', text);
      throw new Error(`Expected JSON but got ${contentType}. Response: ${text.substring(0, 200)}`);
    }
    
    const data = await response.json();
    console.log('✅ Success! Received data:', JSON.stringify(data, null, 2).substring(0, 500) + '...');
    
  } catch (error) {
    console.error('❌ Error during fetch:', error);
    console.error('❌ Error name:', error.name);
    console.error('❌ Error message:', error.message);
    console.error('❌ Error stack:', error.stack);
    
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      console.error('🔍 This appears to be a fetch API issue');
    }
  }
}

// Test if we're in a browser environment
if (typeof window !== 'undefined') {
  console.log('🌐 Running in browser environment');
  window.testFrontendAPI = testFrontendAPI;
} else {
  console.log('🖥️ Running in Node.js environment');
  // For Node.js, we need to use a different approach since fetch might not be available
  const https = require('https');
  const http = require('http');
  
  function nodeFetch(url) {
    return new Promise((resolve, reject) => {
      const client = url.startsWith('https:') ? https : http;
      const req = client.get(url, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          resolve({
            ok: res.statusCode >= 200 && res.statusCode < 300,
            status: res.statusCode,
            headers: res.headers,
            text: () => Promise.resolve(data),
            json: () => Promise.resolve(JSON.parse(data))
          });
        });
      });
      req.on('error', reject);
      req.end();
    });
  }
  
  // Override fetch for Node.js
  global.fetch = nodeFetch;
  
  testFrontendAPI();
}
