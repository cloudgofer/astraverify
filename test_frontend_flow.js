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

async function testFrontendFlow() {
    log('🚀 Testing Frontend Flow (Simulating User Interaction)', 'bright');
    log('==================================================', 'blue');

    const BACKEND_URL = 'https://astraverify-backend-ml2mhibdvq-uc.a.run.app';
    const domain = 'cloudgofer.com';

    log(`Testing domain: ${domain}`, 'cyan');
    log('==================================================\n', 'blue');

    // Step 1: Initial statistics fetch (what happens on page load)
    log('1. Fetching initial statistics (page load)...', 'yellow');
    try {
        const statsResponse = await makeRequest(`${BACKEND_URL}/api/public/statistics`);
        if (statsResponse.status === 200 && statsResponse.data.success) {
            log('✅ Statistics loaded successfully', 'green');
            log(`   Total analyses: ${statsResponse.data.data.total_analyses}`, 'cyan');
        } else {
            log('❌ Statistics failed', 'red');
            log(`   Status: ${statsResponse.status}`, 'red');
        }
    } catch (error) {
        log('❌ Statistics failed', 'red');
        log(`   Error: ${error.message}`, 'red');
    }

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Step 2: Progressive domain check (first API call)
    log('\n2. Making progressive domain check...', 'yellow');
    try {
        const progressiveUrl = `${BACKEND_URL}/api/check?domain=${encodeURIComponent(domain)}&progressive=true`;
        log(`   URL: ${progressiveUrl}`, 'cyan');
        
        const progressiveResponse = await makeRequest(progressiveUrl);
        
        if (progressiveResponse.status === 200) {
            log('✅ Progressive check successful', 'green');
            log(`   Domain: ${progressiveResponse.data.domain}`, 'cyan');
            log(`   Security Score: ${progressiveResponse.data.security_score}`, 'cyan');
            
            // Check if all required fields are present
            const requiredFields = ['domain', 'security_score', 'email_provider', 'component_scores'];
            const missingFields = requiredFields.filter(field => !progressiveResponse.data[field]);
            
            if (missingFields.length > 0) {
                log(`⚠️  Missing fields: ${missingFields.join(', ')}`, 'yellow');
            } else {
                log('✅ All required fields present', 'green');
            }
        } else {
            log('❌ Progressive check failed', 'red');
            log(`   Status: ${progressiveResponse.status}`, 'red');
            log(`   Response: ${JSON.stringify(progressiveResponse.data)}`, 'red');
        }
    } catch (error) {
        log('❌ Progressive check failed', 'red');
        log(`   Error: ${error.message}`, 'red');
    }

    await new Promise(resolve => setTimeout(resolve, 2000));

    // Step 3: DKIM completion check (second API call)
    log('\n3. Making DKIM completion check...', 'yellow');
    try {
        const dkimUrl = `${BACKEND_URL}/api/check/dkim?domain=${encodeURIComponent(domain)}`;
        log(`   URL: ${dkimUrl}`, 'cyan');
        
        const dkimResponse = await makeRequest(dkimUrl);
        
        if (dkimResponse.status === 200 && dkimResponse.data.success) {
            log('✅ DKIM check successful', 'green');
            log(`   Domain: ${dkimResponse.data.domain}`, 'cyan');
            log(`   DKIM Status: ${dkimResponse.data.dkim.status}`, 'cyan');
            log(`   Selectors Checked: ${dkimResponse.data.dkim.selectors_checked}`, 'cyan');
            
            // Check if recommendations are present
            if (dkimResponse.data.recommendations) {
                log(`   Recommendations: ${dkimResponse.data.recommendations.length} items`, 'cyan');
            } else {
                log('⚠️  No recommendations in response', 'yellow');
            }
        } else {
            log('❌ DKIM check failed', 'red');
            log(`   Status: ${dkimResponse.status}`, 'red');
            log(`   Response: ${JSON.stringify(dkimResponse.data)}`, 'red');
        }
    } catch (error) {
        log('❌ DKIM check failed', 'red');
        log(`   Error: ${error.message}`, 'red');
    }

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Step 4: Final statistics refresh
    log('\n4. Refreshing statistics after analysis...', 'yellow');
    try {
        const finalStatsResponse = await makeRequest(`${BACKEND_URL}/api/public/statistics`);
        if (finalStatsResponse.status === 200 && finalStatsResponse.data.success) {
            log('✅ Final statistics refresh successful', 'green');
            log(`   Total analyses: ${finalStatsResponse.data.data.total_analyses}`, 'cyan');
        } else {
            log('❌ Final statistics refresh failed', 'red');
        }
    } catch (error) {
        log('❌ Final statistics refresh failed', 'red');
        log(`   Error: ${error.message}`, 'red');
    }

    log('\n==================================================', 'blue');
    log('🔍 FLOW ANALYSIS SUMMARY', 'bright');
    log('==================================================', 'blue');
    log('If all steps above passed, the backend APIs are working correctly.', 'cyan');
    log('The blanking issue is likely caused by:', 'yellow');
    log('1. JavaScript error in the React app', 'red');
    log('2. State management issue (setResult, setLoading, etc.)', 'red');
    log('3. CORS issue with the specific domain', 'red');
    log('4. Frontend trying to access undefined properties', 'red');
    log('5. React rendering error after state update', 'red');
    log('\n==================================================', 'blue');
    log('Next steps: Check browser console for JavaScript errors', 'bright');
    log('==================================================', 'blue');
}

// Run the test
testFrontendFlow().catch(console.error);
