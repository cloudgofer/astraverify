// Comprehensive STAGE Environment Test Suite
// Tests security features, rate limiting, abuse prevention, and mobile responsiveness

const STAGING_API_URL = 'https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app';
const STAGING_FRONTEND_URL = 'https://astraverify-frontend-staging-ml2mhibdvq-uc.a.run.app';

// Test configuration
const TEST_CONFIG = {
    domains: [
        'gmail.com',
        'outlook.com',
        'yahoo.com',
        'test-invalid-domain-12345.com',
        '192.168.1.1', // Invalid domain (IP)
        'test123.com',
        'example.com'
    ],
    testIterations: 15, // For rate limiting tests
    delayBetweenRequests: 100, // ms
    mobileViewports: [
        { width: 375, height: 667, name: 'iPhone SE' },
        { width: 414, height: 896, name: 'iPhone 11' },
        { width: 768, height: 1024, name: 'iPad' },
        { width: 1024, height: 768, name: 'iPad Landscape' }
    ]
};

// Test results storage
let testResults = {
    security: {},
    rateLimiting: {},
    abusePrevention: {},
    mobileResponsiveness: {},
    apiEndpoints: {},
    overall: { passed: 0, failed: 0, total: 0 }
};

// Utility functions
function log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : type === 'warning' ? '⚠️' : 'ℹ️';
    console.log(`${prefix} [${timestamp}] ${message}`);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// API Test Functions
async function testHealthEndpoint() {
    log('Testing health endpoint...');
    try {
        const response = await fetch(`${STAGING_API_URL}/api/health`);
        const data = await response.json();
        
        if (response.ok && data.status === 'healthy' && data.security_enabled === true) {
            log('Health endpoint test passed', 'success');
            testResults.apiEndpoints.health = { status: 'passed', data };
            return true;
        } else {
            log(`Health endpoint test failed: ${JSON.stringify(data)}`, 'error');
            testResults.apiEndpoints.health = { status: 'failed', data };
            return false;
        }
    } catch (error) {
        log(`Health endpoint test error: ${error.message}`, 'error');
        testResults.apiEndpoints.health = { status: 'failed', error: error.message };
        return false;
    }
}

async function testDomainCheck(domain, expectedSuccess = true) {
    log(`Testing domain check: ${domain}`);
    try {
        const response = await fetch(`${STAGING_API_URL}/api/check`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'AstraVerify-Test-Suite/1.0'
            },
            body: JSON.stringify({ domain })
        });
        
        const data = await response.json();
        
        // Check for rate limiting headers
        const rateLimitHeaders = {
            'X-RateLimit-Limit': response.headers.get('X-RateLimit-Limit'),
            'X-RateLimit-Remaining': response.headers.get('X-RateLimit-Remaining'),
            'X-RateLimit-Reset': response.headers.get('X-RateLimit-Reset')
        };
        
        if (expectedSuccess && response.ok) {
            log(`Domain check passed for ${domain}`, 'success');
            return { success: true, data, rateLimitHeaders };
        } else if (!expectedSuccess && !response.ok) {
            log(`Domain check correctly failed for ${domain}`, 'success');
            return { success: true, data, rateLimitHeaders };
        } else {
            log(`Domain check unexpected result for ${domain}: ${JSON.stringify(data)}`, 'error');
            return { success: false, data, rateLimitHeaders };
        }
    } catch (error) {
        log(`Domain check error for ${domain}: ${error.message}`, 'error');
        return { success: false, error: error.message };
    }
}

// Security Tests
async function testSecurityFeatures() {
    log('=== Testing Security Features ===');
    
    // Test 1: Invalid API key
    log('Testing invalid API key...');
    try {
        const response = await fetch(`${STAGING_API_URL}/api/admin/stats`, {
            headers: {
                'X-Admin-API-Key': 'invalid-key'
            }
        });
        
        if (response.status === 401) {
            log('Invalid API key correctly rejected', 'success');
            testResults.security.invalidApiKey = 'passed';
        } else {
            log(`Invalid API key test failed: expected 401, got ${response.status}`, 'error');
            testResults.security.invalidApiKey = 'failed';
        }
    } catch (error) {
        log(`Invalid API key test error: ${error.message}`, 'error');
        testResults.security.invalidApiKey = 'failed';
    }
    
    // Test 2: Missing API key
    log('Testing missing API key...');
    try {
        const response = await fetch(`${STAGING_API_URL}/api/admin/stats`);
        
        if (response.status === 401) {
            log('Missing API key correctly rejected', 'success');
            testResults.security.missingApiKey = 'passed';
        } else {
            log(`Missing API key test failed: expected 401, got ${response.status}`, 'error');
            testResults.security.missingApiKey = 'failed';
        }
    } catch (error) {
        log(`Missing API key test error: ${error.message}`, 'error');
        testResults.security.missingApiKey = 'failed';
    }
    
    // Test 3: CORS headers
    log('Testing CORS headers...');
    try {
        const response = await fetch(`${STAGING_API_URL}/api/health`, {
            method: 'OPTIONS',
            headers: {
                'Origin': 'https://test.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        });
        
        const corsHeaders = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers')
        };
        
        if (corsHeaders['Access-Control-Allow-Origin']) {
            log('CORS headers present', 'success');
            testResults.security.corsHeaders = 'passed';
        } else {
            log('CORS headers missing', 'error');
            testResults.security.corsHeaders = 'failed';
        }
    } catch (error) {
        log(`CORS test error: ${error.message}`, 'error');
        testResults.security.corsHeaders = 'failed';
    }
}

// Rate Limiting Tests
async function testRateLimiting() {
    log('=== Testing Rate Limiting ===');
    
    // Test 1: Normal rate limits
    log('Testing normal rate limits...');
    const results = [];
    
    for (let i = 0; i < TEST_CONFIG.testIterations; i++) {
        const result = await testDomainCheck('gmail.com');
        results.push(result);
        
        if (result.data && result.data.error && result.data.error.includes('Rate limit exceeded')) {
            log(`Rate limit hit after ${i + 1} requests`, 'warning');
            testResults.rateLimiting.normalLimits = { status: 'passed', requestsBeforeLimit: i + 1 };
            break;
        }
        
        await sleep(TEST_CONFIG.delayBetweenRequests);
    }
    
    if (results.length === TEST_CONFIG.testIterations) {
        log('Rate limit not hit within expected range', 'warning');
        testResults.rateLimiting.normalLimits = { status: 'warning', requestsBeforeLimit: TEST_CONFIG.testIterations };
    }
    
    // Test 2: Rate limit headers
    const lastResult = results[results.length - 1];
    if (lastResult.rateLimitHeaders['X-RateLimit-Limit']) {
        log('Rate limit headers present', 'success');
        testResults.rateLimiting.headers = 'passed';
    } else {
        log('Rate limit headers missing', 'error');
        testResults.rateLimiting.headers = 'failed';
    }
    
    // Wait for rate limit to reset
    log('Waiting for rate limit to reset...');
    await sleep(60000); // Wait 1 minute
}

// Abuse Prevention Tests
async function testAbusePrevention() {
    log('=== Testing Abuse Prevention ===');
    
    // Test 1: Invalid domains
    log('Testing invalid domain detection...');
    const invalidDomains = ['192.168.1.1', 'test-invalid-domain-12345.com', '123.456.789.000'];
    
    for (const domain of invalidDomains) {
        const result = await testDomainCheck(domain, false);
        if (result.success) {
            log(`Invalid domain ${domain} correctly handled`, 'success');
        } else {
            log(`Invalid domain ${domain} test failed`, 'error');
        }
    }
    
    // Test 2: Rapid requests (potential abuse)
    log('Testing rapid request detection...');
    const rapidRequests = [];
    for (let i = 0; i < 20; i++) {
        rapidRequests.push(testDomainCheck(`test${i}.com`));
    }
    
    const rapidResults = await Promise.all(rapidRequests);
    const blockedRequests = rapidResults.filter(r => r.data && r.data.error && r.data.error.includes('Access denied'));
    
    if (blockedRequests.length > 0) {
        log(`Abuse prevention working: ${blockedRequests.length} requests blocked`, 'success');
        testResults.abusePrevention.rapidRequests = 'passed';
    } else {
        log('No rapid requests blocked - may need adjustment', 'warning');
        testResults.abusePrevention.rapidRequests = 'warning';
    }
    
    // Wait before next tests
    await sleep(5000);
}

// Mobile Responsiveness Tests
async function testMobileResponsiveness() {
    log('=== Testing Mobile Responsiveness ===');
    
    // This would require a browser environment
    // For now, we'll test the frontend URL accessibility
    log('Testing frontend accessibility...');
    try {
        const response = await fetch(STAGING_FRONTEND_URL);
        if (response.ok) {
            log('Frontend accessible', 'success');
            testResults.mobileResponsiveness.frontendAccess = 'passed';
        } else {
            log(`Frontend not accessible: ${response.status}`, 'error');
            testResults.mobileResponsiveness.frontendAccess = 'failed';
        }
    } catch (error) {
        log(`Frontend test error: ${error.message}`, 'error');
        testResults.mobileResponsiveness.frontendAccess = 'failed';
    }
}

// API Endpoint Tests
async function testApiEndpoints() {
    log('=== Testing API Endpoints ===');
    
    // Test domain check with valid domains
    for (const domain of ['gmail.com', 'outlook.com', 'yahoo.com']) {
        const result = await testDomainCheck(domain);
        if (result.success) {
            log(`API endpoint test passed for ${domain}`, 'success');
            testResults.apiEndpoints[domain] = 'passed';
        } else {
            log(`API endpoint test failed for ${domain}`, 'error');
            testResults.apiEndpoints[domain] = 'failed';
        }
        await sleep(1000); // Wait between requests
    }
}

// Generate Test Report
function generateReport() {
    log('=== Test Report ===');
    
    const report = {
        timestamp: new Date().toISOString(),
        environment: 'STAGING',
        summary: {
            total: testResults.overall.total,
            passed: testResults.overall.passed,
            failed: testResults.overall.failed,
            successRate: ((testResults.overall.passed / testResults.overall.total) * 100).toFixed(2) + '%'
        },
        details: testResults
    };
    
    console.log('\n📊 COMPREHENSIVE TEST REPORT');
    console.log('============================');
    console.log(`Environment: ${report.environment}`);
    console.log(`Timestamp: ${report.timestamp}`);
    console.log(`Success Rate: ${report.summary.successRate}`);
    console.log(`Total Tests: ${report.summary.total}`);
    console.log(`Passed: ${report.summary.passed}`);
    console.log(`Failed: ${report.summary.failed}`);
    
    console.log('\n🔒 Security Features:');
    Object.entries(testResults.security).forEach(([test, result]) => {
        const status = result === 'passed' ? '✅' : '❌';
        console.log(`  ${status} ${test}: ${result}`);
    });
    
    console.log('\n⏱️ Rate Limiting:');
    Object.entries(testResults.rateLimiting).forEach(([test, result]) => {
        const status = result.status === 'passed' ? '✅' : result.status === 'warning' ? '⚠️' : '❌';
        console.log(`  ${status} ${test}: ${result.status}`);
    });
    
    console.log('\n🛡️ Abuse Prevention:');
    Object.entries(testResults.abusePrevention).forEach(([test, result]) => {
        const status = result === 'passed' ? '✅' : result === 'warning' ? '⚠️' : '❌';
        console.log(`  ${status} ${test}: ${result}`);
    });
    
    console.log('\n📱 Mobile Responsiveness:');
    Object.entries(testResults.mobileResponsiveness).forEach(([test, result]) => {
        const status = result === 'passed' ? '✅' : '❌';
        console.log(`  ${status} ${test}: ${result}`);
    });
    
    console.log('\n🔌 API Endpoints:');
    Object.entries(testResults.apiEndpoints).forEach(([test, result]) => {
        const status = result.status === 'passed' ? '✅' : '❌';
        console.log(`  ${status} ${test}: ${result.status}`);
    });
    
    return report;
}

// Main test runner
async function runAllTests() {
    log('🚀 Starting Comprehensive STAGE Environment Tests');
    log(`API URL: ${STAGING_API_URL}`);
    log(`Frontend URL: ${STAGING_FRONTEND_URL}`);
    
    try {
        // Run all test suites
        await testHealthEndpoint();
        await testSecurityFeatures();
        await testRateLimiting();
        await testAbusePrevention();
        await testMobileResponsiveness();
        await testApiEndpoints();
        
        // Generate and display report
        const report = generateReport();
        
        // Save report to file
        const fs = require('fs');
        fs.writeFileSync('stage_environment_test_report.json', JSON.stringify(report, null, 2));
        log('Test report saved to stage_environment_test_report.json', 'success');
        
        // Exit with appropriate code
        if (testResults.overall.failed === 0) {
            log('🎉 All tests passed!', 'success');
            process.exit(0);
        } else {
            log(`⚠️ ${testResults.overall.failed} tests failed`, 'warning');
            process.exit(1);
        }
        
    } catch (error) {
        log(`Test suite error: ${error.message}`, 'error');
        process.exit(1);
    }
}

// Update test results counter
function updateTestCounter(success) {
    testResults.overall.total++;
    if (success) {
        testResults.overall.passed++;
    } else {
        testResults.overall.failed++;
    }
}

// Run tests if this script is executed directly
if (require.main === module) {
    runAllTests();
}

module.exports = {
    runAllTests,
    testResults,
    TEST_CONFIG
};
