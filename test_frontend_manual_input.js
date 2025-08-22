const https = require('https');

async function testFrontendManualInput() {
    console.log('🔍 Testing Frontend Manual Domain Input\n');
    
    try {
        // Test the frontend with a simple domain to see if it loads properly
        const frontendUrl = 'https://astraverify-frontend-staging-1098627686587.us-central1.run.app/';
        
        console.log('📋 Testing Frontend URL:', frontendUrl);
        
        // Make a request to the frontend
        const response = await new Promise((resolve, reject) => {
            https.get(frontendUrl, (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => resolve({ statusCode: res.statusCode, data }));
            }).on('error', reject);
        });
        
        if (response.statusCode === 200) {
            console.log('✅ Frontend is accessible');
            console.log('- Page length:', response.data.length, 'characters');
            
            // Check for React app content
            const hasReactApp = response.data.includes('root') || response.data.includes('React');
            console.log('- React app detected:', hasReactApp);
            
            // Check for domain input field
            const hasDomainInput = response.data.includes('domain-input') || response.data.includes('example.com');
            console.log('- Domain input field found:', hasDomainInput);
            
            // Check for JavaScript files
            const hasJavaScript = response.data.includes('main.ea981fc2.js');
            console.log('- JavaScript files referenced:', hasJavaScript);
            
            // Check for CSS files
            const hasCSS = response.data.includes('main.e5a3edc4.css');
            console.log('- CSS files referenced:', hasCSS);
            
            if (hasDomainInput && hasJavaScript && hasCSS) {
                console.log('✅ Frontend appears to be properly configured');
                console.log('ℹ️  The issue is likely with the automatic domain loading from URL parameters');
                console.log('🔍 This could be due to:');
                console.log('   - JavaScript execution timing issues');
                console.log('   - React useEffect dependency problems');
                console.log('   - URL parameter parsing issues');
                console.log('   - State management problems');
            } else {
                console.log('❌ Frontend is missing essential components');
            }
        } else {
            console.log('❌ Frontend returned status code:', response.statusCode);
        }
        
    } catch (error) {
        console.error('❌ Error testing frontend:', error.message);
    }
}

testFrontendManualInput();
