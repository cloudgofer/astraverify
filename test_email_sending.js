const axios = require('axios');

// Production URLs
const PRODUCTION_BACKEND_URL = 'https://astraverify-backend-ml2mhibdvq-uc.a.run.app';

// Test email
const TEST_EMAIL = 'nitin.jain+AstraVerifyProdTest@CloudGofer.com';

console.log('📧 AstraVerify Email Sending Test');
console.log('==================================');
console.log(`Backend URL: ${PRODUCTION_BACKEND_URL}`);
console.log(`Test Email: ${TEST_EMAIL}`);
console.log('');

async function testEmailSending() {
    console.log('1. Testing Email Sending...');
    try {
        // First, get a real domain analysis result
        console.log('   Getting domain analysis for cloudgofer.com...');
        const domainResponse = await axios.get(`${PRODUCTION_BACKEND_URL}/api/check`, {
            params: {
                domain: 'cloudgofer.com'
            }
        });
        
        if (domainResponse.status !== 200) {
            throw new Error('Failed to get domain analysis');
        }
        
        const analysisResult = domainResponse.data;
        console.log(`   Domain analysis completed. Security Score: ${analysisResult.security_score}`);
        
        // Now send the email with the real analysis result
        console.log('   Sending email with analysis results...');
        const emailResponse = await axios.post(`${PRODUCTION_BACKEND_URL}/api/email-report`, {
            email: TEST_EMAIL,
            domain: 'cloudgofer.com',
            analysis_result: analysisResult,
            opt_in_marketing: false
        });
        
        console.log('✅ Email sending test successful');
        console.log(`   Status: ${emailResponse.status}`);
        console.log(`   Success: ${emailResponse.data.success}`);
        console.log(`   Message: ${emailResponse.data.message}`);
        console.log(`   Email Sent: ${emailResponse.data.email_sent}`);
        console.log(`   Email Configured: ${emailResponse.data.email_configured}`);
        
        return true;
    } catch (error) {
        console.log('❌ Email sending test failed');
        console.log(`   Error: ${error.message}`);
        if (error.response) {
            console.log(`   Status: ${error.response.status}`);
            console.log(`   Data: ${JSON.stringify(error.response.data)}`);
        }
        return false;
    }
}

async function testEmailSendingWithDifferentDomain() {
    console.log('\n2. Testing Email Sending with Different Domain...');
    try {
        // Get analysis for a different domain
        console.log('   Getting domain analysis for techstorm.ie...');
        const domainResponse = await axios.get(`${PRODUCTION_BACKEND_URL}/api/check`, {
            params: {
                domain: 'techstorm.ie'
            }
        });
        
        if (domainResponse.status !== 200) {
            throw new Error('Failed to get domain analysis');
        }
        
        const analysisResult = domainResponse.data;
        console.log(`   Domain analysis completed. Security Score: ${analysisResult.security_score}`);
        
        // Send email with different domain results
        console.log('   Sending email with techstorm.ie analysis results...');
        const emailResponse = await axios.post(`${PRODUCTION_BACKEND_URL}/api/email-report`, {
            email: TEST_EMAIL,
            domain: 'techstorm.ie',
            analysis_result: analysisResult,
            opt_in_marketing: false
        });
        
        console.log('✅ Email sending with different domain successful');
        console.log(`   Status: ${emailResponse.status}`);
        console.log(`   Success: ${emailResponse.data.success}`);
        console.log(`   Message: ${emailResponse.data.message}`);
        
        return true;
    } catch (error) {
        console.log('❌ Email sending with different domain failed');
        console.log(`   Error: ${error.message}`);
        if (error.response) {
            console.log(`   Status: ${error.response.status}`);
            console.log(`   Data: ${JSON.stringify(error.response.data)}`);
        }
        return false;
    }
}

async function testEmailValidation() {
    console.log('\n3. Testing Email Validation...');
    try {
        // Test with invalid email format
        console.log('   Testing invalid email format...');
        const response = await axios.post(`${PRODUCTION_BACKEND_URL}/api/email-report`, {
            email: 'invalid-email',
            domain: 'cloudgofer.com',
            analysis_result: {
                security_score: 85,
                mx: { enabled: true, status: 'Valid' },
                spf: { enabled: true, status: 'Valid' },
                dkim: { enabled: true, status: 'Valid' },
                dmarc: { enabled: true, status: 'Valid' }
            }
        });
        
        console.log('❌ Email validation test failed - should have rejected invalid email');
        return false;
    } catch (error) {
        if (error.response && error.response.status === 400) {
            console.log('✅ Email validation working correctly');
            console.log(`   Status: ${error.response.status}`);
            console.log(`   Error: ${error.response.data.error}`);
            return true;
        } else {
            console.log('❌ Email validation test failed');
            console.log(`   Error: ${error.message}`);
            return false;
        }
    }
}

async function runEmailTests() {
    console.log('Starting email sending tests...\n');
    
    const results = {
        emailSending: await testEmailSending(),
        differentDomain: await testEmailSendingWithDifferentDomain(),
        emailValidation: await testEmailValidation()
    };
    
    // Summary
    console.log('\n📊 Email Test Summary');
    console.log('=====================');
    console.log(`Email Sending: ${results.emailSending ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`Different Domain: ${results.differentDomain ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`Email Validation: ${results.emailValidation ? '✅ PASS' : '❌ FAIL'}`);
    
    const allPassed = results.emailSending && results.differentDomain && results.emailValidation;
    
    console.log(`\nOverall Result: ${allPassed ? '✅ ALL EMAIL TESTS PASSED' : '❌ SOME EMAIL TESTS FAILED'}`);
    
    if (allPassed) {
        console.log('\n🎉 Email functionality is working correctly!');
        console.log('✅ Email sending is operational');
        console.log('✅ Email validation is working');
        console.log('✅ Multiple domains supported');
        console.log(`📧 Test emails sent to: ${TEST_EMAIL}`);
        console.log('Please check your email inbox for the test emails.');
    } else {
        console.log('\n⚠️  Some email issues detected');
        console.log('Please review the failed tests above');
    }
}

// Run the tests
runEmailTests().catch(console.error);
