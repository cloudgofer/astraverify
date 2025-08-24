import React, { useState } from 'react';
import config from './config';
import './App.css';

function App() {
  const [domain, setDomain] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const checkDomain = async () => {
    if (!domain.trim()) {
      setError('Please enter a domain name');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const url = `${config.API_BASE_URL}${config.ENDPOINTS.CHECK_DOMAIN}?domain=${encodeURIComponent(domain.trim())}`;
      console.log('Making request to:', url);
      
      const response = await fetch(url);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', response.status, errorText);
        throw new Error(`HTTP error! status: ${response.status} - ${errorText.substring(0, 100)}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        console.error('Non-JSON response:', text);
        throw new Error(`Expected JSON but got ${contentType}. Response: ${text.substring(0, 200)}`);
      }
      
      const data = await response.json();
      // Add timestamp
      data.analysis_timestamp = new Date().toISOString();
      setResult(data);
    } catch (err) {
      console.error('Full error details:', err);
      setError(`Error checking domain: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      checkDomain();
    }
  };

  const getScoreColor = (score) => {
    if (score >= 90) return '#4CAF50';
    if (score >= 75) return '#8BC34A';
    if (score >= 50) return '#FFC107';
    if (score >= 25) return '#FF9800';
    return '#F44336';
  };

  const getRecommendationIcon = (type) => {
    switch (type) {
      case 'critical': return '🚨';
      case 'important': return '⚠️';
      case 'info': return 'ℹ️';
      default: return '💡';
    }
  };

  const getRecommendationColor = (type) => {
    switch (type) {
      case 'critical': return '#F44336';
      case 'important': return '#FF9800';
      case 'info': return '#2196F3';
      default: return '#9E9E9E';
    }
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
            disabled={loading}
          />
          <button 
            onClick={checkDomain} 
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
            <div className="result-header">
              <h2>Security Analysis for: {result.domain}</h2>
              <div className="security-score">
                <div className="score-circle" style={{ borderColor: getScoreColor(result.security_score.score) }}>
                  <span className="score-number">{result.security_score.score}</span>
                  <span className="score-grade">{result.security_score.grade}</span>
                </div>
                <div className="score-details">
                  <h3>{result.security_score.status}</h3>
                  <p>Email Security Score</p>
                </div>
              </div>
            </div>

            <div className="analysis-grid">
              <div className={`analysis-card ${result.mx.enabled ? 'success' : 'failure'}`}>
                <div className="card-header">
                  <h3>MX Records</h3>
                  <span className={`status-badge ${result.mx.enabled ? 'success' : 'failure'}`}>
                    {result.mx.status}
                  </span>
                </div>
                <p className="card-description">{result.mx.description}</p>
                {result.mx.records.length > 0 && (
                  <div className="records-list">
                    {result.mx.records.map((record, index) => (
                      <div key={index} className="record-item">
                        <span className="record-priority">Priority: {record.priority}</span>
                        <span className="record-server">{record.server}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className={`analysis-card ${result.spf.enabled ? 'success' : 'failure'}`}>
                <div className="card-header">
                  <h3>SPF Records</h3>
                  <span className={`status-badge ${result.spf.enabled ? 'success' : 'failure'}`}>
                    {result.spf.status}
                  </span>
                </div>
                <p className="card-description">{result.spf.description}</p>
                {result.spf.records.length > 0 && (
                  <div className="records-list">
                    {result.spf.records.map((record, index) => (
                      <div key={index} className="record-item">
                        <code className="record-text">{record.record}</code>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className={`analysis-card ${result.dkim.enabled ? 'success' : 'failure'}`}>
                <div className="card-header">
                  <h3>DKIM Records</h3>
                  <span className={`status-badge ${result.dkim.enabled ? 'success' : 'failure'}`}>
                    {result.dkim.status}
                  </span>
                </div>
                <p className="card-description">{result.dkim.description}</p>
                {result.dkim.records.length > 0 && (
                  <div className="records-list">
                    {result.dkim.records.map((record, index) => (
                      <div key={index} className="record-item">
                        <span className="record-selector">Selector: {record.selector}</span>
                        <code className="record-text">{record.record}</code>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className={`analysis-card ${result.dmarc.enabled ? 'success' : 'failure'}`}>
                <div className="card-header">
                  <h3>DMARC Records</h3>
                  <span className={`status-badge ${result.dmarc.enabled ? 'success' : 'failure'}`}>
                    {result.dmarc.status}
                  </span>
                </div>
                <p className="card-description">{result.dmarc.description}</p>
                {result.dmarc.records.length > 0 && (
                  <div className="records-list">
                    {result.dmarc.records.map((record, index) => (
                      <div key={index} className="record-item">
                        <code className="record-text">{record.record}</code>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {result.recommendations.length > 0 && (
              <div className="recommendations-section">
                <h3>Recommendations</h3>
                <div className="recommendations-list">
                  {result.recommendations.map((rec, index) => (
                    <div key={index} className="recommendation-item" style={{ borderLeftColor: getRecommendationColor(rec.type) }}>
                      <div className="recommendation-icon">{getRecommendationIcon(rec.type)}</div>
                      <div className="recommendation-content">
                        <h4>{rec.title}</h4>
                        <p>{rec.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="analysis-footer">
              <p>Analysis completed at: {new Date(result.analysis_timestamp).toLocaleString()}</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
