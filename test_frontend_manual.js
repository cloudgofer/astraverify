const https = require('https');

async function testFrontendManual() {
    console.log('🔍 Testing Frontend Manual Domain Analysis\n');
    
    try {
        // Test the frontend without domain parameter first
        const frontendUrl = 'https://astraverify-frontend-staging-1098627686587.us-central1.run.app/';
        
        console.log('📋 Testing Frontend URL (no domain):', frontendUrl);
        
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
            
            if (hasDomainInput) {
                console.log('✅ Frontend appears to be working correctly');
                console.log('ℹ️  The issue might be with automatic domain loading from URL parameters');
            } else {
                console.log('❌ Frontend is not loading properly');
            }
        } else {
            console.log('❌ Frontend returned status code:', response.statusCode);
        }
        
    } catch (error) {
        console.error('❌ Error testing frontend:', error.message);
    }
}

testFrontendManual();
