import { useEffect, useState } from 'react';
import { auth } from '../../utils/auth';
import Toast from '../../components/common/Toast';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function OAuthCallback({ onSuccess }) {
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get token from URL (backend redirects here with token)
        const params = new URLSearchParams(window.location.search);
        const token = params.get('token');
        const error = params.get('error');

        if (error) {
          throw new Error(`OAuth error: ${error}`);
        }

        if (!token) {
          throw new Error('No authentication token received');
        }

        // Fetch user info using the token
        const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || 'Failed to fetch user info');
        }

        // Store token and user info
        auth.setToken(token);
        await auth.setUser(data);

        setStatus('success');
        setToast({
          message: `Welcome ${data.name || 'back'}! Login successful.`,
          type: 'success',
          duration: 2500,
        });

        // Call success callback which will handle navigation
        setTimeout(() => {
          onSuccess(data);
        }, 1000);
      } catch (err) {
        console.error('OAuth callback error:', err);
        setStatus('error');
        setError(err.message);

        // Redirect to login after error
        setTimeout(() => {
          window.location.href = '/';
        }, 3000);
      }
    };

    handleCallback();
  }, [onSuccess]);

  return (
    <div className="auth-container">
      <div className="auth-card">
        {status === 'processing' && (
          <>
            <div className="spinner-large" style={{ marginBottom: '20px' }}></div>
            <h2>Signing you in...</h2>
            <p style={{ color: '#6b7280', marginTop: '10px' }}>
              Please wait while we complete your authentication
            </p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="success-icon" style={{ marginBottom: '20px' }}>
              <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#10a37f" strokeWidth="2">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                <polyline points="22 4 12 14.01 9 11.01"></polyline>
              </svg>
            </div>
            <h2>Success!</h2>
            <p style={{ color: '#6b7280', marginTop: '10px' }}>
              Redirecting to AcademIQ...
            </p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="error-icon" style={{ marginBottom: '20px' }}>
              <svg width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="15" y1="9" x2="9" y2="15"></line>
                <line x1="9" y1="9" x2="15" y2="15"></line>
              </svg>
            </div>
            <h2>Authentication Failed</h2>
            <p style={{ color: '#991b1b', marginTop: '10px' }}>
              {error}
            </p>
            <p style={{ color: '#6b7280', marginTop: '10px', fontSize: '0.9rem' }}>
              Redirecting to login...
            </p>
          </>
        )}
      </div>

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
