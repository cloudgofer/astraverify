#!/usr/bin/env node

const https = require('https');
const http = require('http');

// Colors for output
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
    console.log(`${colors[color]}${message}${colors.reset}`);
}

function makeRequest(url, options = {}) {
    return new Promise((resolve, reject) => {
        const urlObj = new URL(url);
        const requestOptions = {
            hostname: urlObj.hostname,
            port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
            path: urlObj.pathname + urlObj.search,
            method: options.method || 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                ...options.headers
            }
        };

        const client = urlObj.protocol === 'https:' ? https : http;
        
        const req = client.request(requestOptions, (res) => {
            let data = '';
            res.on('data', (chunk) => data += chunk);
            res.on('end', () => {
                try {
                    const jsonData = JSON.parse(data);
                    resolve({ status: res.statusCode, data: jsonData, headers: res.headers });
                } catch (e) {
                    resolve({ status: res.statusCode, data: data, headers: res.headers });
                }
            });
        });

        req.on('error', reject);
        
        if (options.body) {
            req.write(options.body);
        }
        
        req.end();
    });
}

async function verifyProductionDeployment() {
    log('🚀 AstraVerify Production Deployment Verification', 'bright');
    log('================================================', 'blue');
    
    const BACKEND_URL = 'https://astraverify-backend-ml2mhibdvq-uc.a.run.app';
    const FRONTEND_URL = 'https://astraverify-frontend-ml2mhibdvq-uc.a.run.app';
    
    log(`Backend URL: ${BACKEND_URL}`, 'cyan');
    log(`Frontend URL: ${FRONTEND_URL}`, 'cyan');
    log('================================================\n', 'blue');

    let testsPassed = 0;
    let testsFailed = 0;

    // Test 1: Backend Health Check
    log('1. Testing Backend Health...', 'yellow');
    try {
        const healthResponse = await makeRequest(`${BACKEND_URL}/api/health`);
        if (healthResponse.status === 200 && healthResponse.data.status === 'healthy') {
            log('✅ Backend health check passed', 'green');
            log(`   Environment: ${healthResponse.data.environment}`, 'cyan');
            log(`   Security Enabled: ${healthResponse.data.security_enabled}`, 'cyan');
            testsPassed++;
        } else {
            log('❌ Backend health check failed', 'red');
            log(`   Status: ${healthResponse.status}`, 'red');
            log(`   Response: ${JSON.stringify(healthResponse.data)}`, 'red');
            testsFailed++;
        }
    } catch (error) {
        log('❌ Backend health check failed', 'red');
        log(`   Error: ${error.message}`, 'red');
        testsFailed++;
    }

    // Wait a moment to avoid rapid requests
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Test 2: Frontend Accessibility
    log('\n2. Testing Frontend Accessibility...', 'yellow');
    try {
        const frontendResponse = await makeRequest(FRONTEND_URL);
        if (frontendResponse.status === 200 && frontendResponse.data.includes('AstraVerify')) {
            log('✅ Frontend is accessible', 'green');
            log(`   Status: ${frontendResponse.status}`, 'cyan');
            testsPassed++;
        } else {
            log('❌ Frontend accessibility failed', 'red');
            log(`   Status: ${frontendResponse.status}`, 'red');
            testsFailed++;
        }
    } catch (error) {
        log('❌ Frontend accessibility failed', 'red');
        log(`   Error: ${error.message}`, 'red');
        testsFailed++;
    }

    // Wait a moment to avoid rapid requests
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Test 3: Domain Verification - cloudgofer.com
    log('\n3. Testing Domain Verification (cloudgofer.com)...', 'yellow');
    try {
        const domainResponse = await makeRequest(`${BACKEND_URL}/api/check?domain=cloudgofer.com`);
        if (domainResponse.status === 200 && domainResponse.data.domain === 'cloudgofer.com') {
            log('✅ Domain verification for cloudgofer.com passed', 'green');
            log(`   Security Score: ${domainResponse.data.security_score}`, 'cyan');
            log(`   Email Provider: ${domainResponse.data.email_provider}`, 'cyan');
            testsPassed++;
        } else {
            log('❌ Domain verification for cloudgofer.com failed', 'red');
            log(`   Status: ${domainResponse.status}`, 'red');
            log(`   Response: ${JSON.stringify(domainResponse.data)}`, 'red');
            testsFailed++;
        }
    } catch (error) {
        log('❌ Domain verification for cloudgofer.com failed', 'red');
        log(`   Error: ${error.message}`, 'red');
        testsFailed++;
    }

    // Wait a moment to avoid rapid requests
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Test 4: Domain Verification - astraverify.com
    log('\n4. Testing Domain Verification (astraverify.com)...', 'yellow');
    try {
        const domainResponse = await makeRequest(`${BACKEND_URL}/api/check?domain=astraverify.com`);
        if (domainResponse.status === 200 && domainResponse.data.domain === 'astraverify.com') {
            log('✅ Domain verification for astraverify.com passed', 'green');
            log(`   Security Score: ${domainResponse.data.security_score}`, 'cyan');
            log(`   Email Provider: ${domainResponse.data.email_provider}`, 'cyan');
            testsPassed++;
        } else {
            log('❌ Domain verification for astraverify.com failed', 'red');
            log(`   Status: ${domainResponse.status}`, 'red');
            log(`   Response: ${JSON.stringify(domainResponse.data)}`, 'red');
            testsFailed++;
        }
    } catch (error) {
        log('❌ Domain verification for astraverify.com failed', 'red');
        log(`   Error: ${error.message}`, 'red');
        testsFailed++;
    }

    // Wait a moment to avoid rapid requests
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Test 5: Domain Verification - techstorm.ie
    log('\n5. Testing Domain Verification (techstorm.ie)...', 'yellow');
    try {
        const domainResponse = await makeRequest(`${BACKEND_URL}/api/check?domain=techstorm.ie`);
        if (domainResponse.status === 200 && domainResponse.data.domain === 'techstorm.ie') {
            log('✅ Domain verification for techstorm.ie passed', 'green');
            log(`   Security Score: ${domainResponse.data.security_score}`, 'cyan');
            log(`   Email Provider: ${domainResponse.data.email_provider}`, 'cyan');
            testsPassed++;
        } else {
            log('❌ Domain verification for techstorm.ie failed', 'red');
            log(`   Status: ${domainResponse.status}`, 'red');
            log(`   Response: ${JSON.stringify(domainResponse.data)}`, 'red');
            testsFailed++;
        }
    } catch (error) {
        log('❌ Domain verification for techstorm.ie failed', 'red');
        log(`   Error: ${error.message}`, 'red');
        testsFailed++;
    }

    // Wait a moment to avoid rapid requests
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Test 6: Email Functionality
    log('\n6. Testing Email Functionality...', 'yellow');
    try {
        // First get analysis result
        const analysisResponse = await makeRequest(`${BACKEND_URL}/api/check?domain=cloudgofer.com`);
        if (analysisResponse.status === 200) {
            const emailPayload = {
                domain: 'cloudgofer.com',
                email: 'nitin.jain+AstraVerifyProdTest@CloudGofer.com',
                opt_in: true,
                analysis_result: analysisResponse.data
            };

            const emailResponse = await makeRequest(`${BACKEND_URL}/api/email-report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(emailPayload)
            });

            if (emailResponse.status === 200 && emailResponse.data.success === true) {
                log('✅ Email functionality test passed', 'green');
                log('   Test email sent to: nitin.jain+AstraVerifyProdTest@CloudGofer.com', 'cyan');
                testsPassed++;
            } else {
                log('❌ Email functionality test failed', 'red');
                log(`   Status: ${emailResponse.status}`, 'red');
                log(`   Response: ${JSON.stringify(emailResponse.data)}`, 'red');
                testsFailed++;
            }
        } else {
            log('❌ Email functionality test failed - could not get analysis result', 'red');
            testsFailed++;
        }
    } catch (error) {
        log('❌ Email functionality test failed', 'red');
        log(`   Error: ${error.message}`, 'red');
        testsFailed++;
    }

    // Summary
    log('\n================================================', 'blue');
    log('📊 PRODUCTION DEPLOYMENT VERIFICATION SUMMARY', 'bright');
    log('================================================', 'blue');
    log(`Total Tests: ${testsPassed + testsFailed}`, 'cyan');
    log(`Passed: ${testsPassed}`, 'green');
    log(`Failed: ${testsFailed}`, 'red');
    log(`Success Rate: ${((testsPassed / (testsPassed + testsFailed)) * 100).toFixed(1)}%`, 'cyan');
    
    if (testsFailed === 0) {
        log('\n🎉 Production deployment verification successful!', 'green');
        log('✅ All core functionality is working correctly', 'green');
        log('✅ Domain verification is operational', 'green');
        log('✅ Email functionality is working', 'green');
        log('✅ Frontend is accessible', 'green');
        log('✅ Backend is healthy', 'green');
    } else {
        log('\n⚠️  Some verification tests failed.', 'yellow');
        log('Please review the issues above before considering deployment complete.', 'yellow');
    }

    log('\n================================================', 'blue');
    log('Production URLs:', 'bright');
    log(`Frontend: ${FRONTEND_URL}`, 'cyan');
    log(`Backend: ${BACKEND_URL}`, 'cyan');
    log('Version: v2025.08.19.01-Beta', 'cyan');
    log('================================================', 'blue');
}

// Run the verification
verifyProductionDeployment().catch(console.error);
