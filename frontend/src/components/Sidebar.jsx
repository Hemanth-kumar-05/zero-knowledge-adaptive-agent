import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Sidebar.css';
import Modal from './Modal';

function Sidebar({ sessions, currentSession, onNewChat, onSelectSession, onRefresh, isOpen, onToggle, user, healthStatus, onLogout, onDeleteSession }) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [deleteModal, setDeleteModal] = useState({ isOpen: false, sessionId: null });
  const [imageError, setImageError] = useState(false);
  const navigate = useNavigate();
  
  const getInitials = (name) => {
    if (!name) return 'U';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };
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
            <div key={session.id} className="session-item-wrapper">
              <button
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
              <button
                className="delete-session-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  setDeleteModal({ isOpen: true, sessionId: session.id });
                }}
                title="Delete session"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
              </button>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          {healthStatus && (
            <div className="health-status" title={`System: ${healthStatus.status || 'unknown'}`}>
              <div className="health-indicator" style={{ backgroundColor: getHealthColor() }}></div>
              <span>{healthStatus.status || 'unknown'}</span>
            </div>
          )}
          <div className="user-section">
            <div className="user-info" onClick={() => setShowUserMenu(!showUserMenu)}>
              <div className={`user-avatar ${user?.profile_picture && !imageError ? 'has-image' : ''}`}>
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
              <span className="user-name">{user?.name || 'Anonymous User'}</span>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginLeft: 'auto' }}>
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </div>
            {showUserMenu && (
              <div className="user-menu">
                <button className="user-menu-item" onClick={() => {
                  setShowUserMenu(false);
                  navigate('/preferences');
                }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M12 1v6m0 6v6m-6-6h6m6 0h6M4.93 4.93l4.24 4.24m5.66 5.66l4.24 4.24M4.93 19.07l4.24-4.24m5.66-5.66l4.24-4.24"></path>
                  </svg>
                  <span>Preferences</span>
                </button>
                <button className="user-menu-item logout" onClick={() => {
                  setShowUserMenu(false);
                  onLogout();
                }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                    <polyline points="16 17 21 12 16 7"></polyline>
                    <line x1="21" y1="12" x2="9" y2="12"></line>
                  </svg>
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {isOpen && <div className="sidebar-overlay" onClick={onToggle}></div>}
      
      <Modal
        isOpen={deleteModal.isOpen}
        onClose={() => setDeleteModal({ isOpen: false, sessionId: null })}
        onConfirm={() => onDeleteSession(deleteModal.sessionId)}
        title="Delete Session"
        message="Delete this session and all its messages?"
        confirmText="Delete"
        cancelText="Cancel"
        confirmVariant="danger"
      />
    </>
  );
}

export default Sidebar;
