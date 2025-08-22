const https = require('https');

async function testMXIssuesFix() {
    console.log('🔍 Testing MX Issues Fix for kellpartners.com\n');
    
    try {
        // Test the staging frontend
        const frontendUrl = 'https://astraverify-frontend-staging-1098627686587.us-central1.run.app/?domain=kellpartners.com';
        
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
            
            // Check for various content patterns
            console.log('\n🔍 Content Analysis:');
            console.log('- Page length:', response.data.length, 'characters');
            
            // Check for React app loading
            const hasReactApp = response.data.includes('root') || response.data.includes('React');
            console.log('- React app detected:', hasReactApp);
            
            // Check for domain input field
            const hasDomainInput = response.data.includes('domain-input') || response.data.includes('example.com');
            console.log('- Domain input field found:', hasDomainInput);
            
            // Check for loading states
            const hasLoading = response.data.includes('loading') || response.data.includes('Analyzing');
            console.log('- Loading states found:', hasLoading);
            
            // Check for MX-related content
            const hasMXIssues = response.data.includes('No MX Records Found') || 
                               response.data.includes('MX records found - email delivery will fail');
            console.log('- MX issues in Issues Found section:', hasMXIssues);
            
            const hasMXRecommendations = response.data.includes('Add MX Records') ||
                                       response.data.includes('MX records are essential');
            console.log('- MX recommendations found:', hasMXRecommendations);
            
            // Check for issues section
            const hasIssuesSection = response.data.includes('Issues Found') || response.data.includes('issues-section');
            console.log('- Issues Found section present:', hasIssuesSection);
            
            // Check for recommendations section
            const hasRecommendationsSection = response.data.includes('Recommendations') || response.data.includes('recommendations-section');
            console.log('- Recommendations section present:', hasRecommendationsSection);
            
            // Check for any analysis results
            const hasAnalysisResults = response.data.includes('security_score') || response.data.includes('mx') || response.data.includes('spf');
            console.log('- Analysis results present:', hasAnalysisResults);
            
            if (hasMXIssues) {
                console.log('\n✅ SUCCESS: MX record issue is now properly displayed in Issues Found section');
            } else if (hasMXRecommendations) {
                console.log('\nℹ️  INFO: MX record issue appears in recommendations section (this is expected)');
            } else {
                console.log('\n❌ ISSUE: MX record issue not found anywhere in the response');
                console.log('🔍 This suggests the domain analysis is not being performed automatically');
            }
            
        } else {
            console.log('❌ Frontend returned status code:', response.statusCode);
        }
        
    } catch (error) {
        console.error('❌ Error testing MX issues fix:', error.message);
    }
}

testMXIssuesFix();
