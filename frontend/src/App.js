import React, { useState, useEffect, useCallback } from 'react';
import config from './config';
import { getFooterText } from './version';
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
        
        console.log('🔍 DKIM completion response:', dkimData);
        console.log('🔍 DKIM recommendations:', dkimData.recommendations);
        
        setResult(prevResult => {
          const newResult = {
            ...prevResult,
            dkim: dkimData.dkim,
            email_provider: dkimData.email_provider,
            security_score: dkimData.security_score,
            recommendations: dkimData.recommendations || [],
            progressive: false,
            message: `Analysis complete! Checked ${dkimData.dkim.selectors_checked || 0} DKIM selectors.`
          };
          console.log('🔍 Updated result:', newResult);
          console.log('🔍 Final recommendations:', newResult.recommendations);
          return newResult;
        });
        
        // Refresh statistics after successful analysis
        setTimeout(() => {
          refreshStatistics();
        }, 1000);
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
      const response = await fetch(`${config.API_BASE_URL}/api/email-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: emailAddress,
          domain: domain,
          analysis_result: result,
          opt_in_marketing: emailOptIn,
          timestamp: new Date().toISOString()
        }),
      });

      if (response.ok) {
        const responseData = await response.json();
        if (responseData.success) {
          alert('Email report sent successfully! Check your inbox for the detailed security analysis.');
          setShowEmailModal(false);
          setEmailAddress('');
          setEmailOptIn(false);
        } else {
          alert(`Failed to send email: ${responseData.error || 'Unknown error'}`);
        }
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

  const getComponentScore = (base, bonus = 0, componentName = null) => {
    const total = base + bonus;
    let max = 25; // Default max
    
    // Set component-specific max scores
    if (componentName === 'dmarc') {
      max = 30; // DMARC has higher max score
    } else if (componentName === 'dkim') {
      max = 20; // DKIM has lower max score
    }
    
    return Math.min(total, max);
  };

  const getComponentMaxScore = (componentName) => {
    switch (componentName) {
      case 'dmarc':
        return 30;
      case 'dkim':
        return 20;
      default:
        return 25;
    }
  };

  const getComponentIcon = (enabled, score, overallScore = 0) => {
    // If no records exist or score is 0, show red X (missing/failed)
    if (!enabled || score === 0) return '❌';
    
    // If score is good (80% or higher), show green checkmark
    if (score >= 20) return '✅'; // 20/25 = 80% for most components
    if (score >= 24) return '✅'; // 24/30 = 80% for DMARC
    if (score >= 16) return '✅'; // 16/20 = 80% for DKIM
    
    // If score is moderate (50% or higher), show green checkmark
    if (score >= 13) return '✅'; // 13/25 = 52% for most components
    if (score >= 15) return '✅'; // 15/30 = 50% for DMARC
    if (score >= 10) return '✅'; // 10/20 = 50% for DKIM
    
    // If score is low but present, show yellow warning
    if (score >= 1) return '⚠️';
    
    // Fallback to red X for any other case
    return '❌';
  };

  const getComponentIconClass = (icon) => {
    if (icon === '✅') return 'success';
    if (icon === '⚠️') return 'warning';
    return 'error';
  };

  const getBonusExplanation = (componentName, baseScore, bonusScore) => {
    if (bonusScore === 0) return null;
    
    const detailedExplanations = {
      mx: {
        2: "Multiple MX records for redundancy\n+2 points",
        3: "Trusted email provider (Google, Microsoft, etc.)\n+3 points",
        5: "Multiple MX records for redundancy\n+2 points\nTrusted email provider\n+3 points",
        7: "Multiple MX records for redundancy\n+2 points\nTrusted email provider\n+3 points\nSecure mail server configuration\n+2 points"
      },
      spf: {
        2: "Strong SPF policy (-all)\n+2 points",
        3: "Strong SPF policy (-all)\n+2 points\nInclude mechanisms for delegation\n+1 point",
        4: "Strong SPF policy (-all)\n+2 points\nInclude mechanisms for delegation\n+1 point\nDirect IP specifications\n+1 point",
        5: "Strong SPF policy (-all)\n+2 points\nInclude mechanisms for delegation\n+1 point\nDirect IP specifications\n+1 point\nDomain A/MX records\n+1 point",
        7: "Strong SPF policy (-all)\n+2 points\nInclude mechanisms for delegation\n+2 points\nDirect IP specifications\n+2 points\nDomain A/MX records\n+1 point"
      },
      dmarc: {
        2: "Strict DMARC policy (p=reject)\n+2 points",
        3: "Strict DMARC policy (p=reject)\n+2 points\nFull coverage (pct=100)\n+1 point",
        4: "Strict DMARC policy (p=reject)\n+2 points\nFull coverage (pct=100)\n+1 point\nAggregate reports configured (rua=)\n+1 point",
        5: "Strict DMARC policy (p=reject)\n+2 points\nFull coverage (pct=100)\n+1 point\nAggregate reports configured (rua=)\n+1 point\nForensic reports configured (ruf=)\n+1 point",
        6: "Strict DMARC policy (p=reject)\n+2 points\nStrict subdomain policy (sp=reject)\n+3 points\nFull coverage (pct=100)\n+1 point",
        8: "Strict DMARC policy (p=reject)\n+2 points\nStrict subdomain policy (sp=reject)\n+3 points\nFull coverage (pct=100)\n+1 point\nAggregate reports configured (rua=)\n+1 point\nForensic reports configured (ruf=)\n+1 point"
      },
      dkim: {
        2: "Multiple DKIM selectors for diversity\n+2 points",
        3: "Multiple DKIM selectors for diversity\n+2 points\nStrong algorithm (RSA-2048+, Ed25519)\n+1 point",
        4: "Multiple DKIM selectors for diversity\n+2 points\nStrong algorithm (RSA-2048+, Ed25519)\n+1 point\nStrong key length (2048+ bits)\n+1 point",
        5: "Multiple DKIM selectors for diversity\n+2 points\nStrong algorithm (RSA-2048+, Ed25519)\n+1 point\nStrong key length (2048+ bits)\n+1 point\nAdditional security features\n+1 point"
      }
    };
    
    const componentExplanations = detailedExplanations[componentName] || {};
    return componentExplanations[bonusScore] || `+${bonusScore} bonus points for advanced configuration`;
  };

  const getMissingPointsExplanation = (componentName, currentScore, maxScore) => {
    const missingPoints = maxScore - currentScore;
    if (missingPoints <= 0) return null;
    
    const detailedExplanations = {
      mx: {
        missing: missingPoints,
        details: "Redundancy (3+ MX records)\n+5 points\nTrusted email provider\n+3 points\nSecure mail server configuration\n+2 points"
      },
      spf: {
        missing: missingPoints,
        details: "Strict SPF policy (-all)\n+8 points\nInclude mechanisms for delegation\n+2 points\nDirect IP specifications\n+2 points\nDomain A/MX records\n+1 point\nNo redirect mechanisms\n+2 points"
      },
      dmarc: {
        missing: missingPoints,
        details: "Strict DMARC policy (p=reject)\n+8 points\nStrict subdomain policy (sp=reject)\n+3 points\nFull coverage (pct=100)\n+2 points\nAggregate reports configured (rua=)\n+2 points\nForensic reports configured (ruf=)\n+1 point"
      },
      dkim: {
        missing: missingPoints,
        details: "Multiple DKIM selectors\n+4 points\nStrong algorithm (RSA-2048+, Ed25519)\n+3 points\nStrong key length (2048+ bits)\n+2 points"
      }
    };
    
    const componentInfo = detailedExplanations[componentName];
    if (!componentInfo) return null;
    
    return `${componentInfo.missing} points missing:\n${componentInfo.details}`;
  };

  const getRecommendationIcon = (type) => {
    switch (type) {
      case 'critical': return '⚠️';
      case 'important': return '⚠️';
      case 'info': return 'ℹ️';
      case 'ok': return '✅';
      default: return 'ℹ️';
    }
  };

  const getRecommendationIconClass = (type) => {
    switch (type) {
      case 'critical': return 'warning';
      case 'important': return 'warning';
      case 'info': return 'info';
      case 'ok': return 'success';
      default: return 'info';
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

    const refreshStatistics = async () => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/public/statistics`);
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.data) {
          setStatistics(data.data);
        }
      }
    } catch (error) {
      console.error('Error refreshing statistics:', error);
    }
  };

  useEffect(() => {
    const fetchStatistics = async () => {
      try {
        const response = await fetch(`${config.API_BASE_URL}/api/public/statistics`);
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.data) {
            setStatistics(data.data);
          }
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
                        backgroundColor: '#6c757d'
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
                        <span className="status-icon">✓</span>
                      </div>
                      <div className="progress-item">
                        <span className="component-name">SPF Records</span>
                        <span className="status-icon">✓</span>
                      </div>
                      <div className="progress-item">
                        <span className="component-name">DMARC Records</span>
                        <span className="status-icon">✓</span>
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
                            backgroundColor: '#6c757d'
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
                        {result.security_score.scoring_details.mx_base}/{getComponentMaxScore('mx')} pts
                      </span>
                      {result.security_score.scoring_details.mx_bonus > 0 && (
                        <span className="bonus-indicator-score">+{result.security_score.scoring_details.mx_bonus} Bonus</span>
                      )}
                    </div>
                    <div className="score-component">
                      <span className="component-name">SPF Records:</span>
                      <span className={`component-score ${result.security_score.scoring_details.spf_base === 0 ? 'zero' : ''}`}>
                        {result.security_score.scoring_details.spf_base}/{getComponentMaxScore('spf')} pts
                      </span>
                      {result.security_score.scoring_details.spf_bonus > 0 && (
                        <span className="bonus-indicator-score">+{result.security_score.scoring_details.spf_bonus} Bonus</span>
                      )}
                    </div>
                    <div className="score-component">
                      <span className="component-name">DMARC Records:</span>
                      <span className={`component-score ${result.security_score.scoring_details.dmarc_base === 0 ? 'zero' : ''}`}>
                        {result.security_score.scoring_details.dmarc_base}/{getComponentMaxScore('dmarc')} pts
                      </span>
                      {result.security_score.scoring_details.dmarc_bonus > 0 && (
                        <span className="bonus-indicator-score">+{result.security_score.scoring_details.dmarc_bonus} Bonus</span>
                      )}
                    </div>
                    <div className="score-component">
                      <span className="component-name">DKIM Records:</span>
                      <span className={`component-score ${result.security_score.scoring_details.dkim_base === 0 ? 'zero' : ''}`}>
                        {result.security_score.scoring_details.dkim_base}/{getComponentMaxScore('dkim')} pts
                      </span>
                      {result.security_score.scoring_details.dkim_bonus > 0 && (
                        <span className="bonus-indicator-score">+{result.security_score.scoring_details.dkim_bonus} Bonus</span>
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
                        <span className={`status-icon ${getComponentIconClass(getComponentIcon(result.mx?.enabled, getComponentScore(result.security_score?.scoring_details?.mx_base || 0, result.security_score?.scoring_details?.mx_bonus || 0, 'mx')))}`}>
                          {getComponentIcon(result.mx?.enabled, getComponentScore(result.security_score?.scoring_details?.mx_base || 0, result.security_score?.scoring_details?.mx_bonus || 0, 'mx'))}
                        </span>
                        <span className="component-score">
                          {getComponentScore(result.security_score?.scoring_details?.mx_base || 0, result.security_score?.scoring_details?.mx_bonus || 0, 'mx')}/{getComponentMaxScore('mx')}
                        </span>
                        <span className={`expand-icon ${expandedComponents.mx ? 'expanded' : ''}`}>
                          ▼
                        </span>
                      </div>
                    </div>
                    {expandedComponents.mx && (
                      <div className="component-expanded-content">
                        <div className="component-description">
                          <h5>{getComponentDescription('mx').title}</h5>
                          <p>{getComponentDescription('mx').description}</p>
                          <div className={`status-message ${result.mx?.enabled ? 'success' : 'failure'}`}>
                            <span className={`status-icon ${result.mx?.enabled ? 'success' : 'error'}`}>
                              {result.mx?.enabled ? '✅' : '❌'}
                            </span>
                            <span>{result.mx?.enabled ? getComponentDescription('mx').successMessage : getComponentDescription('mx').failureMessage}</span>
                          </div>
                        </div>
                        <div className="records-section">
                          <h5>Current Mail Servers:</h5>
                          {renderRecords('mx', result.mx?.records)}
                        </div>
                        
                        {/* Score Explanations */}
                        {result.security_score?.scoring_details?.mx_bonus > 0 && (
                          <div className="bonus-explanation">
                            <span className="bonus-indicator">+{result.security_score.scoring_details.mx_bonus} bonus points earned:</span>
                            <div className="bonus-details">
                              {getBonusExplanation('mx', result.security_score.scoring_details.mx_base, result.security_score.scoring_details.mx_bonus).split('\n').map((line, index) => (
                                <div key={index} className="bonus-line">{line}</div>
                              ))}
                            </div>
                          </div>
                        )}
                        {result.security_score?.scoring_details?.mx_base === 0 && (
                          <div className="missing-points-explanation">
                            <span className="missing-title">Missing: {getComponentMaxScore('mx')} points</span>
                            <div className="missing-details">
                              <div className="missing-line">• Basic MX records: +15 points</div>
                              <div className="missing-line">• Redundancy (3+ MX records): +5 points</div>
                              <div className="missing-line">• Trusted email provider: +3 points</div>
                              <div className="missing-line">• Secure mail server configuration: +2 points</div>
                            </div>
                          </div>
                        )}
                        {result.security_score?.scoring_details?.mx_base > 0 && result.security_score.scoring_details.mx_base < getComponentMaxScore('mx') && (
                          <div className="missing-points-explanation">
                            <span className="missing-title">Missing: {getComponentMaxScore('mx') - (result.security_score.scoring_details.mx_base + (result.security_score.scoring_details.mx_bonus || 0))} points</span>
                            <div className="missing-details">
                              {getMissingPointsExplanation('mx', result.security_score.scoring_details.mx_base + (result.security_score.scoring_details.mx_bonus || 0), getComponentMaxScore('mx')).split('\n').slice(1).map((line, index) => (
                                <div key={index} className="missing-line">• {line}</div>
                              ))}
                            </div>
                          </div>
                        )}
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
                        <span className={`status-icon ${getComponentIconClass(getComponentIcon(result.spf?.enabled, getComponentScore(result.security_score?.scoring_details?.spf_base || 0, result.security_score?.scoring_details?.spf_bonus || 0, 'spf')))}`}>
                          {getComponentIcon(result.spf?.enabled, getComponentScore(result.security_score?.scoring_details?.spf_base || 0, result.security_score?.scoring_details?.spf_bonus || 0, 'spf'))}
                        </span>
                        <span className="component-score">
                          {getComponentScore(result.security_score?.scoring_details?.spf_base || 0, result.security_score?.scoring_details?.spf_bonus || 0, 'spf')}/{getComponentMaxScore('spf')}
                        </span>
                        <span className={`expand-icon ${expandedComponents.spf ? 'expanded' : ''}`}>
                          ▼
                        </span>
                      </div>
                    </div>
                    {expandedComponents.spf && (
                      <div className="component-expanded-content">
                        <div className="component-description">
                          <h5>{getComponentDescription('spf').title}</h5>
                          <p>{getComponentDescription('spf').description}</p>
                          <div className={`status-message ${result.spf?.enabled ? 'success' : 'failure'}`}>
                            <span className={`status-icon ${result.spf?.enabled ? 'success' : 'error'}`}>
                              {result.spf?.enabled ? '✅' : '❌'}
                            </span>
                            <span>{result.spf?.enabled ? getComponentDescription('spf').successMessage : getComponentDescription('spf').failureMessage}</span>
                          </div>
                        </div>
                        <div className="records-section">
                          <h5>Current SPF Records:</h5>
                          {renderRecords('spf', result.spf?.records)}
                        </div>
                        
                        {/* Score Explanations */}
                        {result.security_score?.scoring_details?.spf_bonus > 0 && (
                          <div className="bonus-explanation">
                            <span className="bonus-indicator">+{result.security_score.scoring_details.spf_bonus} bonus points earned:</span>
                            <div className="bonus-details">
                              {getBonusExplanation('spf', result.security_score.scoring_details.spf_base, result.security_score.scoring_details.spf_bonus).split('\n').map((line, index) => (
                                <div key={index} className="bonus-line">{line}</div>
                              ))}
                            </div>
                          </div>
                        )}
                        {result.security_score?.scoring_details?.spf_base === 0 && (
                          <div className="missing-points-explanation">
                            <span className="missing-title">Missing: {getComponentMaxScore('spf')} points</span>
                            <div className="missing-details">
                              <div className="missing-line">• Basic SPF records: +10 points</div>
                              <div className="missing-line">• Strict SPF policy (-all): +8 points</div>
                              <div className="missing-line">• Include mechanisms for delegation: +2 points</div>
                              <div className="missing-line">• Direct IP specifications: +2 points</div>
                              <div className="missing-line">• Domain A/MX records: +1 point</div>
                              <div className="missing-line">• No redirect mechanisms: +2 points</div>
                            </div>
                          </div>
                        )}
                        {result.security_score?.scoring_details?.spf_base > 0 && result.security_score.scoring_details.spf_base < getComponentMaxScore('spf') && (
                          <div className="missing-points-explanation">
                            <span className="missing-title">Missing: {getComponentMaxScore('spf') - (result.security_score.scoring_details.spf_base + (result.security_score.scoring_details.spf_bonus || 0))} points</span>
                            <div className="missing-details">
                              {getMissingPointsExplanation('spf', result.security_score.scoring_details.spf_base + (result.security_score.scoring_details.spf_bonus || 0), getComponentMaxScore('spf')).split('\n').slice(1).map((line, index) => (
                                <div key={index} className="missing-line">• {line}</div>
                              ))}
                            </div>
                          </div>
                        )}
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
                        <span className={`status-icon ${getComponentIconClass(getComponentIcon(result.dkim?.enabled, getComponentScore(result.security_score?.scoring_details?.dkim_base || 0, result.security_score?.scoring_details?.dkim_bonus || 0, 'dkim')))}`}>
                          {getComponentIcon(result.dkim?.enabled, getComponentScore(result.security_score?.scoring_details?.dkim_base || 0, result.security_score?.scoring_details?.dkim_bonus || 0, 'dkim'))}
                        </span>
                        <span className="component-score">
                          {getComponentScore(result.security_score?.scoring_details?.dkim_base || 0, result.security_score?.scoring_details?.dkim_bonus || 0, 'dkim')}/{getComponentMaxScore('dkim')}
                        </span>
                        <span className={`expand-icon ${expandedComponents.dkim ? 'expanded' : ''}`}>
                          ▼
                        </span>
                      </div>
                    </div>
                    {expandedComponents.dkim && (
                      <div className="component-expanded-content">
                        <div className="component-description">
                          <h5>{getComponentDescription('dkim').title}</h5>
                          <p>{getComponentDescription('dkim').description}</p>
                          <div className={`status-message ${result.dkim?.enabled ? 'success' : 'failure'}`}>
                            <span className={`status-icon ${result.dkim?.enabled ? 'success' : 'error'}`}>
                              {result.dkim?.enabled ? '✅' : '❌'}
                            </span>
                            <span>{result.dkim?.enabled ? getComponentDescription('dkim').successMessage : getComponentDescription('dkim').failureMessage}</span>
                          </div>
                        </div>
                        <div className="records-section">
                          <h5>Current DKIM Records:</h5>
                          {renderRecords('dkim', result.dkim?.records)}
                        </div>
                        
                        {/* Score Explanations */}
                        {result.security_score?.scoring_details?.dkim_bonus > 0 && (
                          <div className="bonus-explanation">
                            <span className="bonus-indicator">+{result.security_score.scoring_details.dkim_bonus} bonus points earned:</span>
                            <div className="bonus-details">
                              {getBonusExplanation('dkim', result.security_score.scoring_details.dkim_base, result.security_score.scoring_details.dkim_bonus).split('\n').map((line, index) => (
                                <div key={index} className="bonus-line">{line}</div>
                              ))}
                            </div>
                          </div>
                        )}
                        {result.security_score?.scoring_details?.dkim_base === 0 && (
                          <div className="missing-points-explanation">
                            <span className="missing-title">Missing: {getComponentMaxScore('dkim')} points</span>
                            <div className="missing-details">
                              <div className="missing-line">• Basic DKIM records: +10 points</div>
                              <div className="missing-line">• Multiple DKIM selectors: +4 points</div>
                              <div className="missing-line">• Strong algorithm (RSA-2048+, Ed25519): +3 points</div>
                              <div className="missing-line">• Strong key length (2048+ bits): +2 points</div>
                            </div>
                          </div>
                        )}
                        {result.security_score?.scoring_details?.dkim_base > 0 && result.security_score.scoring_details.dkim_base < getComponentMaxScore('dkim') && (
                          <div className="missing-points-explanation">
                            <span className="missing-title">Missing: {getComponentMaxScore('dkim') - (result.security_score.scoring_details.dkim_base + (result.security_score.scoring_details.dkim_bonus || 0))} points</span>
                            <div className="missing-details">
                              {getMissingPointsExplanation('dkim', result.security_score.scoring_details.dkim_base + (result.security_score.scoring_details.dkim_bonus || 0), getComponentMaxScore('dkim')).split('\n').slice(1).map((line, index) => (
                                <div key={index} className="missing-line">• {line}</div>
                              ))}
                            </div>
                          </div>
                        )}
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
                        <span className={`status-icon ${getComponentIconClass(getComponentIcon(result.dmarc?.enabled, getComponentScore(result.security_score?.scoring_details?.dmarc_base || 0, result.security_score?.scoring_details?.dmarc_bonus || 0, 'dmarc')))}`}>
                          {getComponentIcon(result.dmarc?.enabled, getComponentScore(result.security_score?.scoring_details?.dmarc_base || 0, result.security_score?.scoring_details?.dmarc_bonus || 0, 'dmarc'))}
                        </span>
                        <span className="component-score">
                          {getComponentScore(result.security_score?.scoring_details?.dmarc_base || 0, result.security_score?.scoring_details?.dmarc_bonus || 0, 'dmarc')}/{getComponentMaxScore('dmarc')}
                        </span>
                        <span className={`expand-icon ${expandedComponents.dmarc ? 'expanded' : ''}`}>
                          ▼
                        </span>
                      </div>
                    </div>
                    {expandedComponents.dmarc && (
                      <div className="component-expanded-content">
                        <div className="component-description">
                          <h5>{getComponentDescription('dmarc').title}</h5>
                          <p>{getComponentDescription('dmarc').description}</p>
                          <div className={`status-message ${result.dmarc?.enabled ? 'success' : 'failure'}`}>
                            <span className={`status-icon ${result.dmarc?.enabled ? 'success' : 'error'}`}>
                              {result.dmarc?.enabled ? '✅' : '❌'}
                            </span>
                            <span>{result.dmarc?.enabled ? getComponentDescription('dmarc').successMessage : getComponentDescription('dmarc').failureMessage}</span>
                          </div>
                        </div>
                        <div className="records-section">
                          <h5>Current DMARC Records:</h5>
                          {renderRecords('dmarc', result.dmarc?.records)}
                        </div>
                        
                        {/* Score Explanations */}
                        {result.security_score?.scoring_details?.dmarc_bonus > 0 && (
                          <div className="bonus-explanation">
                            <span className="bonus-indicator">+{result.security_score.scoring_details.dmarc_bonus} bonus points earned:</span>
                            <div className="bonus-details">
                              {getBonusExplanation('dmarc', result.security_score.scoring_details.dmarc_base, result.security_score.scoring_details.dmarc_bonus).split('\n').map((line, index) => (
                                <div key={index} className="bonus-line">{line}</div>
                              ))}
                            </div>
                          </div>
                        )}
                        {result.security_score?.scoring_details?.dmarc_base === 0 && (
                          <div className="missing-points-explanation">
                            <span className="missing-title">Missing: {getComponentMaxScore('dmarc')} points</span>
                            <div className="missing-details">
                              <div className="missing-line">• Basic DMARC records: +15 points</div>
                              <div className="missing-line">• Strict DMARC policy (p=reject): +8 points</div>
                              <div className="missing-line">• Strict subdomain policy (sp=reject): +3 points</div>
                              <div className="missing-line">• Full coverage (pct=100): +2 points</div>
                              <div className="missing-line">• Aggregate reports configured (rua=): +2 points</div>
                              <div className="missing-line">• Forensic reports configured (ruf=): +1 point</div>
                            </div>
                          </div>
                        )}
                        {result.security_score?.scoring_details?.dmarc_base > 0 && result.security_score.scoring_details.dmarc_base < getComponentMaxScore('dmarc') && (
                          <div className="missing-points-explanation">
                            <span className="missing-title">Missing: {getComponentMaxScore('dmarc') - (result.security_score.scoring_details.dmarc_base + (result.security_score.scoring_details.dmarc_bonus || 0))} points</span>
                            <div className="missing-details">
                              {getMissingPointsExplanation('dmarc', result.security_score.scoring_details.dmarc_base + (result.security_score.scoring_details.dmarc_bonus || 0), getComponentMaxScore('dmarc')).split('\n').slice(1).map((line, index) => (
                                <div key={index} className="missing-line">• {line}</div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}



            {/* Issues and Recommendations Section - Split into two sections like email */}
            {!result.progressive && (
              <>
                {/* Issues Found Section */}
                {(() => {
                  const issues = [];
                  if (!result.dkim?.enabled) {
                    issues.push({
                      title: "No DKIM Records Found",
                      description: "No DKIM records found - emails may be marked as spam",
                      type: "critical"
                    });
                  }
                  if (!result.spf?.enabled) {
                    issues.push({
                      title: "No SPF Record Found",
                      description: "No SPF record found - domain vulnerable to email spoofing",
                      type: "critical"
                    });
                  }
                  if (!result.dmarc?.enabled) {
                    issues.push({
                      title: "No DMARC Record Found", 
                      description: "No DMARC record found - email authentication not enforced",
                      type: "critical"
                    });
                  }
                  return issues.length > 0;
                })() && (
                  <div className="issues-section">
                    <h3>🔍 Issues Found</h3>
                    <div className="issues-list">
                      {(() => {
                        const issues = [];
                        if (!result.dkim?.enabled) {
                          issues.push({
                            title: "No DKIM Records Found",
                            description: "No DKIM records found - emails may be marked as spam",
                            type: "critical"
                          });
                        }
                        if (!result.spf?.enabled) {
                          issues.push({
                            title: "No SPF Record Found",
                            description: "No SPF record found - domain vulnerable to email spoofing",
                            type: "critical"
                          });
                        }
                        if (!result.dmarc?.enabled) {
                          issues.push({
                            title: "No DMARC Record Found", 
                            description: "No DMARC record found - email authentication not enforced",
                            type: "critical"
                          });
                        }
                        return issues;
                      })().map((issue, index) => (
                        <div key={index} className={`issue-card ${getRecommendationIconClass(issue.type)}`}>
                          <div className="issue-header">
                            <div className="issue-icon">{getRecommendationIcon(issue.type)}</div>
                            <h4 className="issue-title">{issue.title}</h4>
                          </div>
                          <div className="issue-content">
                            <p className="issue-description">{issue.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Recommendations Section */}
                <div className="recommendations-section">
                  <h3>💡 Recommendations</h3>
                  {(() => {
                    console.log('🔍 Recommendations Debug:', {
                      hasRecommendations: !!result.recommendations,
                      recommendationsLength: result.recommendations?.length,
                      recommendations: result.recommendations,
                      isProgressive: result.progressive,
                      shouldShowIssues: result.recommendations && result.recommendations.length > 0
                    });
                    return result.recommendations && result.recommendations.length > 0;
                  })() ? (
                    <div className="recommendations-list">
                      {result.recommendations.map((rec, index) => (
                        <div key={index} className={`recommendation-card ${getRecommendationIconClass(rec.type)}`}>
                          <div className="recommendation-header">
                            <div className="recommendation-icon">{getRecommendationIcon(rec.type)}</div>
                            <h4 className="recommendation-title">{rec.title}</h4>
                          </div>
                          <div className="recommendation-content">
                            <p className="recommendation-description">{rec.description}</p>
                            {(rec.impact || rec.effort || rec.estimated_time) && (
                              <div className="recommendation-details">
                                {rec.impact && <span className="recommendation-impact">Impact: {rec.impact}</span>}
                                {rec.effort && <span className="recommendation-effort">Effort: {rec.effort}</span>}
                                {rec.estimated_time && <span className="recommendation-time">Time: {rec.estimated_time}</span>}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="no-recommendations">
                      <div className="no-recommendations-icon">✅</div>
                      <h4>No Recommendations Found</h4>
                      <p>Your domain has good email security configuration. All major security components are properly configured.</p>
                    </div>
                  )}
                </div>
              </>
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
                  Get a detailed report of this security analysis sent to your email
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
      
      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-content">
          <p className="footer-text">{getFooterText()}</p>
        </div>
      </footer>
    </div>
  );
}

export default App;

