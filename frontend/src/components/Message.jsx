import React, { useState } from 'react';
import './Message.css';

function Message({ message }) {
  const isUser = message.role === 'user';
  const [showSources, setShowSources] = useState(false);
  const hasSources = message.metadata?.sources && message.metadata.sources.length > 0;
  const isError = message.metadata?.isError;

  return (
    <div className={`message ${message.role} ${isError ? 'error' : ''}`}>
      <div className="message-avatar">
        {isUser ? (
          <div className="user-avatar">AU</div>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
          </svg>
        )}
      </div>
      <div className="message-content">
        <p className="message-text">{message.content}</p>
        
        {hasSources && (
          <div className="sources-section">
            <button 
              className="sources-toggle"
              onClick={() => setShowSources(!showSources)}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
              </svg>
              <span>{message.metadata.sources.length} source{message.metadata.sources.length !== 1 ? 's' : ''}</span>
              <svg 
                width="12" 
                height="12" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                strokeWidth="2"
                style={{ transform: showSources ? 'rotate(180deg)' : 'rotate(0)', transition: 'transform 0.2s' }}
              >
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </button>
            
            {showSources && (
              <div className="sources-list">
                {message.metadata.sources.map((source, index) => (
                  <div key={index} className="source-item">
                    <div className="source-header">
                      <strong>{source.doc_id || `Source ${index + 1}`}</strong>
                      {source.similarity !== undefined && (
                        <span className="source-score">
                          {(source.similarity * 100).toFixed(0)}% match
                        </span>
                      )}
                    </div>
                    {source.section && (
                      <p className="source-section">{source.section}</p>
                    )}
                    {source.confidence !== undefined && (
                      <span className="source-confidence">
                        Confidence: {(source.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {message.metadata?.confidence && (
          <div className="message-meta">
            <span className="confidence-badge">
              Confidence: {message.metadata.confidence}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export default Message;
