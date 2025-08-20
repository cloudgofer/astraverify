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
    cyan: '\x1b[36m',
    magenta: '\x1b[35m'
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

async function testEnvironment(envName, backendUrl, frontendUrl) {
    log(`\n🔍 Testing ${envName.toUpperCase()} Environment`, 'bright');
    log('=' .repeat(50), 'blue');
    
    let testsPassed = 0;
    let testsFailed = 0;
    const results = {};

    // Test 1: Backend Health
    log(`\n1. Testing Backend Health (${backendUrl})...`, 'yellow');
    try {
        const healthResponse = await makeRequest(`${backendUrl}/api/health`);
        if (healthResponse.status === 200) {
            log('✅ Backend health check passed', 'green');
            results.health = {
                status: healthResponse.status,
                environment: healthResponse.data.environment,
                security_enabled: healthResponse.data.security_enabled
            };
            testsPassed++;
        } else {
            log('❌ Backend health check failed', 'red');
            log(`   Status: ${healthResponse.status}`, 'red');
            testsFailed++;
        }
    } catch (error) {
        log('❌ Backend health check failed', 'red');
        log(`   Error: ${error.message}`, 'red');
        testsFailed++;
    }

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Test 2: Public Statistics
    log(`\n2. Testing Public Statistics...`, 'yellow');
    try {
        const statsResponse = await makeRequest(`${backendUrl}/api/public/statistics`);
        if (statsResponse.status === 200 && statsResponse.data.success) {
            log('✅ Public statistics accessible', 'green');
            results.statistics = {
                status: statsResponse.status,
                total_analyses: statsResponse.data.data.total_analyses,
                unique_domains: statsResponse.data.data.unique_domains,
                average_security_score: statsResponse.data.data.average_security_score
            };
            testsPassed++;
        } else {
            log('❌ Public statistics failed', 'red');
            log(`   Status: ${statsResponse.status}`, 'red');
            log(`   Response: ${JSON.stringify(statsResponse.data)}`, 'red');
            testsFailed++;
        }
    } catch (error) {
        log('❌ Public statistics failed', 'red');
        log(`   Error: ${error.message}`, 'red');
        testsFailed++;
    }

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Test 3: Domain Check
    log(`\n3. Testing Domain Check (cloudgofer.com)...`, 'yellow');
    try {
        const domainResponse = await makeRequest(`${backendUrl}/api/check?domain=cloudgofer.com`);
        if (domainResponse.status === 200 && domainResponse.data.domain === 'cloudgofer.com') {
            log('✅ Domain check working', 'green');
            results.domainCheck = {
                status: domainResponse.status,
                domain: domainResponse.data.domain,
                security_score: domainResponse.data.security_score,
                email_provider: domainResponse.data.email_provider
            };
            testsPassed++;
        } else {
            log('❌ Domain check failed', 'red');
            log(`   Status: ${domainResponse.status}`, 'red');
            log(`   Response: ${JSON.stringify(domainResponse.data)}`, 'red');
            testsFailed++;
        }
    } catch (error) {
        log('❌ Domain check failed', 'red');
        log(`   Error: ${error.message}`, 'red');
        testsFailed++;
    }

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Test 4: Frontend Loading
    log(`\n4. Testing Frontend Loading (${frontendUrl})...`, 'yellow');
    try {
        const frontendResponse = await makeRequest(frontendUrl);
        if (frontendResponse.status === 200) {
            log('✅ Frontend loading successful', 'green');
            results.frontend = {
                status: frontendResponse.status,
                content_length: frontendResponse.data.length
            };
            testsPassed++;
        } else {
            log('❌ Frontend loading failed', 'red');
            log(`   Status: ${frontendResponse.status}`, 'red');
            testsFailed++;
        }
    } catch (error) {
        log('❌ Frontend loading failed', 'red');
        log(`   Error: ${error.message}`, 'red');
        testsFailed++;
    }

    await new Promise(resolve => setTimeout(resolve, 1000));

    // Test 5: DKIM Check Endpoint
    log(`\n5. Testing DKIM Check Endpoint...`, 'yellow');
    try {
        const dkimResponse = await makeRequest(`${backendUrl}/api/check/dkim?domain=cloudgofer.com`);
        if (dkimResponse.status === 200) {
            log('✅ DKIM check endpoint working', 'green');
            results.dkimCheck = {
                status: dkimResponse.status,
                success: dkimResponse.data.success
            };
            testsPassed++;
        } else {
            log('❌ DKIM check endpoint failed', 'red');
            log(`   Status: ${dkimResponse.status}`, 'red');
            testsFailed++;
        }
    } catch (error) {
        log('❌ DKIM check endpoint failed', 'red');
        log(`   Error: ${error.message}`, 'red');
        testsFailed++;
    }

    // Summary
    log(`\n📊 ${envName.toUpperCase()} ENVIRONMENT SUMMARY`, 'bright');
    log('=' .repeat(50), 'blue');
    log(`Total Tests: ${testsPassed + testsFailed}`, 'cyan');
    log(`Passed: ${testsPassed}`, 'green');
    log(`Failed: ${testsFailed}`, 'red');
    log(`Success Rate: ${((testsPassed / (testsPassed + testsFailed)) * 100).toFixed(1)}%`, 'cyan');

    return {
        environment: envName,
        testsPassed,
        testsFailed,
        successRate: ((testsPassed / (testsPassed + testsFailed)) * 100).toFixed(1),
        results
    };
}

async function compareEnvironments() {
    log('🚀 AstraVerify Environment Comparison Test', 'bright');
    log('==================================================', 'blue');

    const environments = [
        {
            name: 'LOCAL',
            backend: 'http://localhost:8080',
            frontend: 'http://localhost:3000'
        },
        {
            name: 'STAGE',
            backend: 'https://astraverify-backend-staging-ml2mhibdvq-uc.a.run.app',
            frontend: 'https://astraverify-frontend-staging-ml2mhibdvq-uc.a.run.app'
        },
        {
            name: 'PROD',
            backend: 'https://astraverify-backend-ml2mhibdvq-uc.a.run.app',
            frontend: 'https://astraverify.com'
        }
    ];

    const results = [];

    for (const env of environments) {
        try {
            const result = await testEnvironment(env.name, env.backend, env.frontend);
            results.push(result);
        } catch (error) {
            log(`❌ Failed to test ${env.name} environment: ${error.message}`, 'red');
            results.push({
                environment: env.name,
                testsPassed: 0,
                testsFailed: 5,
                successRate: '0.0',
                results: {},
                error: error.message
            });
        }
        
        // Wait between environments
        await new Promise(resolve => setTimeout(resolve, 2000));
    }

    // Final Comparison
    log('\n🔍 ENVIRONMENT COMPARISON SUMMARY', 'bright');
    log('==================================================', 'blue');
    
    results.forEach(result => {
        const status = result.successRate >= 80 ? '✅' : result.successRate >= 50 ? '⚠️' : '❌';
        log(`${status} ${result.environment}: ${result.successRate}% (${result.testsPassed}/${result.testsPassed + result.testsFailed})`, 
            result.successRate >= 80 ? 'green' : result.successRate >= 50 ? 'yellow' : 'red');
    });

    // Identify differences
    log('\n📋 KEY DIFFERENCES IDENTIFIED', 'bright');
    log('==================================================', 'blue');
    
    const prodResult = results.find(r => r.environment === 'PROD');
    const stageResult = results.find(r => r.environment === 'STAGE');
    const localResult = results.find(r => r.environment === 'LOCAL');

    if (prodResult && stageResult) {
        if (prodResult.successRate < stageResult.successRate) {
            log('⚠️  PROD has lower success rate than STAGE', 'yellow');
        }
        if (prodResult.successRate < localResult?.successRate) {
            log('⚠️  PROD has lower success rate than LOCAL', 'yellow');
        }
    }

    // Specific endpoint differences
    log('\n🔧 SPECIFIC ENDPOINT ANALYSIS', 'bright');
    log('==================================================', 'blue');
    
    results.forEach(result => {
        if (result.results) {
            log(`\n${result.environment}:`, 'cyan');
            Object.entries(result.results).forEach(([endpoint, data]) => {
                const status = data.status === 200 ? '✅' : '❌';
                log(`  ${status} ${endpoint}: ${data.status}`, data.status === 200 ? 'green' : 'red');
            });
        }
    });

    log('\n==================================================', 'blue');
    log('Environment comparison completed!', 'bright');
    log('==================================================', 'blue');
}

// Run the comparison
compareEnvironments().catch(console.error);
