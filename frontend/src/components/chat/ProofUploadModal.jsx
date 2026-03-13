import React, { useState } from 'react';
import './ProofUploadModal.css';
import api from '../../api/client';

const ProofUploadModal = ({ isOpen, onClose, policyClaimData, sessionId, onSuccess }) => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState([]);
  const [error, setError] = useState(null);

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    
    // Validate file types
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'application/pdf', 'text/plain'];
    const invalidFiles = files.filter(f => !validTypes.includes(f.type));
    
    if (invalidFiles.length > 0) {
      setError('Some files have invalid types. Please upload images, PDFs, or text files only.');
      return;
    }
    
    // Validate file sizes (max 10MB each)
    const oversizedFiles = files.filter(f => f.size > 10 * 1024 * 1024);
    if (oversizedFiles.length > 0) {
      setError('Some files exceed 10MB limit.');
      return;
    }
    
    setSelectedFiles([...selectedFiles, ...files]);
    setError(null);
  };

  const removeFile = (index) => {
    setSelectedFiles(selectedFiles.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select at least one file');
      return;
    }

    setUploading(true);
    setError(null);
    
    try {
      const proofUrls = [];
      const progress = selectedFiles.map(() => 0);
      setUploadProgress(progress);

      // Upload all files
      for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        
        try {
          const result = await api.uploadPolicyProof(
            file,
            policyClaimData.ticket_id_pending
          );
          
          proofUrls.push(result.proof_url);
          progress[i] = 100;
          setUploadProgress([...progress]);
        } catch (err) {
          console.error(`Failed to upload ${file.name}:`, err);
          setError(`Failed to upload ${file.name}`);
          setUploading(false);
          return;
        }
      }

      // Create ticket with proofs
      const ticketResult = await api.createTicketWithProofs(sessionId, proofUrls);
      
      setUploading(false);
      onSuccess(ticketResult.ticket_id);
    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'Failed to submit proof');
      setUploading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="proof-upload-modal-overlay" onClick={onClose}>
      <div className="proof-upload-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="proof-upload-modal-header">
          <h2>Upload Policy Change Proof</h2>
          <button className="proof-upload-modal-close" onClick={onClose}>×</button>
        </div>

        <div className="proof-upload-modal-body">
          <div className="proof-upload-info">
            <p className="proof-upload-message">
              {policyClaimData?.message_to_user}
            </p>
            
            <div className="proof-upload-claim-details">
              <h3>Your Claim:</h3>
              <p className="claim-text">{policyClaimData?.claim_text}</p>
              <div className="claim-meta">
                <span className={`badge badge-${policyClaimData?.confidence_level}`}>
                  {policyClaimData?.confidence_level} confidence
                </span>
                <span className="badge badge-info">{policyClaimData?.claim_type}</span>
              </div>
            </div>
          </div>

          <div className="proof-upload-section">
            <label className="proof-upload-label">
              Select Supporting Documents
              <small>(Images, PDFs, or text files - max 10MB each)</small>
            </label>
            
            <input
              type="file"
              multiple
              accept="image/*,.pdf,.txt"
              onChange={handleFileSelect}
              className="proof-upload-input"
              disabled={uploading}
            />

            {selectedFiles.length > 0 && (
              <div className="proof-upload-file-list">
                <h4>Selected Files ({selectedFiles.length}):</h4>
                {selectedFiles.map((file, index) => (
                  <div key={index} className="proof-upload-file-item">
                    <span className="file-icon">
                      {file.type.startsWith('image/') ? '🖼️' : 
                       file.type === 'application/pdf' ? '📄' : '📝'}
                    </span>
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">
                      {(file.size / 1024).toFixed(0)} KB
                    </span>
                    {uploading && (
                      <div className="file-progress">
                        <div 
                          className="file-progress-bar"
                          style={{ width: `${uploadProgress[index]}%` }}
                        />
                      </div>
                    )}
                    {!uploading && (
                      <button
                        className="file-remove"
                        onClick={() => removeFile(index)}
                      >
                        ×
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {error && (
            <div className="proof-upload-error">
              ⚠️ {error}
            </div>
          )}
        </div>

        <div className="proof-upload-modal-footer">
          <button
            className="btn-secondary"
            onClick={onClose}
            disabled={uploading}
          >
            Cancel
          </button>
          <button
            className="btn-primary"
            onClick={handleUpload}
            disabled={uploading || selectedFiles.length === 0}
          >
            {uploading ? 'Uploading...' : `Submit ${selectedFiles.length} File(s)`}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProofUploadModal;
