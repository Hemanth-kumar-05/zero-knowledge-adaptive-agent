import React from 'react';
import './Sidebar.css';

function Sidebar({ sessions, currentSession, onNewChat, onSelectSession, onRefresh, isOpen, onToggle, healthStatus }) {
  const formatDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getHealthColor = () => {
    if (!healthStatus) return 'gray';
    switch (healthStatus.status) {
      case 'healthy': return '#10a37f';
      case 'degraded': return '#ff9800';
      case 'unhealthy': return '#f44336';
      default: return 'gray';
    }
  };

  return (
    <>
      <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={onNewChat}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            <span>New chat</span>
          </button>
          <button className="refresh-btn" onClick={onRefresh} title="Refresh sessions">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
            </svg>
          </button>
        </div>

        <div className="sessions-list">
          {sessions.length === 0 && (
            <div className="no-sessions">
              <p>No sessions yet</p>
              <p className="hint">Start a new chat to begin</p>
            </div>
          )}
          {sessions.map((session) => (
            <button
              key={session.id}
              className={`session-item ${
                currentSession?.id === session.id ? 'active' : ''
              }`}
              onClick={() => onSelectSession(session)}
              title={`${session.message_count || 0} messages • ${formatDate(session.updated_at || session.created_at)}`}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
              <div className="session-info">
                <span className="session-title">
                  {session.message_count > 0 ? `Chat (${session.message_count})` : 'New Chat'}
                </span>
                <span className="session-time">{formatDate(session.updated_at || session.created_at)}</span>
              </div>
            </button>
          ))}
        </div>

        <div className="sidebar-footer">
          {healthStatus && (
            <div className="health-status" title={`System: ${healthStatus.status || 'unknown'}`}>
              <div className="health-indicator" style={{ backgroundColor: getHealthColor() }}></div>
              <span>{healthStatus.status || 'unknown'}</span>
            </div>
          )}
          <div className="user-info">
            <div className="user-avatar">AU</div>
            <span className="user-name">Anonymous User</span>
          </div>
        </div>
      </div>

      {isOpen && <div className="sidebar-overlay" onClick={onToggle}></div>}
    </>
  );
}

export default Sidebar;
