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

// Test production frontend
async function testProductionFrontend() {
    console.log('🔍 Testing Production Frontend...');
    
    const frontendUrl = 'https://astraverify-frontend-ml2mhibdvq-uc.a.run.app';
    const backendUrl = 'https://astraverify-backend-ml2mhibdvq-uc.a.run.app';
    
    try {
        // Test 1: Check if frontend loads
        console.log('\n1. Testing frontend accessibility...');
        const frontendResponse = await fetch(frontendUrl);
        console.log(`Frontend Status: ${frontendResponse.status}`);
        console.log(`Frontend Content-Type: ${frontendResponse.headers.get('content-type')}`);
        
        const frontendHtml = await frontendResponse.text();
        console.log(`Frontend HTML Length: ${frontendHtml.length} characters`);
        
        // Check if React root div exists
        if (frontendHtml.includes('<div id="root"></div>')) {
            console.log('✅ React root div found');
        } else {
            console.log('❌ React root div not found');
        }
        
        // Check if JavaScript files are referenced
        if (frontendHtml.includes('main.a14e80d4.js')) {
            console.log('✅ Main JavaScript file referenced');
        } else {
            console.log('❌ Main JavaScript file not found');
        }
        
        // Test 2: Check if JavaScript file loads
        console.log('\n2. Testing JavaScript file accessibility...');
        const jsUrl = `${frontendUrl}/static/js/main.a14e80d4.js`;
        const jsResponse = await fetch(jsUrl);
        console.log(`JavaScript Status: ${jsResponse.status}`);
        
        if (jsResponse.ok) {
            const jsContent = await jsResponse.text();
            console.log(`JavaScript Content Length: ${jsContent.length} characters`);
            console.log('✅ JavaScript file loads successfully');
        } else {
            console.log('❌ JavaScript file failed to load');
        }
        
        // Test 3: Check backend API
        console.log('\n3. Testing backend API...');
        const apiResponse = await fetch(`${backendUrl}/api/health`);
        console.log(`API Status: ${apiResponse.status}`);
        
        if (apiResponse.ok) {
            const apiData = await apiResponse.json();
            console.log('✅ Backend API working:', apiData);
        } else {
            console.log('❌ Backend API failed');
        }
        
        // Test 4: Test domain check API
        console.log('\n4. Testing domain check API...');
        const domainCheckUrl = `${backendUrl}/api/check?domain=example.com&progressive=true`;
        const domainResponse = await fetch(domainCheckUrl);
        console.log(`Domain Check Status: ${domainResponse.status}`);
        
        if (domainResponse.ok) {
            const domainData = await domainResponse.json();
            console.log('✅ Domain check API working');
            console.log('Response keys:', Object.keys(domainData));
        } else {
            const errorText = await domainResponse.text();
            console.log('❌ Domain check API failed:', errorText.substring(0, 200));
        }
        
        // Test 5: Check CORS headers
        console.log('\n5. Testing CORS configuration...');
        const corsResponse = await fetch(`${backendUrl}/api/health`, {
            method: 'OPTIONS',
            headers: {
                'Origin': frontendUrl,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        });
        
        console.log(`CORS Status: ${corsResponse.status}`);
        console.log(`CORS Origin: ${corsResponse.headers.get('access-control-allow-origin')}`);
        console.log(`CORS Methods: ${corsResponse.headers.get('access-control-allow-methods')}`);
        
        if (corsResponse.headers.get('access-control-allow-origin') === frontendUrl) {
            console.log('✅ CORS configured correctly');
        } else {
            console.log('❌ CORS configuration issue');
        }
        
    } catch (error) {
        console.error('❌ Test failed:', error.message);
    }
}

// Run the test
testProductionFrontend();
