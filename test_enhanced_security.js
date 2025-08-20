// Enhanced Security Validation Test
// Tests the improved security features after deployment

const STAGING_API_URL = 'https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app';
const LOCAL_API_URL = 'http://localhost:5000';

async function testEnhancedSecurity() {
    console.log('🔒 Testing Enhanced Security Features\n');
    
    const results = {
        securityHeaders: {},
        rateLimiting: {},
        inputValidation: {},
        adminEndpoints: {},
        summary: { passed: 0, failed: 0, total: 0 }
    };
    
    // Test 1: Security Headers
    console.log('1. Testing Security Headers...');
    try {
        const response = await fetch(`${STAGING_API_URL}/api/health`);
        const headers = response.headers;
        
        const securityHeaders = {
            'X-Content-Type-Options': headers.get('X-Content-Type-Options'),
            'X-Frame-Options': headers.get('X-Frame-Options'),
            'X-XSS-Protection': headers.get('X-XSS-Protection'),
            'Strict-Transport-Security': headers.get('Strict-Transport-Security'),
            'Content-Security-Policy': headers.get('Content-Security-Policy'),
            'Referrer-Policy': headers.get('Referrer-Policy'),
            'Permissions-Policy': headers.get('Permissions-Policy')
        };
        
        const presentHeaders = Object.entries(securityHeaders)
            .filter(([key, value]) => value !== null)
            .map(([key]) => key);
        
        if (presentHeaders.length >= 5) {
            console.log(`   ✅ Security headers present: ${presentHeaders.join(', ')}`);
            results.securityHeaders.staging = 'passed';
            results.summary.passed++;
        } else {
            console.log(`   ❌ Missing security headers. Present: ${presentHeaders.join(', ')}`);
            results.securityHeaders.staging = 'failed';
            results.summary.failed++;
        }
        results.summary.total++;
    } catch (error) {
        console.log(`   ❌ Error testing security headers: ${error.message}`);
        results.securityHeaders.staging = 'failed';
        results.summary.failed++;
        results.summary.total++;
    }
    
    // Test 2: Rate Limiting Headers
    console.log('\n2. Testing Rate Limiting Headers...');
    try {
        const response = await fetch(`${STAGING_API_URL}/api/check?domain=gmail.com`);
        const rateLimitHeaders = {
            'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
            'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
            'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset')
        };
        
        const hasRateLimitHeaders = Object.values(rateLimitHeaders).some(header => header !== null);
        
        if (hasRateLimitHeaders) {
            console.log(`   ✅ Rate limiting headers present: ${Object.keys(rateLimitHeaders).filter(key => rateLimitHeaders[key] !== null).join(', ')}`);
            results.rateLimiting.headers = 'passed';
            results.summary.passed++;
        } else {
            console.log(`   ❌ No rate limiting headers detected`);
            results.rateLimiting.headers = 'failed';
            results.summary.failed++;
        }
        results.summary.total++;
    } catch (error) {
        console.log(`   ❌ Error testing rate limiting: ${error.message}`);
        results.rateLimiting.headers = 'failed';
        results.summary.failed++;
        results.summary.total++;
    }
    
    // Test 3: Input Validation
    console.log('\n3. Testing Input Validation...');
    
    // Test IP address rejection
    try {
        const response = await fetch(`${STAGING_API_URL}/api/check?domain=192.168.1.1`);
        if (response.status === 400) {
            const data = await response.json();
            if (data.error && data.error.includes('IP addresses are not valid domains')) {
                console.log('   ✅ IP addresses correctly rejected');
                results.inputValidation.ipRejection = 'passed';
                results.summary.passed++;
            } else {
                console.log('   ⚠️ IP addresses rejected but with unexpected error message');
                results.inputValidation.ipRejection = 'warning';
                results.summary.passed++;
            }
        } else {
            console.log(`   ❌ IP addresses not rejected, got status: ${response.status}`);
            results.inputValidation.ipRejection = 'failed';
            results.summary.failed++;
        }
        results.summary.total++;
    } catch (error) {
        console.log(`   ❌ Error testing IP rejection: ${error.message}`);
        results.inputValidation.ipRejection = 'failed';
        results.summary.failed++;
        results.summary.total++;
    }
    
    // Test XSS rejection
    try {
        const response = await fetch(`${STAGING_API_URL}/api/check?domain=%3Cscript%3Ealert%28%27xss%27%29%3C/script%3E`);
        if (response.status === 400) {
            const data = await response.json();
            if (data.error && data.error.includes('malicious pattern')) {
                console.log('   ✅ XSS attempts correctly rejected');
                results.inputValidation.xssRejection = 'passed';
                results.summary.passed++;
            } else {
                console.log('   ⚠️ XSS attempts rejected but with unexpected error message');
                results.inputValidation.xssRejection = 'warning';
                results.summary.passed++;
            }
        } else {
            console.log(`   ❌ XSS attempts not rejected, got status: ${response.status}`);
            results.inputValidation.xssRejection = 'failed';
            results.summary.failed++;
        }
        results.summary.total++;
    } catch (error) {
        console.log(`   ❌ Error testing XSS rejection: ${error.message}`);
        results.inputValidation.xssRejection = 'failed';
        results.summary.failed++;
        results.summary.total++;
    }
    
    // Test 4: Admin Endpoints
    console.log('\n4. Testing Admin Endpoints...');
    try {
        const response = await fetch(`${STAGING_API_URL}/api/admin/security-dashboard`, {
            headers: { 'X-Admin-API-Key': 'astraverify-admin-2024' }
        });
        
        if (response.status === 200) {
            const data = await response.json();
            if (data.environment === 'staging') {
                console.log('   ✅ Admin security dashboard accessible');
                results.adminEndpoints.dashboard = 'passed';
                results.summary.passed++;
            } else {
                console.log('   ⚠️ Admin dashboard accessible but environment mismatch');
                results.adminEndpoints.dashboard = 'warning';
                results.summary.passed++;
            }
        } else {
            console.log(`   ❌ Admin dashboard not accessible, got status: ${response.status}`);
            results.adminEndpoints.dashboard = 'failed';
            results.summary.failed++;
        }
        results.summary.total++;
    } catch (error) {
        console.log(`   ❌ Error testing admin endpoints: ${error.message}`);
        results.adminEndpoints.dashboard = 'failed';
        results.summary.failed++;
        results.summary.total++;
    }
    
    // Test 5: Valid Domain Processing
    console.log('\n5. Testing Valid Domain Processing...');
    try {
        const response = await fetch(`${STAGING_API_URL}/api/check?domain=gmail.com`);
        if (response.status === 200) {
            const data = await response.json();
            if (data.domain === 'gmail.com' && data.security_score) {
                console.log('   ✅ Valid domains processed correctly');
                results.inputValidation.validDomain = 'passed';
                results.summary.passed++;
            } else {
                console.log('   ⚠️ Valid domain processed but response format unexpected');
                results.inputValidation.validDomain = 'warning';
                results.summary.passed++;
            }
        } else {
            console.log(`   ❌ Valid domain not processed, got status: ${response.status}`);
            results.inputValidation.validDomain = 'failed';
            results.summary.failed++;
        }
        results.summary.total++;
    } catch (error) {
        console.log(`   ❌ Error testing valid domain: ${error.message}`);
        results.inputValidation.validDomain = 'failed';
        results.summary.failed++;
        results.summary.total++;
    }
    
    // Generate summary
    console.log('\n📊 ENHANCED SECURITY TEST SUMMARY');
    console.log('==================================');
    console.log(`Total Tests: ${results.summary.total}`);
    console.log(`Passed: ${results.summary.passed}`);
    console.log(`Failed: ${results.summary.failed}`);
    console.log(`Success Rate: ${((results.summary.passed / results.summary.total) * 100).toFixed(1)}%`);
    
    console.log('\nDetailed Results:');
    console.log('Security Headers:', results.securityHeaders.staging || 'not tested');
    console.log('Rate Limiting Headers:', results.rateLimiting.headers || 'not tested');
    console.log('IP Rejection:', results.inputValidation.ipRejection || 'not tested');
    console.log('XSS Rejection:', results.inputValidation.xssRejection || 'not tested');
    console.log('Admin Dashboard:', results.adminEndpoints.dashboard || 'not tested');
    console.log('Valid Domain Processing:', results.inputValidation.validDomain || 'not tested');
    
    if (results.summary.failed === 0) {
        console.log('\n🎉 All enhanced security features are working correctly!');
        process.exit(0);
    } else {
        console.log('\n⚠️ Some enhanced security features need attention.');
        process.exit(1);
    }
}

// Run the test
testEnhancedSecurity().catch(console.error);
