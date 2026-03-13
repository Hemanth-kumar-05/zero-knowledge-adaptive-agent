import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { auth } from '../../utils/auth';
import api from '../../api/client';
import Toast from '../../components/common/Toast';
import './Auth.css';

function needsVerification(user) {
  if (!user) return true;
  if (user.role === 'admin') return false;
  if (user.verification_required === false) return false;
  return user.verification_status !== 'verified';
}

export default function IdentityVerification({ onVerified }) {
  const navigate = useNavigate();
  const user = auth.getUser();

  const [allowNameEdit, setAllowNameEdit] = useState(false);
  const [profileName, setProfileName] = useState(user?.name || '');
  const [expectedRole, setExpectedRole] = useState('student');
  const [idFiles, setIdFiles] = useState([]);
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [toast, setToast] = useState(null);
  const [isCompletingVerification, setIsCompletingVerification] = useState(false);
  const redirectTimerRef = useRef(null);

  const showToast = (message, type = 'info', duration = 3000) => {
    setToast({ message, type, duration });
  };

  useEffect(() => {
    return () => {
      if (redirectTimerRef.current) {
        clearTimeout(redirectTimerRef.current);
      }
    };
  }, []);

  const canSubmit = useMemo(() => {
    return idFiles.length >= 1 && idFiles.length <= 2 && !submitting;
  }, [idFiles, submitting]);

  const groupedFeedback = useMemo(() => {
    if (!result || result.verified) return [];

    const fallback = [
      'Failure reason: Proof is insufficient.',
      'What AI expects: Upload a clear ID image with readable full name and roll/employee number.',
    ];

    const rawItems = Array.isArray(result.failure_feedback) && result.failure_feedback.length > 0
      ? result.failure_feedback
      : fallback;

    const deduped = [];
    const seen = new Set();
    rawItems.forEach((item) => {
      const text = String(item || '').trim();
      if (!text) return;
      if (seen.has(text)) return;
      seen.add(text);
      deduped.push(text);
    });

    const groups = [];
    let current = null;

    deduped.forEach((line) => {
      if (line.startsWith('Failure reason:')) {
        if (current) groups.push(current);
        current = {
          reason: line.replace('Failure reason:', '').trim(),
          expects: [],
        };
        return;
      }

      if (line.startsWith('What AI expects:')) {
        if (!current) {
          current = {
            reason: 'Proof is insufficient for verification.',
            expects: [],
          };
        }
        current.expects.push(line.replace('What AI expects:', '').trim());
        return;
      }

      if (!current) {
        current = {
          reason: line,
          expects: [],
        };
      } else {
        current.expects.push(line);
      }
    });

    if (current) groups.push(current);

    return groups.map((group) => ({
      ...group,
      expects: Array.from(new Set(group.expects)).filter(Boolean),
    }));
  }, [result]);

  const handleLogout = () => {
    auth.logout();
    navigate('/');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setResult(null);

    if (idFiles.length < 1 || idFiles.length > 2) {
      setError('Please upload one or two ID images.');
      return;
    }

    setSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('allow_name_edit', String(allowNameEdit));
      formData.append('profile_name', profileName || '');
      formData.append('expected_role', expectedRole);
      formData.append('scan_text', '');
      idFiles.forEach((file) => {
        formData.append('id_images', file);
      });

      const data = await api.verifyIdentity(formData);
      setResult(data);

      if (data.verified) {
        setIsCompletingVerification(true);
        const current = auth.getUser() || {};
        const updatedUser = {
          ...current,
          name: allowNameEdit && profileName ? profileName : current.name,
          role: data.assigned_role || current.role,
          verification_required: true,
          verification_status: 'verified',
          verified_role: data.assigned_role || current.role,
        };
        await auth.setUser(updatedUser);
        showToast(`Identity verified successfully as ${data.assigned_role}. Access unlocked.`, 'success', 5000);

        redirectTimerRef.current = setTimeout(() => {
          if (onVerified) {
            onVerified(updatedUser);
            return;
          }
          navigate('/');
        }, 3200);
      }
    } catch (err) {
      setError(err.message || 'Verification failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!auth.isAuthenticated()) {
    navigate('/');
    return null;
  }

  if (!isCompletingVerification && user && !needsVerification(user)) {
    navigate('/');
    return null;
  }

  return (
    <div className="auth-container auth-login-container">
      <div className="auth-card verification-card">
        <div className="auth-header">
          <h1>Identity Verification</h1>
          <p>Step 2 of 2: Verify institutional identity to unlock chat access</p>
        </div>

        <form className="auth-content verification-form" onSubmit={handleSubmit}>
          <div className="verification-grid">
            <label>
              Google Email (read-only)
              <input type="email" value={user?.email || ''} readOnly disabled />
            </label>

            <label>
              Google Name
              <input
                type="text"
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
                disabled={!allowNameEdit}
              />
            </label>
          </div>

          <label className="inline-checkbox">
            <input
              type="checkbox"
              checked={allowNameEdit}
              onChange={(e) => setAllowNameEdit(e.target.checked)}
            />
            Allow editing name for verification matching
          </label>

          <div className="verification-grid">
            <label>
              Expected Role
              <select value={expectedRole} onChange={(e) => setExpectedRole(e.target.value)}>
                <option value="student">student</option>
                <option value="faculty">faculty</option>
              </select>
            </label>

            <label>
              Upload ID Image(s)
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={(e) => {
                  const files = Array.from(e.target.files || []).slice(0, 2);
                  setIdFiles(files);
                }}
                required
              />
              <small className="upload-help-text">
                Upload 1 image (front/back/combined) or 2 images (front + back).
              </small>
            </label>
          </div>

          <div className="verification-actions">
            <button type="submit" className="google-signin-button" disabled={!canSubmit}>
              {submitting ? 'Verifying identity...' : 'Submit for AI Verification'}
            </button>
            <button type="button" className="secondary-button" onClick={handleLogout}>
              Sign out
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}

          {result && (
            <div className="verification-result">
              <h3>Verification Result</h3>
              {result.verified ? (
                <p className="success-message">Identity verified successfully.</p>
              ) : (
                <>
                  <p className="pending-note">Verification is pending. Please re-upload your proof using the guidance below.</p>
                  <div className="pending-feedback-groups">
                    {groupedFeedback.map((group, index) => (
                      <article key={`${group.reason}-${index}`} className="pending-feedback-card">
                        <section className="pending-panel reason-panel">
                          <p className="pending-feedback-title">Failure reason</p>
                          <p className="pending-feedback-reason">{group.reason}</p>
                        </section>

                        <section className="pending-panel expects-panel">
                          <p className="pending-feedback-title">What AI expects</p>
                          {group.expects.length > 0 ? (
                            <ul className="pending-feedback-expects">
                              {group.expects.map((expectation, expectIdx) => (
                                <li key={`${expectation}-${expectIdx}`}>{expectation}</li>
                              ))}
                            </ul>
                          ) : (
                            <p className="pending-feedback-reason">Upload clearer proof with readable name, role, and ID number.</p>
                          )}
                        </section>
                      </article>
                    ))}
                  </div>
                </>
              )}
            </div>
          )}
        </form>
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
