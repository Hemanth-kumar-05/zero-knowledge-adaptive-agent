import React from 'react';
import './ExtensionFilesModal.css';

const ExtensionFilesModal = ({ isOpen, onClose, requiredFiles, onProceed }) => {
  if (!isOpen) return null;

  return (
    <div className="extension-files-modal-overlay" onClick={onClose}>
      <div className="extension-files-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="extension-files-modal-header">
          <h2>Required Files</h2>
          <button className="extension-files-modal-close" onClick={onClose}>×</button>
        </div>

        <div className="extension-files-modal-body">
          <div className="extension-files-info">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
              <polyline points="13 2 13 9 20 9"></polyline>
            </svg>
            <p className="extension-files-message">
              This extension requires the following file types:
            </p>
            <div className="extension-files-list">
              {requiredFiles && requiredFiles.length > 0 ? (
                requiredFiles.map((fileType, index) => (
                  <div key={index} className="extension-file-type">
                    <span className="file-type-badge">{fileType}</span>
                  </div>
                ))
              ) : (
                <div className="extension-file-type">
                  <span className="file-type-badge">.json</span>
                </div>
              )}
            </div>
            <p className="extension-files-note">
              Please prepare these files before proceeding.
            </p>
          </div>
        </div>

        <div className="extension-files-modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-primary" onClick={onProceed}>
            Continue
          </button>
        </div>
      </div>
    </div>
  );
};

export default ExtensionFilesModal;
