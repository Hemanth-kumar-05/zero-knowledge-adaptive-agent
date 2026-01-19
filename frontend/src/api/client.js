import axios from 'axios';

const client = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Response interceptor for error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || error.message;
      throw new Error(message);
    } else if (error.request) {
      // Request made but no response
      throw new Error('No response from server. Please check your connection.');
    } else {
      throw new Error(error.message);
    }
  }
);

const api = {
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
  createSession: async (userId = 'default-user') => {
    const response = await client.post('/sessions/', { user_id: userId });
    // Map backend response to frontend format
    return {
      id: response.data.session_id,
      user_id: userId,
      created_at: new Date().toISOString(),
      message_count: 0,
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
};

export default api;
