import React, { useState, useEffect, useRef } from 'react';
import { Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom';
import './App.css';
import api from './api/client';
import Sidebar from './components/navigation/Sidebar';
import ChatArea from './components/chat/ChatArea';
import Auth from './pages/auth/Auth';
import OAuthCallback from './pages/auth/OAuthCallback';
import IdentityVerification from './pages/auth/IdentityVerification';
import PreferencesPage from './pages/preferences/PreferencesPage';
import MemoryDashboard from './pages/memory/MemoryDashboard';
import PolicyUpdatesPage from './pages/policy/PolicyUpdatesPage';
import ChunkEditorPage from './pages/chunk-editor/ChunkEditorPage';
import ExtensionsPage from './pages/extensions/ExtensionsPage';
import AdminExtensionsPage from './pages/admin/AdminExtensionsPage';
import AdminUsersPage from './pages/admin/AdminUsersPage';
import AdminChromaChunksPage from './pages/admin/AdminChromaChunksPage';
import Toast from './components/common/Toast';
import Dialog from './components/common/Dialog';
import { auth } from './utils/auth';

const EXECUTABLE_DATASET_MAX_BYTES = 5 * 1024 * 1024;
const DATASET_PREVIEW_CHAR_LIMIT = 25000;

function ChatView() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [latestExecutionDatasets, setLatestExecutionDatasets] = useState({});
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  const [user, setUser] = useState(auth.getUser());
  const [toast, setToast] = useState(null);
  
  // Policy proof upload modal state
  const [showProofModal, setShowProofModal] = useState(false);
  const [policyClaimData, setPolicyClaimData] = useState(null);

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
    const handleAuthUserUpdate = () => setUser(auth.getUser());
    window.addEventListener('auth-user-updated', handleAuthUserUpdate);
    return () => window.removeEventListener('auth-user-updated', handleAuthUserUpdate);
  }, []);

  useEffect(() => {
    if (sessionId && sessions.length > 0) {
      const session = sessions.find(s => s.id === sessionId);
      if (session) {
        // Avoid resetting current session object on every sessions refresh.
        // This prevents unnecessary message reloads that can wipe optimistic UI data.
        setCurrentSession(prev => (prev?.id === session.id ? prev : session));
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
      let newestDataset = null;
      for (const message of data.messages || []) {
        const attachment = message.file || message.metadata?.file || null;
        const nameLower = attachment?.name?.toLowerCase() || '';
        const isRunnableDataset =
          Boolean(attachment?.execution_text || attachment?.preview_text) &&
          (
            nameLower.endsWith('.csv') ||
            nameLower.endsWith('.tsv') ||
            nameLower.endsWith('.json') ||
            attachment?.type === 'application/json' ||
            attachment?.type === 'text/csv'
          );
        if (message.role === 'user' && isRunnableDataset) {
          newestDataset = {
            text: attachment.execution_text || attachment.preview_text,
            name: attachment.name || 'dataset.csv',
            truncated: Boolean(attachment.execution_text_truncated ?? attachment.preview_text_truncated),
          };
        }
      }
      if (newestDataset) {
        setLatestExecutionDatasets(prev => ({
          ...prev,
          [sessionId]: newestDataset,
        }));
      }
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

  const handleSendMessage = async (content, file = null) => {
    let sessionToUse = currentSession;

    const buildFileMessageMeta = async (uploadedFile) => {
      if (!uploadedFile) return null;

      const nameLower = uploadedFile.name.toLowerCase();
      const isImage = uploadedFile.type.startsWith('image/');
      const isPdf = uploadedFile.type === 'application/pdf' || nameLower.endsWith('.pdf');
      const isTextLike =
        uploadedFile.type.startsWith('text/') ||
        nameLower.endsWith('.csv') ||
        nameLower.endsWith('.tsv') ||
        nameLower.endsWith('.json') ||
        nameLower.endsWith('.md') ||
        nameLower.endsWith('.py') ||
        nameLower.endsWith('.js') ||
        nameLower.endsWith('.jsx') ||
        nameLower.endsWith('.ts') ||
        nameLower.endsWith('.tsx') ||
        nameLower.endsWith('.sql') ||
        nameLower.endsWith('.yaml') ||
        nameLower.endsWith('.yml');

      const fileMeta = {
        name: uploadedFile.name,
        size: uploadedFile.size,
        type: uploadedFile.type,
        preview_kind: isImage ? 'image' : (isPdf ? 'pdf' : (isTextLike ? 'text' : 'other')),
      };

      if (isImage || isPdf || isTextLike) {
        fileMeta.preview_url = URL.createObjectURL(uploadedFile);
      }

      if (isTextLike && uploadedFile.size <= EXECUTABLE_DATASET_MAX_BYTES) {
        try {
          const rawText = await uploadedFile.text();
          fileMeta.execution_text = rawText;
          fileMeta.execution_text_truncated = false;
          fileMeta.preview_text = rawText.slice(0, DATASET_PREVIEW_CHAR_LIMIT);
          fileMeta.preview_text_truncated = rawText.length > DATASET_PREVIEW_CHAR_LIMIT;
        } catch {
          // Ignore text extraction issues and fall back to URL preview.
        }
      }

      return fileMeta;
    };
    
    // Create new session if none exists
    if (!sessionToUse) {
      try {
        sessionToUse = await createNewSession();
      } catch (error) {
        return;
      }
    }

    // Add user message optimistically
    const fileMessageMeta = file ? await buildFileMessageMeta(file) : null;

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
      file: fileMessageMeta,
    };
    setMessages((prev) => [...prev, userMessage]);
    if (
      (fileMessageMeta?.execution_text || fileMessageMeta?.preview_text) &&
      (
        fileMessageMeta.name?.toLowerCase().endsWith('.csv') ||
        fileMessageMeta.name?.toLowerCase().endsWith('.tsv') ||
        fileMessageMeta.name?.toLowerCase().endsWith('.json') ||
        fileMessageMeta.type === 'application/json' ||
        fileMessageMeta.type === 'text/csv'
      )
    ) {
      setLatestExecutionDatasets(prev => ({
        ...prev,
        [sessionToUse.id]: {
          text: fileMessageMeta.execution_text || fileMessageMeta.preview_text,
          name: fileMessageMeta.name || 'dataset.csv',
          truncated: Boolean(fileMessageMeta.execution_text_truncated ?? fileMessageMeta.preview_text_truncated),
        },
      }));
    }
    setLoading(true);
    setError(null);

    try {
      // If file is provided, send as FormData
      let response;
      if (file) {
        const formData = new FormData();
        formData.append('question', content);
        formData.append('session_id', sessionToUse.id);
        formData.append('file', file);
        response = await api.queryWithFile(formData);
      } else {
        response = await api.query({
          question: content,
          session_id: sessionToUse.id,
        });
      }

      // Check for policy claim detection
      if (response.policy_claim_detected && response.policy_claim_detected.claim_detected) {
        setPolicyClaimData({
          ...response.policy_claim_detected,
          sessionId: sessionToUse.id
        });
        setShowProofModal(true);
      }

      // Add assistant message with sources
      const assistantMessage = {
        id: response.assistant_message_id || `assistant-${Date.now()}`,
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

      setLatestExecutionDatasets(prev => {
        const updated = { ...prev };
        delete updated[sessionId];
        return updated;
      });
      
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
        latestExecutionDataset={currentSession ? latestExecutionDatasets[currentSession.id] || null : null}
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
        showProofModal={showProofModal}
        policyClaimData={policyClaimData}
        onCloseProofModal={() => {
          setShowProofModal(false);
          setPolicyClaimData(null);
        }}
        onProofUploadSuccess={() => {
          setShowProofModal(false);
          setPolicyClaimData(null);
          showToast('Policy update request submitted successfully!', 'success');
        }}
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

  useEffect(() => {
    const handleAuthUserUpdate = () => setUser(auth.getUser());
    window.addEventListener('auth-user-updated', handleAuthUserUpdate);
    return () => window.removeEventListener('auth-user-updated', handleAuthUserUpdate);
  }, []);

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

  useEffect(() => {
    const handleAuthUserUpdate = () => setUser(auth.getUser());
    window.addEventListener('auth-user-updated', handleAuthUserUpdate);
    return () => window.removeEventListener('auth-user-updated', handleAuthUserUpdate);
  }, []);

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

function ChunkEditorView() {
  const navigate = useNavigate();
  const [toast, setToast] = useState(null);
  const [user, setUser] = useState(auth.getUser());

  const showToast = (message, type = 'info', duration = 5000) => {
    setToast({ message, type, duration });
  };

  useEffect(() => {
    // Check if user is authenticated
    if (!user) {
      showToast('Please sign in to access this page', 'error');
      navigate('/policy-updates');
    }
  }, [user, navigate]);

  useEffect(() => {
    const handleAuthUserUpdate = () => setUser(auth.getUser());
    window.addEventListener('auth-user-updated', handleAuthUserUpdate);
    return () => window.removeEventListener('auth-user-updated', handleAuthUserUpdate);
  }, []);

  return (
    <div className="app-container">
      <ChunkEditorPage 
        user={user}
        showToast={showToast}
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

function PolicyUpdatesView() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [toast, setToast] = useState(null);
  const [user, setUser] = useState(auth.getUser());

  const showToast = (message, type = 'info', duration = 5000) => {
    setToast({ message, type, duration });
  };

  useEffect(() => {
    if (user) {
      loadSessions();
    }
  }, [user]);

  useEffect(() => {
    const handleAuthUserUpdate = () => setUser(auth.getUser());
    window.addEventListener('auth-user-updated', handleAuthUserUpdate);
    return () => window.removeEventListener('auth-user-updated', handleAuthUserUpdate);
  }, []);

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
      <PolicyUpdatesPage
        user={user}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        showToast={showToast}
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

function ExtensionsView() {
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [user, setUser] = useState(auth.getUser());
  const [sessions, setSessions] = useState([]);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info', duration = 5000) => {
    setToast({ message, type, duration });
  };

  useEffect(() => {
    // Check if user has access to extensions (faculty or admin)
    if (!user || (user.role !== 'faculty' && user.role !== 'admin')) {
      navigate('/');
    }
  }, [user, navigate]);

  useEffect(() => {
    if (user) {
      loadSessions();
    }
  }, [user]);

  useEffect(() => {
    const handleAuthUserUpdate = () => setUser(auth.getUser());
    window.addEventListener('auth-user-updated', handleAuthUserUpdate);
    return () => window.removeEventListener('auth-user-updated', handleAuthUserUpdate);
  }, []);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      showToast('Failed to load sessions', 'error');
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await api.deleteSession(sessionId);
      await loadSessions();
      showToast('Chat deleted successfully', 'success');
    } catch (error) {
      console.error('Failed to delete session:', error);
      showToast('Failed to delete session', 'error');
    }
  };

  const handleLogout = () => {
    auth.logout();
    setUser(null);
    navigate('/');
  };

  if (!user || (user.role !== 'faculty' && user.role !== 'admin')) {
    return null;
  }

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
      <ExtensionsPage 
        user={user}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
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

function AdminExtensionsView() {
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [user, setUser] = useState(auth.getUser());
  const [sessions, setSessions] = useState([]);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info', duration = 5000) => {
    setToast({ message, type, duration });
  };

  useEffect(() => {
    // Check if user is admin only
    if (!user || user.role !== 'admin') {
      navigate('/extensions'); // Redirect to view-only page
    }
  }, [user, navigate]);

  useEffect(() => {
    if (user) {
      loadSessions();
    }
  }, [user]);

  useEffect(() => {
    const handleAuthUserUpdate = () => setUser(auth.getUser());
    window.addEventListener('auth-user-updated', handleAuthUserUpdate);
    return () => window.removeEventListener('auth-user-updated', handleAuthUserUpdate);
  }, []);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      showToast('Failed to load sessions', 'error');
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await api.deleteSession(sessionId);
      await loadSessions();
      showToast('Chat deleted successfully', 'success');
    } catch (error) {
      console.error('Failed to delete session:', error);
      showToast('Failed to delete session', 'error');
    }
  };

  const handleLogout = () => {
    auth.logout();
    setUser(null);
    navigate('/');
  };

  if (!user || user.role !== 'admin') {
    return null;
  }

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
      <AdminExtensionsPage 
        user={user}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
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

function AdminUsersView() {
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [user, setUser] = useState(auth.getUser());
  const [sessions, setSessions] = useState([]);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info', duration = 5000) => {
    setToast({ message, type, duration });
  };

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      navigate('/');
    }
  }, [user, navigate]);

  useEffect(() => {
    if (user) {
      loadSessions();
    }
  }, [user]);

  useEffect(() => {
    const handleAuthUserUpdate = () => setUser(auth.getUser());
    window.addEventListener('auth-user-updated', handleAuthUserUpdate);
    return () => window.removeEventListener('auth-user-updated', handleAuthUserUpdate);
  }, []);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      showToast('Failed to load sessions', 'error');
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await api.deleteSession(sessionId);
      await loadSessions();
      showToast('Chat deleted successfully', 'success');
    } catch (error) {
      console.error('Failed to delete session:', error);
      showToast('Failed to delete session', 'error');
    }
  };

  const handleLogout = () => {
    auth.logout();
    setUser(null);
    navigate('/');
  };

  if (!user || user.role !== 'admin') {
    return null;
  }

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
      <AdminUsersPage
        user={user}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        showToast={showToast}
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

function AdminChromaChunksView() {
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [user, setUser] = useState(auth.getUser());
  const [sessions, setSessions] = useState([]);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info', duration = 5000) => {
    setToast({ message, type, duration });
  };

  useEffect(() => {
    if (!user || user.role !== 'admin') {
      navigate('/');
    }
  }, [user, navigate]);

  useEffect(() => {
    if (user) {
      loadSessions();
    }
  }, [user]);

  useEffect(() => {
    const handleAuthUserUpdate = () => setUser(auth.getUser());
    window.addEventListener('auth-user-updated', handleAuthUserUpdate);
    return () => window.removeEventListener('auth-user-updated', handleAuthUserUpdate);
  }, []);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data.sessions || []);
    } catch (error) {
      console.error('Failed to load sessions:', error);
      showToast('Failed to load sessions', 'error');
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await api.deleteSession(sessionId);
      await loadSessions();
      showToast('Chat deleted successfully', 'success');
    } catch (error) {
      console.error('Failed to delete session:', error);
      showToast('Failed to delete session', 'error');
    }
  };

  const handleLogout = () => {
    auth.logout();
    setUser(null);
    navigate('/');
  };

  if (!user || user.role !== 'admin') {
    return null;
  }

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
      <AdminChromaChunksPage
        user={user}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        showToast={showToast}
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

function App() {
  const navigate = useNavigate();
  const [globalToast, setGlobalToast] = useState(null);
  const [suspendedDialogOpen, setSuspendedDialogOpen] = useState(false);

  const showGlobalToast = (message, type = 'info', duration = 5000) => {
    setGlobalToast({ message, type, duration });
  };

  useEffect(() => {
    let stopped = false;

    const syncCurrentUser = async () => {
      if (!auth.isAuthenticated()) return;

      const current = auth.getUser();
      if (!current) return;

      try {
        const [authInfo, profileInfo] = await Promise.all([
          api.getCurrentAuthUser().catch(() => null),
          api.getCurrentUserProfile().catch(() => null),
        ]);

        if (stopped) return;
        if (!authInfo && !profileInfo) return;

        const merged = {
          ...current,
          ...(authInfo || {}),
          ...(profileInfo || {}),
        };

        const roleChanged = current.role !== merged.role;
        const verificationChanged = current.verification_status !== merged.verification_status;
        const statusChanged = current.account_status !== merged.account_status;

        if (roleChanged || verificationChanged || statusChanged) {
          auth.syncUser(merged);
        }

        if (roleChanged) {
          showGlobalToast(`Your role was updated to ${merged.role}.`, 'info', 6000);
        }

        if (verificationChanged) {
          showGlobalToast(`Verification status updated to ${merged.verification_status}.`, 'info', 6000);
        }

        if (merged.account_status === 'suspended') {
          setSuspendedDialogOpen(true);
        }
      } catch (error) {
        // Silent background sync failure; regular API calls still surface errors.
      }
    };

    syncCurrentUser();
    const intervalId = setInterval(syncCurrentUser, 30000);

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        syncCurrentUser();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      stopped = true;
      clearInterval(intervalId);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const requiresVerification = (user) => {
    if (!user) return false;
    if (user.role === 'admin') return false;
    if (user.verification_required === false) return false;
    return user.verification_status !== 'verified';
  };

  const VerificationGuard = ({ children }) => {
    const user = auth.getUser();
    if (auth.isAuthenticated() && requiresVerification(user)) {
      return <Navigate to="/verify-identity" replace />;
    }
    return children;
  };

  const handleAuthSuccess = (user) => {
    console.log('Logged in:', user);
    if (requiresVerification(user)) {
      navigate('/verify-identity');
      return;
    }
    navigate('/');
  };

  const handleVerificationSuccess = () => {
    navigate('/');
  };

  return (
    <>
      <Routes>
        <Route path="/" element={<VerificationGuard><ChatView /></VerificationGuard>} />
        <Route path="/:sessionId" element={<VerificationGuard><ChatView /></VerificationGuard>} />
        <Route path="/auth/callback" element={<OAuthCallback onSuccess={handleAuthSuccess} />} />
        <Route path="/verify-identity" element={<IdentityVerification onVerified={handleVerificationSuccess} />} />
        <Route path="/preferences" element={<VerificationGuard><PreferencesView /></VerificationGuard>} />
        <Route path="/memory" element={<VerificationGuard><MemoryView /></VerificationGuard>} />
        <Route path="/extensions" element={<VerificationGuard><ExtensionsView /></VerificationGuard>} />
        <Route path="/extensions/manage" element={<VerificationGuard><AdminExtensionsView /></VerificationGuard>} />
        <Route path="/admin/users" element={<VerificationGuard><AdminUsersView /></VerificationGuard>} />
        <Route path="/admin/chroma-vault" element={<VerificationGuard><AdminChromaChunksView /></VerificationGuard>} />
        <Route path="/policy-updates" element={<VerificationGuard><PolicyUpdatesView /></VerificationGuard>} />
        <Route path="/policy-updates/:ticketId/deprecate" element={<VerificationGuard><ChunkEditorView /></VerificationGuard>} />
      </Routes>

      {globalToast && (
        <Toast
          message={globalToast.message}
          type={globalToast.type}
          duration={globalToast.duration}
          onClose={() => setGlobalToast(null)}
        />
      )}

      <Dialog
        isOpen={suspendedDialogOpen}
        onClose={() => {
          setSuspendedDialogOpen(false);
          auth.logout();
          navigate('/');
        }}
        onConfirm={() => {
          auth.logout();
          navigate('/');
        }}
        title="Account Suspended"
        message="Your account has been suspended by an administrator. Please contact support or admin."
        confirmText="OK"
        cancelText="Close"
        type="alert"
      />
    </>
  );
}

export default App;
