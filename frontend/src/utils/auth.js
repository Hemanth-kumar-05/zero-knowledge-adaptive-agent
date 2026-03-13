// Authentication utility functions

const TOKEN_KEY = 'academiq_token';
const USER_KEY = 'academiq_user';

export const auth = {
  // Store auth data
  setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  },

  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },

  async setUser(user) {
    // If user has a profile picture URL, download and convert to base64
    if (user.profile_picture && user.profile_picture.startsWith('http')) {
      try {
        const base64Image = await this.downloadAndCacheImage(user.profile_picture);
        user.profile_picture = base64Image;
      } catch (error) {
        console.warn('Failed to cache profile picture:', error);
        // Remove the profile picture URL so initials are shown instead
        delete user.profile_picture;
      }
    }
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    window.dispatchEvent(new Event('auth-user-updated'));
  },

  // Fast local update without image re-download, used by periodic profile sync
  syncUser(partialUser) {
    const current = this.getUser() || {};
    const next = { ...current, ...partialUser };

    // Keep already cached base64 avatar when backend still returns URL.
    if (
      typeof current.profile_picture === 'string' &&
      current.profile_picture.startsWith('data:') &&
      typeof next.profile_picture === 'string' &&
      next.profile_picture.startsWith('http')
    ) {
      next.profile_picture = current.profile_picture;
    }

    localStorage.setItem(USER_KEY, JSON.stringify(next));
    window.dispatchEvent(new Event('auth-user-updated'));
    return next;
  },

  getUser() {
    const user = localStorage.getItem(USER_KEY);
    return user ? JSON.parse(user) : null;
  },

  // Download image and convert to base64
  async downloadAndCacheImage(imageUrl) {
    try {
      const response = await fetch(imageUrl);
      
      // Check for rate limit or other errors
      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Rate limit exceeded - using initials instead');
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const blob = await response.blob();
      
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
    } catch (error) {
      throw new Error('Failed to download image: ' + error.message);
    }
  },

  // Check if user is authenticated
  isAuthenticated() {
    return !!this.getToken();
  },

  // Clear auth data
  logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    window.dispatchEvent(new Event('auth-user-updated'));
  },

  // Get authorization header
  getAuthHeader() {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  },
};

// Handle OAuth callback (extract token from URL)
export function handleOAuthCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const error = params.get('error');

  if (error) {
    console.error('OAuth error:', error);
    return { success: false, error };
  }

  if (code) {
    return { success: true, code };
  }

  return { success: false, error: 'No code found' };
}
