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

    // Update URL with the domain being checked
    updateURL(domainValue);

    try {
      // First, get progressive results (fast)
      const progressiveUrl = `${config.API_BASE_URL}${config.ENDPOINTS.CHECK_DOMAIN}?domain=${encodeURIComponent(domainValue)}&progressive=true`;
      console.log('Making progressive request to:', progressiveUrl);
      
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
      setResult(progressiveData);
      
      // Then, complete the DKIM check (comprehensive)
      const dkimUrl = `${config.API_BASE_URL}/api/check/dkim?domain=${encodeURIComponent(domainValue)}`;
      console.log('Making DKIM completion request to:', dkimUrl);
      
      const dkimResponse = await fetch(dkimUrl);
      
      if (dkimResponse.ok) {
        const dkimData = await dkimResponse.json();
        
        // Update the result with completed DKIM data
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
        // Keep the progressive result but mark DKIM as failed
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
    } catch (err) {
      console.error('Full error details:', err);
      setError(`Error checking domain: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }, [domain]);

  // Load public statistics
  const loadStatistics = useCallback(async () => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/public/statistics`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setStatistics(data.data);
        }
      }
    } catch (err) {
      console.error('Failed to load statistics:', err);
    } finally {
      setStatsLoading(false);
    }
  }, []);

  const sendEmailReport = async () => {
    if (!emailAddress.trim()) {
      alert('Please enter an email address');
      return;
    }

    setEmailSending(true);
    try {
      const emailData = {
        email: emailAddress,
        domain: domain,
        analysis_result: result,
        opt_in_marketing: emailOptIn,
        timestamp: new Date().toISOString()
      };

      const response = await fetch(`${config.API_BASE_URL}/api/email-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(emailData)
      });

      if (response.ok) {
        alert('Report sent successfully! Check your email.');
        setShowEmailModal(false);
        setEmailAddress('');
        setEmailOptIn(false);
      } else {
        throw new Error('Failed to send email');
      }
    } catch (err) {
      console.error('Email sending failed:', err);
      alert('Failed to send email report. Please try again.');
    } finally {
      setEmailSending(false);
    }
  };

  // Check for domain parameter in URL on component mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const domainParam = urlParams.get('domain');
    if (domainParam) {
      setDomain(domainParam);
      // Automatically run analysis for the domain in URL with a longer delay
      setTimeout(() => {
        const url = `${config.API_BASE_URL}${config.ENDPOINTS.CHECK_DOMAIN}?domain=${encodeURIComponent(domainParam)}`;
        console.log('Making request to:', url);
        
        setLoading(true);
        setError(null);
        setResult(null);
        setExpandedComponents({});

        // Update URL with the domain being checked
        updateURL(domainParam);

        fetch(url)
          .then(response => {
            if (!response.ok) {
              const errorText = response.text();
              console.error('Response error:', response.status, errorText);
              throw new Error(`HTTP error! status: ${response.status} - ${errorText.substring(0, 100)}`);
            }
            
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
              const text = response.text();
              console.error('Non-JSON response:', text);
              throw new Error(`Expected JSON but got ${contentType}. Response: ${text.substring(0, 200)}`);
            }
            
            return response.json();
          })
          .then(data => {
            data.analysis_timestamp = new Date().toISOString();
            setResult(data);
          })
          .catch(err => {
            console.error('Full error details:', err);
            setError(`Error checking domain: ${err.message}`);
          })
          .finally(() => {
            setLoading(false);
          });
      }, 500);
    }
    
    // Load statistics on component mount
    loadStatistics();
  }, [loadStatistics]); // eslint-disable-line react-hooks/exhaustive-deps

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
    if (score >= 95) return 'A+';
    if (score >= 90) return 'A';
    if (score >= 85) return 'A-';
    if (score >= 80) return 'B+';
    if (score >= 75) return 'B';
    if (score >= 70) return 'B-';
    if (score >= 65) return 'C+';
    if (score >= 60) return 'C';
    if (score >= 55) return 'C-';
    if (score >= 50) return 'D+';
    if (score >= 45) return 'D';
    if (score >= 40) return 'D-';
    return 'F';
  };

  const getScoreStatus = (score) => {
    if (score >= 90) return 'Excellent security configuration!';
    if (score >= 75) return 'Good security configuration!';
    if (score >= 50) return 'Fair security configuration.';
    if (score >= 25) return 'Poor security configuration.';
    return 'Very poor security configuration.';
  };

  const getComponentScore = (base, bonus = 0) => {
    const total = base + bonus;
    const max = 25;
    return Math.min(total, max);
  };

  const getComponentIcon = (enabled, score) => {
    if (!enabled) return '❌';
    if (score >= 25) return '✅';
    if (score >= 15) return '⚠️';
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
      mx: {
        title: "What are MX Records?",
        description: "MX (Mail Exchange) records tell other email servers where to deliver emails for your domain. Think of them as your domain's postal address for email.",
        successMessage: "Your domain is properly configured to receive emails. Email servers know where to deliver messages for your domain.",
        failureMessage: "Your domain is not configured to receive emails. Email servers don't know where to deliver messages for your domain."
      },
      spf: {
        title: "What are SPF Records?",
        description: "SPF (Sender Policy Framework) records help prevent email spoofing by specifying which servers are authorized to send emails for your domain.",
        successMessage: "Your domain is protected against email spoofing. Other servers know which servers are authorized to send emails for your domain.",
        failureMessage: "Your domain is vulnerable to email spoofing. Other servers don't know which servers are authorized to send emails for your domain."
      },
      dkim: {
        title: "What are DKIM Records?",
        description: "DKIM (DomainKeys Identified Mail) records provide email authentication by digitally signing outgoing emails to verify they haven't been tampered with.",
        successMessage: "Your domain's emails are digitally signed for authentication. Recipients can verify that emails haven't been tampered with.",
        failureMessage: "Your domain's emails are not digitally signed. Recipients cannot verify that emails haven't been tampered with."
      },
      dmarc: {
        title: "What are DMARC Records?",
        description: "DMARC (Domain-based Message Authentication, Reporting & Conformance) records provide email authentication reporting and policy enforcement.",
        successMessage: "Your domain has email authentication reporting configured. You can monitor and enforce email authentication policies.",
        failureMessage: "Your domain lacks email authentication reporting. You cannot monitor or enforce email authentication policies."
      }
    };
    return descriptions[componentName] || {};
  };

  const renderRecords = (componentName, records) => {
    if (!records || records.length === 0) {
      return (
        <div className="no-records">
          <p>No {componentName.toUpperCase()} records found</p>
        </div>
      );
    }

    return (
      <div className="records-list">
        {records.map((record, index) => (
          <div key={index} className="record-item">
            {componentName === 'mx' && (
              <>
                <span className="record-priority">Priority {record.priority}:</span>
                <span className="record-server">{record.server}</span>
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

  return (
    <div className="App">
      <header className="App-header">
        <h1>{config.APP_NAME}</h1>
        <p>{config.APP_DESCRIPTION}</p>
      </header>
      
      <main className="App-main">
        <div className="input-section">
          <input
            type="text"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter domain (e.g., example.com)"
            className="domain-input"
            disabled={false}
          />
          <button 
            onClick={() => checkDomain()} 
            disabled={loading || !domain.trim()}
            className="check-button"
          >
            {loading ? 'Analyzing...' : 'Analyze Domain'}
          </button>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {loading && (
          <div className="loading-section">
            <div className="loading-spinner"></div>
            <h3>Analyzing Domain</h3>
            <p>Please wait while we perform a comprehensive security analysis of your domain's email infrastructure.</p>
            <div className="loading-steps">
              <div className="loading-step">Checking MX Records</div>
              <div className="loading-step">Analyzing SPF Configuration</div>
              <div className="loading-step">Validating DKIM Records</div>
              <div className="loading-step">Checking DMARC Policy</div>
            </div>
            <p className="loading-time">Estimated completion time: 2-5 seconds</p>
          </div>
        )}

        {result && (
          <div className="result-section">
            {/* Progressive Loading Indicator */}
            {result.progressive && result.dkim && result.dkim.checking && (
              <div className="progressive-loading">
                <div className="loading-indicator">
                  <div className="spinner"></div>
                  <div className="loading-text">
                    <h3>🔍 Comprehensive DKIM Analysis in Progress</h3>
                    <p>Checking 276+ DKIM selectors for maximum accuracy...</p>
                    <div className="progress-info">
                      <span className="checking-text">Currently checking: {result.dkim.description}</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Overall Security Score Section */}
            <div className="overall-security-score">
              <h2>Overall Security Score</h2>
              <div className="score-display">
                <div className="main-score">
                  <span className="score-number">{result.security_score.score}</span>
                  <span className="score-out-of">out of 100</span>
                </div>
                <div className="grade-display">
                  <span className="grade">{getScoreGrade(result.security_score.score)}</span>
                  <span className="grade-label">Security Grade</span>
                </div>
              </div>
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ 
                    width: `${result.security_score.score}%`,
                    backgroundColor: getScoreColor(result.security_score.score)
                  }}
                ></div>
              </div>
              <p className="score-message">{getScoreStatus(result.security_score.score)}</p>
            </div>

            {/* Score Breakdown Section */}
            {result.security_score.scoring_details && (
              <div className="score-breakdown">
                <h3>Score Breakdown</h3>
                <div className="base-score">
                  <h4>Base Score: {result.security_score.base_score}/100</h4>
                  <div className="score-components">
                    <div className="score-component">
                      <span className="component-name">MX Records:</span>
                      <span className={`component-score ${result.security_score.scoring_details.mx_base === 0 ? 'zero' : ''}`}>
                        {result.security_score.scoring_details.mx_base} pts
                      </span>
                      {result.security_score.scoring_details.mx_bonus > 0 && (
                        <span className="bonus-indicator">+{result.security_score.scoring_details.mx_bonus} bonus</span>
                      )}
                    </div>
                    <div className="score-component">
                      <span className="component-name">SPF Records:</span>
                      <span className={`component-score ${result.security_score.scoring_details.spf_base === 0 ? 'zero' : ''}`}>
                        {result.security_score.scoring_details.spf_base} pts
                      </span>
                      {result.security_score.scoring_details.spf_bonus > 0 && (
                        <span className="bonus-indicator">+{result.security_score.scoring_details.spf_bonus} bonus</span>
                      )}
                    </div>
                    <div className="score-component">
                      <span className="component-name">DMARC Records:</span>
                      <span className={`component-score ${result.security_score.scoring_details.dmarc_base === 0 ? 'zero' : ''}`}>
                        {result.security_score.scoring_details.dmarc_base} pts
                      </span>
                      {result.security_score.scoring_details.dmarc_bonus > 0 && (
                        <span className="bonus-indicator">+{result.security_score.scoring_details.dmarc_bonus} bonus</span>
                      )}
                    </div>
                    <div className="score-component">
                      <span className="component-name">DKIM Records:</span>
                      <span className={`component-score ${result.security_score.scoring_details.dkim_base === 0 ? 'zero' : ''}`}>
                        {result.security_score.scoring_details.dkim_base} pts
                      </span>
                      {result.security_score.scoring_details.dkim_bonus > 0 && (
                        <span className="bonus-indicator">+{result.security_score.scoring_details.dkim_bonus} bonus</span>
                      )}
                    </div>
                  </div>
                </div>
                {result.security_score.bonus_points > 0 && (
                  <div className="bonus-summary">
                    <h4>Bonus Points: +{result.security_score.bonus_points}</h4>
                    <p>Additional points for advanced security configurations</p>
                  </div>
                )}
              </div>
            )}

            {/* Security Summary Section */}
            <div className="security-summary">
              <h3>Security Summary</h3>
              <div className="summary-cards">
                <div className="summary-card primary">
                  <h4>Overall Assessment</h4>
                  <p>Your domain has {result.security_score.score >= 75 ? 'strong' : result.security_score.score >= 50 ? 'moderate' : 'weak'} email security configured. {result.security_score.score >= 75 ? "You're well-protected against most email-based attacks." : result.security_score.score >= 50 ? "There's room for improvement to enhance your security posture." : "Immediate action is recommended to improve your security."}</p>
                </div>
                <div className="summary-cards-row">
                  <div className="summary-card">
                    <h4>Security Level</h4>
                    <div className="security-level">
                      <span className="level-text">{result.security_score.status}</span>
                      <span className="level-detail">
                        {Object.values(result.security_score.scoring_details).filter((score, index) => index % 2 === 0 && score > 0).length}/4 email security components properly configured
                      </span>
                    </div>
                  </div>
                  <div className="summary-card">
                    <h4>Grade Meaning</h4>
                    <p>{result.security_score.score >= 90 ? 'Outstanding email security. Your domain is extremely well-protected.' : result.security_score.score >= 75 ? 'Good email security. Your domain is well-protected.' : result.security_score.score >= 50 ? 'Fair email security. Some improvements recommended.' : 'Poor email security. Immediate action required.'}</p>
                  </div>
                </div>
                <div className="component-status-cards">
                  <div className="status-card">
                    <span className="status-label">Spoofing Protection</span>
                    <span className={`status-value ${result.spf.enabled ? 'protected' : 'unprotected'}`}>
                      {result.spf.enabled ? 'Protected' : 'Unprotected'}
                    </span>
                  </div>
                  <div className="status-card">
                    <span className="status-label">Email Delivery</span>
                    <span className={`status-value ${result.mx.enabled ? 'working' : 'failing'}`}>
                      {result.mx.enabled ? 'Working' : 'Failing'}
                    </span>
                  </div>
                  <div className="status-card">
                    <span className="status-label">Authentication</span>
                    <span className={`status-value ${result.dkim.enabled && result.dmarc.enabled ? 'strong' : result.dkim.enabled || result.dmarc.enabled ? 'partial' : 'weak'}`}>
                      {result.dkim.enabled && result.dmarc.enabled ? 'Strong' : result.dkim.enabled || result.dmarc.enabled ? 'Partial' : 'Weak'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Security Components Section */}
            <div className="security-components">
              <h3>Security Components</h3>
              <div className="components-grid">
                {/* MX Records Component */}
                <div className={`component-card ${result.mx.enabled ? 'success' : 'failure'}`}>
                  <div className="component-header" onClick={() => toggleComponent('mx')}>
                    <div className="component-info">
                      <h4>MX Records</h4>
                      <p>Mail Exchange Configuration</p>
                    </div>
                    <div className="component-status">
                      <span className="status-icon">{getComponentIcon(result.mx.enabled, getComponentScore(result.security_score.scoring_details.mx_base, result.security_score.scoring_details.mx_bonus))}</span>
                      <span className="component-score">
                        {getComponentScore(result.security_score.scoring_details.mx_base, result.security_score.scoring_details.mx_bonus)}/25
                      </span>
                      <span className="expand-icon">
                        {expandedComponents.mx ? '▼' : '▶'}
                      </span>
                    </div>
                  </div>
                  {expandedComponents.mx && (
                    <div className="component-expanded-content">
                      <div className="component-description">
                        <h5>{getComponentDescription('mx').title}</h5>
                        <p>{getComponentDescription('mx').description}</p>
                        <div className={`status-message ${result.mx.enabled ? 'success' : 'failure'}`}>
                          <span className="status-icon">✅</span>
                          <span>{result.mx.enabled ? getComponentDescription('mx').successMessage : getComponentDescription('mx').failureMessage}</span>
                        </div>
                      </div>
                      <div className="records-section">
                        <h5>Current Mail Servers:</h5>
                        {renderRecords('mx', result.mx.records)}
                      </div>
                    </div>
                  )}
                </div>

                {/* SPF Records Component */}
                <div className={`component-card ${result.spf.enabled ? 'success' : 'failure'}`}>
                  <div className="component-header" onClick={() => toggleComponent('spf')}>
                    <div className="component-info">
                      <h4>SPF Records</h4>
                      <p>Sender Policy Framework</p>
                    </div>
                    <div className="component-status">
                      <span className="status-icon">{getComponentIcon(result.spf.enabled, getComponentScore(result.security_score.scoring_details.spf_base, result.security_score.scoring_details.spf_bonus))}</span>
                      <span className="component-score">
                        {getComponentScore(result.security_score.scoring_details.spf_base, result.security_score.scoring_details.spf_bonus)}/25
                      </span>
                      <span className="expand-icon">
                        {expandedComponents.spf ? '▼' : '▶'}
                      </span>
                    </div>
                  </div>
                  {expandedComponents.spf && (
                    <div className="component-expanded-content">
                      <div className="component-description">
                        <h5>{getComponentDescription('spf').title}</h5>
                        <p>{getComponentDescription('spf').description}</p>
                        <div className={`status-message ${result.spf.enabled ? 'success' : 'failure'}`}>
                          <span className="status-icon">✅</span>
                          <span>{result.spf.enabled ? getComponentDescription('spf').successMessage : getComponentDescription('spf').failureMessage}</span>
                        </div>
                      </div>
                      <div className="records-section">
                        <h5>Current SPF Records:</h5>
                        {renderRecords('spf', result.spf.records)}
                      </div>
                    </div>
                  )}
                </div>

                {/* DKIM Records Component */}
                <div className={`component-card ${result.dkim.enabled ? 'success' : 'failure'}`}>
                  <div className="component-header" onClick={() => toggleComponent('dkim')}>
                    <div className="component-info">
                      <h4>DKIM Records</h4>
                      <p>DomainKeys Identified Mail</p>
                    </div>
                    <div className="component-status">
                      <span className="status-icon">{getComponentIcon(result.dkim.enabled, getComponentScore(result.security_score.scoring_details.dkim_base, result.security_score.scoring_details.dkim_bonus))}</span>
                      <span className="component-score">
                        {getComponentScore(result.security_score.scoring_details.dkim_base, result.security_score.scoring_details.dkim_bonus)}/25
                      </span>
                      <span className="expand-icon">
                        {expandedComponents.dkim ? '▼' : '▶'}
                      </span>
                    </div>
                  </div>
                  {expandedComponents.dkim && (
                    <div className="component-expanded-content">
                      <div className="component-description">
                        <h5>{getComponentDescription('dkim').title}</h5>
                        <p>{getComponentDescription('dkim').description}</p>
                        <div className={`status-message ${result.dkim.enabled ? 'success' : 'failure'}`}>
                          <span className="status-icon">✅</span>
                          <span>{result.dkim.enabled ? getComponentDescription('dkim').successMessage : getComponentDescription('dkim').failureMessage}</span>
                        </div>
                      </div>
                      <div className="records-section">
                        <h5>Current DKIM Records:</h5>
                        {renderRecords('dkim', result.dkim.records)}
                      </div>
                    </div>
                  )}
                </div>

                {/* DMARC Records Component */}
                <div className={`component-card ${result.dmarc.enabled ? 'success' : 'failure'}`}>
                  <div className="component-header" onClick={() => toggleComponent('dmarc')}>
                    <div className="component-info">
                      <h4>DMARC Records</h4>
                      <p>Domain-based Message Authentication</p>
                    </div>
                    <div className="component-status">
                      <span className="status-icon">{getComponentIcon(result.dmarc.enabled, getComponentScore(result.security_score.scoring_details.dmarc_base, result.security_score.scoring_details.dmarc_bonus))}</span>
                      <span className="component-score">
                        {getComponentScore(result.security_score.scoring_details.dmarc_base, result.security_score.scoring_details.dmarc_bonus)}/25
                      </span>
                      <span className="expand-icon">
                        {expandedComponents.dmarc ? '▼' : '▶'}
                      </span>
                    </div>
                  </div>
                  {expandedComponents.dmarc && (
                    <div className="component-expanded-content">
                      <div className="component-description">
                        <h5>{getComponentDescription('dmarc').title}</h5>
                        <p>{getComponentDescription('dmarc').description}</p>
                        <div className={`status-message ${result.dmarc.enabled ? 'success' : 'failure'}`}>
                          <span className="status-icon">✅</span>
                          <span>{result.dmarc.enabled ? getComponentDescription('dmarc').successMessage : getComponentDescription('dmarc').failureMessage}</span>
                        </div>
                      </div>
                      <div className="records-section">
                        <h5>Current DMARC Records:</h5>
                        {renderRecords('dmarc', result.dmarc.records)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Security Issues Section */}
            {result.recommendations.length > 0 && (
              <div className="security-issues">
                <h3>Security Issues</h3>
                <div className="issues-list">
                  {result.recommendations.map((rec, index) => (
                    <div key={index} className="issue-card">
                      <div className="issue-icon">{getRecommendationIcon(rec.type)}</div>
                      <div className="issue-content">
                        <h4>{rec.title}</h4>
                        <p>{rec.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Email Report Button */}
            <div className="email-report-section">
              <button
                onClick={() => setShowEmailModal(true)}
                className="email-report-button"
              >
                📧 Email Security Report
              </button>
              <p className="email-report-note">
                Get a detailed PDF report of this security analysis sent to your email
              </p>
            </div>

            <div className="analysis-footer">
              <p>Analysis completed at: {new Date(result.analysis_timestamp).toLocaleString()}</p>
            </div>
          </div>
        )}

        {/* Public Statistics Section */}
        {statsLoading && (
          <div className="statistics-section loading-section">
            <div className="loading-spinner"></div>
            <h3>Loading Public Statistics</h3>
            <p>Please wait while we fetch the latest security statistics for the platform.</p>
          </div>
        )}
                 {!statsLoading && statistics && (
           <div className="statistics-section">
             <h3>Platform Statistics</h3>
             <p className="stats-subtitle">Trusted by organizations worldwide for email security analysis</p>
             <div className="stats-grid">
               <div className="stat-card">
                 <h4>Total Analyses</h4>
                 <p className="stat-number">{statistics.total_analyses.toLocaleString()}</p>
                 <p className="stat-label">Domain security checks performed</p>
               </div>
               <div className="stat-card">
                 <h4>Unique Domains</h4>
                 <p className="stat-number">{statistics.unique_domains.toLocaleString()}</p>
                 <p className="stat-label">Different domains analyzed</p>
               </div>
               <div className="stat-card">
                 <h4>Average Security Score</h4>
                 <p className="stat-number">{statistics.average_security_score.toFixed(1)}</p>
                 <p className="stat-label">Out of 100 points</p>
               </div>
               <div className="stat-card">
                 <h4>Top Provider</h4>
                 <p className="stat-number">
                   {Object.keys(statistics.email_provider_distribution).length > 0 
                     ? Object.keys(statistics.email_provider_distribution)[0] 
                     : 'N/A'}
                 </p>
                 <p className="stat-label">Most common email service</p>
               </div>
             </div>
             <p className="stats-note">* Statistics are aggregated across all users and represent the overall security posture of analyzed domains.</p>
                       </div>
          )}

          {/* Email Report Modal */}
          {showEmailModal && (
            <div className="email-modal-overlay">
              <div className="email-modal">
                <div className="email-modal-header">
                  <div className="email-icon">📧</div>
                  <h2>Security Analysis Complete</h2>
                  <p>Domain: <strong>{domain}</strong></p>
                  <p className="analysis-timestamp">
                    Analysis completed on {new Date().toLocaleDateString()} at {new Date().toLocaleTimeString()}
                  </p>
                </div>
                
                <div className="email-modal-divider"></div>
                
                <div className="email-modal-content">
                  <div className="email-input-section">
                    <input
                      type="email"
                      value={emailAddress}
                      onChange={(e) => setEmailAddress(e.target.value)}
                      placeholder="Enter email to receive this report"
                      className="email-input"
                    />
                    <button
                      onClick={sendEmailReport}
                      disabled={emailSending || !emailAddress.trim()}
                      className="email-button"
                    >
                      {emailSending ? (
                        <>
                          <span className="sending-spinner"></span>
                          Sending...
                        </>
                      ) : (
                        <>
                          <span className="send-icon">📤</span>
                          Email Report
                        </>
                      )}
                    </button>
                  </div>
                  
                  <div className="email-optin">
                    <label className="optin-checkbox">
                      <input
                        type="checkbox"
                        checked={emailOptIn}
                        onChange={(e) => setEmailOptIn(e.target.checked)}
                      />
                      <span className="checkmark"></span>
                      Also email me about new security features
                    </label>
                  </div>
                </div>
                
                <button
                  onClick={() => setShowEmailModal(false)}
                  className="close-modal-button"
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

