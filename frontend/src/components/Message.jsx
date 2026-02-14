import React, { useState } from 'react';
import './Message.css';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import RiskAlertDisplay from './RiskAlertDisplay';

/* ---------------- MARKDOWN CONFIG ---------------- */

marked.setOptions({
  gfm: true,
  breaks: true,
  headerIds: false,
  mangle: false
});

const renderMarkdown = (text) => {
  if (!text) return '';

  // Remove source citations but KEEP formatting
  const cleaned = text
    .replace(/\(Source:[^)]*\)/gi, '')
    .replace(/\(Source:[^)]*$/gi, '')
    .replace(/Source:[^.]*\./gi, '')
    .trim();

  const rawHtml = marked.parse(cleaned);
  return DOMPurify.sanitize(rawHtml);
};

/* ---------------- COMPONENT ---------------- */

function Message({ message, user }) {
  const isUser = message.role === 'user';
  const [showSources, setShowSources] = useState(null);
  const [imageError, setImageError] = useState(false);
  const hasSources =
    message.metadata?.sources && message.metadata.sources.length > 0;
  const isError = message.metadata?.isError;

  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const formatDocName = (docId) => {
    if (!docId) return 'Unknown Document';
    return docId
      .replace('ncie_', '')
      .replace(/_/g, ' ')
      .split(' ')
      .map(
        (word) => word.charAt(0).toUpperCase() + word.slice(1)
      )
      .join(' ');
  };

  const getRelevanceColor = (similarity) => {
    if (similarity >= 0.8) return '#10a37f';
    if (similarity >= 0.6) return '#fbbf24';
    return '#94a3b8';
  };

  const getRelevanceLabel = (similarity) => {
    if (similarity >= 0.8) return 'Highly Relevant';
    if (similarity >= 0.6) return 'Relevant';
    return 'Related';
  };

  const topSources = message.metadata?.sources?.slice(0, 3) || [];
  const hasExtractedPreferences = message.extracted_preferences && message.extracted_preferences.length > 0;
  const hasRiskAlerts = message.metadata?.risk_alerts && message.metadata.risk_alerts.length > 0;

  return (
    <div className={`message ${message.role} ${isError ? 'error' : ''}`}>
      <div className="message-avatar">
        {isUser ? (
          <div
            className={`user-avatar ${
              user?.profile_picture && !imageError ? 'has-image' : ''
            }`}
          >
            {user?.profile_picture && !imageError ? (
              <img 
                src={user.profile_picture} 
                alt="User Avatar"
                onError={() => setImageError(true)}
              />
            ) : (
              <span className="avatar-initials">
                {getInitials(user?.name)}
              </span>
            )}
          </div>
        ) : (
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="currentColor"
          >
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" />
          </svg>
        )}
      </div>

      <div className="message-content">
        {/* Risk Alert Indicator - Top Right */}
        {!isUser && hasRiskAlerts && (
          <div className="message-risk-indicator">
            <RiskAlertDisplay riskAlerts={message.metadata.risk_alerts} />
          </div>
        )}

        {/* 🔥 FIXED MARKDOWN RENDERING */}
        <div
          className="message-text"
          dangerouslySetInnerHTML={{
            __html: renderMarkdown(message.content)
          }}
        />

        {hasSources && topSources.length > 0 && (
          <div className="sources-tags">
            {topSources.map((source, index) => {
              const relevanceColor = getRelevanceColor(
                source.similarity || 0
              );
              return (
                <button
                  key={index}
                  className="source-tag"
                  onClick={() =>
                    setShowSources(
                      showSources === index ? null : index
                    )
                  }
                  title={`${formatDocName(source.doc_id)} - ${
                    source.section
                  }`}
                >
                  <svg
                    width="12"
                    height="12"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  <span>{index + 1}</span>
                </button>
              );
            })}
          </div>
        )}

        {showSources !== null && topSources[showSources] && (
          <div className="source-detail">
            {(() => {
              const source = topSources[showSources];
              const relevanceColor = getRelevanceColor(
                source.similarity || 0
              );
              return (
                <div
                  className="source-detail-content"
                  style={{ borderLeftColor: relevanceColor }}
                >
                  <div className="source-detail-header">
                    <span className="source-detail-title">
                      <strong>
                        {formatDocName(source.doc_id)}
                      </strong>
                    </span>
                    <button
                      className="source-detail-close"
                      onClick={() => setShowSources(null)}
                    >
                      ×
                    </button>
                  </div>

                  <p className="source-detail-section">
                    {source.section}
                  </p>

                  <div className="source-detail-footer">
                    <span
                      className="source-detail-relevance"
                      style={{ color: relevanceColor }}
                    >
                      {getRelevanceLabel(source.similarity)}
                    </span>
                    <span
                      className="source-detail-match"
                      style={{ color: relevanceColor }}
                    >
                      {(source.similarity * 100).toFixed(0)}%
                      match
                    </span>
                  </div>
                </div>
              );
            })()}
          </div>
        )}

        {message.metadata?.confidence && (
          <div className="message-meta">
            <span className="confidence-badge">
              Confidence: {message.metadata.confidence}
            </span>
          </div>
        )}

        {hasExtractedPreferences && isUser && (
          <div className="preference-indicator">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
            </svg>
            <span>Preference learned from this message</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default Message;
