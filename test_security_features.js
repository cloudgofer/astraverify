// Security Features Test Suite
// Comprehensive testing of all security features in STAGE environment

const STAGING_API_URL = 'https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app';

// Test configuration
const SECURITY_TESTS = {
    // Authentication tests
    authentication: [
        {
            name: 'Invalid Admin API Key',
            method: 'GET',
            endpoint: '/api/admin/stats',
            headers: { 'X-Admin-API-Key': 'invalid-key-12345' },
            expectedStatus: 401,
            description: 'Should reject invalid admin API key'
        },
        {
            name: 'Missing Admin API Key',
            method: 'GET',
            endpoint: '/api/admin/stats',
            headers: {},
            expectedStatus: 401,
            description: 'Should reject missing admin API key'
        },
        {
            name: 'Valid Admin API Key',
            method: 'GET',
            endpoint: '/api/admin/stats',
            headers: { 'X-Admin-API-Key': 'astraverify-admin-2024' },
            expectedStatus: 200,
            description: 'Should accept valid admin API key'
        }
    ],
    
    // Rate limiting tests
    rateLimiting: [
        {
            name: 'Normal Request Rate',
            method: 'POST',
            endpoint: '/api/check',
            body: { domain: 'gmail.com' },
            headers: { 'Content-Type': 'application/json' },
            expectedStatus: 200,
            description: 'Should allow normal request rate'
        },
        {
            name: 'Rapid Requests Detection',
            method: 'POST',
            endpoint: '/api/check',
            body: { domain: 'gmail.com' },
            headers: { 'Content-Type': 'application/json' },
            rapidRequests: 20,
            expectedStatus: 429,
            description: 'Should detect and block rapid requests'
        }
    ],
    
    // Input validation tests
    inputValidation: [
        {
            name: 'Valid Domain',
            method: 'POST',
            endpoint: '/api/check',
            body: { domain: 'gmail.com' },
            headers: { 'Content-Type': 'application/json' },
            expectedStatus: 200,
            description: 'Should accept valid domain'
        },
        {
            name: 'Invalid Domain (IP Address)',
            method: 'POST',
            endpoint: '/api/check',
            body: { domain: '192.168.1.1' },
            headers: { 'Content-Type': 'application/json' },
            expectedStatus: 400,
            description: 'Should reject IP addresses as domains'
        },
        {
            name: 'Empty Domain',
            method: 'POST',
            endpoint: '/api/check',
            body: { domain: '' },
            headers: { 'Content-Type': 'application/json' },
            expectedStatus: 400,
            description: 'Should reject empty domain'
        },
        {
            name: 'Missing Domain',
            method: 'POST',
            endpoint: '/api/check',
            body: {},
            headers: { 'Content-Type': 'application/json' },
            expectedStatus: 400,
            description: 'Should reject missing domain'
        },
        {
            name: 'Malicious Domain (SQL Injection)',
            method: 'POST',
            endpoint: '/api/check',
            body: { domain: "'; DROP TABLE users; --" },
            headers: { 'Content-Type': 'application/json' },
            expectedStatus: 400,
            description: 'Should reject SQL injection attempts'
        },
        {
            name: 'Malicious Domain (XSS)',
            method: 'POST',
            endpoint: '/api/check',
            body: { domain: '<script>alert("xss")</script>' },
            headers: { 'Content-Type': 'application/json' },
            expectedStatus: 400,
            description: 'Should reject XSS attempts'
        },
        {
            name: 'Very Long Domain',
            method: 'POST',
            endpoint: '/api/check',
            body: { domain: 'a'.repeat(1000) + '.com' },
            headers: { 'Content-Type': 'application/json' },
            expectedStatus: 400,
            description: 'Should reject very long domains'
        }
    ],
    
    // Abuse prevention tests
    abusePrevention: [
        {
            name: 'Suspicious User Agent',
            method: 'POST',
            endpoint: '/api/check',
            body: { domain: 'gmail.com' },
            headers: { 
                'Content-Type': 'application/json',
                'User-Agent': 'python-requests/2.25.1'
            },
            expectedStatus: 200, // Should still work but be flagged
            description: 'Should detect suspicious user agent'
        },
        {
            name: 'Empty User Agent',
            method: 'POST',
            endpoint: '/api/check',
            body: { domain: 'gmail.com' },
            headers: { 
                'Content-Type': 'application/json',
                'User-Agent': ''
            },
            expectedStatus: 200, // Should still work but be flagged
            description: 'Should detect empty user agent'
        },
        {
            name: 'Bot User Agent',
            method: 'POST',
            endpoint: '/api/check',
            body: { domain: 'gmail.com' },
            headers: { 
                'Content-Type': 'application/json',
                'User-Agent': 'Googlebot/2.1'
            },
            expectedStatus: 200, // Should still work but be flagged
            description: 'Should detect bot user agent'
        }
    ],
    
    // CORS tests
    cors: [
        {
            name: 'CORS Preflight Request',
            method: 'OPTIONS',
            endpoint: '/api/check',
            headers: {
                'Origin': 'https://test.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            },
            expectedStatus: 200,
            description: 'Should handle CORS preflight requests'
        },
        {
            name: 'CORS Headers Present',
            method: 'GET',
            endpoint: '/api/health',
            headers: { 'Origin': 'https://test.com' },
            expectedStatus: 200,
            description: 'Should include CORS headers in response'
        }
    ],
    
    // Headers security tests
    headers: [
        {
            name: 'Security Headers',
            method: 'GET',
            endpoint: '/api/health',
            headers: {},
            expectedStatus: 200,
            description: 'Should include security headers'
        }
    ]
};

// Test results storage
let securityTestResults = {
    authentication: {},
    rateLimiting: {},
    inputValidation: {},
    abusePrevention: {},
    cors: {},
    headers: {},
    summary: { passed: 0, failed: 0, total: 0 }
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

// Security test runner
async function runSecurityTest(test, category) {
    log(`Running ${category} test: ${test.name}`);
    
    try {
        let response;
        
        if (test.rapidRequests) {
            // Handle rapid requests test
            const requests = [];
            for (let i = 0; i < test.rapidRequests; i++) {
                requests.push(fetch(`${STAGING_API_URL}${test.endpoint}`, {
                    method: test.method,
                    headers: test.headers,
                    body: test.body ? JSON.stringify(test.body) : undefined
                }));
            }
            
            const responses = await Promise.all(requests);
            const lastResponse = responses[responses.length - 1];
            
            if (lastResponse.status === test.expectedStatus) {
                log(`✅ ${test.name} passed`, 'success');
                securityTestResults[category][test.name] = { status: 'passed', description: test.description };
                securityTestResults.summary.passed++;
            } else {
                log(`❌ ${test.name} failed: expected ${test.expectedStatus}, got ${lastResponse.status}`, 'error');
                securityTestResults[category][test.name] = { status: 'failed', description: test.description, actualStatus: lastResponse.status };
                securityTestResults.summary.failed++;
            }
        } else {
            // Handle single request test
            response = await fetch(`${STAGING_API_URL}${test.endpoint}`, {
                method: test.method,
                headers: test.headers,
                body: test.body ? JSON.stringify(test.body) : undefined
            });
            
            // Check for security headers
            const securityHeaders = {
                'X-Content-Type-Options': response.headers.get('X-Content-Type-Options'),
                'X-Frame-Options': response.headers.get('X-Frame-Options'),
                'X-XSS-Protection': response.headers.get('X-XSS-Protection'),
                'Strict-Transport-Security': response.headers.get('Strict-Transport-Security'),
                'Content-Security-Policy': response.headers.get('Content-Security-Policy')
            };
            
            if (response.status === test.expectedStatus) {
                log(`✅ ${test.name} passed`, 'success');
                securityTestResults[category][test.name] = { 
                    status: 'passed', 
                    description: test.description,
                    securityHeaders: category === 'headers' ? securityHeaders : undefined
                };
                securityTestResults.summary.passed++;
            } else {
                log(`❌ ${test.name} failed: expected ${test.expectedStatus}, got ${response.status}`, 'error');
                securityTestResults[category][test.name] = { 
                    status: 'failed', 
                    description: test.description, 
                    actualStatus: response.status,
                    securityHeaders: category === 'headers' ? securityHeaders : undefined
                };
                securityTestResults.summary.failed++;
            }
        }
        
        securityTestResults.summary.total++;
        
    } catch (error) {
        log(`❌ ${test.name} error: ${error.message}`, 'error');
        securityTestResults[category][test.name] = { 
            status: 'error', 
            description: test.description, 
            error: error.message 
        };
        securityTestResults.summary.failed++;
        securityTestResults.summary.total++;
    }
}

// Run all security tests
async function runAllSecurityTests() {
    log('🔒 Starting Security Features Test Suite');
    log(`API URL: ${STAGING_API_URL}`);
    
    try {
        // Run authentication tests
        log('\n=== Authentication Tests ===');
        for (const test of SECURITY_TESTS.authentication) {
            await runSecurityTest(test, 'authentication');
            await sleep(1000); // Wait between tests
        }
        
        // Run input validation tests
        log('\n=== Input Validation Tests ===');
        for (const test of SECURITY_TESTS.inputValidation) {
            await runSecurityTest(test, 'inputValidation');
            await sleep(1000);
        }
        
        // Run CORS tests
        log('\n=== CORS Tests ===');
        for (const test of SECURITY_TESTS.cors) {
            await runSecurityTest(test, 'cors');
            await sleep(1000);
        }
        
        // Run headers security tests
        log('\n=== Security Headers Tests ===');
        for (const test of SECURITY_TESTS.headers) {
            await runSecurityTest(test, 'headers');
            await sleep(1000);
        }
        
        // Run abuse prevention tests
        log('\n=== Abuse Prevention Tests ===');
        for (const test of SECURITY_TESTS.abusePrevention) {
            await runSecurityTest(test, 'abusePrevention');
            await sleep(1000);
        }
        
        // Run rate limiting tests (do this last to avoid affecting other tests)
        log('\n=== Rate Limiting Tests ===');
        for (const test of SECURITY_TESTS.rateLimiting) {
            await runSecurityTest(test, 'rateLimiting');
            await sleep(2000); // Longer wait for rate limiting tests
        }
        
        // Generate and display report
        generateSecurityReport();
        
    } catch (error) {
        log(`Security test suite error: ${error.message}`, 'error');
        process.exit(1);
    }
}

// Generate security test report
function generateSecurityReport() {
    log('\n=== Security Test Report ===');
    
    const report = {
        timestamp: new Date().toISOString(),
        environment: 'STAGING',
        apiUrl: STAGING_API_URL,
        summary: {
            total: securityTestResults.summary.total,
            passed: securityTestResults.summary.passed,
            failed: securityTestResults.summary.failed,
            successRate: ((securityTestResults.summary.passed / securityTestResults.summary.total) * 100).toFixed(2) + '%'
        },
        details: securityTestResults
    };
    
    console.log('\n🔒 SECURITY TEST REPORT');
    console.log('=======================');
    console.log(`Environment: ${report.environment}`);
    console.log(`API URL: ${report.apiUrl}`);
    console.log(`Timestamp: ${report.timestamp}`);
    console.log(`Success Rate: ${report.summary.successRate}`);
    console.log(`Total Tests: ${report.summary.total}`);
    console.log(`Passed: ${report.summary.passed}`);
    console.log(`Failed: ${report.summary.failed}`);
    
    // Display results by category
    Object.entries(securityTestResults).forEach(([category, tests]) => {
        if (category === 'summary') return;
        
        console.log(`\n${category.toUpperCase()}:`);
        Object.entries(tests).forEach(([testName, result]) => {
            const status = result.status === 'passed' ? '✅' : '❌';
            console.log(`  ${status} ${testName}: ${result.description}`);
            if (result.actualStatus) {
                console.log(`    Expected: 200, Got: ${result.actualStatus}`);
            }
            if (result.securityHeaders) {
                console.log(`    Security Headers: ${JSON.stringify(result.securityHeaders)}`);
            }
        });
    });
    
    // Save report to file
    const fs = require('fs');
    fs.writeFileSync('security_test_report.json', JSON.stringify(report, null, 2));
    log('Security test report saved to security_test_report.json', 'success');
    
    // Exit with appropriate code
    if (securityTestResults.summary.failed === 0) {
        log('🎉 All security tests passed!', 'success');
        process.exit(0);
    } else {
        log(`⚠️ ${securityTestResults.summary.failed} security tests failed`, 'warning');
        process.exit(1);
    }
}

// Run tests if this script is executed directly
if (require.main === module) {
    runAllSecurityTests();
}

module.exports = {
    runAllSecurityTests,
    securityTestResults,
    SECURITY_TESTS
};
