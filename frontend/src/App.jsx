import React, { useState, useEffect, useRef } from 'react';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import './App.css';
import api from './api/client';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import Auth from './components/Auth';
import OAuthCallback from './components/OAuthCallback';
import PreferencesPage from './components/PreferencesPage';
import MemoryDashboard from './components/MemoryDashboard';
import Toast from './components/Toast';
import { auth } from './utils/auth';

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
  const [user, setUser] = useState(auth.getUser());
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info', duration = 5000) => {
    setToast({ message, type, duration });
  };

  useEffect(() => {
    checkSystemHealth();
    if (user) {
      loadSessions();
    }
  }, [user]);

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
        showToast('System is experiencing issues. Some features may not work properly.', 'error');
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
      showToast('Failed to load sessions. Please refresh the page.', 'error');
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
      showToast('Failed to load messages for this session.', 'error');
    }
  };

  const createNewSession = async () => {
    try {
      setError(null);
      // User ID will come from auth token in backend
      const newSession = await api.createSession();
      const updatedSessions = [newSession, ...sessions];
      setSessions(updatedSessions);
      setCurrentSession(newSession);
      setMessages([]);
      navigate(`/${newSession.id}`);
      showToast('New chat started', 'success');
      return newSession;
    } catch (error) {
      console.error('Failed to create session:', error);
      showToast('Failed to create new session. Please try again.', 'error');
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
          refused: response.refused,
          risk_alerts: response.risk_alerts, // NEW: Risk alerts from AI analysis
          session_limit_warning: response.session_limit_warning // NEW: Session limit warning
        },
      };
      setMessages((prev) => [...prev, assistantMessage]);
      
      // Show session limit warning toast if present
      if (response.session_limit_warning) {
        const warning = response.session_limit_warning;
        if (warning.severity === 'high') {
          showToast(
            `⚠️ ${warning.message}`,
            'warning',
            10000  // Show for 10 seconds
          );
        } else if (warning.severity === 'medium') {
          showToast(
            `ℹ️ ${warning.message}`,
            'info',
            8000  // Show for 8 seconds
          );
        }
      }

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
      showToast('Failed to get response. Please try again.', 'error');
      
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

  const handleLogout = () => {
    auth.logout();
    setUser(null);
    navigate('/');
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await api.deleteSession(sessionId);
      
      // Remove from sessions list
      setSessions(sessions.filter(s => s.id !== sessionId));
      
      // If deleting current session, clear it
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
        navigate('/');
      }
      
      setError(null);
      showToast('Chat deleted successfully', 'success');
    } catch (error) {
      console.error('Failed to delete session:', error);
      showToast('Failed to delete session. Please try again.', 'error');
    }
  };

  // Check if user is authenticated
  if (!auth.isAuthenticated()) {
    return <Auth onLogin={(user) => setUser(user)} />;
  }

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        currentSession={currentSession}
        onNewChat={createNewSession}
        onSelectSession={selectSession}
        onRefresh={refreshSessions}
        onDeleteSession={handleDeleteSession}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        healthStatus={healthStatus}
        user={user}
        onLogout={handleLogout}
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
        user={user}
        showToast={showToast}
        onNewSession={createNewSession}
      />
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

function PreferencesView() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [user, setUser] = useState(auth.getUser());
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
  };

  useEffect(() => {
    if (user) {
      loadSessions();
    }
  }, [user]);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      showToast('Failed to load sessions', 'error');
    }
  };

  const handleLogout = () => {
    auth.logout();
    setUser(null);
    navigate('/');
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await api.deleteSession(sessionId);
      setSessions(sessions.filter(s => s.id !== sessionId));
      showToast('Chat deleted successfully', 'success');
    } catch (error) {
      console.error('Failed to delete session:', error);
      showToast('Failed to delete session', 'error');
    }
  };

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        currentSession={null}
        onNewChat={() => navigate('/')}
        onSelectSession={(session) => navigate(`/${session.id}`)}
        onRefresh={loadSessions}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        user={user}
        healthStatus={null}
        onLogout={handleLogout}
        onDeleteSession={handleDeleteSession}
      />
      <PreferencesPage 
        isSidebarOpen={isSidebarOpen} 
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        showToast={showToast}
         />
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}

function MemoryView() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [user, setUser] = useState(auth.getUser());
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
  };

  useEffect(() => {
    if (user) {
      loadSessions();
    }
  }, [user]);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      showToast('Failed to load sessions', 'error');
    }
  };

  const handleLogout = () => {
    auth.logout();
    setUser(null);
    navigate('/');
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await api.deleteSession(sessionId);
      setSessions(sessions.filter(s => s.id !== sessionId));
      showToast('Chat deleted successfully', 'success');
    } catch (error) {
      console.error('Failed to delete session:', error);
      showToast('Failed to delete session', 'error');
    }
  };

  return (
    <div className="app">
      <Sidebar
        sessions={sessions}
        currentSession={null}
        onNewChat={() => navigate('/')}
        onSelectSession={(session) => navigate(`/${session.id}`)}
        onRefresh={loadSessions}
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        user={user}
        healthStatus={null}
        onLogout={handleLogout}
        onDeleteSession={handleDeleteSession}
      />
      <MemoryDashboard 
        user={user}
        isSidebarOpen={isSidebarOpen} 
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        showToast={showToast}
      />
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}

function App() {
  const navigate = useNavigate();

  const handleAuthSuccess = (user) => {
    console.log('Logged in:', user);
    // Just navigate to home - the ChatView will reload sessions when it mounts
    navigate('/');
  };

  return (
    <Routes>
      <Route path="/" element={<ChatView />} />
      <Route path="/:sessionId" element={<ChatView />} />
      <Route path="/auth/callback" element={<OAuthCallback onSuccess={handleAuthSuccess} />} />
      <Route path="/preferences" element={<PreferencesView />} />
      <Route path="/memory" element={<MemoryView />} />
    </Routes>
  );
}

export default App;
