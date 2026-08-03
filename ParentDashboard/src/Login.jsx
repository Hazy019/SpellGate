import React, { useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Rocket, Mail, Lock, AlertCircle, CheckCircle, Loader,
  Eye, EyeOff, ArrowLeft, Shield, Sun, Moon, X
} from 'lucide-react';
import { useTheme } from './ThemeContext';

import {
  GoogleAuthProvider,
  signInWithPopup,
} from 'firebase/auth';
import { doc, setDoc, serverTimestamp } from 'firebase/firestore';
import { auth, db } from './firebase';
import { useAuth } from './AuthContext';

/* ─────────────────────────────────────────────────────
   HELPERS
───────────────────────────────────────────────────── */
function friendlyError(code) {
  const map = {
    'auth/user-not-found':       'No account found with that email.',
    'auth/wrong-password':       'Incorrect password. Please try again.',
    'auth/email-already-in-use': 'An account with that email already exists.',
    'auth/weak-password':        'Password must be at least 6 characters.',
    'auth/invalid-email':        'Please enter a valid email address.',
    'auth/too-many-requests':    'Too many attempts. Please wait a moment and try again.',
    'auth/invalid-credential':   'Email or password is incorrect.',
    'auth/popup-closed-by-user': 'Sign-in window was closed. Please try again.',
    'auth/popup-blocked':        'Pop-up was blocked by your browser. Please allow pop-ups and try again.',
    'auth/network-request-failed': 'Network error. Please check your internet connection.',
  };
  return map[code] ?? 'Something went wrong. Please try again.';
}

function getPasswordStrength(password) {
  if (!password) return { score: 0, label: '', color: '' };
  let score = 0;
  if (password.length >= 8)           score++;
  if (password.length >= 12)          score++;
  if (/[A-Z]/.test(password))         score++;
  if (/[0-9]/.test(password))         score++;
  if (/[^A-Za-z0-9]/.test(password))  score++;
  if (score <= 1) return { score, label: 'Weak',    color: '#ff3864' };
  if (score <= 2) return { score, label: 'Fair',    color: '#ffc857' };
  if (score <= 3) return { score, label: 'Good',    color: '#00e5ff' };
  return           { score, label: 'Strong',  color: '#3dffa0' };
}

/* ─────────────────────────────────────────────────────
   ALERT COMPONENT
───────────────────────────────────────────────────── */
function Alert({ type, msg }) {
  const isError = type === 'error';
  return (
    <div className={`alert ${isError ? 'alert-error' : 'alert-success'}`} role="alert">
      {isError
        ? <AlertCircle size={15} className="flex-shrink-0 mt-0.5" />
        : <CheckCircle size={15} className="flex-shrink-0 mt-0.5" />}
      <span>{msg}</span>
    </div>
  );
}

/* ─────────────────────────────────────────────────────
   SPELLGATE LOGO COMPONENT
   Unified retro arcade/gateway branding.
───────────────────────────────────────────────────── */
function SpellGateLogo({ size = 24, withHex = true }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 48 48" 
      width={size} 
      height={size} 
      fill="none"
    >
      {withHex && (
        <path 
          d="M 24 3 L 43 14 L 43 34 L 24 45 L 5 34 L 5 14 Z" 
          stroke="var(--neon)" 
          strokeWidth="2.5" 
          strokeLinejoin="round" 
          fill="var(--input-bg)" 
        />
      )}
      
      {/* Lintel (Top Bar) */}
      <path d="M 13 16 L 35 16 L 35 19 L 34 19 L 34 18 L 14 18 L 14 19 L 13 19 Z" fill="var(--neon)" />
      {/* Left Pillar */}
      <rect x="16" y="18" width="3" height="15" fill="var(--neon)" />
      <rect x="14" y="33" width="7" height="2" fill="var(--neon)" />
      {/* Right Pillar */}
      <rect x="29" y="18" width="3" height="15" fill="var(--neon)" />
      <rect x="27" y="33" width="7" height="2" fill="var(--neon)" />
      {/* Hanging Sign */}
      <rect x="20" y="19" width="8" height="9" fill="var(--surface)" stroke="var(--neon)" strokeWidth="1.5" rx="1" />
      {/* Inner Key/Core */}
      <rect x="23" y="22" width="2" height="4" fill="var(--crimson)" rx="0.5" />
    </svg>
  );
}

/* ─────────────────────────────────────────────────────
   LEGAL MODAL COMPONENT
   Written to be warm, clear, and human-centered.
───────────────────────────────────────────────────── */
function LegalModal({ isOpen, onClose, title, children }) {
  React.useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="relative w-full max-w-lg bg-cyber-dark border border-white/10 rounded-2xl shadow-2xl p-6 md:p-8 flex flex-col max-h-[85vh] animate-slide-up"
        style={{
          background: 'var(--surface)',
          borderColor: 'var(--border-hi)',
          color: 'var(--text-primary)'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/5 pb-4">
          <h3 className="text-lg font-bold tracking-tight font-display text-brand" style={{
            background: 'linear-gradient(135deg, var(--neon) 20%, #80f0ff 80%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            {title}
          </h3>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary transition-colors cursor-pointer p-1"
            aria-label="Close dialog"
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Scrollable Body */}
        <div className="overflow-y-auto mt-4 pr-1 text-sm leading-relaxed text-text-muted space-y-4">
          {children}
        </div>

        {/* Footer */}
        <div className="border-t border-white/5 pt-4 mt-6 flex justify-end">
          <button onClick={onClose} className="btn-primary" style={{ padding: '0.45rem 1.25rem', fontSize: '0.8125rem' }}>
            Got it, thanks
          </button>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────
   MAIN LOGIN COMPONENT
───────────────────────────────────────────────────── */
export default function Login() {
  const { login, register, resendVerification } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode]         = useState('login'); // 'login' | 'register' | 'verify' | 'forgot'
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm]   = useState('');
  const [showPass, setShowPass] = useState(false);
  const [showConf, setShowConf] = useState(false);
  const [agree, setAgree]       = useState(false);
  const [error, setError]       = useState('');
  const [success, setSuccess]   = useState('');
  const [loading, setLoading]   = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);

  const strength = mode === 'register' ? getPasswordStrength(password) : null;
  const passwordsMatch = password === confirm;

  const { user } = useAuth();

  React.useEffect(() => {
    if (user) {
      if (user.emailVerified) {
        navigate('/dashboard');
      } else {
        setMode('verify');
        setEmail(user.email || '');
      }
    }
  }, [user, navigate]);

  /* ── Email / Password submit ─────────────────────── */
  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (mode === 'register') {
      if (!agree) {
        setError('Please accept the Privacy Policy and Terms of Service to continue.');
        return;
      }
      if (password !== confirm) {
        setError('Passwords do not match. Please check and try again.');
        return;
      }
      if (password.length < 6) {
        setError('Password must be at least 6 characters.');
        return;
      }
    }

    setLoading(true);
    try {
      if (mode === 'register') {
        await register(email, password);
        setMode('verify');
        setSuccess('Account created! A verification link has been sent to your email inbox.');
      } else {
        const cred = await login(email, password);
        if (!cred.user.emailVerified) {
          setMode('verify');
          setError('Please verify your email before logging in. Check your inbox.');
        } else {
          navigate('/dashboard');
        }
      }
    } catch (err) {
      setError(friendlyError(err.code));
    } finally {
      setLoading(false);
    }
  }

  /* ── Google Sign-in ──────────────────────────────── */
  const handleGoogleSignIn = useCallback(async () => {
    setError('');
    setGoogleLoading(true);
    try {
      const provider = new GoogleAuthProvider();
      const cred = await signInWithPopup(auth, provider);
      // Ensure Firestore docs exist for Google sign-up (first-time user)
      const settingsRef = doc(db, 'users', cred.user.uid, 'child_data', 'settings');
      const progressRef = doc(db, 'users', cred.user.uid, 'child_data', 'progress');
      await setDoc(settingsRef, {
        reward_multiplier: 10,
        force_unlock: false,
        created_at: serverTimestamp(),
      }, { merge: true });
      await setDoc(progressRef, {
        mastered_words: [],
        current_level: 'Novice I',
        sessions: [],
        created_at: serverTimestamp(),
      }, { merge: true });
      navigate('/dashboard');
    } catch (err) {
      setError(friendlyError(err.code));
    } finally {
      setGoogleLoading(false);
    }
  }, [navigate]);

  /* ── Check verification status ───────────────────── */
  async function handleCheckStatus() {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      if (auth.currentUser) {
        await auth.currentUser.reload();
        if (auth.currentUser.emailVerified) {
          navigate('/dashboard');
        } else {
          setError('Email is still unverified. Please check your inbox and click the verification link.');
        }
      } else {
        setError('No active session found. Please sign in again.');
        setMode('login');
      }
    } catch (err) {
      setError(friendlyError(err.code));
    } finally {
      setLoading(false);
    }
  }

  /* ── Resend verification ─────────────────────────── */
  async function handleResend() {
    setLoading(true);
    setError('');
    try {
      await resendVerification();
      setSuccess('Verification email resent! Check your inbox (and spam folder).');
    } catch {
      setError('Could not resend. Please try logging in first to trigger a new email.');
    } finally {
      setLoading(false);
    }
  }

  /* ── Mode switch helper ──────────────────────────── */
  function switchMode(next) {
    setMode(next);
    setError('');
    setSuccess('');
    setPassword('');
    setConfirm('');
    setAgree(false);
  }

  /* ─────────────────────────────────────────────────
     RENDER: Verify email screen
  ───────────────────────────────────────────────── */
  if (mode === 'verify') {
    return (
      <LoginLayout>
        <div className="text-center animate-slide-up">
          <div
            className="w-16 h-16 mx-auto rounded-full flex items-center justify-center mb-6 animate-pulse-ring"
            style={{ background: 'rgba(0,229,255,0.1)', border: '1px solid rgba(0,229,255,0.25)' }}
          >
            <Mail size={26} style={{ color: 'var(--neon)' }} />
          </div>
          <h2 className="text-xl font-bold mb-2">Check your email</h2>
          <p className="text-sm text-muted mb-1 leading-relaxed">
            We sent a verification link to
          </p>
          <p className="font-semibold text-text mb-6 text-sm">{email}</p>
          <p className="text-xs text-dim mb-6">
            Click the link in the email, then return here to sign in. Don't forget to check your spam folder!
          </p>
          {error   && <Alert type="error"   msg={error} />}
          {success && <Alert type="success" msg={success} />}
          <div className="space-y-3 mt-6">
            <button
              onClick={handleCheckStatus}
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 press-effect animate-pulse-ring"
              aria-busy={loading}
            >
              {loading && <Loader size={14} className="animate-spin" />}
              I Have Verified My Email
            </button>
            <button
              onClick={handleResend}
              disabled={loading}
              className="btn-ghost w-full"
              aria-busy={loading}
            >
              {loading && <Loader size={14} className="animate-spin" />}
              Resend Verification Email
            </button>
            <button
              onClick={() => switchMode('login')}
              className="w-full flex items-center justify-center gap-2 text-sm font-medium py-2"
              style={{ color: 'var(--neon)' }}
            >
              <ArrowLeft size={14} /> Back to Sign In
            </button>
          </div>
        </div>
      </LoginLayout>
    );
  }

  /* ─────────────────────────────────────────────────
     RENDER: Login / Register form
  ───────────────────────────────────────────────── */
  return (
    <>
      <LoginLayout>
      {/* Tab toggle */}
      <div
        className="flex p-1 mb-8 rounded-[10px]"
        style={{ background: 'var(--input-bg)', border: '1px solid var(--border)' }}
        role="tablist"
        aria-label="Authentication mode"
      >
        {[
          { id: 'login',    label: 'Sign In' },
          { id: 'register', label: 'Create Account' },
        ].map(t => (
          <button
            key={t.id}
            role="tab"
            aria-selected={mode === t.id}
            onClick={() => switchMode(t.id)}
            className="flex-1 py-2.5 rounded-[8px] text-sm font-semibold transition-all duration-200 cursor-pointer"
            style={{
              background: mode === t.id ? 'var(--neon)' : 'transparent',
              color:      mode === t.id ? 'var(--ink)' : 'var(--text-muted)',
              boxShadow:  mode === t.id ? '0 0 16px rgba(0,229,255,0.3)' : 'none',
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} noValidate className="space-y-5 animate-slide-up" aria-label={mode === 'login' ? 'Sign in form' : 'Create account form'} autoComplete="off">
        {/* Email */}
        <div className="field-group">
          <label htmlFor="email">Email address</label>
          <div style={{ position: 'relative' }}>
            <Mail
              size={15}
              style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)', pointerEvents: 'none' }}
            />
            <input
              id="email"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              placeholder="parent@example.com"
              autoComplete="off"
              className="input-base"
              style={{ paddingLeft: '2.5rem' }}
              aria-required="true"
            />
          </div>
        </div>

        {/* Password */}
        <div className="field-group">
          <label htmlFor="password">Password</label>
          <div style={{ position: 'relative' }}>
            <Lock
              size={15}
              style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)', pointerEvents: 'none' }}
            />
            <input
              id="password"
              type={showPass ? 'text' : 'password'}
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              placeholder={mode === 'register' ? 'Create a strong password' : '••••••••'}
              autoComplete="new-password"
              className="input-base"
              style={{ paddingLeft: '2.5rem', paddingRight: '2.75rem' }}
              aria-required="true"
              aria-describedby={mode === 'register' ? 'password-strength' : undefined}
            />
            <button
              type="button"
              onClick={() => setShowPass(v => !v)}
              style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              aria-label={showPass ? 'Hide password' : 'Show password'}
            >
              {showPass ? <EyeOff size={15} /> : <Eye size={15} />}
            </button>
          </div>
          {/* Password strength bar — only on register */}
          {mode === 'register' && password && (
            <div id="password-strength" style={{ marginTop: '0.5rem' }}>
              <div style={{ display: 'flex', gap: '4px', marginBottom: '0.25rem' }}>
                {[1, 2, 3, 4].map(i => (
                  <div
                    key={i}
                    className="strength-bar flex-1"
                    style={{
                      background: i <= strength.score ? strength.color : 'rgba(255,255,255,0.08)',
                    }}
                  />
                ))}
              </div>
              <p style={{ fontSize: '0.75rem', color: strength.color, fontWeight: 500 }}>
                {strength.label}
                {strength.label === 'Weak' && ' — Try adding numbers or symbols'}
              </p>
            </div>
          )}
        </div>

        {/* Confirm password — register only */}
        {mode === 'register' && (
          <div className="field-group animate-slide-up">
            <label htmlFor="confirm">Confirm password</label>
            <div style={{ position: 'relative' }}>
              <Lock
                size={15}
                style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)', pointerEvents: 'none' }}
              />
              <input
                id="confirm"
                type={showConf ? 'text' : 'password'}
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                required
                placeholder="Repeat your password"
                autoComplete="new-password"
                className="input-base"
                style={{
                  paddingLeft: '2.5rem',
                  paddingRight: '2.75rem',
                  borderColor: confirm && !passwordsMatch ? 'var(--crimson)' : undefined,
                }}
                aria-required="true"
                aria-invalid={confirm ? !passwordsMatch : undefined}
              />
              <button
                type="button"
                onClick={() => setShowConf(v => !v)}
                style={{ position: 'absolute', right: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                aria-label={showConf ? 'Hide password' : 'Show password'}
              >
                {showConf ? <EyeOff size={15} /> : <Eye size={15} />}
              </button>
            </div>
            {confirm && !passwordsMatch && (
              <p style={{ fontSize: '0.75rem', color: 'var(--crimson)', marginTop: '0.25rem' }}>
                Passwords do not match
              </p>
            )}
          </div>
        )}

        {/* Forgot password link — login only */}
        {mode === 'login' && (
          <div style={{ textAlign: 'right', marginTop: '-0.75rem' }}>
            <button
              type="button"
              className="policy-link text-xs font-medium"
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
              onClick={() => setMode('forgot')}
            >
              Forgot password?
            </button>
          </div>
        )}

        {/* Privacy policy checkbox — register only */}
        {mode === 'register' && (
          <label
            className="flex items-start gap-3 cursor-pointer group animate-slide-up"
            style={{ marginTop: '0.25rem' }}
          >
            <div
              onClick={() => setAgree(v => !v)}
              style={{
                width: '18px',
                height: '18px',
                border: `2px solid ${agree ? 'var(--neon)' : 'var(--border-hi)'}`,
                borderRadius: '4px',
                background: agree ? 'var(--neon)' : 'transparent',
                flexShrink: 0,
                marginTop: '2px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all var(--transition)',
                cursor: 'pointer',
              }}
            >
              {agree && <CheckCircle size={11} style={{ color: 'var(--ink)' }} />}
            </div>
            <span className="text-xs text-muted leading-relaxed">
              I agree to the{' '}
              <button type="button" className="policy-link" style={{ background: 'none', border: 'none', padding: 0, font: 'inherit', color: 'var(--neon)', cursor: 'pointer', borderBottom: '1px solid transparent' }} onClick={e => { e.stopPropagation(); setShowPrivacyModal(true); }}>Privacy Policy</button>
              {' '}and{' '}
              <button type="button" className="policy-link" style={{ background: 'none', border: 'none', padding: 0, font: 'inherit', color: 'var(--neon)', cursor: 'pointer', borderBottom: '1px solid transparent' }} onClick={e => { e.stopPropagation(); setShowTermsModal(true); }}>Terms of Service</button>.
              SpellGate never sells or shares your data.
            </span>
          </label>
        )}

        {/* Alerts */}
        {error   && <Alert type="error"   msg={error} />}
        {success && <Alert type="success" msg={success} />}

        {/* Submit */}
        <button
          type="submit"
          disabled={loading || (mode === 'register' && (!agree || !passwordsMatch || !password))}
          className="btn-primary w-full press-effect"
          aria-busy={loading}
        >
          {loading && <Loader size={15} className="animate-spin" />}
          {mode === 'login' ? 'Sign In to Dashboard' : 'Create Account & Verify Email'}
        </button>
      </form>

      {/* Divider */}
      <div className="divider-text my-5 animate-slide-up stagger-3">or continue with</div>

      {/* Social auth — Google */}
      <div className="space-y-2.5 animate-slide-up stagger-4">
        <button
          onClick={handleGoogleSignIn}
          disabled={googleLoading}
          className="btn-social press-effect"
          aria-busy={googleLoading}
          aria-label="Sign in with Google"
        >
          {googleLoading
            ? <Loader size={16} className="animate-spin" />
            : (
              <svg width="17" height="17" viewBox="0 0 24 24" aria-hidden="true">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
            )
          }
          <span>{googleLoading ? 'Connecting…' : 'Continue with Google'}</span>
        </button>
      </div>

      {/* Security note */}
      <p className="flex items-center justify-center gap-1.5 text-xs mt-6 animate-slide-up stagger-5" style={{ color: 'var(--text-dim)' }}>
        <Shield size={11} />
        Secured by Firebase Authentication · Email verification required
      </p>

    </LoginLayout>

    {/* Overlays rendered outside to escape the card backdrop-filter block */}
    {mode === 'forgot' && <ForgotPasswordOverlay onBack={() => switchMode('login')} />}

    {/* Inline Legal Modals */}
    <LegalModal isOpen={showPrivacyModal} onClose={() => setShowPrivacyModal(false)} title="Privacy Policy">
      <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Our Privacy Promise</p>
      <p>
        We built SpellGate because we believe technology should help kids learn, not track them.
        We do not sell, rent, share, or monetize your or your child's data. Ever.
      </p>
      <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '1rem' }}>What We Collect & Sync</p>
      <ul style={{ listStyle: 'disc', paddingLeft: '1.25rem', spaceY: '0.25rem' }}>
        <li>
          <strong>Spelling Progress</strong>: We log the words your child spells correctly, their accuracy rates,
          and session durations. This is sent to your private database so you can monitor them here.
        </li>
        <li>
          <strong>Time Bank State</strong>: We sync the amount of unlocked screen time they have earned so the child client knows when to lock again.
        </li>
      </ul>
      <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '1rem' }}>What Stays 100% Local</p>
      <p>
        To prevent bypassing the lock screen, the Windows app monitors keyboard shortcuts (like Alt+Tab and Task Manager keys)
        only when locking is active. This monitoring happens entirely on your child's PC. No keys are ever recorded, saved, or transmitted.
      </p>
      <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '1rem' }}>Self-Hosted Data Ownership</p>
      <p>
        All synchronized data is stored directly in your own Firebase project. Only you—authenticated with your verified parent credentials—have permissions to access or edit this data.
      </p>
    </LegalModal>

    <LegalModal isOpen={showTermsModal} onClose={() => setShowTermsModal(false)} title="Terms of Service">
      <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Welcome to SpellGate</p>
      <p>
        By using SpellGate, you agree to these simple terms. We keep them short and clear because we respect your time.
      </p>
      <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '1rem' }}>1. Parental Supervision</p>
      <p>
        SpellGate is a parental assistance tool. You determine the curriculum, set the play multipliers, and control the override passcodes.
        It is your responsibility to monitor your child's use.
      </p>
      <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '1rem' }}>2. OS-Level Device Controls</p>
      <p>
        The desktop app requires system-level permissions to hook keyboard shortcuts (Alt+Tab, Win keys) and manage Windows session state.
        By installing, you authorize the app to lock the screen and restrict access based on active spelling tasks.
      </p>
      <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '1rem' }}>3. Emergency Overrides</p>
      <p>
        We include a fail-safe parent passcode override shortcut (default: <kbd style={{ background: 'var(--input-bg)', padding: '2px 6px', borderRadius: 4, border: '1px solid var(--border-hi)' }}>Ctrl+Shift+P</kbd>).
        You agree to keep this passcode secure from your child.
      </p>
      <p style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '1rem' }}>4. Free, Clean, Open Source</p>
      <p>
        SpellGate is open-source under the GPLv3 license. It contains zero ads, zero tracking scripts, and zero subscription fees.
        You are free to compile the source code yourself.
      </p>
    </LegalModal>
    </>
  );
}

/* ─────────────────────────────────────────────────────
   LAYOUT WRAPPER
───────────────────────────────────────────────────── */
function LoginLayout({ children }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <div
      className="min-h-screen flex relative overflow-hidden login-page-root"
      style={{ background: theme === 'light' ? 'var(--surface-base)' : 'var(--ink)' }}
    >
      {/* Visual Rhyming: Dotted pattern mesh background */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-[0.02] z-0" 
        style={{ backgroundImage: theme === 'light' ? 'radial-gradient(rgba(16,19,26,0.3) 1px, transparent 1px)' : 'radial-gradient(rgba(255,255,255,0.7) 1px, transparent 1px)', backgroundSize: '24px 24px' }}
        aria-hidden="true" 
      />

      {/* Theme Toggle Button (Sticky Top Right) */}
      <button
        onClick={toggleTheme}
        className="absolute top-6 right-6 w-10 h-10 rounded-full flex items-center justify-center transition-colors hover:bg-white/10 z-50 login-theme-toggle cursor-pointer"
        style={{
          background: theme === 'light' ? 'rgba(16,19,26,0.06)' : 'rgba(255,255,255,0.06)',
          color: theme === 'light' ? 'var(--text-primary)' : 'var(--text-muted)',
          border: theme === 'light' ? '1px solid var(--border-hairline)' : 'none'
        }}
        aria-label="Toggle theme"
      >
        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
      </button>

      {/* Left Pane: Branding & Features (Visible only on md: and larger) */}
      <div 
        className="hidden md:flex md:w-[42%] border-r flex-col justify-between p-12 relative z-10 select-none login-left-pane"
        style={{
          background: theme === 'light' ? 'var(--surface-card-alt)' : '#090b11',
          borderColor: theme === 'light' ? 'var(--border-hairline)' : 'rgba(255,255,255,0.05)'
        }}
      >
        <div className="absolute inset-0 bg-gradient-to-tr from-cyber-purple/5 via-transparent to-transparent pointer-events-none" />
        
        {/* Brand Header */}
        <Link to="/" className="inline-flex items-center gap-2.5 group" aria-label="Back to SpellGate home">
          <SpellGateLogo size={36} />
          <span
            className="font-display text-base font-bold tracking-[0.18em] uppercase text-neon"
          >
            SpellGate
          </span>
        </Link>

        {/* Feature Highlights */}
        <div className="my-auto space-y-8 max-w-sm text-left">
          <h2 className="text-2xl font-bold tracking-tight text-white font-display leading-tight">
            OS-Level Spelling Security for Young Learners
          </h2>
          <p className="text-white/70 text-xs leading-relaxed opacity-85">
            Monitor, calibrate, and override computer access permissions. SpellGate forces active spelling study directly through a locked arcade interface.
          </p>

          <div className="space-y-5">
            {[
              { icon: <Lock size={15} className="text-neon" />, title: 'Kiosk Security Locking', desc: 'Prevents children from bypassing screen time rules.' },
              { icon: <Shield size={15} className="text-cyber-purple" />, title: 'Real-Time Sync Diagnostics', desc: 'Observe active learning progress from any remote browser.' },
              { icon: <CheckCircle size={15} className="text-mint" />, title: 'Curriculum-Aligned AI Tiering', desc: 'Spelling tests dynamically adjust difficulty based on performance.' }
            ].map((f, i) => (
              <div key={i} className="flex gap-3.5 items-start">
                <div className="w-7 h-7 rounded-lg bg-white/5 flex items-center justify-center border border-white/10 flex-shrink-0 mt-0.5">
                  {f.icon}
                </div>
                <div>
                  <h4 className="text-xs font-bold text-white tracking-wide">{f.title}</h4>
                  <p className="text-[0.6875rem] text-white/60 mt-0.5 leading-relaxed opacity-80">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Meta */}
        <div className="text-[0.6875rem] text-white/40 font-medium tracking-wide text-left">
          © {new Date().getFullYear()} SpellGate Security System. Open source GPLv3.
        </div>
      </div>

      {/* Right Pane: Sign In Form Wrapper */}
      <div 
        className="flex-1 flex flex-col items-center justify-center p-6 md:p-12 relative z-10 login-right-pane"
        style={{
          background: theme === 'light' 
            ? 'var(--surface-base)' 
            : 'radial-gradient(circle at 80% 20%, rgba(74, 222, 128, 0.05) 0%, transparent 50%), radial-gradient(circle at 20% 80%, rgba(147, 51, 234, 0.05) 0%, transparent 50%), #0D111A'
        }}
      >
        <div className="absolute inset-0 pointer-events-none z-0">
          <div style={{
            position: 'absolute', top: '10%', right: '10%',
            width: '40vw', height: '40vw', maxWidth: '500px',
            background: theme === 'light' ? 'radial-gradient(circle, rgba(78,158,31,0.06) 0%, transparent 65%)' : 'radial-gradient(circle, rgba(74,222,128,0.04) 0%, transparent 65%)',
            borderRadius: '50%',
          }} />
        </div>

        <div className="relative z-10 w-full max-w-[390px] flex flex-col gap-6">
          {/* Logo (Visible only on mobile screen widths) */}
          <div className="text-center md:hidden mb-2">
            <Link to="/" className="inline-flex items-center gap-2 mb-3" aria-label="Back to home">
              <SpellGateLogo size={32} />
              <span className="font-display font-bold tracking-wider text-neon uppercase text-sm">SpellGate</span>
            </Link>
            <p className="text-xs font-semibold text-text-muted uppercase tracking-wider opacity-60">Parent Portal</p>
          </div>

          {/* Form Card */}
          <div
            className="glass-hi rounded-2xl p-6 md:p-8 login-form-card"
            style={{
              boxShadow: theme === 'light' 
                ? 'var(--shadow-lg)' 
                : '0 24px 64px -16px rgba(0,0,0,0.7), 0 0 24px rgba(74,222,128,0.08)',
              background: theme === 'light' ? '#FFFFFF' : 'rgba(18, 24, 40, 0.92)',
              borderColor: theme === 'light' ? 'var(--border-hairline)' : 'rgba(74, 222, 128, 0.25)'
            }}
          >
            {children}
          </div>

          <p className="text-center text-[0.6875rem] text-text-dim">
            Parent verification portal · Secured by SSL and Firebase Guard
          </p>
        </div>
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────
   FORGOT PASSWORD OVERLAY
───────────────────────────────────────────────────── */
function ForgotPasswordOverlay({ onBack }) {
  const [email, setEmail]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [sent, setSent]         = useState(false);
  const [error, setError]       = useState('');

  async function handleReset(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const { sendPasswordResetEmail } = await import('firebase/auth');
      await sendPasswordResetEmail(auth, email);
      setSent(true);
    } catch (err) {
      setError(friendlyError(err.code));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center px-4"
      style={{ background: 'rgba(8,9,13,0.85)', backdropFilter: 'blur(12px)' }}
      role="dialog"
      aria-modal="true"
      aria-label="Password reset"
    >
      <div className="glass-hi rounded-[20px] p-8 w-full max-w-[400px] animate-slide-up" style={{ boxShadow: '0 32px 80px -16px rgba(0,0,0,0.6)' }}>
        {sent ? (
          <div className="text-center">
            <div className="w-14 h-14 mx-auto rounded-full flex items-center justify-center mb-5 animate-pulse-ring" style={{ background: 'rgba(61,255,160,0.1)', border: '1px solid rgba(61,255,160,0.25)' }}>
              <CheckCircle size={24} style={{ color: 'var(--mint)' }} />
            </div>
            <h3 className="text-lg font-bold mb-2">Check your inbox</h3>
            <p className="text-sm text-muted mb-6 leading-relaxed">A reset link was sent to <strong className="text-text">{email}</strong>. It expires in 1 hour.</p>
            <button onClick={onBack} className="btn-ghost w-full"><ArrowLeft size={15} /> Back to Sign In</button>
          </div>
        ) : (
          <>
            <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-muted hover:text-text transition-colors mb-6 cursor-pointer" style={{ background: 'none', border: 'none' }}>
              <ArrowLeft size={14} /> Back
            </button>
            <h3 className="text-lg font-bold mb-1">Reset your password</h3>
            <p className="text-sm text-muted mb-6">Enter your email and we'll send you a reset link.</p>
            <form onSubmit={handleReset} className="space-y-4">
              <div className="field-group">
                <label htmlFor="reset-email">Email address</label>
                <div style={{ position: 'relative' }}>
                  <Mail size={15} style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)', pointerEvents: 'none' }} />
                  <input
                    id="reset-email"
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                    placeholder="yourname@email.com"
                    autoComplete="email"
                    className="input-base"
                    style={{ paddingLeft: '2.5rem' }}
                  />
                </div>
              </div>
              {error && <Alert type="error" msg={error} />}
              <button type="submit" disabled={loading} className="btn-primary w-full press-effect">
                {loading && <Loader size={14} className="animate-spin" />}
                Send Reset Link
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
