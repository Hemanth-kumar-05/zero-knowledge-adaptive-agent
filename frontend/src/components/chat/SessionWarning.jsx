import React from 'react';
import './SessionWarning.css';

function SessionWarning({ warning, onNewSession, onContinue }) {
  const isHighSeverity = warning.severity === 'high';
  
  return (
    <div className={`session-warning ${isHighSeverity ? 'high-severity' : 'medium-severity'}`}>
      <div className="session-warning-icon">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      </div>
      
      <div className="session-warning-content">
        <h3 className="session-warning-title">
          {isHighSeverity ? 'Session Limit Reached' : 'Session Getting Long'}
        </h3>
        <p className="session-warning-message">{warning.message}</p>
        <p className="session-warning-suggestion">{warning.suggestion}</p>
        
        <div className="session-warning-actions">
          <button 
            className="warning-btn warning-btn-primary" 
            onClick={onNewSession}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            Start New Session
          </button>
          <button 
            className="warning-btn warning-btn-secondary" 
            onClick={onContinue}
          >
            Continue Here
          </button>
        </div>
      </div>
      
      <button className="session-warning-close" onClick={onContinue}>
        ×
      </button>
    </div>
  );
}

export default SessionWarning;
