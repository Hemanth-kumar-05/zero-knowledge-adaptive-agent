import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { extensionsAPI } from '../../api/extensions';
import './Sidebar.css';
import Modal from '../common/Modal';
import ExtensionFilesModal from '../extensions/ExtensionFilesModal';
import Toast from '../common/Toast';

function Sidebar({ sessions, currentSession, onNewChat, onSelectSession, onRefresh, isOpen, onToggle, user, healthStatus, onLogout, onDeleteSession }) {
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [deleteModal, setDeleteModal] = useState({ isOpen: false, sessionId: null });
  const [imageError, setImageError] = useState(false);
  const [extensions, setExtensions] = useState([]);
  const [isLoadingExtensions, setIsLoadingExtensions] = useState(false);
  const [showFilesModal, setShowFilesModal] = useState(false);
  const [pendingSession, setPendingSession] = useState(null);
  const [requiredFiles, setRequiredFiles] = useState([]);
  const [toast, setToast] = useState(null);
  const navigate = useNavigate();

  const showToast = (message, type = 'info', duration = 5000) => {
    setToast({ message, type, duration });
  };
  
  // Load extensions when user has access
  useEffect(() => {
    const loadExtensions = async () => {
      if (user && (user.role === 'faculty' || user.role === 'admin')) {
        try {
          setIsLoadingExtensions(true);
          const extensionsData = await extensionsAPI.getAllExtensions(true);
          // Show only first 3 as featured
          setExtensions(extensionsData.slice(0, 3));
        } catch (error) {
          console.error('Failed to load extensions:', error);
          setExtensions([]);
        } finally {
          setIsLoadingExtensions(false);
        }
      }
    };

    loadExtensions();
  }, [user]);
  
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

  const handleExtensionClick = async (extension) => {
    try {
      // Create a new session with this extension
      const response = await extensionsAPI.createExtensionSession(extension.id);
      
      // Check if extension requires files
      if (response.requires_files && response.required_file_types && response.required_file_types.length > 0) {
        // Show file requirement modal
        setRequiredFiles(response.required_file_types);
        setPendingSession(response.session_id);
        setShowFilesModal(true);
      } else {
        // Navigate to the new session
        navigate(`/${response.session_id}`);
        
        // Refresh sessions list to show the new session
        if (onRefresh) {
          onRefresh();
        }
      }
    } catch (error) {
      console.error('Error creating extension session:', error);
      showToast('Failed to start extension session. Please try again.', 'error');
    }
  };

  const handleProceedWithFiles = () => {
    setShowFilesModal(false);
    if (pendingSession) {
      navigate(`/${pendingSession}`);
      
      // Refresh sessions list to show the new session
      if (onRefresh) {
        onRefresh();
      }
      setPendingSession(null);
    }
  };

  const handleCancelFiles = () => {
    setShowFilesModal(false);
    setPendingSession(null);
    setRequiredFiles([]);
  };

  const handleExploreExtensions = () => {
    // Role-based redirect: faculty -> /extensions, admin -> /extensions/manage
    if (isAdmin) {
      navigate('/extensions/manage');
    } else {
      navigate('/extensions');
    }
  };

  const handleManageExtensions = () => {
    navigate('/extensions/manage');
  };

  // Check if user has access to extensions
  const hasExtensionAccess = user?.role === 'faculty' || user?.role === 'admin';
  const isAdmin = user?.role === 'admin';

  // Get category color for extension
  const getCategoryColor = (category) => {
    const colors = {
      'Academic': '#10a37f',
      'Planning': '#8b5cf6',
      'Research': '#ec4899',
      'Career': '#f59e0b',
      'Learning': '#06b6d4'
    };
    return colors[category] || '#6366f1';
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

        {/* Extensions Section - Only for Faculty and Admin */}
        {hasExtensionAccess && (
          <div className="extensions-section">
            <div className="extensions-header">
              <span className="extensions-label">Extensions</span>
              {isAdmin && (
                <button
                  className="manage-extensions-link"
                  onClick={handleManageExtensions}
                  title="Manage extensions"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="3"></circle>
                    <path d="M12 1v6m0 6v6m-6-6h6m6 0h6M4.93 4.93l4.24 4.24m5.66 5.66l4.24 4.24M4.93 19.07l4.24-4.24m5.66-5.66l4.24-4.24"></path>
                  </svg>
                </button>
              )}
            </div>
            <div className="extensions-list">
              {isLoadingExtensions ? (
                <div className="extensions-loading">Loading...</div>
              ) : extensions.length > 0 ? (
                <>
                  {extensions.map((extension) => (
                    <div key={extension.id} className="extension-item-wrapper">
                      <button
                        className="extension-item"
                        onClick={() => handleExtensionClick(extension)}
                        title={extension.name}
                      >
                        <div 
                          className="extension-icon" 
                        >
                          <i className={extension.icon} style={{ fontSize: '16px' }}></i>
                        </div>
                        <span className="extension-name">{extension.name}</span>
                      </button>
                    </div>
                  ))}
                  <button
                    className="explore-extensions-btn"
                    onClick={handleExploreExtensions}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="7" height="7"></rect>
                      <rect x="14" y="3" width="7" height="7"></rect>
                      <rect x="14" y="14" width="7" height="7"></rect>
                      <rect x="3" y="14" width="7" height="7"></rect>
                    </svg>
                    <span>Explore Extensions</span>
                  </button>
                </>
              ) : (
                <div className="no-extensions">
                  {isAdmin ? (
                    <>
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: '#4d4d4d', marginBottom: '4px' }}>
                        <rect x="3" y="3" width="7" height="7" rx="1"></rect>
                        <rect x="14" y="3" width="7" height="7" rx="1"></rect>
                        <rect x="14" y="14" width="7" height="7" rx="1"></rect>
                        <rect x="3" y="14" width="7" height="7" rx="1"></rect>
                      </svg>
                      <p>No extensions yet</p>
                      <button className="create-extension-link" onClick={handleManageExtensions}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '4px' }}>
                          <line x1="12" y1="5" x2="12" y2="19"></line>
                          <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                        Create Extension
                      </button>
                    </>
                  ) : (
                    <>
                      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: '#4d4d4d', marginBottom: '4px' }}>
                        <rect x="3" y="3" width="7" height="7" rx="1"></rect>
                        <rect x="14" y="3" width="7" height="7" rx="1"></rect>
                        <rect x="14" y="14" width="7" height="7" rx="1"></rect>
                        <rect x="3" y="14" width="7" height="7" rx="1"></rect>
                      </svg>
                      <p>No extensions available</p>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

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
                title={session.extension_name 
                  ? `${session.extension_name} • ${session.message_count || 0} messages • ${formatDate(session.updated_at || session.created_at)}`
                  : `${session.message_count || 0} messages • ${formatDate(session.updated_at || session.created_at)}`
                }
              >
                {session.extension_icon ? (
                  <i className={session.extension_icon} style={{ fontSize: '16px', width: '16px', textAlign: 'center' }}></i>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                )}
                <div className="session-info">
                  <span className="session-title">
                    {session.extension_name 
                      ? session.extension_name
                      : session.message_count > 0 ? `Chat (${session.message_count})` : 'New Chat'
                    }
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
                <button className="user-menu-item" onClick={() => {
                  setShowUserMenu(false);
                  navigate('/memory');
                }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
                    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
                  </svg>
                  <span>Memory</span>
                </button>
                
                {/* RBAC: Extensions - Available for Faculty and Admin only */}
                {(user?.role === 'faculty' || user?.role === 'admin') && (
                  <button className="user-menu-item" onClick={() => {
                    setShowUserMenu(false);
                    navigate('/extensions');
                  }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="7" height="7"></rect>
                      <rect x="14" y="3" width="7" height="7"></rect>
                      <rect x="14" y="14" width="7" height="7"></rect>
                      <rect x="3" y="14" width="7" height="7"></rect>
                    </svg>
                    <span>Extensions</span>
                  </button>
                )}
                
                {/* RBAC: Policy Updates - Available for Admin only */}
                {user?.role === 'admin' && (
                  <button className="user-menu-item" onClick={() => {
                    setShowUserMenu(false);
                    navigate('/policy-updates');
                  }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="16" y1="13" x2="8" y2="13"></line>
                      <line x1="16" y1="17" x2="8" y2="17"></line>
                      <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                    <span>Policy Updates</span>
                  </button>
                )}

                {user?.role === 'admin' && (
                  <button className="user-menu-item" onClick={() => {
                    setShowUserMenu(false);
                    navigate('/admin/users');
                  }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                      <circle cx="8.5" cy="7" r="4"></circle>
                      <path d="M20 8v6"></path>
                      <path d="M23 11h-6"></path>
                    </svg>
                    <span>User Management</span>
                  </button>
                )}
                
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
      
      <ExtensionFilesModal
        isOpen={showFilesModal}
        onClose={handleCancelFiles}
        requiredFiles={requiredFiles}
        onProceed={handleProceedWithFiles}
      />

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={toast.duration}
          onClose={() => setToast(null)}
        />
      )}
    </>
  );
}

export default Sidebar;
