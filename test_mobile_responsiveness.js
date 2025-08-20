// Mobile Responsiveness Test Suite
// Tests UI on different screen sizes and devices

const puppeteer = require('puppeteer');
const fs = require('fs');

const STAGING_FRONTEND_URL = 'https://astraverify-frontend-staging-ml2mhibdvq-uc.a.run.app';

// Test viewports for different devices
const VIEWPORTS = [
    { width: 375, height: 667, name: 'iPhone SE', device: 'mobile' },
    { width: 414, height: 896, name: 'iPhone 11', device: 'mobile' },
    { width: 768, height: 1024, name: 'iPad', device: 'tablet' },
    { width: 1024, height: 768, name: 'iPad Landscape', device: 'tablet' },
    { width: 1366, height: 768, name: 'Laptop', device: 'desktop' },
    { width: 1920, height: 1080, name: 'Desktop', device: 'desktop' }
];

// Test scenarios
const TEST_SCENARIOS = [
    {
        name: 'Homepage Load',
        action: async (page) => {
            await page.goto(STAGING_FRONTEND_URL, { waitUntil: 'networkidle2' });
            return { success: true, message: 'Homepage loaded successfully' };
        }
    },
    {
        name: 'Domain Input Test',
        action: async (page) => {
            await page.goto(STAGING_FRONTEND_URL, { waitUntil: 'networkidle2' });
            
            // Find and fill domain input
            const inputSelector = 'input[type="text"], input[placeholder*="domain"], #domain-input, .domain-input';
            const input = await page.$(inputSelector);
            
            if (!input) {
                return { success: false, message: 'Domain input field not found' };
            }
            
            await input.type('gmail.com');
            await page.waitForTimeout(1000);
            
            return { success: true, message: 'Domain input working' };
        }
    },
    {
        name: 'Form Submission Test',
        action: async (page) => {
            await page.goto(STAGING_FRONTEND_URL, { waitUntil: 'networkidle2' });
            
            // Find and fill domain input
            const inputSelector = 'input[type="text"], input[placeholder*="domain"], #domain-input, .domain-input';
            const input = await page.$(inputSelector);
            
            if (!input) {
                return { success: false, message: 'Domain input field not found' };
            }
            
            await input.type('gmail.com');
            
            // Find and click submit button
            const submitSelector = 'button[type="submit"], button:contains("Check"), .submit-btn, #submit-btn';
            const submitButton = await page.$(submitSelector);
            
            if (!submitButton) {
                return { success: false, message: 'Submit button not found' };
            }
            
            await submitButton.click();
            
            // Wait for response
            await page.waitForTimeout(3000);
            
            // Check for results or loading state
            const hasResults = await page.evaluate(() => {
                return document.querySelector('.results, .analysis-results, [data-testid="results"]') !== null;
            });
            
            if (hasResults) {
                return { success: true, message: 'Form submission successful' };
            } else {
                return { success: false, message: 'No results found after submission' };
            }
        }
    },
    {
        name: 'Navigation Test',
        action: async (page) => {
            await page.goto(STAGING_FRONTEND_URL, { waitUntil: 'networkidle2' });
            
            // Check for navigation elements
            const navElements = await page.evaluate(() => {
                const navs = document.querySelectorAll('nav, .nav, .navigation, header');
                return navs.length > 0;
            });
            
            if (navElements) {
                return { success: true, message: 'Navigation elements present' };
            } else {
                return { success: false, message: 'No navigation elements found' };
            }
        }
    },
    {
        name: 'Responsive Layout Test',
        action: async (page) => {
            await page.goto(STAGING_FRONTEND_URL, { waitUntil: 'networkidle2' });
            
            // Check for responsive design indicators
            const responsiveIndicators = await page.evaluate(() => {
                const viewport = document.querySelector('meta[name="viewport"]');
                const hasFlexbox = document.querySelector('.flex, [style*="display: flex"], [style*="display:flex"]') !== null;
                const hasGrid = document.querySelector('.grid, [style*="display: grid"], [style*="display:grid"]') !== null;
                const hasMediaQueries = document.querySelector('style') !== null;
                
                return {
                    hasViewport: !!viewport,
                    hasFlexbox,
                    hasGrid,
                    hasMediaQueries
                };
            });
            
            if (responsiveIndicators.hasViewport) {
                return { 
                    success: true, 
                    message: 'Responsive design indicators present',
                    details: responsiveIndicators
                };
            } else {
                return { 
                    success: false, 
                    message: 'Missing viewport meta tag',
                    details: responsiveIndicators
                };
            }
        }
    }
];

// Test results storage
let testResults = {
    viewports: {},
    scenarios: {},
    screenshots: [],
    summary: { passed: 0, failed: 0, total: 0 }
};

// Utility functions
function log(message, type = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = type === 'error' ? '❌' : type === 'success' ? '✅' : type === 'warning' ? '⚠️' : 'ℹ️';
    console.log(`${prefix} [${timestamp}] ${message}`);
}

async function takeScreenshot(page, viewport, scenario, testName) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `screenshots/${viewport.name}-${scenario}-${testName}-${timestamp}.png`;
    
    // Create screenshots directory if it doesn't exist
    if (!fs.existsSync('screenshots')) {
        fs.mkdirSync('screenshots');
    }
    
    await page.screenshot({ 
        path: filename, 
        fullPage: true 
    });
    
    testResults.screenshots.push({
        filename,
        viewport: viewport.name,
        scenario,
        testName,
        timestamp
    });
    
    log(`Screenshot saved: ${filename}`, 'success');
}

async function testViewport(browser, viewport) {
    log(`Testing viewport: ${viewport.name} (${viewport.width}x${viewport.height})`);
    
    const page = await browser.newPage();
    await page.setViewport({
        width: viewport.width,
        height: viewport.height,
        deviceScaleFactor: 1,
        isMobile: viewport.device === 'mobile',
        hasTouch: viewport.device === 'mobile'
    });
    
    // Set user agent for mobile devices
    if (viewport.device === 'mobile') {
        await page.setUserAgent('Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1');
    }
    
    const viewportResults = {};
    
    for (const scenario of TEST_SCENARIOS) {
        log(`  Running scenario: ${scenario.name}`);
        
        try {
            const result = await scenario.action(page);
            viewportResults[scenario.name] = result;
            
            if (result.success) {
                log(`    ✅ ${scenario.name} passed`, 'success');
                testResults.summary.passed++;
            } else {
                log(`    ❌ ${scenario.name} failed: ${result.message}`, 'error');
                testResults.summary.failed++;
            }
            
            // Take screenshot
            await takeScreenshot(page, viewport, scenario.name, result.success ? 'success' : 'failed');
            
            testResults.summary.total++;
            
        } catch (error) {
            log(`    ❌ ${scenario.name} error: ${error.message}`, 'error');
            viewportResults[scenario.name] = { success: false, message: error.message };
            testResults.summary.failed++;
            testResults.summary.total++;
            
            // Take screenshot of error state
            await takeScreenshot(page, viewport, scenario.name, 'error');
        }
        
        // Wait between scenarios
        await page.waitForTimeout(1000);
    }
    
    await page.close();
    testResults.viewports[viewport.name] = viewportResults;
    
    return viewportResults;
}

async function generateReport() {
    log('=== Mobile Responsiveness Test Report ===');
    
    const report = {
        timestamp: new Date().toISOString(),
        environment: 'STAGING',
        frontendUrl: STAGING_FRONTEND_URL,
        summary: {
            total: testResults.summary.total,
            passed: testResults.summary.passed,
            failed: testResults.summary.failed,
            successRate: ((testResults.summary.passed / testResults.summary.total) * 100).toFixed(2) + '%'
        },
        viewports: testResults.viewports,
        screenshots: testResults.screenshots
    };
    
    console.log('\n📱 MOBILE RESPONSIVENESS TEST REPORT');
    console.log('====================================');
    console.log(`Environment: ${report.environment}`);
    console.log(`Frontend URL: ${report.frontendUrl}`);
    console.log(`Timestamp: ${report.timestamp}`);
    console.log(`Success Rate: ${report.summary.successRate}`);
    console.log(`Total Tests: ${report.summary.total}`);
    console.log(`Passed: ${report.summary.passed}`);
    console.log(`Failed: ${report.summary.failed}`);
    
    console.log('\n📱 Viewport Results:');
    Object.entries(testResults.viewports).forEach(([viewport, scenarios]) => {
        console.log(`\n  ${viewport}:`);
        Object.entries(scenarios).forEach(([scenario, result]) => {
            const status = result.success ? '✅' : '❌';
            console.log(`    ${status} ${scenario}: ${result.message}`);
        });
    });
    
    console.log('\n📸 Screenshots:');
    testResults.screenshots.forEach(screenshot => {
        console.log(`  📷 ${screenshot.filename} (${screenshot.viewport} - ${screenshot.scenario})`);
    });
    
    return report;
}

async function runMobileTests() {
    log('🚀 Starting Mobile Responsiveness Tests');
    log(`Frontend URL: ${STAGING_FRONTEND_URL}`);
    
    let browser;
    
    try {
        // Launch browser
        browser = await puppeteer.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        });
        
        log('Browser launched successfully', 'success');
        
        // Test each viewport
        for (const viewport of VIEWPORTS) {
            await testViewport(browser, viewport);
            await new Promise(resolve => setTimeout(resolve, 2000)); // Wait between viewports
        }
        
        // Generate and display report
        const report = generateReport();
        
        // Save report to file
        fs.writeFileSync('mobile_responsiveness_test_report.json', JSON.stringify(report, null, 2));
        log('Test report saved to mobile_responsiveness_test_report.json', 'success');
        
        // Exit with appropriate code
        if (testResults.summary.failed === 0) {
            log('🎉 All mobile tests passed!', 'success');
            process.exit(0);
        } else {
            log(`⚠️ ${testResults.summary.failed} mobile tests failed`, 'warning');
            process.exit(1);
        }
        
    } catch (error) {
        log(`Mobile test suite error: ${error.message}`, 'error');
        process.exit(1);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

// Run tests if this script is executed directly
if (require.main === module) {
    runMobileTests();
}

module.exports = {
    runMobileTests,
    testResults,
    VIEWPORTS,
    TEST_SCENARIOS
};
