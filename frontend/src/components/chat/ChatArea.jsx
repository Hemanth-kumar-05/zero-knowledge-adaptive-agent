import React, { useState, useRef, useEffect } from 'react';
import { FaMagic } from 'react-icons/fa';
import './ChatArea.css';
import Message from './Message';
import SessionWarning from './SessionWarning';
import ProofUploadModal from './ProofUploadModal';

function ChatArea({ 
  messages, 
  onSendMessage, 
  loading, 
  error, 
  onClearError, 
  isSidebarOpen, 
  onToggleSidebar, 
  currentSession, 
  user, 
  showToast, 
  onNewSession,
  showProofModal,
  policyClaimData,
  onCloseProofModal,
  onProofUploadSuccess
}) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);
  const [sessionWarning, setSessionWarning] = useState(null);
  const [dismissedWarning, setDismissedWarning] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [filePreviewUrl, setFilePreviewUrl] = useState(null);

  const formatFileSize = (bytes) => {
    if (!bytes) return '';
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileIcon = (file) => {
    if (file.type.startsWith('image/')) {
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
          <circle cx="8.5" cy="8.5" r="1.5"></circle>
          <polyline points="21 15 16 10 5 21"></polyline>
        </svg>
      );
    }
    if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
      return (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <polyline points="14 2 14 8 20 8"></polyline>
          <line x1="9" y1="13" x2="15" y2="13"></line>
          <line x1="9" y1="17" x2="15" y2="17"></line>
          <polyline points="9 9 10 9 10 9"></polyline>
        </svg>
      );
    }
    return (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"></path>
        <polyline points="13 2 13 9 20 9"></polyline>
      </svg>
    );
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Get extension-specific content
  const getExtensionContent = () => {
    if (!currentSession?.extension_name) {
      return {
        title: 'What can I help with?',
        description: 'Ask me about academic policies, courses, exams, or projects.',
        placeholder: 'Ask about academic policies, exams, courses...',
        icon: null
      };
    }

    // Use extension's custom welcome message and placeholder from session
    return {
      title: currentSession.extension_name,
      description: currentSession.extension_welcome_message || 'Specialized assistant to help with your specific needs.',
      placeholder: currentSession.extension_input_placeholder || 'Ask me anything...',
      icon: currentSession.extension_icon
    };
  };

  const extensionContent = getExtensionContent();

  // Check for session limit warning in latest message
  useEffect(() => {
    if (messages.length > 0 && !dismissedWarning) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === 'assistant' && lastMessage.metadata?.session_limit_warning) {
        setSessionWarning(lastMessage.metadata.session_limit_warning);
      }
    }
  }, [messages, dismissedWarning]);

  // Check for newly extracted preferences
  useEffect(() => {
    if (messages.length > 0 && showToast) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === 'user' && lastMessage.extracted_preferences && lastMessage.extracted_preferences.length > 0) {
        const prefs = lastMessage.extracted_preferences;
        const prefCount = prefs.length;
        const prefSummary = prefs.map(p => p.category.replace(/_/g, ' ')).join(', ');
        showToast(
          <><FaMagic style={{ marginRight: '6px' }} /> Preference{prefCount > 1 ? 's' : ''} saved: {prefSummary}</>,
          'info'
        );
      }
    }
  }, [messages, showToast]);

  // Auto-resize textarea as user types
  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [input]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      onSendMessage(input.trim(), selectedFile);
      setInput('');
      setSelectedFile(null);
      if (filePreviewUrl) {
        URL.revokeObjectURL(filePreviewUrl);
        setFilePreviewUrl(null);
      }
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      if (file.type.startsWith('image/')) {
        if (filePreviewUrl) URL.revokeObjectURL(filePreviewUrl);
        setFilePreviewUrl(URL.createObjectURL(file));
      } else {
        setFilePreviewUrl(null);
      }
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    if (filePreviewUrl) {
      URL.revokeObjectURL(filePreviewUrl);
      setFilePreviewUrl(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleAttachClick = () => {
    fileInputRef.current?.click();
  };

  // Show attachment button only for extension sessions
  const showAttachment = currentSession?.extension_id;

  return (
    <div className="chat-area">
      <div className="chat-header">
        <button className="toggle-sidebar-btn" onClick={onToggleSidebar}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="12" x2="21" y2="12"></line>
            <line x1="3" y1="6" x2="21" y2="6"></line>
            <line x1="3" y1="18" x2="21" y2="18"></line>
          </svg>
        </button>
        <h1 className="chat-title">NCIE Agent</h1>
      </div>

      {error && (
        <div className="error-banner">
          <span>{error}</span>
          <button onClick={onClearError}>×</button>
        </div>
      )}
      
      {sessionWarning && !dismissedWarning && (
        <SessionWarning 
          warning={sessionWarning}
          onNewSession={() => {
            setDismissedWarning(true);
            setSessionWarning(null);
            if (onNewSession) onNewSession();
          }}
          onContinue={() => {
            setDismissedWarning(true);
            setSessionWarning(null);
          }}
        />
      )}

      <div className="messages-container">
        {messages.length === 0 && !loading && (
          <div className="empty-state">
            {extensionContent.icon && (
              <div className="extension-icon-large">
                <i className={extensionContent.icon}></i>
              </div>
            )}
            <h2>{extensionContent.title}</h2>
            <p>{extensionContent.description}</p>
          </div>
        )}

        {messages.map((message) => (
          <Message key={message.id} message={message} user={user} />
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-avatar">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"/>
              </svg>
            </div>
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <form onSubmit={handleSubmit} className="input-form">
          {selectedFile && (
            <div className="file-preview-container">
              {filePreviewUrl ? (
                <div className="file-preview-image-card">
                  <img src={filePreviewUrl} alt="Preview" className="file-preview-thumbnail" />
                  <div className="file-preview-meta">
                    <span className="file-preview-name">{selectedFile.name}</span>
                    <span className="file-preview-size">{formatFileSize(selectedFile.size)}</span>
                  </div>
                  <button type="button" onClick={handleRemoveFile} className="file-preview-remove">×</button>
                </div>
              ) : (
                <div className="file-preview-doc-card">
                  <div className="file-preview-doc-icon">
                    {getFileIcon(selectedFile)}
                  </div>
                  <div className="file-preview-meta">
                    <span className="file-preview-name">{selectedFile.name}</span>
                    <span className="file-preview-size">{formatFileSize(selectedFile.size)}</span>
                  </div>
                  <button type="button" onClick={handleRemoveFile} className="file-preview-remove">×</button>
                </div>
              )}
            </div>
          )}
          <div className="input-row">
            {showAttachment && (
              <>
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                  accept=".json,.pdf,.txt,.png,.jpg,.jpeg"
                />
                <button
                  type="button"
                  onClick={handleAttachClick}
                  className="attach-button"
                  title="Attach file"
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"></path>
                  </svg>
                </button>
              </>
            )}
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={extensionContent.placeholder}
              className="message-input"
              disabled={loading}
            />
            <button
              type="submit"
              className="send-button"
              disabled={!input.trim() || loading}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
          </div>
        </form>
        <p className="input-hint">
          NCIE Agent can make mistakes. Check important info.
        </p>
      </div>

      {/* Proof Upload Modal */}
      <ProofUploadModal
        isOpen={showProofModal}
        onClose={onCloseProofModal}
        policyClaimData={policyClaimData}
        sessionId={currentSession?.id}
        onSuccess={onProofUploadSuccess}
      />
    </div>
  );
}

export default ChatArea;
