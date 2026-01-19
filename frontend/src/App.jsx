import React, { useState, useEffect, useRef } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import './App.css';
import api from './api/client';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';

function ChatView() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);

  useEffect(() => {
    checkSystemHealth();
    loadSessions();
  }, []);

  useEffect(() => {
    if (sessionId && sessions.length > 0) {
      const session = sessions.find(s => s.id === sessionId);
      if (session) {
        setCurrentSession(session);
      } else {
        // Session ID in URL doesn't exist, redirect to home
        navigate('/');
      }
    }
  }, [sessionId, sessions, navigate]);

  useEffect(() => {
    if (currentSession) {
      loadMessages(currentSession.id);
    } else {
      setMessages([]);
    }
  }, [currentSession]);

  const checkSystemHealth = async () => {
    try {
      const health = await api.checkHealth();
      setHealthStatus(health);
      if (health.status === 'unhealthy') {
        setError('System is experiencing issues. Some features may not work properly.');
      }
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthStatus({ status: 'unknown' });
    }
  };

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data.sessions || []);
      setError(null);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      setError('Failed to load sessions. Please refresh the page.');
    }
  };

  const loadMessages = async (sessionId) => {
    try {
      const data = await api.getSessionMessages(sessionId);
      setMessages(data.messages || []);
      setError(null);
    } catch (error) {
      console.error('Failed to load messages:', error);
      setMessages([]);
      setError('Failed to load messages for this session.');
    }
  };

  const createNewSession = async () => {
    try {
      setError(null);
      const newSession = await api.createSession('default-user');
      const updatedSessions = [newSession, ...sessions];
      setSessions(updatedSessions);
      setCurrentSession(newSession);
      setMessages([]);
      navigate(`/${newSession.id}`);
      return newSession;
    } catch (error) {
      console.error('Failed to create session:', error);
      setError('Failed to create new session. Please try again.');
      throw error;
    }
  };

  const handleSendMessage = async (content) => {
    let sessionToUse = currentSession;
    
    // Create new session if none exists
    if (!sessionToUse) {
      try {
        sessionToUse = await createNewSession();
      } catch (error) {
        return;
      }
    }

    // Add user message optimistically
    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      const response = await api.query({
        question: content,
        session_id: sessionToUse.id,
      });

      // Add assistant message with sources
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        metadata: { 
          sources: response.sources,
          confidence: response.confidence,
          refused: response.refused
        },
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Update session in list (increment message count)
      setSessions(prevSessions => 
        prevSessions.map(s => 
          s.id === sessionToUse.id 
            ? { ...s, message_count: (s.message_count || 0) + 2, updated_at: new Date().toISOString() }
            : s
        )
      );
    } catch (error) {
      console.error('Failed to send message:', error);
      setError('Failed to get response. Please try again.');
      
      // Add error message
      const errorMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.message || 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        metadata: { isError: true },
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const selectSession = (session) => {
    setError(null);
    navigate(`/${session.id}`);
  };

  const refreshSessions = () => {
    loadSessions();
  };

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        currentSession={currentSession}
        onNewChat={createNewSession}
        onSelectSession={selectSession}
        onRefresh={refreshSessions}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        healthStatus={healthStatus}
      />
      <ChatArea
        messages={messages}
        onSendMessage={handleSendMessage}
        loading={loading}
        error={error}
        onClearError={() => setError(null)}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        currentSession={currentSession}
      />
    </div>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<ChatView />} />
      <Route path="/:sessionId" element={<ChatView />} />
    </Routes>
  );
}

export default App;
