// Test script to verify DKIM scoring fix
const testDomain = 'predikly.com';

async function testDKIMScoring() {
    try {
        console.log('Testing DKIM scoring for domain:', testDomain);
        
        const response = await fetch(`http://localhost:5000/analyze?domain=${testDomain}`);
        const data = await response.json();
        
        console.log('Response received');
        console.log('Security score:', data.security_score);
        
        if (data.security_score && data.security_score.scoring_details) {
            const dkim = data.security_score.scoring_details;
            console.log('DKIM Base Score:', dkim.dkim_base);
            console.log('DKIM Bonus Score:', dkim.dkim_bonus);
            console.log('Expected DKIM Max: 20');
            console.log('Actual DKIM Base:', dkim.dkim_base);
            
            if (dkim.dkim_base === 25) {
                console.log('❌ ISSUE: DKIM base score is still 25 (should be 20)');
            } else if (dkim.dkim_base === 20) {
                console.log('✅ FIXED: DKIM base score is now 20');
            } else {
                console.log('⚠️ UNKNOWN: DKIM base score is', dkim.dkim_base);
            }
        } else {
            console.log('❌ No scoring details found in response');
        }
        
    } catch (error) {
        console.error('Error testing DKIM scoring:', error);
    }
}

// Run the test
testDKIMScoring();
