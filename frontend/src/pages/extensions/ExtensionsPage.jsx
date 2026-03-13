import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { extensionsAPI } from '../../api/extensions';
import ExtensionFilesModal from '../../components/extensions/ExtensionFilesModal';
import './ExtensionsPage.css';

function ExtensionsPage({ user, onToggleSidebar }) {
  const navigate = useNavigate();
  const [extensions, setExtensions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [showFilesModal, setShowFilesModal] = useState(false);
  const [pendingSession, setPendingSession] = useState(null);
  const [requiredFiles, setRequiredFiles] = useState([]);

  const categories = ['All', 'Academic', 'Planning', 'Research', 'Career', 'Learning'];

  useEffect(() => {
    loadExtensions();
  }, []);

  const loadExtensions = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await extensionsAPI.getAllExtensions(true); // Only active extensions
      setExtensions(data);
    } catch (err) {
      setError('Failed to load extensions');
      console.error('Error loading extensions:', err);
    } finally {
      setIsLoading(false);
    }
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
      setError('Failed to start extension session');
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

  // Color mapping for categories
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
    <div className="extensions-page">
      <div className="extensions-page-header">
        <button className="toggle-sidebar-btn" onClick={onToggleSidebar}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="6" x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>

        <div className="header-content">
          <div className="header-left">
            <h1>Extensions</h1>
            <p className="subtitle">Choose a specialized extension to enhance your experience</p>
          </div>
        </div>
      </div>

      <div className="extensions-page-content">
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
            <p>No extensions match your search criteria</p>
          </div>
        ) : (
          <div className="extensions-grid">
            {filteredExtensions.map(extension => (
              <div
                key={extension.id}
                className="extension-card"
                onClick={() => handleExtensionClick(extension)}
                >
                <div 
                  className="extension-icon" 
                >
                  <i className={extension.icon}></i>
                </div>
                <div className="extension-info">
                  <h3>{extension.name}</h3>
                  <p>{extension.description}</p>
                  <span className="extension-category">{extension.category}</span>
                </div>
                <div className="extension-arrow">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                    <polyline points="12 5 19 12 12 19"></polyline>
                  </svg>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <ExtensionFilesModal
        isOpen={showFilesModal}
        onClose={handleCancelFiles}
        requiredFiles={requiredFiles}
        onProceed={handleProceedWithFiles}
      />
    </div>
  );
}

export default ExtensionsPage;
