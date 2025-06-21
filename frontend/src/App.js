// src/App.js
import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [target, setTarget] = useState('');
  const [scanDepth, setScanDepth] = useState('normal');
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedPlaybook, setSelectedPlaybook] = useState(null);
  const [executionResult, setExecutionResult] = useState('');
  const [engagementHistory, setEngagementHistory] = useState([]);

  const analyzeTarget = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target,
          scan_depth: scanDepth
        })
      });
      
      const data = await response.json();
      setRecommendations(data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const executePlaybook = async (playbookId, commands) => {
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/execute/${playbookId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(commands)
      });
      
      const data = await response.json();
      setExecutionResult(data.output);
      setSelectedPlaybook(playbookId);
      
      // Refresh history
      fetchEngagementHistory();
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchEngagementHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/engagements?limit=5');
      const data = await response.json();
      setEngagementHistory(data);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  useEffect(() => {
    fetchEngagementHistory();
  }, []);

  return (
    <div className="container">
      <header className="header">
        <h1>SHADOW CHAMELEON</h1>
        <p>Your AI Red Team Partner That Evolves With Every Engagement</p>
      </header>

      <div className="main-content">
        <div className="input-section">
          <h2>Target Analysis</h2>
          <div className="input-group">
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="Enter domain or IP address"
            />
            <select value={scanDepth} onChange={(e) => setScanDepth(e.target.value)}>
              <option value="quick">Quick Scan</option>
              <option value="normal">Normal Scan</option>
              <option value="thorough">Thorough Scan</option>
            </select>
            <button onClick={analyzeTarget} disabled={isLoading || !target}>
              {isLoading ? 'Analyzing...' : 'Analyze Target'}
            </button>
          </div>
        </div>

        {isLoading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Analyzing target and generating attack paths...</p>
          </div>
        )}

        {recommendations.length > 0 && (
          <div className="recommendations-section">
            <h2>Recommended Playbooks</h2>
            <div className="playbooks-grid">
              {recommendations.map((pb) => (
                <div key={pb.playbook_id} className={`playbook-card ${selectedPlaybook === pb.playbook_id ? 'selected' : ''}`}>
                  <h3>{pb.name}</h3>
                  <p>{pb.description}</p>
                  <div className="confidence-meter">
                    <div 
                      className="confidence-bar" 
                      style={{ width: `${pb.confidence * 100}%` }}
                    ></div>
                    <span>Confidence: {Math.round(pb.confidence * 100)}%</span>
                  </div>
                  
                  {pb.visualization && (
                    <div className="graph-visualization">
                      <img 
                        src={`data:image/png;base64,${pb.visualization}`} 
                        alt="Attack graph visualization"
                      />
                    </div>
                  )}
                  
                  <div className="commands-preview">
                    <h4>Commands:</h4>
                    <ul>
                      {pb.commands.map((cmd, i) => (
                        <li key={i}><code>{cmd}</code></li>
                      ))}
                    </ul>
                  </div>
                  
                  <button 
                    onClick={() => executePlaybook(pb.playbook_id, pb.commands)}
                    disabled={isLoading}
                  >
                    Execute Playbook
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {executionResult && (
          <div className="execution-results">
            <h2>Execution Results</h2>
            <pre>{executionResult}</pre>
          </div>
        )}

        <div className="history-section">
          <h2>Recent Engagements</h2>
          <div className="history-grid">
            {engagementHistory.map((eng) => (
              <div key={eng.id} className="history-card">
                <h3>{eng.target}</h3>
                <p>{new Date(eng.timestamp).toLocaleString()}</p>
                <div className="tech-summary">
                  <h4>Technologies Found:</h4>
                  <ul>
                    {eng.tech_stack.services.slice(0, 3).map((srv, i) => (
                      <li key={i}>{srv.name} ({srv.port}) - {srv.product}</li>
                    ))}
                    {eng.tech_stack.services.length > 3 && (
                      <li>+{eng.tech_stack.services.length - 3} more...</li>
                    )}
                  </ul>
                </div>
                <button onClick={() => {
                  setRecommendations(eng.results);
                  window.scrollTo(0, document.querySelector('.recommendations-section').offsetTop);
                }}>
                  View Details
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <footer className="footer">
        <p>SHADOW CHAMELEON - AI Red Team Partner</p>
        <p className="disclaimer">
          WARNING: This tool is for authorized security testing only. 
          Unauthorized use against systems you don't own is illegal.
        </p>
      </footer>
    </div>
  );
}

export default App;
