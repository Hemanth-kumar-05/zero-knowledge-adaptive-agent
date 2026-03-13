import axios from 'axios';
import { auth } from '../utils/auth';

const client = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 0, // No timeout - allow long-running operations like semantic search
});

// Request interceptor to add auth token
client.interceptors.request.use(
  (config) => {
    const token = auth.getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data;
      
      // Handle authentication errors
      if (status === 401) {
        const wasLoggedIn = auth.isAuthenticated();
        auth.logout();
        // Only redirect if user was previously logged in to avoid infinite loops
        if (wasLoggedIn && window.location.pathname !== '/') {
          window.location.href = '/';
        }
        throw new Error('Session expired. Please sign in again.');
      }
      
      // Handle specific error codes with user-friendly messages
      let message;
      if (status === 403) {
        message = 'You do not have permission to perform this action.';
      } else if (status === 404) {
        message = 'The requested resource was not found.';
      } else if (status === 429) {
        message = 'Too many requests. Please slow down.';
      } else if (status >= 500) {
        message = 'Server error. Please try again later.';
      } else {
        message = data?.detail || data?.message || error.message;
      }
      
      throw new Error(message);
    } else if (error.request) {
      // Request made but no response
      throw new Error('No response from server. Please check your connection.');
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('Request timeout. Please try again.');
    } else {
      throw new Error(error.message || 'An unexpected error occurred.');
    }
  }
);

const api = {
  getCurrentAuthUser: async () => {
    const response = await axios.get('/api/auth/me', {
      headers: {
        ...auth.getAuthHeader(),
        'Content-Type': 'application/json',
      },
    });
    return response.data;
  },

  getCurrentUserProfile: async () => {
    const response = await client.get('/users/profile');
    return response.data;
  },

  verifyIdentity: async (formData) => {
    const response = await axios.post('/api/auth/verify-identity', formData, {
      headers: {
        ...auth.getAuthHeader(),
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Health endpoints
  checkHealth: async () => {
    try {
      const response = await client.get('/health/');
      return response.data;
    } catch (error) {
      return { status: 'unhealthy', error: error.message };
    }
  },

  checkLiveness: async () => {
    try {
      const response = await client.get('/health/live');
      return response.data;
    } catch (error) {
      return { alive: false, error: error.message };
    }
  },

  checkReadiness: async () => {
    try {
      const response = await client.get('/health/ready');
      return response.data;
    } catch (error) {
      return { ready: false, error: error.message };
    }
  },

  // Session endpoints
  createSession: async (extensionId = null) => {
    const params = extensionId ? { extension_id: extensionId } : {};
    const response = await client.post('/sessions/', {}, { params });
    // Map backend response to frontend format
    return {
      id: response.data.session_id,
      user_id: response.data.user_id,
      created_at: new Date().toISOString(),
      message_count: 0,
      extension_id: response.data.extension_id,
      requires_files: response.data.requires_files,
      required_file_types: response.data.required_file_types,
    };
  },

  getSessions: async () => {
    const response = await client.get('/sessions/');
    // Map backend sessions to frontend format
    const sessions = response.data.sessions.map(session => ({
      id: session.id,
      user_id: session.user_id,
      created_at: session.created_at,
      updated_at: session.updated_at,
      message_count: session.message_count || 0,
      title: `Session ${session.message_count || 0} messages`,
      extension_id: session.extension_id,
      extension_name: session.extension_name,
      extension_icon: session.extension_icon,
      extension_welcome_message: session.extension_welcome_message,
      extension_input_placeholder: session.extension_input_placeholder
    }));
    return { sessions, count: response.data.count };
  },

  getSession: async (sessionId) => {
    const response = await client.get(`/sessions/${sessionId}`);
    return {
      id: response.data.id,
      user_id: response.data.user_id,
      created_at: response.data.created_at,
      updated_at: response.data.updated_at,
      message_count: response.data.message_count || 0,
    };
  },

  deleteSession: async (sessionId) => {
    const response = await client.delete(`/sessions/${sessionId}`);
    return response.data;
  },

  // Message endpoints
  getSessionMessages: async (sessionId) => {
    const response = await client.get(`/sessions/${sessionId}/messages`);
    return {
      messages: response.data.messages,
      count: response.data.count,
    };
  },

  // Query endpoint
  query: async (data) => {
    const response = await client.post('/query', data);
    return response.data;
  },

  // Query with file attachment
  queryWithFile: async (formData) => {
    const response = await client.post('/query', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Preference endpoints
  getPreferences: async () => {
    const response = await client.get('/users/preferences');
    return response.data;
  },

  getUserPreferences: async () => {
    // Alias for getPreferences for consistency
    const response = await client.get('/users/preferences');
    return response.data;
  },

  getPreferencesMetadata: async () => {
    const response = await client.get('/users/preferences/metadata');
    return response.data;
  },

  getPreferencesCategories: async () => {
    const response = await client.get('/users/preferences/categories');
    return response.data;
  },

  updatePreferenceLock: async (key, locked) => {
    const response = await client.put(`/users/preferences/${key}/lock`, { locked });
    return response.data;
  },

  deletePreference: async (key) => {
    const response = await client.delete(`/users/preferences/${key}`);
    return response.data;
  },

  resetPreferences: async () => {
    const response = await client.post('/users/preferences/reset');
    return response.data;
  },

  addManualPreference: async (naturalLanguageInput) => {
    const response = await client.post('/users/preferences/manual', { 
      preference_text: naturalLanguageInput 
    });
    return response.data;
  },

  checkPreferenceConflicts: async () => {
    const response = await client.post('/users/preferences/check-conflicts');
    return response.data;
  },

  resolvePreferenceConflict: async (preferenceKey, action) => {
    const response = await client.post('/users/preferences/resolve-conflict', null, {
      params: { preference_key: preferenceKey, action }
    });
    return response.data;
  },

  // Memory management endpoints
  getMemory: async () => {
    const response = await client.get('/memory/view');
    return response.data;
  },

  storeFact: async (fact, requireConfirmation = true) => {
    const response = await client.post('/memory/store', {
      fact,
      require_confirmation: requireConfirmation
    });
    return response.data;
  },

  updateFact: async (key, updates) => {
    const response = await client.put(`/memory/update/${key}`, updates);
    return response.data;
  },

  forgetFact: async (key) => {
    const response = await client.delete(`/memory/forget/${key}`);
    return response.data;
  },

  resetMemory: async (category = null) => {
    const params = category ? { category } : {};
    const response = await client.delete('/memory/reset', { params });
    return response.data;
  },

  confirmFact: async (key) => {
    const response = await client.post(`/memory/confirm/${key}`);
    return response.data;
  },

  lockFact: async (key, locked) => {
    const response = await client.post(`/memory/lock/${key}`, { locked });
    return response.data;
  },

  setRetention: async (key, retention) => {
    const response = await client.put(`/memory/retention/${key}`, { retention });
    return response.data;
  },

  cleanupFacts: async () => {
    const response = await client.post('/memory/cleanup');
    return response.data;
  },

  // Policy Updates Management (Phase 3)
  getPolicyUpdateTickets: async (status = null) => {
    const params = status ? { status } : {};
    const response = await client.get('/policy-updates/tickets', { params });
    return response.data;
  },

  getPolicyUpdateTicket: async (ticketId) => {
    const response = await client.get(`/policy-updates/tickets/${ticketId}`);
    return response.data;
  },

  approvePolicyUpdate: async (ticketId, approvalData) => {
    const response = await client.post(
      `/policy-updates/tickets/${ticketId}/approve`,
      approvalData
    );
    return response.data;
  },

  rejectPolicyUpdate: async (ticketId, rejectionData) => {
    const response = await client.post(
      `/policy-updates/tickets/${ticketId}/reject`,
      rejectionData
    );
    return response.data;
  },

  getPolicyAuditLog: async (limit = 50, skip = 0) => {
    const response = await client.get('/policy-updates/audit', {
      params: { limit, skip }
    });
    return response.data;
  },

  getPolicyUpdateStats: async () => {
    const response = await client.get('/policy-updates/stats');
    return response.data;
  },

  // Find affected chunks for deprecation (Phase 3)
  findAffectedChunks: async (ticketId) => {
    const response = await client.post(
      `/policy-updates/tickets/${ticketId}/find-affected-chunks`
    );
    return response.data;
  },

  // Apply policy deprecation (Phase 3)
  applyPolicyDeprecation: async (ticketId, deprecationData) => {
    const response = await client.post(
      `/policy-updates/tickets/${ticketId}/apply-deprecation`,
      deprecationData
    );
    return response.data;
  },

  // Policy Proof Upload (Phase 3)
  uploadPolicyProof: async (file, ticketIdPending) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('ticket_id_pending', ticketIdPending);
    
    const response = await client.post('/policy-proofs/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  createTicketWithProofs: async (sessionId, proofUrls) => {
    const response = await client.post('/policy-proofs/create-ticket', {
      session_id: sessionId,
      proof_urls: proofUrls
    });
    return response.data;
  },

  // Admin user management
  getAdminUsers: async () => {
    const response = await client.get('/users/admin/users');
    return response.data;
  },

  updateAdminUserRole: async (userId, role) => {
    const response = await client.patch(`/users/admin/users/${userId}/role`, { role });
    return response.data;
  },

  updateAdminUserStatus: async (userId, accountStatus) => {
    const response = await client.patch(`/users/admin/users/${userId}/status`, {
      account_status: accountStatus,
    });
    return response.data;
  },

  resetAdminUserVerification: async (userId) => {
    const response = await client.post(`/users/admin/users/${userId}/verification/reset`);
    return response.data;
  },
};

export { client };
export default api;
