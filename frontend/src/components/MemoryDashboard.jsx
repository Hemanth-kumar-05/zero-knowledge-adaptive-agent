import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './MemoryDashboard.css';
import api from '../api/client';
import Dialog from './Dialog';

/**
 * MemoryDashboard Component
 * Allows users to view and manage their stored facts
 */
function MemoryDashboard({ user, isSidebarOpen, onToggleSidebar, showToast }) {
  const navigate = useNavigate();
  const [facts, setFacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [stats, setStats] = useState({ total_count: 0, categories: {} });
  const [dialogState, setDialogState] = useState({
    isOpen: false,
    type: 'confirm',
    title: '',
    message: '',
    onConfirm: null
  });
  
  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }
    fetchMemory();
  }, [user, navigate]);

  const fetchMemory = async () => {
    try {
      setLoading(true);
      const response = await api.getMemory();
      setFacts(response.facts || []);
      setStats({
        total_count: response.total_count || 0,
        categories: response.categories || {}
      });
      setError(null);
    } catch (err) {
      setError('Failed to load memory. Please try again.');
      console.error('Error fetching memory:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFact = async (key) => {
    setDialogState({
      isOpen: true,
      type: 'danger',
      title: 'Delete Fact',
      message: `Are you sure you want to forget "${key}"? This action cannot be undone.`,
      onConfirm: async () => {
        try {
          await api.forgetFact(key);
          setFacts(facts.filter(f => f.key !== key));
          setStats(prev => ({
            total_count: prev.total_count - 1,
            categories: {
              ...prev.categories,
              [facts.find(f => f.key === key)?.category]: 
                (prev.categories[facts.find(f => f.key === key)?.category] || 1) - 1
            }
          }));
          showToast('Fact deleted successfully', 'success');
        } catch (err) {
          showToast('Failed to delete fact. Please try again.', 'error');
          console.error('Error deleting fact:', err);
        }
      }
    });
  };

  const handleLockFact = async (key, currentLockState) => {
    try {
      await api.lockFact(key, !currentLockState);
      setFacts(facts.map(f => 
        f.key === key ? { ...f, locked: !currentLockState } : f
      ));
      showToast(`Fact ${!currentLockState ? 'locked' : 'unlocked'} successfully`, 'success');
    } catch (err) {
      showToast('Failed to lock/unlock fact. Please try again.', 'error');
      console.error('Error locking fact:', err);
    }
  };

  const handleResetMemory = async (category = null) => {
    const title = category ? 'Delete Category' : 'Delete Everything';
    const message = category
      ? `Delete all facts in category "${getCategoryLabel(category)}"? This action cannot be undone!`
      : 'Delete ALL your stored information? This cannot be undone!';
    
    setDialogState({
      isOpen: true,
      type: 'danger',
      title,
      message,
      onConfirm: async () => {
        try {
          await api.resetMemory(category);
          if (category) {
            setFacts(facts.filter(f => f.category !== category));
            setStats(prev => ({
              total_count: prev.total_count - (prev.categories[category] || 0),
              categories: { ...prev.categories, [category]: 0 }
            }));
            showToast(`All ${getCategoryLabel(category)} facts deleted`, 'success');
          } else {
            setFacts([]);
            setStats({ total_count: 0, categories: {} });
            showToast('All memory deleted successfully', 'success');
          }
        } catch (err) {
          showToast('Failed to reset memory. Please try again.', 'error');
          console.error('Error resetting memory:', err);
        }
      }
    });
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'identity':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        );
      case 'academic_context':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
            <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
          </svg>
        );
      case 'concern':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        );
      default:
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
        );
    }
  };

  const getCategoryLabel = (category) => {
    return category.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const getRetentionBadge = (retention) => {
    const badges = {
      permanent: { label: 'Permanent', class: 'retention-permanent' },
      semester: { label: 'Semester', class: 'retention-semester' },
      session: { label: 'Session', class: 'retention-session' }
    };
    return badges[retention] || badges.permanent;
  };

  const formatValue = (value) => {
    if (Array.isArray(value)) {
      return value.join(', ');
    }
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  const filteredFacts = categoryFilter === 'all'
    ? facts
    : facts.filter(f => f.category === categoryFilter);

  if (loading) {
    return (
      <div className="memory-dashboard">
        <div className="memory-header">
          <button className="toggle-sidebar-btn" onClick={onToggleSidebar}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>
          <div className="header-left">
            <div>
              <h1 className="page-title">My Memory</h1>
            </div>
          </div>
        </div>
        <div className="memory-content">
          <div className="loading-spinner">Loading...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="memory-dashboard">
      <div className="memory-header">
        <button className="toggle-sidebar-btn" onClick={onToggleSidebar}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
        <div className="header-left">
          <div>
            <h1 className="page-title">My Memory</h1>
            {/* <p className="page-subtitle">
              View and manage information I remember about you
            </p> */}
          </div>
        </div>
      </div>

      <div className="memory-content">
        {error && (
          <div className="error-banner">
            {error}
          </div>
        )}

        {/* Statistics */}
        {/* <div className="memory-stats">
        <div className="stat-card">
          <div className="stat-value">{stats.total_count}</div>
          <div className="stat-label">Total Facts</div>
        </div>
        {Object.entries(stats.categories).map(([category, count]) => (
          count > 0 && (
            <div key={category} className="stat-card">
              <div className="stat-icon">{getCategoryIcon(category)}</div>
              <div className="stat-value">{count}</div>
              <div className="stat-label">{getCategoryLabel(category)}</div>
            </div>
          )
        ))}
        </div> */}

        {/* Filters */}
        <div className="memory-filters">
        <button
          className={`filter-btn ${categoryFilter === 'all' ? 'active' : ''}`}
          onClick={() => setCategoryFilter('all')}
        >
          All ({stats.total_count})
        </button>
        {Object.entries(stats.categories).map(([category, count]) => (
          count > 0 && (
            <button
              key={category}
              className={`filter-btn ${categoryFilter === category ? 'active' : ''}`}
              onClick={() => setCategoryFilter(category)}
            >
              {getCategoryIcon(category)} {getCategoryLabel(category)} ({count})
            </button>
          )
        ))}
        </div>

        {/* Facts List */}
        <div className="facts-container">
        {filteredFacts.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2a10 10 0 0 0-10 10v8a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-8A10 10 0 0 0 12 2z"></path>
                <path d="M8 10h.01M16 10h.01M8 14c.5 1 1.5 2 4 2s3.5-1 4-2"></path>
              </svg>
            </div>
            <h3>No facts stored yet</h3>
            <p>
              As you chat with me, I'll learn information about you like your name,
              courses, and preferences. You'll have full control over what I remember.
            </p>
          </div>
        ) : (
          <div className="facts-grid">
            {filteredFacts.map((fact) => {
              const retentionBadge = getRetentionBadge(fact.retention);
              return (
                <div key={fact.key} className="fact-card">
                  <div className="fact-header">
                    <div className="fact-category">
                      <span className="category-icon">
                        {getCategoryIcon(fact.category)}
                      </span>
                      <span className="category-name">
                        {getCategoryLabel(fact.category)}
                      </span>
                    </div>
                    <div className="fact-actions">
                      <button
                        className={`lock-btn ${fact.locked ? 'locked' : ''}`}
                        onClick={() => handleLockFact(fact.key, fact.locked)}
                        title={fact.locked ? 'Unlock fact' : 'Lock fact'}
                      >
                        {fact.locked ? (
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                            <path d="M7 11V7a5 5 0 0 1 9.9-1"></path>
                          </svg>
                        ) : (
                          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                            <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                          </svg>
                        )}
                      </button>
                      <button
                        className="delete-btn"
                        onClick={() => handleDeleteFact(fact.key)}
                        title="Delete fact"
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="3 6 5 6 21 6"></polyline>
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                      </button>
                    </div>
                  </div>
                  
                  <div className="fact-body">
                    <div className="fact-key">
                      {fact.key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </div>
                    <div className="fact-value">
                      {formatValue(fact.value)}
                    </div>
                  </div>
                  
                  <div className="fact-footer">
                    <span className={`retention-badge ${retentionBadge.class}`}>
                      {retentionBadge.label}
                    </span>
                    {fact.confirmed_by_user && (
                      <span className="confirmed-badge">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                          <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                        Confirmed
                      </span>
                    )}
                    {fact.locked && (
                      <span className="locked-badge">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                          <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                        </svg>
                        Locked
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
        </div>

        {/* Danger Zone */}
        {facts.length > 0 && (
        <div className="danger-zone">
          <h3>Danger Zone</h3>
          <p>Permanently delete stored information</p>
          <div className="danger-actions">
            {categoryFilter !== 'all' && (
              <button
                className="danger-btn"
                onClick={() => handleResetMemory(categoryFilter)}
              >
                Delete All {getCategoryLabel(categoryFilter)} Facts
              </button>
            )}
            <button
              className="danger-btn-critical"
              onClick={() => handleResetMemory()}
            >
              Delete Everything
            </button>
          </div>
        </div>
        )}
      </div>
      
      <Dialog
        isOpen={dialogState.isOpen}
        onClose={() => setDialogState({ ...dialogState, isOpen: false })}
        onConfirm={dialogState.onConfirm}
        title={dialogState.title}
        message={dialogState.message}
        type={dialogState.type}
        confirmText={dialogState.type === 'danger' ? 'Delete' : 'Confirm'}
        cancelText="Cancel"
      />
    </div>
  );
}

export default MemoryDashboard;
