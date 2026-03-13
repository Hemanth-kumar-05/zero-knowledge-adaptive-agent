import { useState } from 'react';
import { FaExclamationTriangle } from 'react-icons/fa';
import './Auth.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function Auth({ onLogin }) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Get Google OAuth URL from backend
      const response = await fetch(`${API_BASE_URL}/api/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error('Failed to get authentication URL');
      }

      // Redirect to Google OAuth
      window.location.href = data.auth_url;
    } catch (err) {
      setError(err.message);
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container auth-login-container">
      <div className="auth-card auth-login-shell">
        <section className="auth-brand-panel">
          <div className="auth-brand-top">
            <p className="auth-kicker">INSTITUTIONAL AI PLATFORM</p>
            <h1>AcademIQ Agent Cloud</h1>
            <p className="auth-description">
              Zero-knowledge academic intelligence with controlled memory, secure multi-user isolation,
              and AI-assisted role verification.
            </p>
          </div>

          {/* <div className="auth-feature-grid">
            <svg
              className="feature-roadmap"
              viewBox="0 0 100 100"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <path className="roadmap-line" d="M12 10 C 60 12, 42 30, 88 34 S 36 58, 12 62 S 58 84, 86 88" />
              <circle className="roadmap-stop" cx="14" cy="10" r="1.8" />
              <circle className="roadmap-stop" cx="86" cy="34" r="1.8" />
              <circle className="roadmap-stop" cx="14" cy="62" r="1.8" />
              <circle className="roadmap-stop" cx="84" cy="88" r="1.8" />
            </svg>

            <article className="auth-feature-card feature-left">
              <span className="feature-badge">01</span>
              <h3>Adaptive Knowledge</h3>
            </article>
            <article className="auth-feature-card feature-right">
              <span className="feature-badge">02</span>
              <h3>Identity Security</h3>
            </article>
            <article className="auth-feature-card feature-left">
              <span className="feature-badge">03</span>
              <h3>Role-Aware Access</h3>
            </article>
            <article className="auth-feature-card feature-right">
              <span className="feature-badge">04</span>
              <h3>Governed Evolution</h3>
            </article>
          </div> */}
        </section>

        <section className="auth-signin-panel">
          <div className="auth-header">
            <h2>Secure Sign In</h2>
            <p>Sign in to continue to your institutional workspace</p>
          </div>

          <div className="auth-content">
            <div className="signin-flow-note">
              <p><strong>Onboarding Flow</strong></p>
              <p>1. Google Sign In</p>
              <p>2. Submit front and back institutional ID (scan or upload)</p>
              <p>3. AI verification and automatic role assignment</p>
            </div>

            <button
              className="google-signin-button"
              onClick={handleGoogleLogin}
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <div className="spinner"></div>
                  <span>Connecting to Google...</span>
                </>
              ) : (
                <>
                  <svg className="google-icon" viewBox="0 0 24 24">
                    <path
                      fill="#4285F4"
                      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                    />
                    <path
                      fill="#34A853"
                      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                    />
                    <path
                      fill="#FBBC05"
                      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                    />
                    <path
                      fill="#EA4335"
                      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                    />
                  </svg>
                  Continue with Google
                </>
              )}
            </button>

            {error && (
              <div className="error-message">
                <FaExclamationTriangle style={{ marginRight: '6px' }} /> {error}
              </div>
            )}
          </div>

          <div className="auth-footer">
            <p className="text-sm">
              By signing in, you agree to our Terms of Service and Privacy Policy
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
