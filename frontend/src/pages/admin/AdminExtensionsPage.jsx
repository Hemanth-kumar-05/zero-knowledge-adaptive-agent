import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ExtensionCreateModal from '../../components/extensions/ExtensionCreateModal';
import ExtensionFilesModal from '../../components/extensions/ExtensionFilesModal';
import Toast from '../../components/common/Toast';
import { extensionsAPI } from '../../api/extensions';
import './AdminExtensionsPage.css';

function AdminExtensionsPage({ user, onToggleSidebar }) {
  const navigate = useNavigate();
  const [extensions, setExtensions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [showFilesModal, setShowFilesModal] = useState(false);
  const [pendingSession, setPendingSession] = useState(null);
  const [requiredFiles, setRequiredFiles] = useState([]);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info', duration = 5000) => {
    setToast({ message, type, duration });
  };

  const categories = ['All', 'Academic', 'Planning', 'Research', 'Career', 'Learning'];

  useEffect(() => {
    // Check if user is admin
    if (user?.role !== 'admin') {
      navigate('/extensions');
      return;
    }

    loadExtensions();
  }, [user, navigate]);

  const loadExtensions = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await extensionsAPI.getAllExtensions(false); // Show all (including inactive)
      setExtensions(data);
    } catch (err) {
      setError('Failed to load extensions');
      console.error('Error loading extensions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateExtension = async (extensionData) => {
    try {
      await extensionsAPI.createExtension(extensionData);
      await loadExtensions(); // Reload extensions list
      setIsCreateModalOpen(false);
    } catch (err) {
      throw err; // Let modal handle the error
    }
  };

  const handleDeleteExtension = async (extensionId) => {
    try {
      await extensionsAPI.deleteExtension(extensionId);
      await loadExtensions(); // Reload extensions list
      setDeleteConfirm(null);
      showToast('Extension deleted successfully.', 'success');
    } catch (err) {
      showToast('Failed to delete extension: ' + err.message, 'error');
    }
  };

  const confirmDelete = (extension) => {
    setDeleteConfirm(extension);
  };

  const filteredExtensions = extensions.filter(ext => {
    const matchesSearch = ext.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         ext.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || ext.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

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
      }
    } catch (error) {
      console.error('Error creating extension session:', error);
      setError('Failed to start extension session. Please try again.');
    }
  };

  const handleProceedWithFiles = () => {
    setShowFilesModal(false);
    if (pendingSession) {
      navigate(`/${pendingSession}`);
      setPendingSession(null);
    }
  };

  const handleCancelFiles = () => {
    setShowFilesModal(false);
    setPendingSession(null);
    setRequiredFiles([]);
  };

  return (
    <div className="admin-extensions-page">
      <div className="admin-extensions-header">
        <button className="mobile-menu-btn" onClick={onToggleSidebar}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>

        <div className="header-content">
          <div className="header-left">
            <h1>Extensions Management</h1>
            <p className="subtitle">Create and manage AI extensions for your institution</p>
          </div>
        </div>

        <button 
            className="create-extension-btn"
            onClick={() => setIsCreateModalOpen(true)}
        >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Create Extension
        </button>
      </div>

      <div className="admin-extensions-content">
        <div className="search-filter-bar">
          <div className="search-box">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <input
              type="text"
              placeholder="Search extensions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <div className="category-filters">
            {categories.map(category => (
              <button
                key={category}
                className={`category-btn ${selectedCategory === category ? 'active' : ''}`}
                onClick={() => setSelectedCategory(category)}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <div className="error-message">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading extensions...</p>
          </div>
        ) : filteredExtensions.length === 0 ? (
          <div className="empty-state">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
            <h3>No extensions found</h3>
            <p>Create your first extension to get started</p>
            <button 
              className="create-extension-btn"
              onClick={() => setIsCreateModalOpen(true)}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              Create Extension
            </button>
          </div>
        ) : (
          <div className="extensions-grid">
            {filteredExtensions.map(extension => (
              <div key={extension.id} className={`extension-card ${!extension.isActive ? 'inactive' : ''}`}>
                <div className="extension-card-header">
                  <div className="extension-icon">
                    <i className={extension.icon}></i>
                  </div>
                  <div className="extension-info">
                    <h3>{extension.name}</h3>
                    <span className="extension-category">{extension.category}</span>
                  </div>
                  {!extension.isActive && (
                    <span className="inactive-badge">Inactive</span>
                  )}
                </div>

                <p className="extension-description">{extension.description}</p>

                <div className="extension-meta">
                  <span className="meta-item">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="10"></circle>
                      <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                    {new Date(extension.createdAt).toLocaleDateString()}
                  </span>
                  {extension.requiredFiles?.length > 0 && (
                    <span className="meta-item">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
                        <polyline points="13 2 13 9 20 9"></polyline>
                      </svg>
                      {extension.requiredFiles.length} file(s)
                    </span>
                  )}
                </div>

                <div className="extension-actions">
                  <button 
                    className="action-btn use-btn"
                    onClick={() => handleExtensionClick(extension)}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="9 18 15 12 9 6"></polyline>
                    </svg>
                    Use Extension
                  </button>
                  <button 
                    className="action-btn delete-btn"
                    onClick={() => confirmDelete(extension)}
                  >
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <ExtensionCreateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateExtension}
      />

      <ExtensionFilesModal
        isOpen={showFilesModal}
        onClose={handleCancelFiles}
        requiredFiles={requiredFiles}
        onProceed={handleProceedWithFiles}
      />

      {deleteConfirm && (
        <div className="delete-confirm-overlay" onClick={() => setDeleteConfirm(null)}>
          <div className="delete-confirm-modal" onClick={(e) => e.stopPropagation()}>
            <div className="delete-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
              </svg>
            </div>
            <h3>Delete Extension?</h3>
            <p>
              Are you sure you want to delete <strong>{deleteConfirm.name}</strong>? 
              This action cannot be undone.
            </p>
            <div className="delete-confirm-actions">
              <button 
                className="btn-secondary"
                onClick={() => setDeleteConfirm(null)}
              >
                Cancel
              </button>
              <button 
                className="btn-danger"
                onClick={() => handleDeleteExtension(deleteConfirm.id)}
              >
                Delete Extension
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={toast.duration}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}

export default AdminExtensionsPage;
