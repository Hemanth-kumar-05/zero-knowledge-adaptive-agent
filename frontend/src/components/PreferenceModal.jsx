import React, { useState, useEffect } from 'react';
import './PreferenceModal.css';

const PreferenceModal = ({ 
  isOpen, 
  onClose, 
  onSubmit, 
  initialValue = '',
  title = 'Add Your Preference',
  submitText = 'Add Preference',
  isSubmitting = false
}) => {
  const [input, setInput] = useState(initialValue);

  useEffect(() => {
    setInput(initialValue);
  }, [initialValue, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input);
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget && !isSubmitting) {
      onClose();
    }
  };

  const handleCancel = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  return (
    <div className="preference-modal-overlay" onClick={handleOverlayClick}>
      <div className="preference-modal">
        <div className="preference-modal-header">
          <h2>{title}</h2>
          <button 
            className="close-btn" 
            onClick={handleCancel}
            disabled={isSubmitting}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="preference-modal-body">
            <p className="preference-modal-description">
              Describe how you'd like the AI to respond in natural language
            </p>
            
            <textarea
              className="preference-input"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g., I prefer detailed explanations with code examples, or I like concise answers without extra context..."
              rows={6}
              disabled={isSubmitting}
              autoFocus
            />
          </div>

          <div className="preference-modal-actions">
            <button
              type="button"
              className="modal-btn cancel-btn"
              onClick={handleCancel}
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="modal-btn submit-btn"
              disabled={!input.trim() || isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <div className="modal-spinner"></div>
                  <span>Processing...</span>
                </>
              ) : (
                submitText
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PreferenceModal;
