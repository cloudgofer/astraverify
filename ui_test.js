const puppeteer = require('puppeteer');

// Device configurations
const devices = {
  phone: {
    name: 'iPhone 12',
    width: 390,
    height: 844,
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'
  },
  tablet: {
    name: 'iPad Pro',
    width: 1024,
    height: 1366,
    userAgent: 'Mozilla/5.0 (iPad; CPU OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1'
  },
  desktop: {
    name: 'Desktop',
    width: 1920,
    height: 1080,
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
  }
};

// Test domains
const testDomains = [
  'cloudgofer.com', // High score domain
  'example.com',     // Low score domain
  'nonexistentdomain123456789.com' // Domain with missing records
];

async function runUITests() {
  const browser = await puppeteer.launch({ 
    headless: false, // Set to true for CI/CD
    defaultViewport: null,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  console.log('🚀 Starting UI Tests for AstraVerify...\n');

  for (const [deviceType, device] of Object.entries(devices)) {
    console.log(`📱 Testing on ${device.name} (${device.width}x${device.height})`);
    console.log('='.repeat(50));

    const page = await browser.newPage();
    await page.setViewport({ width: device.width, height: device.height });
    await page.setUserAgent(device.userAgent);

    try {
      // Navigate to the application
      await page.goto('https://astraverify-frontend-ml2mhibdvq-uc.a.run.app', { 
        waitUntil: 'networkidle2',
        timeout: 30000 
      });

      // Test 1: Initial Page Load
      console.log('✅ Testing initial page load...');
      await testInitialPageLoad(page, deviceType);

      // Test 2: Input Field Responsiveness
      console.log('✅ Testing input field responsiveness...');
      await testInputFieldResponsiveness(page, deviceType);

      // Test 3: Domain Analysis Functionality
      console.log('✅ Testing domain analysis functionality...');
      for (const domain of testDomains) {
        await testDomainAnalysis(page, domain, deviceType);
      }

      // Test 4: Score Breakdown Display
      console.log('✅ Testing score breakdown display...');
      await testScoreBreakdown(page, deviceType);

      // Test 5: Statistics Section
      console.log('✅ Testing statistics section...');
      await testStatisticsSection(page, deviceType);

      // Test 6: Mobile-Specific Features
      if (deviceType === 'phone') {
        console.log('✅ Testing mobile-specific features...');
        await testMobileFeatures(page);
      }

      console.log(`✅ All tests passed for ${device.name}\n`);

    } catch (error) {
      console.error(`❌ Test failed for ${device.name}:`, error.message);
    } finally {
      await page.close();
    }
  }

  await browser.close();
  console.log('🎉 UI Testing completed!');
}

async function testInitialPageLoad(page, deviceType) {
  // Check if main elements are visible
  await page.waitForSelector('.App', { timeout: 10000 });
  
  const header = await page.$('.header h1');
  const input = await page.$('.domain-input');
  const button = await page.$('.check-button');
  
  if (!header || !input || !button) {
    throw new Error('Essential UI elements not found');
  }

  // Check header text
  const headerText = await page.$eval('.header h1', el => el.textContent);
  if (!headerText.includes('AstraVerify')) {
    throw new Error('Header text not found');
  }

  console.log(`   ✓ Page loaded successfully on ${deviceType}`);
}

async function testInputFieldResponsiveness(page, deviceType) {
  const input = await page.$('.domain-input');
  
  // Get input dimensions and position
  const inputBox = await input.boundingBox();
  
  // Check if input is within viewport
  const viewport = await page.viewport();
  
  if (deviceType === 'phone') {
    // On mobile, input should be full width
    if (inputBox.width < viewport.width * 0.8) {
      throw new Error('Input field not properly sized for mobile');
    }
  }
  
  // Test input functionality
  await input.click();
  await input.type('test.com');
  const inputValue = await page.$eval('.domain-input', el => el.value);
  
  if (inputValue !== 'test.com') {
    throw new Error('Input field not working properly');
  }
  
  // Clear input
  await input.click({ clickCount: 3 });
  await input.type('');
  
  console.log(`   ✓ Input field responsive on ${deviceType}`);
}

async function testDomainAnalysis(page, domain, deviceType) {
  // Type domain and submit
  await page.type('.domain-input', domain);
  await page.click('.check-button');
  
  // Wait for analysis to complete
  await page.waitForFunction(() => {
    const result = document.querySelector('.result-section');
    return result && !result.querySelector('.loading-spinner');
  }, { timeout: 30000 });
  
  // Check if results are displayed
  const resultSection = await page.$('.result-section');
  if (!resultSection) {
    throw new Error(`No results displayed for ${domain}`);
  }
  
  // Check security score
  const scoreElement = await page.$('.security-score');
  if (!scoreElement) {
    throw new Error('Security score not displayed');
  }
  
  console.log(`   ✓ Domain analysis completed for ${domain} on ${deviceType}`);
}

async function testScoreBreakdown(page, deviceType) {
  // Wait for score breakdown to be visible
  await page.waitForSelector('.score-breakdown', { timeout: 10000 });
  
  // Check if all components are displayed
  const components = ['MX Records', 'SPF Records', 'DMARC Records', 'DKIM Records'];
  
  for (const component of components) {
    const element = await page.$(`text=${component}`);
    if (!element) {
      throw new Error(`Score breakdown component not found: ${component}`);
    }
  }
  
  // Check color coding (green for positive, red for zero)
  const scoreElements = await page.$$('.component-score');
  for (const element of scoreElements) {
    const text = await element.evaluate(el => el.textContent);
    const className = await element.evaluate(el => el.className);
    
    const score = parseInt(text);
    if (score === 0 && !className.includes('zero')) {
      throw new Error('Zero score not colored red');
    }
    if (score > 0 && className.includes('zero')) {
      throw new Error('Positive score incorrectly colored red');
    }
  }
  
  // Check bonus points color (should be green)
  const bonusElements = await page.$$('.bonus-indicator');
  for (const element of bonusElements) {
    const color = await element.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return styles.color;
    });
    
    if (!color.includes('rgb(76, 175, 80)')) { // #4CAF50
      throw new Error('Bonus points not colored green');
    }
  }
  
  console.log(`   ✓ Score breakdown properly displayed on ${deviceType}`);
}

async function testStatisticsSection(page, deviceType) {
  // Wait for statistics to load
  await page.waitForFunction(() => {
    const stats = document.querySelector('.statistics-section');
    return stats && !stats.querySelector('.loading-spinner');
  }, { timeout: 10000 });
  
  // Check if statistics are displayed
  const statsSection = await page.$('.statistics-section');
  if (!statsSection) {
    throw new Error('Statistics section not found');
  }
  
  // Check for key statistics
  const statCards = await page.$$('.stat-card');
  if (statCards.length < 3) {
    throw new Error('Not enough statistics cards displayed');
  }
  
  console.log(`   ✓ Statistics section properly displayed on ${deviceType}`);
}

async function testMobileFeatures(page) {
  // Test touch interactions
  const input = await page.$('.domain-input');
  await input.tap();
  
  // Test button touch
  const button = await page.$('.check-button');
  await button.tap();
  
  // Check if mobile-specific styles are applied
  const appElement = await page.$('.App');
  const styles = await appElement.evaluate(el => {
    const computed = window.getComputedStyle(el);
    return {
      padding: computed.padding,
      maxWidth: computed.maxWidth
    };
  });
  
  // Mobile should have appropriate padding
  if (parseInt(styles.padding) < 10) {
    throw new Error('Mobile padding not applied correctly');
  }
  
  console.log('   ✓ Mobile-specific features working correctly');
}

// Run the tests
if (require.main === module) {
  runUITests().catch(console.error);
}

module.exports = { runUITests };
