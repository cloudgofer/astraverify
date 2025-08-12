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
  const [isEditing, setIsEditing] = useState(false);

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
            {error}
          </div>
        )}

        {loading && !result && (
          <div className="progressive-loading">
            <div className="loading-text">
              <h3>🔍 Starting Security Analysis</h3>
              <p>Initializing comprehensive domain analysis...</p>
              <div className="progress-info">
                <div className="component-progress">
                  <div className="progress-item">
                    <span className="component-name">Initializing</span>
                    <span className="status-icon">
                      <span className="hourglass-animation">⏳</span>
                    </span>
                  </div>
                </div>
                <div className="overall-progress">
                  <div className="progress-bar">
                    <div 
                      className="progress-fill animated" 
                      style={{ 
                        width: '25%',
                        backgroundColor: '#4CAF50'
                      }}
                    ></div>
                  </div>
                  <p className="progress-text">Initializing analysis...</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {result && (
          <div className="result-section">
            {/* Progressive Loading Indicator */}
            {(() => {
              const shouldShow = result.progressive && result.dkim && result.dkim.checking;
              console.log('PROGRESSIVE UI DEBUG:', {
                progressive: result.progressive,
                dkim: result.dkim,
                dkimChecking: result.dkim?.checking,
                shouldShow
              });
              return shouldShow;
            })() && (
              <div className="progressive-loading">
                <div className="loading-text">
                  <h3>🔍 Comprehensive Security Analysis in Progress</h3>
                  <p>Analyzing email security components...</p>
                  <div className="progress-info">
                    <div className="component-progress">
                      <div className="progress-item">
                        <span className="component-name">MX Records</span>
                        <span className="status-icon">✅</span>
                      </div>
                      <div className="progress-item">
                        <span className="component-name">SPF Records</span>
                        <span className="status-icon">✅</span>
                      </div>
                      <div className="progress-item">
                        <span className="component-name">DMARC Records</span>
                        <span className="status-icon">✅</span>
                      </div>
                      <div className="progress-item">
                        <span className="component-name">DKIM Records</span>
                        <span className="status-icon">
                          <span className="hourglass-animation">⏳</span>
                        </span>
                      </div>
                    </div>
                    <div className="overall-progress">
                      <div className="progress-bar">
                        <div 
                          className="progress-fill animated" 
                          style={{ 
                            width: '75%',
                            backgroundColor: '#4CAF50'
                          }}
                        ></div>
                      </div>
                      <p className="progress-text">3 of 4 components analyzed</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            {/* Overall Security Score Section */}
            {result.security_score && !result.progressive && (
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
            )}

            {/* Score Breakdown Section - Only show when analysis is complete */}
            {result.security_score && result.security_score.scoring_details && !result.progressive && (
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

            {/* Security Summary Section - Only show when analysis is complete */}
            {!result.progressive && (
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
                          {result.security_score.scoring_details ? Object.values(result.security_score.scoring_details).filter((score, index) => index % 2 === 0 && score > 0).length : 0}/4 email security components properly configured
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
                      <span className={`status-value ${result.spf?.enabled ? 'protected' : 'unprotected'}`}>
                        {result.spf?.enabled ? 'Protected' : 'Unprotected'}
                      </span>
                    </div>
                    <div className="status-card">
                      <span className="status-label">Email Delivery</span>
                      <span className={`status-value ${result.mx?.enabled ? 'working' : 'failing'}`}>
                        {result.mx?.enabled ? 'Working' : 'Failing'}
                      </span>
                    </div>
                    <div className="status-card">
                      <span className="status-label">Authentication</span>
                      <span className={`status-value ${result.dkim?.enabled && result.dmarc?.enabled ? 'strong' : result.dkim?.enabled || result.dmarc?.enabled ? 'partial' : 'weak'}`}>
                        {result.dkim?.enabled && result.dmarc?.enabled ? 'Strong' : result.dkim?.enabled || result.dmarc?.enabled ? 'Partial' : 'Weak'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Security Components Section - Only show when analysis is complete */}
            {!result.progressive && (
              <div className="security-components">
                <h3>Security Components</h3>
                <div className="components-grid">
                  {/* MX Records Component */}
                  <div className={`component-card ${result.mx?.enabled ? 'success' : 'failure'}`}>
                    <div className="component-header" onClick={() => toggleComponent('mx')}>
                      <div className="component-info">
                        <h4>MX Records</h4>
                        <p>Mail Exchange Configuration</p>
                      </div>
                      <div className="component-status">
                        <span className="status-icon">{getComponentIcon(result.mx?.enabled, getComponentScore(result.security_score?.scoring_details?.mx_base || 0, result.security_score?.scoring_details?.mx_bonus || 0))}</span>
                        <span className="component-score">
                          {getComponentScore(result.security_score?.scoring_details?.mx_base || 0, result.security_score?.scoring_details?.mx_bonus || 0)}/25
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
                          <div className={`status-message ${result.mx?.enabled ? 'success' : 'failure'}`}>
                            <span className="status-icon">✅</span>
                            <span>{result.mx?.enabled ? getComponentDescription('mx').successMessage : getComponentDescription('mx').failureMessage}</span>
                          </div>
                        </div>
                        <div className="records-section">
                          <h5>Current Mail Servers:</h5>
                          {renderRecords('mx', result.mx?.records)}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* SPF Records Component */}
                  <div className={`component-card ${result.spf?.enabled ? 'success' : 'failure'}`}>
                    <div className="component-header" onClick={() => toggleComponent('spf')}>
                      <div className="component-info">
                        <h4>SPF Records</h4>
                        <p>Sender Policy Framework</p>
                      </div>
                      <div className="component-status">
                        <span className="status-icon">{getComponentIcon(result.spf?.enabled, getComponentScore(result.security_score?.scoring_details?.spf_base || 0, result.security_score?.scoring_details?.spf_bonus || 0))}</span>
                        <span className="component-score">
                          {getComponentScore(result.security_score?.scoring_details?.spf_base || 0, result.security_score?.scoring_details?.spf_bonus || 0)}/25
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
                          <div className={`status-message ${result.spf?.enabled ? 'success' : 'failure'}`}>
                            <span className="status-icon">✅</span>
                            <span>{result.spf?.enabled ? getComponentDescription('spf').successMessage : getComponentDescription('spf').failureMessage}</span>
                          </div>
                        </div>
                        <div className="records-section">
                          <h5>Current SPF Records:</h5>
                          {renderRecords('spf', result.spf?.records)}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* DKIM Records Component */}
                  <div className={`component-card ${result.dkim?.enabled ? 'success' : 'failure'}`}>
                    <div className="component-header" onClick={() => toggleComponent('dkim')}>
                      <div className="component-info">
                        <h4>DKIM Records</h4>
                        <p>DomainKeys Identified Mail</p>
                      </div>
                      <div className="component-status">
                        <span className="status-icon">{getComponentIcon(result.dkim?.enabled, getComponentScore(result.security_score?.scoring_details?.dkim_base || 0, result.security_score?.scoring_details?.dkim_bonus || 0))}</span>
                        <span className="component-score">
                          {getComponentScore(result.security_score?.scoring_details?.dkim_base || 0, result.security_score?.scoring_details?.dkim_bonus || 0)}/20
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
                          <div className={`status-message ${result.dkim?.enabled ? 'success' : 'failure'}`}>
                            <span className="status-icon">✅</span>
                            <span>{result.dkim?.enabled ? getComponentDescription('dkim').successMessage : getComponentDescription('dkim').failureMessage}</span>
                          </div>
                        </div>
                        <div className="records-section">
                          <h5>Current DKIM Records:</h5>
                          {renderRecords('dkim', result.dkim?.records)}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* DMARC Records Component */}
                  <div className={`component-card ${result.dmarc?.enabled ? 'success' : 'failure'}`}>
                    <div className="component-header" onClick={() => toggleComponent('dmarc')}>
                      <div className="component-info">
                        <h4>DMARC Records</h4>
                        <p>Domain-based Message Authentication</p>
                      </div>
                      <div className="component-status">
                        <span className="status-icon">{getComponentIcon(result.dmarc?.enabled, getComponentScore(result.security_score?.scoring_details?.dmarc_base || 0, result.security_score?.scoring_details?.dmarc_bonus || 0))}</span>
                        <span className="component-score">
                          {getComponentScore(result.security_score?.scoring_details?.dmarc_base || 0, result.security_score?.scoring_details?.dmarc_bonus || 0)}/30
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
                          <div className={`status-message ${result.dmarc?.enabled ? 'success' : 'failure'}`}>
                            <span className="status-icon">✅</span>
                            <span>{result.dmarc?.enabled ? getComponentDescription('dmarc').successMessage : getComponentDescription('dmarc').failureMessage}</span>
                          </div>
                        </div>
                        <div className="records-section">
                          <h5>Current DMARC Records:</h5>
                          {renderRecords('dmarc', result.dmarc?.records)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Security Issues Section - Only show when analysis is complete */}
            {result.recommendations && result.recommendations.length > 0 && !result.progressive && (
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

            {/* Email Report Button - Only show when analysis is complete */}
            {!result.progressive && (
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
            )}

            {/* Analysis Footer - Only show when analysis is complete */}
            {!result.progressive && (
              <div className="analysis-footer">
                <p>Analysis completed at: {new Date(result.analysis_timestamp).toLocaleString()}</p>
              </div>
            )}
          </div>
        )}

        {/* Public Statistics Section */}
        {statsLoading && (
          <div className="statistics-section loading-section">
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
                <p className="stat-number">{statistics?.total_analyses?.toLocaleString() || '0'}</p>
                <p className="stat-label">Domain security checks performed</p>
              </div>
              <div className="stat-card">
                <h4>Unique Domains</h4>
                <p className="stat-number">{statistics?.unique_domains?.toLocaleString() || '0'}</p>
                <p className="stat-label">Different domains analyzed</p>
              </div>
              <div className="stat-card">
                <h4>Average Security Score</h4>
                <p className="stat-number">{statistics?.average_security_score?.toFixed(1) || '0.0'}</p>
                <p className="stat-label">Out of 100 points</p>
              </div>
              <div className="stat-card">
                <h4>Top Provider</h4>
                <p className="stat-number">
                  {statistics.email_provider_distribution && Object.keys(statistics.email_provider_distribution).length > 0 
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

