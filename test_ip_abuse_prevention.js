const axios = require('axios');

// Configuration
const BASE_URL = 'http://localhost:8080'; // Adjust if your backend runs on different port
const TEST_DOMAIN = 'example.com';

// Test scenarios
const testScenarios = [
    {
        name: 'Normal Request',
        description: 'Single normal request should succeed',
        requests: 1,
        delay: 1000,
        expectedStatus: 200
    },
    {
        name: 'Rate Limiting Test',
        description: 'Multiple rapid requests should trigger rate limiting',
        requests: 15, // More than the 10 requests per minute limit
        delay: 100, // Very fast requests
        expectedStatus: 429
    },
    {
        name: 'Abuse Detection Test',
        description: 'Suspicious patterns should trigger abuse detection',
        requests: 5,
        delay: 50, // Very fast requests to trigger rapid_requests flag
        suspiciousUserAgent: 'bot/crawler',
        expectedStatus: 403 // Should be blocked
    }
];

async function makeRequest(domain, userAgent = null) {
    try {
        const headers = {};
        if (userAgent) {
            headers['User-Agent'] = userAgent;
        }
        
        const response = await axios.post(`${BASE_URL}/api/analyze`, {
            domain: domain
        }, { headers });
        
        return {
            status: response.status,
            data: response.data,
            headers: response.headers
        };
    } catch (error) {
        return {
            status: error.response?.status || 500,
            data: error.response?.data || { error: error.message },
            headers: error.response?.headers || {}
        };
    }
}

async function runTest(scenario) {
    console.log(`\n🧪 Running: ${scenario.name}`);
    console.log(`📝 ${scenario.description}`);
    console.log(`📊 Expected status: ${scenario.expectedStatus}`);
    
    const results = [];
    
    for (let i = 0; i < scenario.requests; i++) {
        const userAgent = scenario.suspiciousUserAgent || 'Mozilla/5.0 (Test Client)';
        const result = await makeRequest(TEST_DOMAIN, userAgent);
        
        results.push({
            request: i + 1,
            status: result.status,
            error: result.data.error,
            rateLimitInfo: result.headers['x-ratelimit-remaining']
        });
        
        console.log(`  Request ${i + 1}: Status ${result.status}${result.data.error ? ` - ${result.data.error}` : ''}`);
        
        if (scenario.delay > 0 && i < scenario.requests - 1) {
            await new Promise(resolve => setTimeout(resolve, scenario.delay));
        }
    }
    
    // Analyze results
    const finalStatus = results[results.length - 1].status;
    const success = finalStatus === scenario.expectedStatus;
    
    console.log(`\n${success ? '✅' : '❌'} Test ${success ? 'PASSED' : 'FAILED'}`);
    console.log(`   Final status: ${finalStatus} (expected: ${scenario.expectedStatus})`);
    
    if (results.some(r => r.status === 429)) {
        console.log(`   Rate limiting detected: ✅`);
    }
    
    if (results.some(r => r.status === 403)) {
        console.log(`   IP blocking detected: ✅`);
    }
    
    return {
        scenario: scenario.name,
        success,
        results,
        finalStatus
    };
}

async function testSecurityEndpoints() {
    console.log('\n🔍 Testing Security Endpoints...');
    
    try {
        // Test health endpoint
        const healthResponse = await axios.get(`${BASE_URL}/api/health`);
        console.log(`✅ Health endpoint: ${healthResponse.data.security_enabled ? 'Security enabled' : 'Security disabled'}`);
        
        // Test blocked IPs endpoint (if available)
        try {
            const blockedResponse = await axios.get(`${BASE_URL}/api/admin/blocked-ips`, {
                headers: { 'X-Admin-Key': 'astraverify-admin-2024' }
            });
            console.log(`✅ Blocked IPs endpoint: ${blockedResponse.data.total_blocked || 0} IPs blocked`);
        } catch (error) {
            console.log(`⚠️  Blocked IPs endpoint not available or unauthorized`);
        }
        
    } catch (error) {
        console.log(`❌ Health endpoint failed: ${error.message}`);
    }
}

async function main() {
    console.log('🚀 Starting IP Abuse Prevention Test Suite');
    console.log(`📍 Testing against: ${BASE_URL}`);
    console.log(`🎯 Test domain: ${TEST_DOMAIN}`);
    
    // Test security endpoints first
    await testSecurityEndpoints();
    
    // Run test scenarios
    const testResults = [];
    
    for (const scenario of testScenarios) {
        const result = await runTest(scenario);
        testResults.push(result);
        
        // Wait between tests
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Summary
    console.log('\n📊 Test Summary:');
    console.log('================');
    
    const passedTests = testResults.filter(r => r.success).length;
    const totalTests = testResults.length;
    
    testResults.forEach(result => {
        const status = result.success ? '✅ PASS' : '❌ FAIL';
        console.log(`${status} ${result.scenario}`);
    });
    
    console.log(`\n🎯 Overall: ${passedTests}/${totalTests} tests passed`);
    
    if (passedTests === totalTests) {
        console.log('🎉 All IP abuse prevention tests passed! The system is working correctly.');
    } else {
        console.log('⚠️  Some tests failed. Please check the implementation.');
    }
}

// Run the tests
main().catch(console.error);
