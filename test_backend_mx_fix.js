const https = require('https');

async function testBackendMXFix() {
    console.log('🔍 Testing Backend MX Issues Fix for kellpartners.com\n');
    
    try {
        // Test the backend API directly
        const apiUrl = 'https://astraverify-backend-ml2mhibdvq-uc.a.run.app/api/check?domain=kellpartners.com';
        
        console.log('📋 Testing Backend API URL:', apiUrl);
        
        // Make a request to the backend
        const response = await new Promise((resolve, reject) => {
            https.get(apiUrl, (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => resolve({ statusCode: res.statusCode, data }));
            }).on('error', reject);
        });
        
        if (response.statusCode === 200) {
            console.log('✅ Backend API is accessible');
            
            try {
                const result = JSON.parse(response.data);
                
                console.log('\n🔍 Backend Analysis Results:');
                console.log('- Domain:', result.domain);
                console.log('- Email Provider:', result.email_provider);
                console.log('- Security Score:', result.security_score?.score || 'N/A');
                
                // Check MX record status
                console.log('\n📧 MX Record Analysis:');
                console.log('- MX Enabled:', result.mx?.enabled);
                console.log('- MX Status:', result.mx?.status);
                console.log('- MX Description:', result.mx?.description);
                console.log('- MX Records Count:', result.mx?.records?.length || 0);
                
                // Check other components
                console.log('\n🔒 Other Components:');
                console.log('- SPF Enabled:', result.spf?.enabled);
                console.log('- DKIM Enabled:', result.dkim?.enabled);
                console.log('- DMARC Enabled:', result.dmarc?.enabled);
                
                // Check recommendations
                console.log('\n💡 Recommendations:');
                if (result.recommendations && result.recommendations.length > 0) {
                    result.recommendations.forEach((rec, index) => {
                        console.log(`${index + 1}. [${rec.type.toUpperCase()}] ${rec.title}`);
                        console.log(`   Description: ${rec.description}`);
                    });
                    
                    // Check for MX-specific recommendations
                    const mxRecommendations = result.recommendations.filter(rec => 
                        rec.title.includes('MX') || rec.description.includes('MX')
                    );
                    
                    if (mxRecommendations.length > 0) {
                        console.log('\n✅ SUCCESS: Backend is correctly generating MX record recommendations');
                        mxRecommendations.forEach(rec => {
                            console.log(`   - ${rec.title}: ${rec.description}`);
                        });
                    } else {
                        console.log('\n❌ ISSUE: No MX-specific recommendations found');
                    }
                } else {
                    console.log('❌ ISSUE: No recommendations generated');
                }
                
                // Verify the fix
                if (!result.mx?.enabled && result.recommendations?.some(rec => rec.title.includes('MX'))) {
                    console.log('\n✅ FIX VERIFIED: Backend correctly detects missing MX records and generates recommendations');
                } else if (!result.mx?.enabled) {
                    console.log('\n❌ ISSUE: MX records are missing but no MX recommendations generated');
                } else {
                    console.log('\nℹ️  INFO: MX records are present (unexpected for kellpartners.com)');
                }
                
            } catch (parseError) {
                console.error('❌ Error parsing JSON response:', parseError.message);
                console.log('Raw response:', response.data.substring(0, 500));
            }
            
        } else {
            console.log('❌ Backend returned status code:', response.statusCode);
            console.log('Response:', response.data);
        }
        
    } catch (error) {
        console.error('❌ Error testing backend MX fix:', error.message);
    }
}

testBackendMXFix();
