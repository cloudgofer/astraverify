import React, { useState, useCallback, useEffect } from 'react';
import config from './config';
import './App.css';

function App() {
  const [domain, setDomain] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [emailAddress, setEmailAddress] = useState('');
  const [emailOptIn, setEmailOptIn] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailSending, setEmailSending] = useState(false);
  const [expandedComponents, setExpandedComponents] = useState({});
  const [isEditing, setIsEditing] = useState(false);
  const [statistics, setStatistics] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);

  const updateURL = (domain) => {
    const url = new URL(window.location);
    url.searchParams.set('domain', domain);
    window.history.replaceState({}, '', url);
  };

  const checkDomain = useCallback(async (domainToCheck = null) => {
    const domainValue = domainToCheck || domain.trim();
    
    if (!domainValue) {
      setError('Please enter a domain name');
      return;
    }

    console.log('🔍 DEBUG: Starting domain check for:', domainValue);
    console.log('🔍 DEBUG: Config API_BASE_URL:', config.API_BASE_URL);
    console.log('🔍 DEBUG: Config ENDPOINTS:', config.ENDPOINTS);

    setLoading(true);
    setError(null);
    setResult(null);
    setExpandedComponents({});

    updateURL(domainValue);

    try {
      const progressiveUrl = `${config.API_BASE_URL}${config.ENDPOINTS.CHECK_DOMAIN}?domain=${encodeURIComponent(domainValue)}&progressive=true`;
      console.log('🔍 DEBUG: Progressive URL:', progressiveUrl);
      console.log('🔍 DEBUG: Making fetch request...');
      
      // Test if fetch is available
      if (typeof fetch === 'undefined') {
        throw new Error('Fetch API is not available in this environment');
      }

      // Test network connectivity first
      try {
        console.log('🔍 DEBUG: Testing basic connectivity...');
        const testResponse = await fetch(config.API_BASE_URL, { 
          method: 'HEAD',
          mode: 'cors'
        });
        console.log('🔍 DEBUG: Basic connectivity test result:', testResponse.status);
      } catch (connectivityError) {
        console.error('🔍 DEBUG: Connectivity test failed:', connectivityError);
        throw new Error(`Network connectivity issue: ${connectivityError.message}`);
      }
      
      const progressiveResponse = await fetch(progressiveUrl, {
        method: 'GET',
        mode: 'cors',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      
      console.log('🔍 DEBUG: Progressive response received:', {
        status: progressiveResponse.status,
        ok: progressiveResponse.ok,
        statusText: progressiveResponse.statusText,
        headers: Object.fromEntries(progressiveResponse.headers.entries())
      });
      
      if (!progressiveResponse.ok) {
        const errorText = await progressiveResponse.text();
        console.error('🔍 DEBUG: Progressive response error:', progressiveResponse.status, errorText);
        throw new Error(`HTTP error! status: ${progressiveResponse.status} - ${errorText.substring(0, 100)}`);
      }
      
      const contentType = progressiveResponse.headers.get('content-type');
      console.log('🔍 DEBUG: Content-Type:', contentType);
      
      if (!contentType || !contentType.includes('application/json')) {
        const text = await progressiveResponse.text();
        console.error('🔍 DEBUG: Non-JSON progressive response:', text);
        throw new Error(`Expected JSON but got ${contentType}. Response: ${text.substring(0, 200)}`);
      }
      
      const progressiveData = await progressiveResponse.json();
      progressiveData.analysis_timestamp = new Date().toISOString();
      console.log('🔍 DEBUG: Progressive data received:', progressiveData);
      setResult(progressiveData);
      
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const dkimUrl = `${config.API_BASE_URL}/api/check/dkim?domain=${encodeURIComponent(domainValue)}`;
      console.log('🔍 DEBUG: Making DKIM completion request to:', dkimUrl);
      
      const dkimResponse = await fetch(dkimUrl);
      
      if (dkimResponse.ok) {
        const dkimData = await dkimResponse.json();
        console.log('🔍 DEBUG: DKIM data received:', dkimData);
        
        setResult(prevResult => ({
          ...prevResult,
          dkim: dkimData.dkim,
          email_provider: dkimData.email_provider,
          security_score: dkimData.security_score,
          progressive: false,
          message: `Analysis complete! Checked ${dkimData.dkim.selectors_checked || 0} DKIM selectors.`
        }));
      } else {
        console.error('🔍 DEBUG: DKIM completion failed:', dkimResponse.status);
        setResult(prevResult => ({
          ...prevResult,
          dkim: {
            ...prevResult.dkim,
            status: "Error",
            description: "DKIM check failed",
            checking: false
          }
        }));
      }
    } catch (error) {
      console.error('🔍 DEBUG: Error checking domain:', error);
      console.error('🔍 DEBUG: Error name:', error.name);
      console.error('🔍 DEBUG: Error message:', error.message);
      console.error('🔍 DEBUG: Error stack:', error.stack);
      
      // Provide more specific error messages
      let errorMessage = error.message;
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        errorMessage = 'Network request failed. Please check your internet connection and try again.';
      } else if (error.message.includes('Failed to fetch')) {
        errorMessage = 'Unable to connect to the server. Please ensure the backend is running and try again.';
      } else if (error.message.includes('CORS')) {
        errorMessage = 'Cross-origin request blocked. Please check server configuration.';
      }
      
      setError(`Error analyzing domain: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, [domain]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      checkDomain();
    }
  };

  const toggleComponent = (componentName) => {
    setExpandedComponents(prev => ({
      ...prev,
      [componentName]: !prev[componentName]
    }));
  };

  const getScoreColor = (score) => {
    if (score >= 90) return '#4CAF50';
    if (score >= 75) return '#8BC34A';
    if (score >= 50) return '#FFC107';
    if (score >= 25) return '#FF9800';
    return '#F44336';
  };

  const getScoreGrade = (score) => {
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  };

  const getScoreStatus = (score) => {
    if (score >= 90) return 'Excellent';
    if (score >= 80) return 'Good';
    if (score >= 70) return 'Fair';
    if (score >= 60) return 'Poor';
    return 'Critical';
  };

  const getComponentScore = (base, bonus = 0) => {
    return Math.min(100, base + bonus);
  };

  const getComponentIcon = (enabled, score) => {
    if (!enabled) return '❌';
    if (score >= 90) return '✅';
    if (score >= 70) return '⚠️';
    return '❌';
  };

  const getRecommendationIcon = (type) => {
    switch (type) {
      case 'critical': return '🚨';
      case 'important': return '⚠️';
      case 'info': return 'ℹ️';
      default: return '💡';
    }
  };

  const getComponentDescription = (componentName) => {
    const descriptions = {
      mx: 'Mail Exchange records route email to your domain',
      spf: 'Sender Policy Framework prevents email spoofing',
      dkim: 'DomainKeys Identified Mail provides email authentication',
      dmarc: 'Domain-based Message Authentication, Reporting & Conformance'
    };
    return descriptions[componentName] || '';
  };

  const renderRecords = (componentName, records) => {
    if (!records || records.length === 0) {
      return <p className="text-gray-500">No records found</p>;
    }

    return (
      <div className="space-y-2">
        {records.map((record, index) => (
          <div key={index} className="bg-gray-50 p-3 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm break-all">{record.record || record.full_record}</span>
              <span className={`ml-2 px-2 py-1 text-xs rounded ${
                record.valid ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {record.valid ? 'Valid' : 'Invalid'}
              </span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const domainParam = urlParams.get('domain');
    if (domainParam && !domain && !loading && !isEditing) {
      setDomain(domainParam);
      setTimeout(() => {
        checkDomain(domainParam);
      }, 500);
    }
  }, []); // Only run once on mount

  useEffect(() => {
    const fetchStatistics = async () => {
      try {
        const response = await fetch(`${config.API_BASE_URL}/api/statistics`);
        if (response.ok) {
          const data = await response.json();
          setStatistics(data);
        }
      } catch (error) {
        console.error('Error fetching statistics:', error);
      } finally {
        setStatsLoading(false);
      }
    };

    fetchStatistics();
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>{config.APP_NAME}</h1>
        <p>{config.APP_DESCRIPTION}</p>
      </header>
      
      <main className="App-main">
        <form 
          className="input-section" 
          onSubmit={(e) => {
            e.preventDefault();
            checkDomain();
          }}
          aria-label="Analyze email domain security"
        >
          <div className="input-wrapper">
            <label htmlFor="domain-input" className="sr-only">
              Enter domain name
            </label>
            <input
              id="domain-input"
              name="domain"
              type="text"
              inputMode="url"
              value={domain}
              onChange={(e) => {
                setIsEditing(true);
                setDomain(e.target.value);
              }}
              onFocus={() => setIsEditing(true)}
              onBlur={() => setTimeout(() => setIsEditing(false), 100)}
              onKeyPress={handleKeyPress}
              placeholder="example.com"
              className="domain-input"
              disabled={loading}
              aria-label="Enter a domain to analyze"
              aria-describedby="domain-input-help"
            />
            <div id="domain-input-help" className="sr-only">
              Enter a domain name without http:// or www
            </div>
          </div>
          
          <button 
            type="submit"
            disabled={loading || !domain.trim()}
            className="check-button"
            aria-busy={loading ? "true" : "false"}
          >
            {loading ? 'Analyzing...' : 'Analyze Domain'}
          </button>
        </form>

        {error && (
          <div className="error-message">
            <h3>🔍 Debug Information:</h3>
            <p><strong>Error:</strong> {error}</p>
            <p><strong>API Base URL:</strong> {config.API_BASE_URL}</p>
            <p><strong>Endpoint:</strong> {config.ENDPOINTS.CHECK_DOMAIN}</p>
            <p><strong>Current URL:</strong> {window.location.href}</p>
            <p><strong>User Agent:</strong> {navigator.userAgent}</p>
            <p><strong>Fetch Available:</strong> {typeof fetch !== 'undefined' ? 'Yes' : 'No'}</p>
          </div>
        )}

        {result && (
          <div className="results-section">
            {/* Results content would go here */}
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
