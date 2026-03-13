import React from 'react';
import './Dialog.css';

const Dialog = ({ 
  isOpen, 
  onClose, 
  onConfirm,
  onCancel, // Optional custom cancel handler
  title, 
  message, 
  confirmText = 'Confirm', 
  cancelText = 'Cancel',
  type = 'confirm' // 'confirm', 'alert', 'danger', 'success'
}) => {
  if (!isOpen) return null;

  const handleConfirm = () => {
    if (onConfirm) {
      onConfirm();
    }
    onClose();
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      onClose();
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="dialog-overlay" onClick={handleOverlayClick}>
      <div className={`dialog-box ${type}`}>
        <div className="dialog-header">
          <h3>{title}</h3>
        </div>
        
        <div className="dialog-body">
          <p>{message}</p>
        </div>
        
        <div className="dialog-actions">
          {type !== 'alert' && (
            <button 
              className="dialog-btn cancel-btn" 
              onClick={handleCancel}
            >
              {cancelText}
            </button>
          )}
          <button 
            className={`dialog-btn confirm-btn ${type === 'danger' ? 'danger' : ''} ${type === 'success' ? 'success' : ''}`}
            onClick={handleConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dialog;
