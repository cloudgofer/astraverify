import React, { useState, useEffect, useCallback } from 'react';
import config from './config';
import './App.css';

function App() {
  const [domain, setDomain] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedComponents, setExpandedComponents] = useState({});
  const [statistics, setStatistics] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [emailAddress, setEmailAddress] = useState('');
  const [emailOptIn, setEmailOptIn] = useState(false);
  const [emailSending, setEmailSending] = useState(false);

  const updateURL = (domain) => {
    const url = new URL(window.location);
    if (domain) {
      url.searchParams.set('domain', domain);
    } else {
      url.searchParams.delete('domain');
    }
    window.history.pushState({}, '', url);
  };

  const checkDomain = useCallback(async (domainToCheck = null) => {
    const domainValue = domainToCheck || domain.trim();
    
    if (!domainValue) {
      setError('Please enter a domain name');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setExpandedComponents({});

    updateURL(domainValue);

    try {
      const progressiveUrl = `${config.API_BASE_URL}${config.ENDPOINTS.CHECK_DOMAIN}?domain=${encodeURIComponent(domainValue)}&progressive=true`;
      console.log('PROGRESSIVE LOADING: Making progressive request to:', progressiveUrl);
      
      const progressiveResponse = await fetch(progressiveUrl);
      
      if (!progressiveResponse.ok) {
        const errorText = await progressiveResponse.text();
        console.error('Progressive response error:', progressiveResponse.status, errorText);
        throw new Error(`HTTP error! status: ${progressiveResponse.status} - ${errorText.substring(0, 100)}`);
      }
      
      const contentType = progressiveResponse.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await progressiveResponse.text();
        console.error('Non-JSON progressive response:', text);
        throw new Error(`Expected JSON but got ${contentType}. Response: ${text.substring(0, 200)}`);
      }
      
      const progressiveData = await progressiveResponse.json();
      progressiveData.analysis_timestamp = new Date().toISOString();
      console.log('PROGRESSIVE LOADING: Received progressive data:', progressiveData);
      setResult(progressiveData);
      
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const dkimUrl = `${config.API_BASE_URL}/api/check/dkim?domain=${encodeURIComponent(domainValue)}`;
      console.log('Making DKIM completion request to:', dkimUrl);
      
      const dkimResponse = await fetch(dkimUrl);
      
      if (dkimResponse.ok) {
        const dkimData = await dkimResponse.json();
        
        setResult(prevResult => ({
          ...prevResult,
          dkim: dkimData.dkim,
          email_provider: dkimData.email_provider,
          security_score: dkimData.security_score,
          progressive: false,
          message: `Analysis complete! Checked ${dkimData.dkim.selectors_checked || 0} DKIM selectors.`
        }));
      } else {
        console.error('DKIM completion failed:', dkimResponse.status);
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
      console.error('Error checking domain:', error);
      setError(`Error analyzing domain: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }, [domain]);

  const sendEmailReport = async () => {
    if (!emailAddress.trim()) {
      return;
    }

    setEmailSending(true);
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/send-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: emailAddress,
          domain: domain,
          result: result,
          opt_in: emailOptIn
        }),
      });

      if (response.ok) {
        alert('Email report sent successfully!');
        setShowEmailModal(false);
        setEmailAddress('');
        setEmailOptIn(false);
      } else {
        const errorData = await response.json();
        alert(`Failed to send email: ${errorData.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Error sending email report:', error);
      alert('Failed to send email report. Please try again.');
    } finally {
      setEmailSending(false);
    }
  };

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
    if (score >= 90) return '#10B981'; // green-500
    if (score >= 75) return '#3B82F6'; // blue-500
    if (score >= 50) return '#F59E0B'; // amber-500
    return '#EF4444'; // red-500
  };

  const getScoreGrade = (score) => {
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  };

  const getScoreStatus = (score) => {
    if (score >= 90) return 'Outstanding email security. Your domain is extremely well-protected.';
    if (score >= 75) return 'Good email security. Your domain is well-protected.';
    if (score >= 50) return 'Fair email security. Some improvements recommended.';
    return 'Poor email security. Immediate action required.';
  };

  const getComponentScore = (base, bonus = 0) => {
    return base + bonus;
  };

  const getComponentIcon = (enabled, score) => {
    if (enabled) {
      if (score >= 20) return '✅';
      if (score >= 10) return '⚠️';
      return '❌';
    }
    return '❌';
  };

  const getRecommendationIcon = (type) => {
    switch (type) {
      case 'critical': return '🔴';
      case 'important': return '🟡';
      case 'suggestion': return '🔵';
      default: return 'ℹ️';
    }
  };

  const getComponentDescription = (componentName) => {
    const descriptions = {
      mx: {
        title: 'Mail Exchange Records',
        description: 'MX records specify which mail servers are responsible for receiving email for your domain.',
        successMessage: 'Your domain has properly configured MX records.',
        failureMessage: 'Your domain is missing MX records or they are incorrectly configured.'
      },
      spf: {
        title: 'Sender Policy Framework',
        description: 'SPF records help prevent email spoofing by specifying which servers are authorized to send email from your domain.',
        successMessage: 'Your domain has SPF records configured.',
        failureMessage: 'Your domain is missing SPF records, making it vulnerable to email spoofing.'
      },
      dkim: {
        title: 'DomainKeys Identified Mail',
        description: 'DKIM adds a digital signature to outgoing emails to verify they came from your domain.',
        successMessage: 'Your domain has DKIM configured.',
        failureMessage: 'Your domain is missing DKIM configuration.'
      },
      dmarc: {
        title: 'Domain-based Message Authentication',
        description: 'DMARC tells receiving servers what to do with emails that fail SPF or DKIM checks.',
        successMessage: 'Your domain has DMARC configured.',
        failureMessage: 'Your domain is missing DMARC configuration.'
      }
    };
    return descriptions[componentName] || {};
  };

  const renderRecords = (componentName, records) => {
    if (!records || records.length === 0) {
      return <div className="no-records">No records found</div>;
    }

    return (
      <div className="records-list">
        {records.map((record, index) => (
          <div key={index} className="record-item">
            {componentName === 'mx' && (
              <>
                <span className="record-priority">Priority: {record.priority}</span>
                <span className="record-server">Server: {record.server}</span>
              </>
            )}
            {componentName === 'spf' && (
              <code className="record-text">{record.record}</code>
            )}
            {componentName === 'dkim' && (
              <>
                <span className="record-selector">Selector: {record.selector}</span>
                <code className="record-text">{record.record}</code>
              </>
            )}
            {componentName === 'dmarc' && (
              <code className="record-text">{record.record}</code>
            )}
          </div>
        ))}
      </div>
    );
  };

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const domainParam = urlParams.get('domain');
    if (domainParam) {
      setDomain(domainParam);
      checkDomain(domainParam);
    }
  }, [checkDomain]);

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
    <div className="min-h-screen bg-white text-gray-900 font-sans">
      <header className="bg-white shadow-sm border-b border-gray-200 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">{config.APP_NAME}</h1>
          <p className="text-lg text-gray-600">{config.APP_DESCRIPTION}</p>
        </div>
      </header>
      
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <form 
          className="bg-white rounded-2xl shadow-soft border border-gray-200 p-6 md:p-8 mb-8" 
          onSubmit={(e) => {
            e.preventDefault();
            checkDomain();
          }}
          aria-label="Analyze email domain security"
        >
          <div className="flex flex-col md:flex-row gap-4 md:gap-6">
            <div className="flex-1">
              <label htmlFor="domain-input" className="sr-only">
                Enter domain name
              </label>
              <input
                id="domain-input"
                name="domain"
                type="text"
                inputMode="url"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="example.com"
                className="w-full px-4 py-3 md:py-4 text-base md:text-lg border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-all duration-200 bg-white text-gray-900 placeholder-gray-500 disabled:bg-gray-50 disabled:text-gray-500"
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
              className="w-full md:w-auto px-6 py-3 md:py-4 text-base md:text-lg font-semibold text-white bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-xl transition-all duration-200 shadow-medium hover:shadow-large disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:shadow-medium"
              aria-busy={loading ? "true" : "false"}
            >
              {loading ? 'Analyzing...' : 'Analyze Domain'}
            </button>
          </div>
        </form>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-xl mb-6">
            <div className="flex items-center">
              <svg className="w-5 h-5 mr-2 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
              {error}
            </div>
          </div>
        )}

        {loading && !result && (
          <div className="bg-white rounded-2xl shadow-soft border border-gray-200 p-6 md:p-8 mb-8">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-6">
                <svg className="w-8 h-8 text-primary-600 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Starting Security Analysis</h3>
              <p className="text-gray-600 mb-6">Initializing comprehensive domain analysis...</p>
              
              <div className="max-w-md mx-auto">
                <div className="bg-gray-100 rounded-full h-2 mb-4">
                  <div className="bg-primary-600 h-2 rounded-full transition-all duration-1000 ease-out" style={{ width: '25%' }}></div>
                </div>
                <p className="text-sm text-gray-500">Initializing analysis...</p>
              </div>
            </div>
          </div>
        )}

        {result && (
          <div className="space-y-8">
            {/* Progressive Loading Indicator */}
            {(() => {
              const shouldShow = result.progressive && result.dkim && result.dkim.checking;
              return shouldShow;
            })() && (
              <div className="bg-white rounded-2xl shadow-soft border border-gray-200 p-6 md:p-8">
                <div className="text-center">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-6">
                    <svg className="w-8 h-8 text-primary-600 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                  </div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Comprehensive Security Analysis in Progress</h3>
                  <p className="text-gray-600 mb-6">Analyzing email security components...</p>
                  
                  <div className="max-w-lg mx-auto space-y-4">
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <span className="text-gray-700 font-medium">MX Records</span>
                      <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <span className="text-gray-700 font-medium">SPF Records</span>
                      <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
                      <span className="text-gray-700 font-medium">DMARC Records</span>
                      <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-primary-50 rounded-lg">
                      <span className="text-gray-700 font-medium">DKIM Records</span>
                      <svg className="w-5 h-5 text-primary-600 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    </div>
                  </div>
                  
                  <div className="max-w-md mx-auto mt-6">
                    <div className="bg-gray-100 rounded-full h-2 mb-4">
                      <div className="bg-primary-600 h-2 rounded-full transition-all duration-1000 ease-out" style={{ width: '75%' }}></div>
                    </div>
                    <p className="text-sm text-gray-500">3 of 4 components analyzed</p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Overall Security Score Section */}
            {result.security_score && !result.progressive && (
              <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-2xl shadow-large text-white p-8 md:p-12">
                <h2 className="text-3xl md:text-4xl font-bold text-center mb-8">Overall Security Score</h2>
                <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-16 mb-8">
                  <div className="text-center">
                    <div className="text-6xl md:text-7xl font-bold mb-2">{result.security_score.score}</div>
                    <div className="text-lg text-primary-100">out of 100</div>
                  </div>
                  <div className="text-center">
                    <div className="text-5xl md:text-6xl font-bold mb-2">{getScoreGrade(result.security_score.score)}</div>
                    <div className="text-lg text-primary-100">Security Grade</div>
                  </div>
                </div>
                <div className="max-w-2xl mx-auto">
                  <div className="bg-white/20 rounded-full h-3 mb-4">
                    <div 
                      className="h-3 rounded-full transition-all duration-1000 ease-out" 
                      style={{ 
                        width: `${result.security_score.score}%`,
                        backgroundColor: getScoreColor(result.security_score.score)
                      }}
                    ></div>
                  </div>
                  <p className="text-center text-primary-100">{getScoreStatus(result.security_score.score)}</p>
                </div>
              </div>
            )}

            {/* Security Components Section */}
            {!result.progressive && (
              <div className="bg-white rounded-2xl shadow-soft border border-gray-200 p-6 md:p-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-6">Security Components</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* MX Records */}
                  <div className={`p-6 rounded-xl border ${result.mx?.enabled ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-semibold text-gray-900">MX Records</h4>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">{getComponentIcon(result.mx?.enabled, getComponentScore(result.security_score?.scoring_details?.mx_base || 0, result.security_score?.scoring_details?.mx_bonus || 0))}</span>
                        <span className="text-sm font-medium">{getComponentScore(result.security_score?.scoring_details?.mx_base || 0, result.security_score?.scoring_details?.mx_bonus || 0)}/25</span>
                      </div>
                    </div>
                    <p className="text-gray-600 text-sm">Mail Exchange Configuration</p>
                  </div>

                  {/* SPF Records */}
                  <div className={`p-6 rounded-xl border ${result.spf?.enabled ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-semibold text-gray-900">SPF Records</h4>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">{getComponentIcon(result.spf?.enabled, getComponentScore(result.security_score?.scoring_details?.spf_base || 0, result.security_score?.scoring_details?.spf_bonus || 0))}</span>
                        <span className="text-sm font-medium">{getComponentScore(result.security_score?.scoring_details?.spf_base || 0, result.security_score?.scoring_details?.spf_bonus || 0)}/25</span>
                      </div>
                    </div>
                    <p className="text-gray-600 text-sm">Sender Policy Framework</p>
                  </div>

                  {/* DMARC Records */}
                  <div className={`p-6 rounded-xl border ${result.dmarc?.enabled ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-semibold text-gray-900">DMARC Records</h4>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">{getComponentIcon(result.dmarc?.enabled, getComponentScore(result.security_score?.scoring_details?.dmarc_base || 0, result.security_score?.scoring_details?.dmarc_bonus || 0))}</span>
                        <span className="text-sm font-medium">{getComponentScore(result.security_score?.scoring_details?.dmarc_base || 0, result.security_score?.scoring_details?.dmarc_bonus || 0)}/30</span>
                      </div>
                    </div>
                    <p className="text-gray-600 text-sm">Domain-based Message Authentication</p>
                  </div>

                  {/* DKIM Records */}
                  <div className={`p-6 rounded-xl border ${result.dkim?.enabled ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-lg font-semibold text-gray-900">DKIM Records</h4>
                      <div className="flex items-center space-x-2">
                        <span className="text-2xl">{getComponentIcon(result.dkim?.enabled, getComponentScore(result.security_score?.scoring_details?.dkim_base || 0, result.security_score?.scoring_details?.dkim_bonus || 0))}</span>
                        <span className="text-sm font-medium">{getComponentScore(result.security_score?.scoring_details?.dkim_base || 0, result.security_score?.scoring_details?.dkim_bonus || 0)}/20</span>
                      </div>
                    </div>
                    <p className="text-gray-600 text-sm">DomainKeys Identified Mail</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Public Statistics Section */}
        {statsLoading && (
          <div className="bg-white rounded-2xl shadow-soft border border-gray-200 p-6 md:p-8 mt-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Loading Public Statistics</h3>
            <p className="text-gray-600">Please wait while we fetch the latest security statistics for the platform.</p>
          </div>
        )}

        {!statsLoading && statistics && (
          <div className="bg-white rounded-2xl shadow-soft border border-gray-200 p-6 md:p-8 mt-8">
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Platform Statistics</h3>
            <p className="text-gray-600 mb-6">Trusted by organizations worldwide for email security analysis</p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900 mb-2">Total Analyses</h4>
                <p className="text-3xl font-bold text-primary-600">{statistics?.total_analyses?.toLocaleString() || '0'}</p>
                <p className="text-sm text-gray-600">Domain security checks performed</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900 mb-2">Unique Domains</h4>
                <p className="text-3xl font-bold text-primary-600">{statistics?.unique_domains?.toLocaleString() || '0'}</p>
                <p className="text-sm text-gray-600">Different domains analyzed</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900 mb-2">Average Security Score</h4>
                <p className="text-3xl font-bold text-primary-600">{statistics?.average_security_score?.toFixed(1) || '0.0'}</p>
                <p className="text-sm text-gray-600">Out of 100 points</p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900 mb-2">Top Provider</h4>
                <p className="text-3xl font-bold text-primary-600">
                  {statistics.email_provider_distribution && Object.keys(statistics.email_provider_distribution).length > 0 
                    ? Object.keys(statistics.email_provider_distribution)[0] 
                    : 'N/A'}
                </p>
                <p className="text-sm text-gray-600">Most common email service</p>
              </div>
            </div>
            <p className="text-sm text-gray-500 mt-6 text-center">* Statistics are aggregated across all users and represent the overall security posture of analyzed domains.</p>
          </div>
        )}

        {/* Email Report Modal */}
        {showEmailModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-2xl shadow-large max-w-md w-full p-6">
              <div className="text-center mb-6">
                <div className="text-4xl mb-4">📧</div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Security Analysis Complete</h2>
                <p className="text-gray-600">Domain: <strong>{domain}</strong></p>
                <p className="text-sm text-gray-500 mt-2">
                  Analysis completed on {new Date().toLocaleDateString()} at {new Date().toLocaleTimeString()}
                </p>
              </div>
              
              <div className="space-y-4">
                <input
                  type="email"
                  value={emailAddress}
                  onChange={(e) => setEmailAddress(e.target.value)}
                  placeholder="Enter email to receive this report"
                  className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
                <button
                  onClick={sendEmailReport}
                  disabled={emailSending || !emailAddress.trim()}
                  className="w-full px-6 py-3 text-white bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-xl transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {emailSending ? 'Sending...' : '📤 Email Report'}
                </button>
                
                <label className="flex items-center space-x-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={emailOptIn}
                    onChange={(e) => setEmailOptIn(e.target.checked)}
                    className="w-4 h-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <span className="text-sm text-gray-600">Also email me about new security features</span>
                </label>
              </div>
              
              <button
                onClick={() => setShowEmailModal(false)}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 text-2xl font-bold"
              >
                ✕
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
