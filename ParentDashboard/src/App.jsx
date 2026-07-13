import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Download, Rocket, Shield, Star, Zap, RefreshCw,
  ArrowRight, Check, ChevronDown, Menu, X, Lock, Brain, Award,
  Activity, Sun, Moon, Users, Terminal, CheckCircle2
} from 'lucide-react';
import { useTheme } from './ThemeContext';
import { useAuth } from './AuthContext';

/* ─────────────────────────────────────────────────────
   CONSTANTS
───────────────────────────────────────────────────── */
const GITHUB_RELEASE_URL =
  'https://github.com/Hazy019/SpellGate/releases/latest/download/SpellGateSetup.exe';

const NAV_LINKS = [
  { href: '#features',     label: 'Features' },
  { href: '#how-it-works', label: 'How It Works' },
  { href: '#security',     label: 'Security' },
  { href: '#faq',          label: 'FAQ' },
];

const FEATURES = [
  { icon: <Lock />,       color: '#00e5ff', bg: 'rgba(0,229,255,0.06)',   title: 'Kiosk Lock Mode',       body: 'Locks the child PC at the system level. Blocks Task Manager, Alt+Tab, and escape shortcuts. Screen opens only when spelling.' },
  { icon: <Brain />,      color: '#ffc857', bg: 'rgba(255,200,87,0.06)',  title: 'Adaptive AI Engine',    body: 'Features multiple vocabulary tiers calibrated for Grade 4 learners. Dynamically selects words and operates fully offline.' },
  { icon: <RefreshCw />,  color: '#3dffa0', bg: 'rgba(61,255,160,0.06)',  title: 'Active Repetition',     body: 'Spaced review algorithms automatically retest mastered words over subsequent sessions. Unfinished words return to rotation.' },
  { icon: <Activity />,   color: '#00e5ff', bg: 'rgba(0,229,255,0.06)',   title: 'Live Portal Monitor',   body: 'Track spelling accuracy, view struggle metrics, and check remote system connectivity instantly from any web browser.' },
  { icon: <Zap />,        color: '#ffc857', bg: 'rgba(255,200,87,0.06)',  title: 'Offline Standalone',    body: 'Bakes in a standard dictionary of grade-appropriate words. Continues running securely without requiring active internet.' },
  { icon: <Award />,      color: '#3dffa0', bg: 'rgba(61,255,160,0.06)',  title: 'Earning Records',       body: 'Keeps detailed logs of earned PC usage time, word mastery thresholds, and daily accuracy metrics in real-time.' },
];

const STEPS = [
  { num: '01', title: 'Download & Install',    body: 'Download the launcher and run the installer on your child\'s PC. Complete local setup in 2 minutes.' },
  { num: '02', title: 'Create Portal Profile', body: 'Register your parent account. You will receive an instant verification link to protect your access.' },
  { num: '03', title: 'Log in on the client',  body: 'Start SpellGate on the child\'s PC and authorize using your verified parent portal credentials.' },
  { num: '04', title: 'Start Monitoring!',     body: 'SpellGate automatically runs on startup. Control multipliers and overrides directly from the dashboard.' },
];

const FAQ_ITEMS = [
  { q: 'What OS does SpellGate run on?',            a: 'Windows 10 and Windows 11 are fully supported. The installer configures all startup hooks automatically.' },
  { q: 'Can my child bypass the lock?',             a: 'SpellGate registers deep keyboard hooks to block Alt+Tab, Windows keys, and Task Manager. A parent override passcode (Ctrl+Shift+P) is available for emergencies.' },
  { q: 'Is my child\'s data safe?',                 a: 'All logs and settings are stored in your secure Firebase Firestore instance. Only the authenticated, verified parent account can query the data.' },
  { q: 'Does it work without internet?',            a: 'Yes. SpellGate contains a built-in offline vocabulary bank. AI-driven expansion occurs when online, but security rules and locking are fully operational offline.' },
  { q: 'How do I control earned screen time?',      a: 'In the Parent Portal settings, you set the multiplier (e.g. 10s of playtime per word). If they spell 10 words, they get 100 seconds of unlocked access before the PC automatically locks again.' },
];

/* ─────────────────────────────────────────────────────
   HOOKS
───────────────────────────────────────────────────── */
function useTilt(ref) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) return;
    const onMove = (e) => {
      const r = el.getBoundingClientRect();
      const x = ((e.clientX - r.left) / r.width  - 0.5) * 8;
      const y = ((e.clientY - r.top)  / r.height - 0.5) * -6;
      el.style.transform = `perspective(1000px) rotateX(${y}deg) rotateY(${x}deg) scale(1.01)`;
    };
    const onLeave = () => { el.style.transform = ''; };
    el.addEventListener('mousemove', onMove);
    el.addEventListener('mouseleave', onLeave);
    return () => { el.removeEventListener('mousemove', onMove); el.removeEventListener('mouseleave', onLeave); };
  }, [ref]);
}

/* Parallax scroll hook – returns live scrollY offset */
function useParallax() {
  const [scrollY, setScrollY] = useState(0);
  useEffect(() => {
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced) return;
    let raf;
    const onScroll = () => {
      raf = requestAnimationFrame(() => setScrollY(window.scrollY));
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => { window.removeEventListener('scroll', onScroll); cancelAnimationFrame(raf); };
  }, []);
  return scrollY;
}

function useFadeIn() {
  useEffect(() => {
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const els = document.querySelectorAll('.reveal');
    if (prefersReduced) {
      els.forEach(el => el.classList.add('revealed'));
      return;
    }
    const obs = new IntersectionObserver(
      (entries) => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); obs.unobserve(e.target); } }),
      { threshold: 0.05, rootMargin: '0px 0px -20px 0px' }
    );
    els.forEach(el => obs.observe(el));
    return () => obs.disconnect();
  }, []);
}

/* ─────────────────────────────────────────────────────
   SUB-COMPONENTS
───────────────────────────────────────────────────── */
function FeatureCard({ icon, color, bg, title, body, delay = 0 }) {
  return (
    <div 
      className="reveal glass hover-neon rounded-[20px] p-6 group cursor-default"
      style={{ 
        animationDelay: `${delay}ms`, 
        borderColor: color + '22',
        transition: 'border-color 0.3s, box-shadow 0.3s, transform 0.4s cubic-bezier(0.34,1.56,0.64,1)',
        display: 'flex',
        flexDirection: 'column',
        height: '100%'
      }}
    >
      <div 
        className="w-10 h-10 rounded-xl flex items-center justify-center mb-5"
        style={{ 
          background: bg, color,
          transition: 'transform 0.4s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.3s'
        }}
        onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.18) rotate(-4deg)'; e.currentTarget.style.boxShadow = `0 0 20px ${color}44`; }}
        onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1) rotate(0deg)'; e.currentTarget.style.boxShadow = 'none'; }}
      >
        {React.cloneElement(icon, { size: 20 })}
      </div>
      <h3 className="text-sm font-bold mb-2 tracking-tight" style={{ color: 'var(--text-primary)' }}>{title}</h3>
      <p className="text-xs leading-relaxed" style={{ color: 'var(--text-muted)', flexGrow: 1 }}>{body}</p>
    </div>
  );
}

function FaqItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="glass rounded-[12px] overflow-hidden border border-white/5" style={{ transition: 'box-shadow 0.2s' }}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-6 py-4.5 text-left gap-4 cursor-pointer"
        style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)' }}
        aria-expanded={open}
      >
        <span className="text-sm font-semibold">{q}</span>
        <ChevronDown
          size={16}
          style={{
            color: 'var(--text-muted)',
            flexShrink: 0,
            transform: open ? 'rotate(180deg)' : 'none',
            transition: 'transform 0.3s ease'
          }}
        />
      </button>
      <div style={{
        maxHeight: open ? '300px' : '0',
        opacity: open ? 1 : 0,
        overflow: 'hidden',
        transition: 'max-height 0.38s cubic-bezier(0.4,0,0.2,1), opacity 0.28s ease',
        paddingLeft: '1.5rem', paddingRight: '1.5rem',
        paddingBottom: open ? '1.25rem' : '0',
      }}>
        <p className="text-xs leading-relaxed text-text-muted">{a}</p>
      </div>
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
  useEffect(() => {
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
          <h3 className="text-lg font-bold tracking-tight font-display text-brand">
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
   MAIN APP
───────────────────────────────────────────────────── */
const App = () => {
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [downloading, setDownloading]       = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled]             = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [terminalLogs, setTerminalLogs]     = useState([
    '[INIT] System monitor listening on child PC...',
    '[INFO] Host name detected: CHILD-PC',
    '[OK] Connection status: LIVE_SYNC'
  ]);
  const heroRef = useRef(null);
  const scrollY = useParallax();

  useTilt(heroRef);
  useFadeIn();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Simulates real-time logs in the "Star of the Show" hero terminal mockup
  useEffect(() => {
    const events = [
      'Heartbeat packet received from CHILD-PC',
      'Child started spelling session [Level: Intermediate]',
      'Spelled correct: "OPINION" [+10s playtime]',
      'Spelled correct: "SCRAMBLE" [+10s playtime]',
      'Heartbeat ping check: [Latency: 48ms]',
      'Time allowance exhausted: PC Locked successfully',
      'Spelled correct: "GLOBE" [+10s playtime]'
    ];
    let i = 0;
    const interval = setInterval(() => {
      const timestamp = new Date().toLocaleTimeString();
      setTerminalLogs(prev => [
        ...prev.slice(-4),
        `[${timestamp}] ${events[i % events.length]}`
      ]);
      i++;
    }, 4500);
    return () => clearInterval(interval);
  }, []);

  const handleDownload = () => {
    if (!user) {
      navigate('/login');
      return;
    }
    setDownloading(true);
    const a = document.createElement('a');
    a.href = GITHUB_RELEASE_URL;
    a.download = 'SpellGate.exe';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => setDownloading(false), 3000);
  };

  const bg    = 'var(--ink)';
  const brd   = 'var(--border)';
  const neon  = 'var(--neon)';
  const txt   = 'var(--text-primary)';
  const muted = 'var(--text-muted)';
  const dim   = 'var(--text-dim)';

  return (
    <div style={{ minHeight: '100vh', background: bg, color: txt, overflowX: 'hidden', fontFamily: 'var(--font-body)' }}>

      {/* Visual Rhyming: Dotted pattern mesh fixed background – parallax deep layer */}
      <div 
        style={{ 
          position: 'fixed', 
          inset: 0, 
          pointerEvents: 'none', 
          zIndex: 0, 
          opacity: 0.025, 
          backgroundImage: 'radial-gradient(rgba(255,255,255,0.7) 1px, transparent 1px)', 
          backgroundSize: '32px 32px',
          transform: `translateY(${scrollY * 0.12}px)`,
        }}
        aria-hidden="true" 
      />

      {/* Atmospheric accent ambient orbs – parallax mid layer */}
      <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 0 }} aria-hidden="true">
        <div style={{ 
          position: 'absolute', top: '-15%', left: '-10%', 
          width: '60vw', height: '60vw', maxWidth: '750px', 
          background: 'radial-gradient(circle, rgba(0,229,255,0.06) 0%, transparent 68%)', 
          borderRadius: '50%',
          transform: `translateY(${scrollY * 0.18}px)`,
          transition: 'transform 0.1s linear',
        }} />
        <div style={{ 
          position: 'absolute', bottom: '10%', right: '-10%', 
          width: '50vw', height: '50vw', maxWidth: '650px', 
          background: 'radial-gradient(circle, rgba(139,92,246,0.04) 0%, transparent 68%)', 
          borderRadius: '50%',
          transform: `translateY(${scrollY * -0.08}px)`,
          transition: 'transform 0.1s linear',
        }} />
      </div>

      {/* ── NAVBAR ────────────────────────────────────────── */}
      <header style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
        background: scrolled ? (theme === 'dark' ? 'rgba(8,9,13,0.85)' : 'rgba(244,246,250,0.85)') : 'transparent',
        borderBottom: scrolled ? `1px solid ${brd}` : '1px solid transparent',
        backdropFilter: scrolled ? 'blur(20px)' : 'none',
        transition: 'background 0.3s, border-color 0.3s',
      }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '1rem 1.5rem', display: 'flex', alignItems: 'center', justifyBetween: 'space-between' }}>
          {/* Logo */}
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', textDecoration: 'none' }} aria-label="SpellGate Home">
            <SpellGateLogo size={34} />
            <span style={{ fontFamily: 'var(--font-display)', fontSize: '1rem', fontWeight: 850, letterSpacing: '0.2em', textTransform: 'uppercase', color: neon }}>SpellGate</span>
          </Link>

          {/* Desktop Nav with micro-interaction underline */}
          <nav className="hidden md:flex" style={{ gap: '2rem', alignItems: 'center', marginLeft: 'auto', marginRight: '2.5rem' }}>
            {NAV_LINKS.map(l => (
              <a 
                key={l.href} href={l.href} 
                className="nav-link-item"
                style={{ 
                  color: muted, fontSize: '0.8125rem', fontWeight: 600, 
                  textDecoration: 'none', letterSpacing: '0.02em',
                  position: 'relative', paddingBottom: '2px',
                  transition: 'color 0.2s',
                }}
                onMouseEnter={e => e.currentTarget.style.color = txt}
                onMouseLeave={e => e.currentTarget.style.color = muted}
              >
                {l.label}
                <span style={{
                  position: 'absolute', bottom: -2, left: 0, right: 0,
                  height: '1.5px', background: 'var(--neon)',
                  transform: 'scaleX(0)', transformOrigin: 'left',
                  transition: 'transform 0.28s cubic-bezier(0.4,0,0.2,1)',
                }}
                  className="nav-underline"
                />
              </a>
            ))}
          </nav>

          {/* Desktop CTA */}
          <div className="hidden md:flex" style={{ gap: '0.75rem', alignItems: 'center' }}>
            <button onClick={toggleTheme} className="press-effect" aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              style={{ width: 34, height: 34, borderRadius: '50%', border: `1px solid ${brd}`, background: 'transparent', color: muted, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'border-color 0.2s, color 0.2s' }}>
              {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
            </button>
            <Link to={user ? "/dashboard" : "/login"} className="btn-ghost" style={{ fontSize: '0.75rem', padding: '0.45rem 1rem' }}>{user ? "Dashboard" : "Parent Login"}</Link>
            <button onClick={handleDownload} disabled={downloading} className="btn-primary press-effect" style={{ fontSize: '0.75rem', padding: '0.45rem 1rem' }}>
              {downloading ? <><RefreshCw size={12} className="animate-spin" /> Fetching…</> : <><Download size={12} /> Get App</>}
            </button>
          </div>

          {/* Mobile Hamburger */}
          <button className="md:hidden press-effect" onClick={() => setMobileMenuOpen(o => !o)} aria-label="Toggle menu"
            style={{ background: 'transparent', border: 'none', color: muted, cursor: 'pointer', marginLeft: 'auto' }}>
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>

        {/* Mobile Drawer */}
        <div style={{
          maxHeight: mobileMenuOpen ? '380px' : '0',
          overflow: 'hidden',
          transition: 'max-height 0.35s cubic-bezier(0.4,0,0.2,1)',
          background: theme === 'dark' ? 'rgba(8,9,13,0.96)' : 'rgba(244,246,250,0.96)',
          borderBottom: mobileMenuOpen ? `1px solid ${brd}` : 'none',
          backdropFilter: 'blur(20px)',
        }}>
          <nav style={{ padding: '0.5rem 1.5rem 1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {NAV_LINKS.map(l => (
              <a key={l.href} href={l.href} onClick={() => setMobileMenuOpen(false)}
                style={{ color: muted, fontSize: '0.875rem', fontWeight: 600, textDecoration: 'none' }}>{l.label}</a>
            ))}
            <hr style={{ border: 'none', borderTop: `1px solid ${brd}` }} />
            <button onClick={toggleTheme} style={{ background: 'none', border: 'none', color: muted, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8125rem', fontWeight: 600, textAlign: 'left', padding: 0 }}>
              {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
              {theme === 'dark' ? 'Switch to Light' : 'Switch to Dark'}
            </button>
            <Link to={user ? "/dashboard" : "/login"} onClick={() => setMobileMenuOpen(false)} style={{ color: muted, fontSize: '0.875rem', fontWeight: 600, textDecoration: 'none' }}>{user ? "Dashboard" : "Parent Login"}</Link>
            <button onClick={handleDownload} className="btn-primary w-full"><Download size={14} /> Download Launcher</button>
          </nav>
        </div>
      </header>

      {/* ── HERO ──────────────────────────────────────────── */}
      <section style={{ position: 'relative', zIndex: 10, minHeight: '100vh', display: 'flex', alignItems: 'center', justifyCenter: 'center', padding: '7.5rem 1.5rem 4.5rem', textAlign: 'center' }}>
        <div style={{ maxWidth: '960px', margin: '0 auto', width: '100%' }}>
          
          <div className="reveal badge badge-neon animate-slide-up" style={{ marginBottom: '1.75rem', display: 'inline-flex' }}>
            <Star size={11} className="text-neon" /> Interactive Spelling & Control Platform
          </div>

          {/* Scroll-triggered hero headline with stagger */}
          <h1 
            className="reveal animate-slide-up stagger-1 font-display" 
            style={{ 
              fontSize: 'clamp(2.25rem, 7.5vw, 4.5rem)', fontWeight: 900, 
              lineHeight: 1.08, letterSpacing: '-0.025em', 
              margin: '0 0 1.25rem', color: txt,
              transform: `translateY(${scrollY * -0.04}px)`,
            }}
          >
            Exchange screen time for
            <br />
            <span className="text-shimmer">spelling mastery.</span>
          </h1>

          <p 
            className="reveal animate-slide-up stagger-2 text-text-muted" 
            style={{ 
              fontSize: 'clamp(0.9375rem, 2.2vw, 1.125rem)', maxWidth: '580px', 
              margin: '0 auto 2.5rem', lineHeight: 1.65, opacity: 0.9,
              transform: `translateY(${scrollY * -0.025}px)`,
            }}
          >
            SpellGate secures Windows under an interactive kiosk game. Children unlock access to the system by completing curriculum-aligned spelling tasks.
          </p>

          <div className="reveal animate-slide-up stagger-3" style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center', justifyContent: 'center' }}>
            <button onClick={handleDownload} disabled={downloading} className="btn-primary press-effect" style={{ fontSize: '0.875rem', padding: '0.8rem 1.85rem' }}>
              {downloading ? <><RefreshCw size={16} className="animate-spin" /> Preparing Client…</> : <><Download size={16} /> Get SpellGate Launcher</>}
            </button>
            <Link to={user ? "/dashboard" : "/login"} className="btn-ghost press-effect" style={{ fontSize: '0.875rem', padding: '0.8rem 1.85rem' }}>
              {user ? "Go to Dashboard" : "Access Parent Portal"} <ArrowRight size={15} />
            </Link>
          </div>
          <p className="reveal animate-slide-up stagger-4 text-text-dim" style={{ fontSize: '0.6875rem', marginTop: '1rem', letterSpacing: '0.02em', fontWeight: 500 }}>Windows 10 / 11 · Zero Configuration Needed · 100% Free</p>

          {/* Star of the Show / Mock Browser Mockup (Scroll Stopping & Depth) */}
          <div ref={heroRef} className="reveal animate-slide-up stagger-5" style={{ marginTop: '4.5rem', transition: 'transform 0.25s ease' }}>
            <div style={{ 
              maxWidth: '820px', 
              margin: '0 auto', 
              borderRadius: 16, 
              overflow: 'hidden', 
              background: 'rgba(13,15,23,0.75)', 
              border: '1px solid rgba(255,255,255,0.06)', 
              boxShadow: '0 32px 80px -16px rgba(0,229,255,0.08), inset 0 1px 0 rgba(255,255,255,0.05)',
              position: 'relative'
            }}>
              
              {/* Depth: Floating Live Sync status badge overlapping screen */}
              <div 
                className="absolute top-18 right-6 z-20 inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[0.6875rem] font-bold tracking-wider uppercase bg-mint/15 text-mint border border-mint/20 animate-pulse"
                style={{ boxShadow: '0 4px 16px rgba(61,255,160,0.15)' }}
              >
                <CheckCircle2 size={12} /> Live Link Active
              </div>

              {/* Browser window topbar */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '12px 18px', borderBottom: `1px solid ${brd}`, background: 'rgba(255,255,255,0.01)' }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: 'rgba(255,95,87,0.5)', display: 'inline-block' }} />
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: 'rgba(254,188,46,0.5)', display: 'inline-block' }} />
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: 'rgba(40,200,64,0.5)', display: 'inline-block' }} />
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.625rem', color: 'rgba(255,255,255,0.4)', flex: 1, textAlign: 'center', letterSpacing: '0.04em' }}>spellgate-console · parent-portal-sync</span>
                <Lock size={11} style={{ color: '#3dffa0' }} />
              </div>

              {/* Grid Content inside Mock Window */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 p-5" style={{ minHeight: '260px' }}>
                
                {/* Simulated Stats Left Column (3/5 width) */}
                <div className="md:col-span-3 flex flex-col gap-4">
                  {/* Glass Stats group */}
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { label: 'Sync Status', val: 'ONLINE', clr: '#00e5ff', bg: 'rgba(0,229,255,0.05)' },
                      { label: 'Words Mastery', val: '142', clr: '#ffc857', bg: 'rgba(255,200,87,0.05)' },
                      { label: 'Time Bank', val: '12m 40s', clr: '#3dffa0', bg: 'rgba(61,255,160,0.05)' }
                    ].map(card => (
                      <div key={card.label} className="rounded-lg p-3 text-left border border-white/5" style={{ background: card.bg, borderColor: card.clr + '15' }}>
                        <span style={{ fontSize: '0.625rem', fontWeight: 600, color: 'rgba(255,255,255,0.45)', display: 'block', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{card.label}</span>
                        <span style={{ fontSize: '0.9375rem', fontWeight: 800, color: card.clr, fontFamily: 'var(--font-mono)' }}>{card.val}</span>
                      </div>
                    ))}
                  </div>

                  {/* Gorgeous visual SVG progress chart */}
                  <div className="rounded-lg p-4 flex-1 border border-white/5 bg-ink/30 flex flex-col justify-between" style={{ background: 'rgba(0,0,0,0.2)' }}>
                    <span className="text-[0.625rem] font-bold text-left uppercase tracking-wider" style={{ color: 'rgba(255,255,255,0.45)' }}>Mastery Velocity</span>
                    <div style={{ height: '110px', width: '100%', position: 'relative', marginTop: 10 }}>
                      <svg viewBox="0 0 100 35" width="100%" height="100%" preserveAspectRatio="none">
                        <defs>
                          <linearGradient id="chart-glow" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="var(--neon)" stopOpacity="0.15" />
                            <stop offset="100%" stopColor="var(--neon)" stopOpacity="0.0" />
                          </linearGradient>
                        </defs>
                        <path d="M 0 35 Q 15 25, 30 28 T 60 12 T 90 4 T 100 2 L 100 35 Z" fill="url(#chart-glow)" />
                        <path d="M 0 35 Q 15 25, 30 28 T 60 12 T 90 4 T 100 2" fill="none" stroke="var(--neon)" strokeWidth="1.2" />
                        <circle cx="90" cy="4" r="1.5" fill="var(--neon)" className="animate-pulse" />
                      </svg>
                    </div>
                  </div>
                </div>

                {/* Simulated Live Terminal Right Column (2/5 width) */}
                <div className="md:col-span-2 rounded-lg bg-black/60 border border-white/5 p-4 flex flex-col font-mono text-left relative">
                  <div className="absolute top-2.5 right-3.5 flex items-center gap-1.5">
                    <Terminal size={10} style={{ color: '#00e5ff' }} />
                    <span className="text-[0.5625rem] font-bold tracking-wider uppercase" style={{ color: 'rgba(255,255,255,0.35)' }}>Live Output</span>
                  </div>
                  <h4 className="text-[0.625rem] font-bold mb-3 uppercase tracking-wider" style={{ color: 'rgba(255,255,255,0.45)' }}>Device Log Terminal</h4>
                  <div className="flex-1 flex flex-col gap-1.5 overflow-hidden text-[0.6875rem] text-[#3dffa0]">
                    {terminalLogs.map((log, index) => (
                      <div key={index} className="truncate opacity-90 border-l border-neon/20 pl-2">
                        {log}
                      </div>
                    ))}
                  </div>
                </div>

              </div>

            </div>
          </div>
        </div>
      </section>

      {/* ── SOCIAL PROOF ──────────────────────────────────── */}
      <div style={{ position: 'relative', zIndex: 10, padding: '1.5rem', borderTop: `1px solid ${brd}`, borderBottom: `1px solid ${brd}`, background: theme === 'dark' ? 'rgba(13,15,23,0.6)' : 'rgba(248,250,252,0.8)' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '2.5rem' }}>
          {[
            ['#00e5ff', <Shield size={14} />, 'System-Level Integrity'],
            ['#ffc857', <Zap size={14} />, 'Gemini AI Calibrated'],
            ['#3dffa0', <Check size={14} />, 'No Subscription Model'],
            ['#00e5ff', <RefreshCw size={14} />, '100% Offline Capable'],
            ['#ffc857', <Users size={14} />, 'Grade 4 Curriculum Aligned']
          ].map(([clr, icon, label]) => (
            <span key={label} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.8125rem', fontWeight: 600, color: dim, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              <span style={{ color: clr }}>{icon}</span> {label}
            </span>
          ))}
        </div>
      </div>

      {/* ── FEATURES ──────────────────────────────────────── */}
      <section id="features" style={{ position: 'relative', zIndex: 10, padding: '6.5rem 1.5rem' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto' }}>
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '4.5rem' }}>
            <div className="badge badge-neon" style={{ marginBottom: '1rem', display: 'inline-flex' }}>System Features</div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(1.75rem, 4vw, 2.75rem)', fontWeight: 900, margin: '0 0 1rem', color: txt, tracking: '-0.01em' }}>
              Built for learning. Calibrated for security.
            </h2>
            <p style={{ color: muted, maxWidth: '580px', margin: '0 auto', lineHeight: 1.65, fontSize: '0.875rem' }}>Every system component was engineered to incentivize vocabulary development while enforcing strict system boundaries.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map((f, i) => <FeatureCard key={i} {...f} delay={i * 60} />)}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ──────────────────────────────────── */}
      <section id="how-it-works" style={{ position: 'relative', zIndex: 10, padding: '6.5rem 1.5rem', borderTop: `1px solid ${brd}`, background: theme === 'dark' ? 'rgba(13,15,23,0.6)' : 'rgba(248,250,252,0.8)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '4.5rem' }}>
            <div className="badge badge-amber" style={{ marginBottom: '1rem', display: 'inline-flex' }}>Deployment Path</div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(1.75rem, 4vw, 2.75rem)', fontWeight: 900, margin: '0 0 1rem', color: txt }}>Streamlined Onboarding</h2>
            <p style={{ color: muted, lineHeight: 1.65, fontSize: '0.875rem' }}>Zero complicated commands. Set up and link the local lock app to your portal in under 5 minutes.</p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
            {STEPS.map((s, i) => (
              <div key={i} className="reveal glass rounded-[14px] hover-amber transition-all duration-300" style={{ padding: '1.5rem', animationDelay: `${i * 80}ms` }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '2.25rem', fontWeight: 900, color: 'var(--amber)', opacity: 0.25, marginBottom: '0.75rem' }}>{s.num}</div>
                <h3 style={{ fontWeight: 700, fontSize: '0.875rem', color: txt, marginBottom: '0.5rem' }}>{s.title}</h3>
                <p style={{ fontSize: '0.75rem', color: muted, lineHeight: 1.55 }}>{s.body}</p>
              </div>
            ))}
          </div>
          <div style={{ textAlign: 'center', marginTop: '3.5rem' }}>
            <button onClick={handleDownload} disabled={downloading} className="btn-primary press-effect" style={{ fontSize: '0.875rem' }}>
              <Download size={15} /> Download Client Package
            </button>
          </div>
        </div>
      </section>

      {/* ── SECURITY ──────────────────────────────────────── */}
      <section id="security" style={{ position: 'relative', zIndex: 10, padding: '6.5rem 1.5rem' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '4rem', alignItems: 'center' }}>
          <div className="reveal">
            <div className="badge badge-mint" style={{ marginBottom: '1.25rem', display: 'inline-flex' }}>Security Metrics</div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(1.5rem, 3.5vw, 2.5rem)', fontWeight: 900, lineHeight: 1.15, margin: '0 0 1.5rem', color: txt }}>
              Hardened Access Control
            </h2>
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {[
                { icon: <Lock size={15} />, title: 'Strict Identity Controls',  body: 'Data is protected via custom Firestore rules matching only verified parent users.' },
                { icon: <Shield size={15} />, title: 'Low-Level Keyboard Hooks', body: 'Local app monitors OS key logs to block task-switching options (Alt+Tab, Windows keys).' },
                { icon: <Check size={15} />, title: 'Zero Third-Party Logs',     body: 'All activity logs remain strictly confidential. SpellGate uses no tracking cookies or ads.' },
                { icon: <Zap size={15} />, title: 'Cryptographic Checksums',    body: 'Integrity is protected locally via machine-bound HMAC signatures on progress files.' },
              ].map((p, i) => (
                <li key={i} style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
                  <div style={{ width: 30, height: 30, borderRadius: 6, background: 'rgba(61,255,160,0.06)', color: '#3dffa0', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, marginTop: 2 }}>{p.icon}</div>
                  <div>
                    <p style={{ fontWeight: 700, fontSize: '0.875rem', color: txt, margin: '0 0 0.25rem' }}>{p.title}</p>
                    <p style={{ fontSize: '0.75rem', color: muted, lineHeight: 1.55, margin: 0 }}>{p.body}</p>
                  </div>
                </li>
              ))}
            </ul>
            <p style={{ fontSize: '0.6875rem', color: dim, marginTop: '2rem' }}>
              For legal frameworks see our{' '}
              <button onClick={() => setShowPrivacyModal(true)} className="policy-link" style={{ background: 'none', border: 'none', padding: 0, font: 'inherit', color: 'var(--neon)', cursor: 'pointer', borderBottom: '1px solid transparent' }}>Privacy Policy</button>{' '}and{' '}
              <button onClick={() => setShowTermsModal(true)} className="policy-link" style={{ background: 'none', border: 'none', padding: 0, font: 'inherit', color: 'var(--neon)', cursor: 'pointer', borderBottom: '1px solid transparent' }}>Terms of Service</button>.
            </p>
          </div>
          <div className="reveal glass-hi" style={{ borderRadius: 16, padding: '1.75rem', boxShadow: '0 24px 64px -16px rgba(61,255,160,0.04)', border: '1px solid rgba(61,255,160,0.15)' }}>
            <h3 style={{ fontWeight: 700, fontSize: '0.875rem', marginBottom: '1rem', color: '#3dffa0', display: 'flex', alignItems: 'center', gap: 6, margin: '0 0 1rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              <Shield size={14} /> Firestore Ruleset
            </h3>
            <pre style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', lineHeight: 1.6, color: theme === 'dark' ? '#9cb8d2' : '#334155', margin: 0, overflowX: 'auto' }}>{`match /users/{userId}/{document=**} {
  allow read, update, delete: if
    request.auth != null &&
    request.auth.uid == userId &&
    request.auth.token.email_verified == true;

  allow create: if
    request.auth != null &&
    request.auth.uid == userId;
}`}</pre>
            <p style={{ fontSize: '0.6875rem', color: dim, marginTop: '1rem' }}>Rules strictly isolate settings data and enforce email validation thresholds.</p>
          </div>
        </div>
      </section>

      {/* ── FAQ ───────────────────────────────────────────── */}
      <section id="faq" style={{ position: 'relative', zIndex: 10, padding: '6.5rem 1.5rem', borderTop: `1px solid ${brd}`, background: theme === 'dark' ? 'rgba(13,15,23,0.6)' : 'rgba(248,250,252,0.8)' }}>
        <div style={{ maxWidth: '700px', margin: '0 auto' }}>
          <div className="reveal" style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
            <div className="badge badge-neon" style={{ marginBottom: '1rem', display: 'inline-flex' }}>Common FAQ</div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(1.75rem, 4vw, 2.5rem)', fontWeight: 900, color: txt, margin: 0 }}>System Queries</h2>
          </div>
          <div className="reveal" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {FAQ_ITEMS.map((item, i) => <FaqItem key={i} {...item} />)}
          </div>
        </div>
      </section>

      {/* ── FOOTER ────────────────────────────────────────── */}
      <footer style={{ position: 'relative', zIndex: 10, borderTop: `1px solid ${brd}`, padding: '4rem 1.5rem 2rem', background: theme === 'dark' ? 'rgba(8,9,13,0.92)' : 'rgba(244,246,250,0.95)' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '2.5rem', marginBottom: '3.5rem' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: '0.75rem' }}>
                <SpellGateLogo size={30} />
                <span style={{ fontFamily: 'var(--font-display)', fontWeight: 850, fontSize: '0.8125rem', letterSpacing: '0.2em', textTransform: 'uppercase', color: neon }}>SpellGate</span>
              </div>
              <p style={{ fontSize: '0.75rem', color: muted, lineHeight: 1.6, margin: '0 0 1.25rem' }}>A curriculum-focused utility that turns screen access limits into constructive spelling study incentives.</p>
              <div style={{ display: 'flex', gap: '0.75rem' }}>
                {[
                  { href: 'https://github.com/Hazy019/SpellGate', label: 'GitHub', svg: <svg width="14" height="14" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.438 9.8 8.205 11.387.6.113.82-.258.82-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.63-5.37-12-12-12z"/></svg> },
                  { href: 'https://twitter.com',                   label: 'Twitter', svg: <svg width="13" height="13" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.253 5.622zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg> },
                ].map(s => (
                  <a key={s.label} href={s.href} target="_blank" rel="noopener noreferrer" aria-label={s.label}
                    style={{ width: 30, height: 30, borderRadius: 6, border: `1px solid ${brd}`, background: 'transparent', color: muted, display: 'flex', alignItems: 'center', justifyContent: 'center', textDecoration: 'none', transition: 'border-color 0.2s, color 0.2s' }}
                    onMouseEnter={e => { e.currentTarget.style.borderColor = neon; e.currentTarget.style.color = neon; }}
                    onMouseLeave={e => { e.currentTarget.style.borderColor = brd; e.currentTarget.style.color = muted; }}>
                    {s.svg}
                  </a>
                ))}
              </div>
            </div>
            <div>
              <p style={{ fontSize: '0.625rem', fontWeight: 750, letterSpacing: '0.1em', textTransform: 'uppercase', color: dim, marginBottom: '0.85rem' }}>Navigation</p>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
                {[...NAV_LINKS, { href: user ? '/dashboard' : '/login', label: user ? 'Dashboard' : 'Parent Login' }].map(l => (
                  <li key={l.href}><a href={l.href} style={{ fontSize: '0.75rem', color: muted, textDecoration: 'none', transition: 'color 0.2s', fontWeight: 550 }}
                    onMouseEnter={e => e.target.style.color = txt} onMouseLeave={e => e.target.style.color = muted}>{l.label}</a></li>
                ))}
              </ul>
            </div>
            <div>
              <p style={{ fontSize: '0.625rem', fontWeight: 750, letterSpacing: '0.1em', textTransform: 'uppercase', color: dim, marginBottom: '0.85rem' }}>Security & Legal</p>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.55rem' }}>
                <li>
                  <button onClick={() => setShowPrivacyModal(true)} style={{ background: 'none', border: 'none', padding: 0, fontSize: '0.75rem', color: muted, textDecoration: 'none', transition: 'color 0.2s', fontWeight: 550, cursor: 'pointer', textAlign: 'left' }}
                    onMouseEnter={e => e.target.style.color = txt} onMouseLeave={e => e.target.style.color = muted}>Privacy Policy</button>
                </li>
                <li>
                  <button onClick={() => setShowTermsModal(true)} style={{ background: 'none', border: 'none', padding: 0, fontSize: '0.75rem', color: muted, textDecoration: 'none', transition: 'color 0.2s', fontWeight: 550, cursor: 'pointer', textAlign: 'left' }}
                    onMouseEnter={e => e.target.style.color = txt} onMouseLeave={e => e.target.style.color = muted}>Terms of Service</button>
                </li>
              </ul>
            </div>
          </div>
          <div style={{ borderTop: `1px solid ${brd}`, paddingTop: '1.25rem', display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem' }}>
            <p style={{ fontSize: '0.6875rem', color: dim, margin: 0 }}>© {new Date().getFullYear()} SpellGate Security System. Open source GPLv3.</p>
            <p style={{ fontSize: '0.6875rem', color: dim, margin: 0 }}>Engineered for Grade 4 education</p>
          </div>
        </div>
      </footer>

      {/* Reusable Legal Modals containing clear human copy */}
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
    </div>
  );
};

export default App;
