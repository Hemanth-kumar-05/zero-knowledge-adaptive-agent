// Extensions API utilities
import { client } from './client';

export const extensionsAPI = {
  // Get all extensions
  getAllExtensions: async (activeOnly = true) => {
    const response = await client.get('/extensions', {
      params: { active_only: activeOnly }
    });
    return response.data;
  },

  // Get single extension
  getExtension: async (extensionId) => {
    const response = await client.get(`/extensions/${extensionId}`);
    return response.data;
  },

  // Create extension (admin only)
  createExtension: async (extensionData) => {
    // Check if extensionData is FormData (script-based) or plain object (prompt-based)
    const isFormData = extensionData instanceof FormData;
    
    const config = isFormData ? {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    } : {};

    const response = await client.post('/extensions', extensionData, config);
    return response.data;
  },

  // Delete extension (admin only)
  deleteExtension: async (extensionId) => {
    await client.delete(`/extensions/${extensionId}`);
    return true;
  },

  // Get extensions by category
  getExtensionsByCategory: async (category) => {
    const response = await client.get(`/extensions/category/${category}`);
    return response.data;
  },

  // Create a new session with an extension
  createExtensionSession: async (extensionId) => {
    const response = await client.post('/sessions/', {}, {
      params: { extension_id: extensionId }
    });
    return response.data;
  }
};
