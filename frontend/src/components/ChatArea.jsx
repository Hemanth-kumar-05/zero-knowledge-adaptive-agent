import React, { useState, useRef, useEffect } from 'react';
import { FaMagic } from 'react-icons/fa';
import './ChatArea.css';
import Message from './Message';
import SessionWarning from './SessionWarning';

function ChatArea({ messages, onSendMessage, loading, error, onClearError, isSidebarOpen, onToggleSidebar, currentSession, user, showToast, onNewSession }) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const [sessionWarning, setSessionWarning] = useState(null);
  const [dismissedWarning, setDismissedWarning] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

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
            <h2>What can I help with?</h2>
            <p>Ask me about academic policies, courses, exams, or projects.</p>
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
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about academic policies, exams, courses..."
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
        </form>
        <p className="input-hint">
          NCIE Agent can make mistakes. Check important info.
        </p>
      </div>
    </div>
  );
}

export default ChatArea;
