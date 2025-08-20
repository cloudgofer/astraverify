// Quick STAGE Environment Validation
// Provides actionable recommendations for security improvements

const STAGING_API_URL = 'https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app';

async function quickValidation() {
    console.log('🔍 Quick STAGE Environment Validation\n');
    
    const results = {
        security: {},
        performance: {},
        recommendations: []
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
            'Content-Security-Policy': headers.get('Content-Security-Policy')
        };
        
        const missingHeaders = Object.entries(securityHeaders)
            .filter(([key, value]) => !value)
            .map(([key]) => key);
        
        if (missingHeaders.length > 0) {
            console.log(`   ❌ Missing security headers: ${missingHeaders.join(', ')}`);
            results.recommendations.push('Add security headers to all responses');
        } else {
            console.log('   ✅ All security headers present');
        }
    } catch (error) {
        console.log(`   ❌ Error testing security headers: ${error.message}`);
    }
    
    // Test 2: Rate Limiting
    console.log('\n2. Testing Rate Limiting...');
    try {
        const response = await fetch(`${STAGING_API_URL}/api/check?domain=gmail.com`);
        const rateLimitHeaders = {
            'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
            'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
            'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset')
        };
        
        const hasRateLimitHeaders = Object.values(rateLimitHeaders).some(header => header !== null);
        
        if (!hasRateLimitHeaders) {
            console.log('   ❌ No rate limiting headers detected');
            results.recommendations.push('Implement rate limiting with proper headers');
        } else {
            console.log('   ✅ Rate limiting headers present');
        }
    } catch (error) {
        console.log(`   ❌ Error testing rate limiting: ${error.message}`);
    }
    
    // Test 3: Input Validation
    console.log('\n3. Testing Input Validation...');
    try {
        const response = await fetch(`${STAGING_API_URL}/api/check?domain=192.168.1.1`);
        const data = await response.json();
        
        if (response.ok && data.domain === '192.168.1.1') {
            console.log('   ❌ IP addresses are processed instead of rejected');
            results.recommendations.push('Add input validation to reject IP addresses as domains');
        } else {
            console.log('   ✅ Input validation working correctly');
        }
    } catch (error) {
        console.log(`   ❌ Error testing input validation: ${error.message}`);
    }
    
    // Test 4: Performance
    console.log('\n4. Testing Performance...');
    try {
        const startTime = Date.now();
        const response = await fetch(`${STAGING_API_URL}/api/health`);
        const endTime = Date.now();
        const responseTime = endTime - startTime;
        
        if (responseTime < 500) {
            console.log(`   ✅ Response time: ${responseTime}ms (Good)`);
        } else {
            console.log(`   ⚠️ Response time: ${responseTime}ms (Slow)`);
            results.recommendations.push('Optimize response times for better performance');
        }
    } catch (error) {
        console.log(`   ❌ Error testing performance: ${error.message}`);
    }
    
    // Test 5: Admin Endpoints
    console.log('\n5. Testing Admin Endpoints...');
    try {
        const response = await fetch(`${STAGING_API_URL}/api/admin/security-dashboard`, {
            headers: { 'X-Admin-API-Key': 'astraverify-admin-2024' }
        });
        
        if (response.status === 404) {
            console.log('   ❌ Admin endpoints not configured');
            results.recommendations.push('Configure admin endpoints for security monitoring');
        } else if (response.status === 200) {
            console.log('   ✅ Admin endpoints working');
        } else {
            console.log(`   ⚠️ Admin endpoints returned status: ${response.status}`);
        }
    } catch (error) {
        console.log(`   ❌ Error testing admin endpoints: ${error.message}`);
    }
    
    // Generate recommendations
    console.log('\n📋 ACTIONABLE RECOMMENDATIONS');
    console.log('==============================');
    
    if (results.recommendations.length === 0) {
        console.log('✅ No immediate issues found. STAGE environment is ready!');
    } else {
        results.recommendations.forEach((rec, index) => {
            console.log(`${index + 1}. ${rec}`);
        });
        
        console.log('\n🚨 PRIORITY ACTIONS:');
        console.log('1. HIGH: Implement security headers and rate limiting');
        console.log('2. MEDIUM: Add input validation and admin endpoints');
        console.log('3. LOW: Optimize performance if needed');
        
        console.log('\n📝 IMPLEMENTATION GUIDE:');
        console.log('- Security Headers: Add middleware to set security headers');
        console.log('- Rate Limiting: Implement Redis-based rate limiting');
        console.log('- Input Validation: Add domain validation before processing');
        console.log('- Admin Endpoints: Create admin routes with proper authentication');
    }
    
    console.log('\n🔗 USEFUL RESOURCES:');
    console.log('- Security Headers: https://owasp.org/www-project-secure-headers/');
    console.log('- Rate Limiting: https://flask-limiter.readthedocs.io/');
    console.log('- Input Validation: https://flask-wtf.readthedocs.io/');
}

// Run validation
quickValidation().catch(console.error);
