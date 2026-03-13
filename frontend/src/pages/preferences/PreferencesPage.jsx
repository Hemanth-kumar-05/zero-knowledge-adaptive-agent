import React, { useState, useEffect } from 'react';
import { FaExclamationTriangle } from 'react-icons/fa';
import api from '../../api/client';
import Dialog from '../../components/common/Dialog';
import PreferenceModal from '../../components/preferences/PreferenceModal';
import './PreferencesPage.css';

const PreferencesPage = ({ isSidebarOpen, onToggleSidebar, showToast }) => {
  const [preferences, setPreferences] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [categories, setCategories] = useState({});
  const [conflicts, setConflicts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingPreference, setEditingPreference] = useState(null);
  const [dialog, setDialog] = useState({ isOpen: false, type: 'confirm', title: '', message: '', onConfirm: null });

  useEffect(() => {
    fetchPreferences();
    fetchMetadata();
    fetchCategories();
    fetchConflicts();
  }, []);

  const fetchPreferences = async () => {
    try {
      const response = await api.getPreferences();
      console.log('Fetched preferences:', response);
      setPreferences(response.preferences || []);
      setLoading(false);
    } catch (err) {
      const errorMessage = err.message || 'Failed to load preferences';
      if (showToast) {
        showToast(errorMessage, 'error');
      }
      setLoading(false);
      console.error('Error loading preferences:', err);
    }
  };

  const fetchMetadata = async () => {
    try {
      const response = await api.getPreferencesMetadata();
      setMetadata(response.metadata);
    } catch (err) {
      console.error('Failed to load metadata:', err);
      if (showToast) {
        showToast('Failed to load preference statistics', 'error');
      }
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.getPreferencesCategories();
      setCategories(response.categories || {});
    } catch (err) {
      console.error('Failed to load categories:', err);
      if (showToast) {
        showToast('Failed to load preference categories', 'error');
      }
    }
  };

  const fetchConflicts = async () => {
    try {
      const response = await api.checkPreferenceConflicts();
      setConflicts(response.conflicts || []);
      console.log('Detected conflicts:', response.conflicts);
    } catch (err) {
      console.error('Failed to check conflicts:', err);
    }
  };

  const isConflicting = (preferenceKey) => {
    return conflicts.some(
      conflict => 
        conflict.preference1.key === preferenceKey || 
        conflict.preference2.key === preferenceKey
    );
  };

  const getConflictInfo = (preferenceKey) => {
    const conflict = conflicts.find(
      c => c.preference1.key === preferenceKey || c.preference2.key === preferenceKey
    );
    if (!conflict) return null;

    const otherPref = conflict.preference1.key === preferenceKey 
      ? conflict.preference2 
      : conflict.preference1;
    
    return {
      message: `Conflicts with: ${otherPref.value} (${otherPref.category})`,
      otherKey: otherPref.key
    };
  };

  const handleResolveConflict = (preferenceKey) => {
    const conflictInfo = getConflictInfo(preferenceKey);
    if (!conflictInfo) return;

    setDialog({
      isOpen: true,
      type: 'confirm',
      title: 'Resolve Preference Conflict',
      message: `This preference conflicts with another: "${conflictInfo.message}". Which would you like to keep?`,
      confirmText: 'Keep This',
      cancelText: 'Delete This',
      onConfirm: async () => {
        // Keep this preference, delete the conflicting one
        try {
          await api.resolvePreferenceConflict(conflictInfo.otherKey, 'delete');
          fetchPreferences();
          fetchConflicts();
          if (showToast) {
            showToast('Conflict resolved successfully', 'success');
          }
        } catch (err) {
          if (showToast) {
            showToast(err.message || 'Failed to resolve conflict', 'error');
          }
        }
        setDialog({ ...dialog, isOpen: false });
      },
      onCancel: async () => {
        // Delete this preference
        try {
          await api.resolvePreferenceConflict(preferenceKey, 'delete');
          fetchPreferences();
          fetchConflicts();
          if (showToast) {
            showToast('Conflict resolved successfully', 'success');
          }
        } catch (err) {
          if (showToast) {
            showToast(err.message || 'Failed to resolve conflict', 'error');
          }
        }
        setDialog({ ...dialog, isOpen: false });
      }
    });
  };

  const handleLockToggle = async (key, currentlyLocked) => {
    try {
      await api.updatePreferenceLock(key, !currentlyLocked);
      fetchPreferences();
      if (showToast) {
        showToast(
          currentlyLocked ? 'Preference removed from active use' : 'Preference applied successfully',
          'success'
        );
      }
    } catch (err) {
      const errorMessage = err.message || 'Failed to update lock status';
      if (showToast) {
        showToast(errorMessage, 'error');
      }
      console.error('Error toggling lock:', err);
    }
  };

  const handleDelete = (key) => {
    setDialog({
      isOpen: true,
      type: 'danger',
      title: 'Delete Preference',
      message: 'Are you sure you want to delete this preference? This action cannot be undone.',
      confirmText: 'Delete',
      onConfirm: async () => {
        try {
          await api.deletePreference(key);
          fetchPreferences();
          fetchMetadata();
          if (showToast) {
            showToast('Preference deleted successfully', 'success');
          }
        } catch (err) {
          const errorMessage = err.message || 'Failed to delete preference';
          if (showToast) {
            showToast(errorMessage, 'error');
          }
          console.error('Error deleting preference:', errorMessage);
          console.error(err);
        }
      }
    });
  };

  const handleResetAll = () => {
    setDialog({
      isOpen: true,
      type: 'danger',
      title: 'Reset All Preferences',
      message: 'Are you sure you want to reset all preferences? This will permanently delete all your preferences and cannot be undone.',
      confirmText: 'Reset All',
      onConfirm: async () => {
        try {
          await api.resetPreferences();
          fetchPreferences();
          fetchMetadata();
          if (showToast) {
            showToast('All preferences reset successfully', 'success');
          }
        } catch (err) {
          const errorMessage = err.message || 'Failed to reset preferences';
          if (showToast) {
            showToast(errorMessage, 'error');
          }
          console.error('Error resetting preferences:', errorMessage);
          console.error(err);
        }
      }
    });
  };

  const handleManualPreference = async (input) => {
    setIsSubmitting(true);
    try {
      await api.addManualPreference(input);
      setShowAddModal(false);
      fetchPreferences();
      fetchMetadata();
      if (showToast) {
        showToast('Preference added successfully', 'success');
      }
    } catch (err) {
      const errorMessage = err.message || 'Failed to add preference';
      if (showToast) {
        showToast(errorMessage, 'error');
      }
      console.error('Error adding manual preference:', err);
    } finally {
      setIsSubmitting(false);
    }
  };
  const handleEdit = (pref) => {
    if (pref.source !== 'manual') {
      if (showToast) {
        showToast('Only manually added preferences can be edited', 'error');
      }
      return;
    }
    setEditingPreference(pref);
    setShowEditModal(true);
  };

  const handleUpdatePreference = async (input) => {
    setIsSubmitting(true);
    try {
      // Delete old preference first
      await api.deletePreference(editingPreference.key);
      // Add new one with updated text
      await api.addManualPreference(input);
      setEditingPreference(null);
      setShowEditModal(false);
      fetchPreferences();
      fetchMetadata();
      if (showToast) {
        showToast('Preference updated successfully', 'success');
      }
    } catch (err) {
      const errorMessage = err.message || 'Failed to update preference';
      if (showToast) {
        showToast(errorMessage, 'error');
      }
      console.error('Error updating preference:', err);
    } finally {
      setIsSubmitting(false);
    }
  };
  const getConfidenceBadge = (confidence) => {
    if (confidence >= 0.9) return { label: 'Very High', className: 'confidence-very-high' };
    if (confidence >= 0.75) return { label: 'High', className: 'confidence-high' };
    if (confidence >= 0.6) return { label: 'Medium', className: 'confidence-medium' };
    return { label: 'Low', className: 'confidence-low' };
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  if (loading) {
    return (
      <div className="preferences-page">
        <div className="loading-container">
          <div className="loading-spinner">
            <div className="preferences-spinner"></div>
          </div>
          <p className="loading-text">Loading preferences...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="preferences-page">
      <div className="preferences-header">
        <button 
          className="toggle-sidebar-btn" 
          onClick={onToggleSidebar}
          title={isSidebarOpen ? "Close sidebar" : "Open sidebar"}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
        <div className="header-left">
          <h1 className="page-title">AI Preferences</h1>
          <span className="page-subtitle">Personalize how the AI responds to you</span>
        </div>
        <div className="header-actions">
          <button 
            className="btn-add-preference" 
            onClick={() => setShowAddModal(true)}
            title="Add preference manually"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Add Preference
          </button>
          {preferences.length > 0 && (
            <button 
              className="btn-reset" 
              onClick={handleResetAll}
              title="Reset all preferences"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
              Reset All
            </button>
          )}
        </div>
      </div>

      <div className="preferences-container">

        {/* {metadata && (
          <div className="stats-overview">
            <div className="stat-item">
              <div className="stat-icon preferences-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="M12 1v6m0 6v6"></path>
                </svg>
              </div>
              <div className="stat-info">
                <span className="stat-number">{metadata.total_preferences || 0}</span>
                <span className="stat-label">Preferences</span>
              </div>
            </div>
            
            <div className="stat-item">
              <div className="stat-icon interactions-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
              </div>
              <div className="stat-info">
                <span className="stat-number">{metadata.total_interactions || 0}</span>
                <span className="stat-label">Interactions</span>
              </div>
            </div>
            
            <div className="stat-item">
              <div className="stat-icon updates-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2"/>
                </svg>
              </div>
              <div className="stat-info">
                <span className="stat-number">{metadata.preference_updates_count || 0}</span>
                <span className="stat-label">Updates</span>
              </div>
            </div>
            
            <div className="stat-item">
              <div className="stat-icon time-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <polyline points="12 6 12 12 16 14"></polyline>
                </svg>
              </div>
              <div className="stat-info">
                <span className="stat-number small">
                  {metadata.last_preference_update 
                    ? new Date(metadata.last_preference_update).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                    : 'Never'}
                </span>
                <span className="stat-label">Last Update</span>
              </div>
            </div>
          </div>
        )} */}

        {preferences.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
              </svg>
            </div>
            <h2>No Preferences Yet</h2>
            <p>Start chatting with the AI and your preferences will be automatically learned from your conversations.</p>
            {/* <div className="empty-tips">
              <div className="tip-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>Preferences are extracted every 5 messages</span>
              </div>
              <div className="tip-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>Lock preferences to prevent changes</span>
              </div>
              <div className="tip-item">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <span>Higher confidence = more accurate detection</span>
              </div>
            </div> */}
          </div>
        ) : (
          <div className="preferences-content">
            <div className="content-header">
              <h2>Your Preferences ({preferences.length})</h2>
              <div className="info-badge">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="16" x2="12" y2="12"></line>
                  <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                Automatically learned from conversations
              </div>
            </div>

            <div className="preferences-list">
              {preferences.map((pref) => {
                const badge = getConfidenceBadge(pref.confidence);
                const hasConflict = isConflicting(pref.key);
                const conflictInfo = hasConflict ? getConflictInfo(pref.key) : null;
                
                return (
                  <div key={pref.key} className={`preference-row ${pref.locked ? 'locked' : ''} ${hasConflict ? 'has-conflict' : ''}`}>
                    <div className="preference-main">
                      <div className="preference-label">
                        <div className="label-header">
                          <span className="label-title">{pref.category ? pref.category.replace(/_/g, ' ') : 'General'}</span>
                          {pref.locked && (
                            <span className="locked-indicator" title="This preference is currently applied">
                              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="20 6 9 17 4 12"></polyline>
                              </svg>
                            </span>
                          )}
                          {hasConflict && (
                            <span className="conflict-indicator" title={conflictInfo?.message}>
                              <FaExclamationTriangle />
                            </span>
                          )}
                        </div>
                        {hasConflict && conflictInfo && (
                          <div className="conflict-message">{conflictInfo.message}</div>
                        )}
                        {pref.explanation && !pref.custom_instruction && (
                          <div className="label-description">{pref.explanation}</div>
                        )}
                      </div>

                      <div className="preference-value-section">
                        {pref.custom_instruction ? (
                          <div className="value-display custom-instruction">{pref.custom_instruction}</div>
                        ) : (
                          <div className="value-display">{pref.value.replace(/_/g, ' ')}</div>
                        )}
                      </div>
                    </div>

                    <div className="preference-actions">
                      {hasConflict && (
                        <button
                          className="action-btn-icon resolve-conflict"
                          onClick={() => handleResolveConflict(pref.key)}
                          title="Resolve conflict"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                          </svg>
                        </button>
                      )}
                      {pref.source === 'manual' && (
                        <button
                          className="action-btn-icon"
                          onClick={() => handleEdit(pref)}
                          title="Edit preference"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                          </svg>
                        </button>
                      )}
                      <button
                        className="action-btn-icon checkbox-btn"
                        onClick={() => handleLockToggle(pref.key, pref.locked)}
                        title={pref.locked ? 'Remove from active use' : 'Apply this preference'}
                      >
                        {pref.locked ? (
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="icon-checked">
                            <rect x="3" y="3" width="18" height="18" rx="3" ry="3"></rect>
                            <polyline points="24 1 12 15 8 10"></polyline>
                          </svg>
                        ) : (
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="icon-unchecked">
                            <rect x="3" y="3" width="18" height="18" rx="3" ry="3"></rect>
                          </svg>
                        )}
                      </button>
                      <button
                        className="action-btn-icon delete"
                        onClick={() => handleDelete(pref.key)}
                        disabled={pref.locked}
                        title={pref.locked ? 'Remove from active use before deleting' : 'Delete'}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Add Preference Modal */}
      <PreferenceModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onSubmit={handleManualPreference}
        isSubmitting={isSubmitting}
      />

      {/* Edit Preference Modal */}
      <PreferenceModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setEditingPreference(null);
        }}
        onSubmit={handleUpdatePreference}
        initialValue={editingPreference?.custom_instruction || editingPreference?.extracted_from_message || editingPreference?.explanation || editingPreference?.value || ''}
        title="Edit Preference"
        submitText="Update Preference"
        isSubmitting={isSubmitting}
      />

      {/* Confirmation Dialog */}
      <Dialog
        isOpen={dialog.isOpen}
        onClose={() => setDialog({ ...dialog, isOpen: false })}
        onConfirm={dialog.onConfirm}
        title={dialog.title}
        message={dialog.message}
        confirmText={dialog.confirmText}
        cancelText={dialog.cancelText}
        type={dialog.type}
      />
    </div>
  );
};

export default PreferencesPage;
