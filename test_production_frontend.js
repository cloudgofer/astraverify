#!/usr/bin/env node

const https = require('https');

// Colors for output
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
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

        const req = https.request(requestOptions, (res) => {
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

async function testProductionFrontend() {
    log('🚀 Testing Production Frontend Issue', 'bright');
    log('==================================================', 'blue');

    const BACKEND_URL = 'https://astraverify-backend-ml2mhibdvq-uc.a.run.app';
    const FRONTEND_URL = 'https://astraverify.com';

    log(`Backend URL: ${BACKEND_URL}`, 'cyan');
    log(`Frontend URL: ${FRONTEND_URL}`, 'cyan');
    log('==================================================\n', 'blue');

    // Test 1: Check if frontend loads
    log('1. Testing Frontend Loading...', 'yellow');
    try {
        const frontendResponse = await makeRequest(FRONTEND_URL);
        if (frontendResponse.status === 200) {
            log('✅ Frontend loads successfully', 'green');
            
            // Check if it contains the expected content
            if (frontendResponse.data.includes('AstraVerify') && frontendResponse.data.includes('root')) {
                log('✅ Frontend contains expected React app structure', 'green');
            } else {
                log('⚠️  Frontend content may be incomplete', 'yellow');
            }
        } else {
            log('❌ Frontend loading failed', 'red');
            log(`   Status: ${frontendResponse.status}`, 'red');
        }
    } catch (error) {
        log('❌ Frontend loading failed', 'red');
        log(`   Error: ${error.message}`, 'red');
    }

    await new Promise(resolve => setTimeout(resolve, 2000));

    // Test 2: Check backend API that frontend calls
    log('\n2. Testing Backend APIs that Frontend Uses...', 'yellow');
    
    // Test statistics endpoint
    try {
        const statsResponse = await makeRequest(`${BACKEND_URL}/api/public/statistics`);
        if (statsResponse.status === 200 && statsResponse.data.success) {
            log('✅ Statistics API working', 'green');
            log(`   Total analyses: ${statsResponse.data.data.total_analyses}`, 'cyan');
        } else {
            log('❌ Statistics API failed', 'red');
            log(`   Status: ${statsResponse.status}`, 'red');
        }
    } catch (error) {
        log('❌ Statistics API failed', 'red');
        log(`   Error: ${error.message}`, 'red');
    }

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Test domain check endpoint
    try {
        const domainResponse = await makeRequest(`${BACKEND_URL}/api/check?domain=cloudgofer.com`);
        if (domainResponse.status === 200 && domainResponse.data.domain === 'cloudgofer.com') {
            log('✅ Domain check API working', 'green');
            log(`   Security score: ${domainResponse.data.security_score}`, 'cyan');
        } else {
            log('❌ Domain check API failed', 'red');
            log(`   Status: ${domainResponse.status}`, 'red');
        }
    } catch (error) {
        log('❌ Domain check API failed', 'red');
        log(`   Error: ${error.message}`, 'red');
    }

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Test 3: Check for CORS issues
    log('\n3. Testing CORS Configuration...', 'yellow');
    try {
        const corsResponse = await makeRequest(`${BACKEND_URL}/api/health`, {
            headers: {
                'Origin': 'https://astraverify.com',
                'Referer': 'https://astraverify.com/'
            }
        });
        
        if (corsResponse.status === 200) {
            log('✅ CORS appears to be working', 'green');
            if (corsResponse.headers['access-control-allow-origin']) {
                log(`   CORS header: ${corsResponse.headers['access-control-allow-origin']}`, 'cyan');
            }
        } else {
            log('❌ CORS may be blocking requests', 'red');
        }
    } catch (error) {
        log('❌ CORS test failed', 'red');
        log(`   Error: ${error.message}`, 'red');
    }

    // Test 4: Check if there are any JavaScript errors by examining the build
    log('\n4. Analyzing Frontend Build...', 'yellow');
    try {
        const jsResponse = await makeRequest('https://astraverify.com/static/js/main.a14e80d4.js');
        if (jsResponse.status === 200) {
            log('✅ JavaScript bundle loads successfully', 'green');
            log(`   Bundle size: ${jsResponse.data.length} bytes`, 'cyan');
            
            // Check for common error patterns
            if (jsResponse.data.includes('error') || jsResponse.data.includes('Error')) {
                log('⚠️  JavaScript bundle contains error-related code', 'yellow');
            }
        } else {
            log('❌ JavaScript bundle failed to load', 'red');
        }
    } catch (error) {
        log('❌ JavaScript bundle test failed', 'red');
        log(`   Error: ${error.message}`, 'red');
    }

    // Test 5: Simulate the exact flow that might cause blanking
    log('\n5. Simulating Frontend-Backend Interaction...', 'yellow');
    try {
        // First get statistics (what frontend does on load)
        const statsResponse = await makeRequest(`${BACKEND_URL}/api/public/statistics`);
        
        // Then simulate a domain check (what happens after user input)
        const domainResponse = await makeRequest(`${BACKEND_URL}/api/check?domain=cloudgofer.com`);
        
        if (statsResponse.status === 200 && domainResponse.status === 200) {
            log('✅ Backend APIs respond correctly to frontend requests', 'green');
            log('   This suggests the issue is in frontend JavaScript, not backend', 'cyan');
        } else {
            log('❌ Backend APIs have issues', 'red');
        }
    } catch (error) {
        log('❌ Frontend-backend interaction test failed', 'red');
        log(`   Error: ${error.message}`, 'red');
    }

    log('\n==================================================', 'blue');
    log('🔍 DIAGNOSIS SUMMARY', 'bright');
    log('==================================================', 'blue');
    log('Based on the tests above:', 'cyan');
    log('1. If backend APIs work but frontend blanks out, the issue is likely:', 'yellow');
    log('   - JavaScript error in the React app', 'red');
    log('   - CORS configuration issue', 'red');
    log('   - Frontend trying to call non-existent endpoints', 'red');
    log('   - State management issue in React', 'red');
    log('2. If backend APIs fail, the issue is in the backend', 'yellow');
    log('3. If frontend doesn\'t load at all, it\'s a deployment issue', 'yellow');
    log('\n==================================================', 'blue');
    log('Next steps: Check browser console for JavaScript errors', 'bright');
    log('==================================================', 'blue');
}

// Run the test
testProductionFrontend().catch(console.error);
