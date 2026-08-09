import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence, useScroll, useTransform, useInView } from 'framer-motion';
import {
  Download, Shield, Star, Zap, RefreshCw, ArrowRight, ChevronDown, Menu, X, Lock, Brain,
  Award, Activity, Sun, Moon, Users, Terminal, CheckCircle2, HelpCircle, Laptop, Smartphone,
  Eye, Sparkles, Key, Check, Server
} from 'lucide-react';
import { useTheme } from './ThemeContext';
import { useAuth } from './AuthContext';

/* ─────────────────────────────────────────────────────
   CONSTANTS & CONFIG
───────────────────────────────────────────────────── */
// Direct binary download from local public bundle (with fallback to direct GitHub release tag v1.1.0)
const INSTALLER_URL = '/SpellGateSetup.exe';
const GITHUB_RELEASE_FALLBACK = 'https://github.com/Hazy019/SpellGate/releases/download/v1.1.0/SpellGateSetup.exe';

const NAV_LINKS = [
  { href: '#hero', label: 'Home' },
  { href: '#features', label: 'Features' },
  { href: '#how-it-works', label: 'How It Works' },
  { href: '#security', label: 'Security' },
  { href: '#faq', label: 'FAQ' },
];

/* Floating 3D Keycaps spelling S-P-E-L-L */
const KEYCAPS = [
  { char: 'S', left: '8%', top: '28%', depth: 1.1, delay: 0.0, size: 'w-12 h-12 md:w-14 md:h-14 text-lg md:text-xl', mobile: true },
  { char: 'P', left: '22%', top: '72%', depth: 1.3, delay: 0.4, size: 'w-14 h-14 md:w-16 md:h-16 text-xl md:text-2xl', mobile: true },
  { char: 'E', left: '76%', top: '24%', depth: 0.9, delay: 0.8, size: 'w-11 h-11 md:w-13 md:h-13 text-base md:text-lg', mobile: false },
  { char: 'L', left: '88%', top: '64%', depth: 1.2, delay: 1.2, size: 'w-13 h-13 md:w-15 md:h-15 text-lg md:text-xl', mobile: true },
  { char: 'L', left: '48%', top: '88%', depth: 1.4, delay: 1.6, size: 'w-14 h-14 md:w-16 md:h-16 text-xl md:text-2xl', mobile: false },
];

/* Core Features (3 Top + 2 Bottom equal content depth) */
const FEATURES = [
  {
    icon: <Brain className="text-arcade-green" size={22} />,
    title: 'Adaptive Spelling Engine',
    body: 'Dynamically scales vocabulary complexity across Novice, Apprentice, and Scholar difficulty tiers based on real-time accuracy.',
    badge: '3-Tier AI Cascade'
  },
  {
    icon: <Lock className="text-arcade-green" size={22} />,
    title: 'Kiosk Lockdown Mode',
    body: 'Secures Windows at system level. Kernel-level hooks block Task Manager, Alt+Tab, and Windows shortcut bypasses.',
    badge: '100% Anti-Bypass'
  },
  {
    icon: <Zap className="text-arcade-green" size={22} />,
    title: 'Real-Time Force Unlock',
    body: 'Instantly override lock states or issue custom screen-time bonuses remotely from the cloud-connected Parent Dashboard.',
    badge: 'Instant Portal Sync'
  },
  {
    icon: <RefreshCw className="text-arcade-green" size={22} />,
    title: '100% Offline Resilient',
    body: 'Pre-baked with 150+ Grade 4 offline word banks. Operates seamlessly without internet and syncs when back online.',
    badge: 'Zero Internet Needed'
  },
  {
    icon: <Award className="text-arcade-green" size={22} />,
    title: 'Spaced Repetition Recall',
    body: 'Automated Ebbinghaus retention algorithm continuously resurfaces previously missed words until total mastery is achieved.',
    badge: 'Memory Retention'
  },
];

/* How It Works Steps */
const STEPS = [
  {
    num: '01',
    title: 'Install Windows Client',
    body: 'Download the launcher and run setup on your child’s PC. Startup hooks configure automatically in under 2 minutes.'
  },
  {
    num: '02',
    title: 'Generate Pair Code',
    body: 'Launch SpellGate on the child PC to display a unique 6-digit cryptographic pairing key.'
  },
  {
    num: '03',
    title: 'Link Parent App',
    body: 'Enter the pair code into your Parent Dashboard to establish real-time Firestore sync and remote management.'
  },
  {
    num: '04',
    title: 'Earn & Play',
    body: 'Kids spell words to earn PC screen time. When time runs out, SpellGate locks the PC until the next challenge.'
  },
];

/* FAQ Accordion Items (Real Parent-Facing Content per §0) */
const FAQ_ITEMS = [
  {
    q: "Is my child's data safe?",
    a: "Yes, absolutely. SpellGate stores all family settings and activity logs in your private Firestore database. API keys are never bundled in the executable and are fetched securely via the OS credential manager at runtime. Strict database security rules restrict access exclusively to authenticated parents with verified emails. We never sell, track, or share your data."
  },
  {
    q: "What happens if the internet goes down?",
    a: "SpellGate continues running without interruption. The Windows client comes pre-loaded with over 150 offline word banks and enforces local kiosk lock rules offline. Any screen time earned or words mastered offline are stored locally in machine-bound encrypted caches and sync automatically once reconnected."
  },
  {
    q: "Can my kid bypass the lock screen?",
    a: "No. SpellGate runs a low-level background watchdog daemon that installs system-level keyboard hooks. This actively suppresses Task Manager, Alt+Tab, Windows keys, and process termination attempts. In emergencies, parents can press Ctrl+Shift+P to enter their master override passcode."
  },
  {
    q: "How do I set the exchange rate?",
    a: "In your Parent Dashboard Portal settings, you can customize the screen-time multiplier (e.g. 15 seconds of PC time per correctly spelled word). You can also set daily maximum caps, bonus rewards for streak masteries, or adjust rates per difficulty tier."
  },
  {
    q: "Does this work on Mac?",
    a: "Currently, SpellGate is engineered exclusively for Windows 10 and Windows 11. This allows us to leverage native Windows APIs and low-level kernel hooks required to deliver an un-bypassable kiosk lock experience."
  }
];

/* ─────────────────────────────────────────────────────
   HUD RETICLE BRACKETS MOTIF COMPONENT
───────────────────────────────────────────────────── */
function HudReticles() {
  return (
    <>
      <span className="hud-reticle hud-reticle-tl" />
      <span className="hud-reticle hud-reticle-tr" />
      <span className="hud-reticle hud-reticle-bl" />
      <span className="hud-reticle hud-reticle-br" />
    </>
  );
}

/* ─────────────────────────────────────────────────────
   ANIMATED COUNT-UP NUMBER HELPER
───────────────────────────────────────────────────── */
function CountUpNumber({ value }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-40px' });
  const [displayVal, setDisplayVal] = useState('0');

  useEffect(() => {
    if (!isInView) return;

    // Check if value contains numbers
    const match = value.match(/(\d+)/);
    if (!match) {
      setDisplayVal(value);
      return;
    }

    const num = parseInt(match[1], 10);
    const prefix = value.substring(0, value.indexOf(match[1]));
    const suffix = value.substring(value.indexOf(match[1]) + match[1].length);

    let startTimestamp = null;
    const duration = 900;

    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(easeOut * num);

      setDisplayVal(`${prefix}${current}${suffix}`);

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        setDisplayVal(value);
      }
    };

    requestAnimationFrame(step);
  }, [isInView, value]);

  return <span ref={ref}>{displayVal}</span>;
}

/* ─────────────────────────────────────────────────────
   SPELLGATE BRAND LOGO COMPONENT
───────────────────────────────────────────────────── */
function SpellGateLogo({ size = 28 }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 48 48"
      width={size}
      height={size}
      fill="none"
    >
      <path
        d="M 24 3 L 43 14 L 43 34 L 24 45 L 5 34 L 5 14 Z"
        stroke="var(--arcade-green)"
        strokeWidth="2.5"
        strokeLinejoin="round"
        fill="rgba(74, 222, 128, 0.06)"
      />
      <path d="M 13 16 L 35 16 L 35 19 L 34 19 L 34 18 L 14 18 L 14 19 L 13 19 Z" fill="var(--arcade-green)" />
      <rect x="16" y="18" width="3" height="15" fill="var(--arcade-green)" />
      <rect x="14" y="33" width="7" height="2" fill="var(--arcade-green)" />
      <rect x="29" y="18" width="3" height="15" fill="var(--arcade-green)" />
      <rect x="27" y="33" width="7" height="2" fill="var(--arcade-green)" />
      <rect x="20" y="19" width="8" height="9" fill="#070A10" stroke="var(--arcade-green)" strokeWidth="1.5" rx="1" />
      <rect x="23" y="22" width="2" height="4" fill="var(--cyber-violet)" rx="0.5" />
    </svg>
  );
}

/* ─────────────────────────────────────────────────────
   LEGAL MODAL COMPONENT
───────────────────────────────────────────────────── */
function LegalModal({ isOpen, onClose, title, children }) {
  useEffect(() => {
    document.body.style.overflow = isOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className="relative w-full max-w-xl bg-slate-glass border border-white/10 rounded-2xl shadow-2xl p-6 md:p-8 flex flex-col max-h-[85vh]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <h3 className="text-lg font-bold font-display text-white">{title}</h3>
          <button onClick={onClose} className="text-white/60 hover:text-white transition-colors cursor-pointer p-1">
            <X size={20} />
          </button>
        </div>
        <div className="overflow-y-auto mt-4 pr-2 text-sm leading-relaxed text-white/85 space-y-4 font-body">
          {children}
        </div>
        <div className="border-t border-white/10 pt-4 mt-6 flex justify-end">
          <button onClick={onClose} className="btn-arcade-primary text-xs px-4 py-2">Close</button>
        </div>
      </motion.div>
    </div>
  );
}

/* ─────────────────────────────────────────────────────
   MAIN LANDING PAGE APPLICATION (v2 MASTER DESIGN & MOTION)
───────────────────────────────────────────────────── */
export default function App() {
  const { theme, toggleTheme } = useTheme();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [downloading, setDownloading] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [showTermsModal, setShowTermsModal] = useState(false);
  const [activeFaq, setActiveFaq] = useState(null);

  /* Scroll Parallax Hooks */
  const { scrollY } = useScroll();
  const laptopParallax = useTransform(scrollY, [0, 800], [0, -70]);
  const phoneParallax = useTransform(scrollY, [0, 800], [0, -110]);
  const keycapsParallax = useTransform(scrollY, [0, 800], [0, -90]);

  /* Scroll-triggered Laser Conduit line progress for How It Works */
  const howItWorksRef = useRef(null);
  const { scrollYProgress: conduitProgress } = useScroll({
    target: howItWorksRef,
    offset: ["start 70%", "end 50%"]
  });
  const conduitWidth = useTransform(conduitProgress, [0, 1], ["0%", "100%"]);

  /* Live Terminal Logs for Watchdog Showcase */
  const [terminalLogs, setTerminalLogs] = useState([
    '[INIT] Watchdog daemon active on host CHILD-PC',
    '[AUTH] API keys loaded via Windows Credential Store',
    '[HOOKS] Keyboard hooks engaged: TaskManager & Alt-Tab BLOCKED',
    '[FIRESTORE] Rule validated: UID match for parent profile'
  ]);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  /* Typewriter continuous terminal log stream (~1 line per 800ms) */
  useEffect(() => {
    const events = [
      '[WATCHDOG] Alt-Tab shortcut attempt intercepted and suppressed',
      '[SPELL] Word challenge: "OPINION" -> Correct (+15s earned)',
      '[HEARTBEAT] Ping latency: 18ms -> Live Sync active',
      '[SPELL] Word challenge: "SCRAMBLE" -> Correct (+15s earned)',
      '[FIRESTORE] Synchronized 2 words mastered to parent portal',
      '[WATCHDOG] Process termination attempt blocked on PID 4192',
      '[SPELL] Word challenge: "GLOBE" -> Correct (+15s earned)'
    ];
    let i = 0;
    const interval = setInterval(() => {
      const timestamp = new Date().toLocaleTimeString();
      setTerminalLogs(prev => [
        ...prev.slice(-5),
        `[${timestamp}] ${events[i % events.length]}`
      ]);
      i++;
    }, 1800);
    return () => clearInterval(interval);
  }, []);

  const handleDownload = () => {
    setDownloading(true);
    // Trigger a direct browser download from the bundled public file
    const a = document.createElement('a');
    a.href = INSTALLER_URL;
    a.download = 'SpellGateSetup.exe';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => setDownloading(false), 3000);
  };

  return (
    <div className="relative min-h-screen bg-[#070A10] text-white overflow-x-hidden font-body selection:bg-arcade-green selection:text-[#070A10]">

      {/* ── BACK LAYER: Animated Grid Background ──────────────────────── */}
      <div
        className="fixed inset-0 pointer-events-none z-0 opacity-15"
        style={{
          backgroundImage: `linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px),
                            linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px)`,
          backgroundSize: '48px 48px'
        }}
        aria-hidden="true"
      />

      {/* Atmospheric Glowing Orbs */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden" aria-hidden="true">
        <div className="absolute -top-40 -left-40 w-[600px] h-[600px] bg-arcade-green/10 rounded-full blur-[140px]" />
        <div className="absolute top-1/3 -right-40 w-[500px] h-[500px] bg-cyber-violet/10 rounded-full blur-[140px]" />
        <div className="absolute -bottom-40 left-1/4 w-[600px] h-[600px] bg-arcade-green/5 rounded-full blur-[160px]" />
      </div>

      {/* ── FRONT LAYER: FLOATING 3D KEYCAPS (S-P-E-L-L) ──────────────── */}
      <motion.div
        style={{ y: keycapsParallax }}
        className="absolute inset-x-0 top-0 h-[900px] pointer-events-none z-30 max-w-7xl mx-auto overflow-hidden"
      >
        {KEYCAPS.map((kc, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, scale: 0.5, y: 40 }}
            animate={{
              opacity: 1,
              scale: 1,
              y: [0, -14 * kc.depth, 0],
              rotate: [0, 5 * (idx % 2 === 0 ? 1 : -1), 0]
            }}
            transition={{
              opacity: { duration: 0.8, delay: kc.delay },
              scale: { duration: 0.8, delay: kc.delay },
              y: { duration: 3.5 + idx * 0.5, repeat: Infinity, ease: 'easeInOut', delay: kc.delay },
              rotate: { duration: 4.5 + idx * 0.5, repeat: Infinity, ease: 'easeInOut', delay: kc.delay }
            }}
            style={{
              position: 'absolute',
              left: kc.left,
              top: kc.top,
              filter: `drop-shadow(0 12px 24px rgba(0,0,0,0.8))`
            }}
            className={`keycap-3d ${kc.size} ${!kc.mobile ? 'hidden md:inline-flex' : 'inline-flex'}`}
          >
            {kc.char}
          </motion.div>
        ))}
      </motion.div>

      {/* ── NAVBAR ────────────────────────────────────────────────────── */}
      <header className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-[#070A10]/90 backdrop-blur-xl border-b border-white/10 py-3.5 is-scrolled' : 'bg-transparent py-5 is-top'
        }`}>
        <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">

          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 text-white no-underline group" aria-label="SpellGate Home">
            <SpellGateLogo size={32} />
            <span className="font-display text-lg font-extrabold tracking-widest uppercase text-arcade-green group-hover:text-white transition-colors nav-logo-wordmark">
              SpellGate
            </span>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map(link => (
              <a
                key={link.href}
                href={link.href}
                className="text-xs font-semibold text-white/80 hover:text-white transition-colors uppercase tracking-wider relative py-1 nav-link-item"
              >
                {link.label}
                <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-arcade-green scale-x-0 origin-left transition-transform duration-200 nav-underline" />
              </a>
            ))}
          </nav>

          {/* Desktop Right Action Buttons */}
          <div className="hidden md:flex items-center gap-3">
            <button
              onClick={toggleTheme}
              className="w-9 h-9 rounded-full border border-white/10 bg-white/5 flex items-center justify-center text-white/70 hover:text-white hover:border-arcade-green/40 transition-colors cursor-pointer"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
            </button>

            <Link
              to={user ? "/dashboard" : "/login"}
              className="btn-cyber-secondary text-xs px-4 py-2"
            >
              {user ? "Parent Dashboard" : "Parent Login"}
            </Link>

            <button
              onClick={handleDownload}
              disabled={downloading}
              className="btn-arcade-primary text-xs px-4 py-2"
            >
              {downloading ? (
                <><RefreshCw size={14} className="animate-spin" /> Downloading…</>
              ) : (
                <><Download size={14} /> Get App</>
              )}
            </button>
          </div>

          {/* Mobile Hamburger Toggle */}
          <button
            onClick={() => setMobileMenuOpen(o => !o)}
            className={`md:hidden p-2 rounded-lg cursor-pointer transition-colors ${
              scrolled && theme === 'light'
                ? 'text-[#10131A] hover:bg-black/5'
                : 'text-white/90 hover:text-white hover:bg-white/10'
            }`}
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation Drawer */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className={`md:hidden overflow-hidden border-b transition-colors duration-300 mobile-nav-drawer ${
                scrolled && theme === 'light'
                  ? 'bg-[#F7F5F0]/98 backdrop-blur-xl border-[var(--border-hairline)] shadow-lg'
                  : 'bg-[#070A10]/95 backdrop-blur-xl border-white/10'
              }`}
            >
              <nav className="flex flex-col gap-4 px-6 py-6 text-sm">
                {NAV_LINKS.map(link => (
                  <a
                    key={link.href}
                    href={link.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className="font-semibold text-base transition-colors mobile-nav-link"
                  >
                    {link.label}
                  </a>
                ))}
                <div className="flex items-center justify-between pt-2">
                  <span className="text-xs font-mono font-semibold opacity-90 mobile-nav-theme-label">
                    Theme Mode
                  </span>
                  <button
                    onClick={toggleTheme}
                    className="px-3.5 py-2 rounded-lg border flex items-center gap-2 text-xs font-bold cursor-pointer transition-colors mobile-nav-theme-btn"
                    aria-label="Toggle theme"
                  >
                    {theme === 'dark' ? <><Sun size={14} className="text-amber-400" /> Light Mode</> : <><Moon size={14} className="text-arcade-green" /> Dark Mode</>}
                  </button>
                </div>
                <hr className="border-white/15 my-1 mobile-nav-hr" />
                <Link
                  to={user ? "/dashboard" : "/login"}
                  onClick={() => setMobileMenuOpen(false)}
                  className="font-bold text-sm mobile-nav-portal-link"
                >
                  {user ? "Go to Dashboard" : "Parent Dashboard Portal"}
                </Link>
                <button
                  onClick={handleDownload}
                  className="btn-arcade-primary w-full justify-center text-xs py-3 mt-2"
                >
                  <Download size={14} /> Download Client Launcher
                </button>
              </nav>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* ── 5.1 HERO SECTION (BALANCED TWO-COLUMN SPLIT - MASTER PROMPT V7) ────────── */}
      <section id="hero" className="relative z-10 min-h-screen flex items-center pt-28 pb-16 px-6 overflow-hidden">

        {/* Ambient Void Background Glow Spill */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[550px] bg-gradient-to-r from-arcade-green/20 via-emerald-500/10 to-cyber-violet/25 blur-[140px] rounded-full -z-10 pointer-events-none" />

        <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">

          {/* ── LEFT COLUMN (~50% width / lg:col-span-6) ───────────────────── */}
          <div className="lg:col-span-6 text-left relative z-20">

            {/* Micro-Badge */}
            <motion.div
              initial={{ opacity: 0, y: -16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-arcade-green/10 border border-arcade-green/30 text-arcade-green text-xs font-mono font-semibold uppercase tracking-wider mb-6"
            >
              <Sparkles size={13} /> Grade 4 Screen-Time Management Kiosk
            </motion.div>

            {/* Staggered Line Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.08 }}
              className="font-display text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.08] text-white mb-6"
            >
              Transform Screen Time Into <br />
              <span className="bg-gradient-to-r from-arcade-green via-emerald-300 to-purple-400 bg-clip-text text-transparent">
                Spelling Mastery.
              </span>
            </motion.h1>

            {/* Subheadline */}
            <motion.p
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.18 }}
              className="text-white/90 text-base sm:text-lg max-w-xl leading-relaxed mb-8"
            >
              SpellGate locks Windows PCs behind AI-driven spelling challenges. Kids spell to earn play time; parents monitor and control in real-time.
            </motion.p>

            {/* Action CTAs (Exclusion Zone Safe - Part A) */}
            <motion.div
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.26 }}
              className="flex flex-wrap items-center gap-4 mb-4 relative z-30"
            >
              <button
                onClick={handleDownload}
                disabled={downloading}
                className="btn-arcade-primary text-sm px-7 py-3.5 text-black font-bold"
              >
                {downloading ? (
                  <><RefreshCw size={16} className="animate-spin" /> Preparing Package…</>
                ) : (
                  <><Download size={16} /> Get Started Free <ArrowRight size={16} /></>
                )}
              </button>

              <Link
                to={user ? "/dashboard" : "/login"}
                className="btn-cyber-secondary text-sm px-7 py-3.5"
              >
                <Shield size={16} /> Parent Dashboard Portal
              </Link>
            </motion.div>

            <p className="text-white/70 text-xs font-mono mt-3">
              Windows 10 / 11 · Zero Configuration Needed · 100% Free Open Source
            </p>

            {/* Systemic Exclusion Zone Keycaps (Frosted 3D Glass - Part A & D) */}
            <div className="absolute -top-8 -left-8 keycap-glass-3d keycap-glass-3d-floating w-11 h-11 text-base shadow-xl hidden lg:flex pointer-events-none" style={{ animationDelay: '0s' }}>
              S
            </div>
            <div className="absolute top-1/2 -left-12 keycap-glass-3d keycap-glass-3d-floating w-10 h-10 text-sm shadow-xl hidden lg:flex pointer-events-none" style={{ animationDelay: '1.2s' }}>
              P
            </div>
          </div>

          {/* ── RIGHT COLUMN (~50% width / lg:col-span-6) — UNCONTAINED WIDE HERO (Part A & B) ── */}
          <div className="lg:col-span-6 relative flex items-center justify-center">

            {/* Ambient Uncontained Void Glow Spill Behind Hero Graphic */}
            <div className="absolute -inset-4 bg-gradient-to-r from-arcade-green/20 via-emerald-500/10 to-cyber-violet/25 blur-3xl rounded-full -z-10 opacity-70 pointer-events-none" />

            {/* Uncontained Hero Device Scene Graphic (Proportional Anchor) */}
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.7, delay: 0.2, ease: 'easeOut' }}
              style={{ y: laptopParallax }}
              className="relative w-full max-w-lg lg:max-w-xl group overflow-visible"
            >
              <div className="relative w-full flex items-center justify-center">
                <img
                  src="/laptop.png"
                  alt="SpellGate kiosk game on laptop connected to the parent dashboard on phone with floating SPELL keycaps"
                  className="w-full h-auto rounded-2xl object-contain transition-transform duration-700 group-hover:scale-[1.02] filter drop-shadow-[0_24px_60px_rgba(74,222,128,0.25)]"
                  loading="eager"
                />
              </div>
            </motion.div>

            {/* Systemic Exclusion Zone Keycaps (Part A & D: Frosted 3D Glass) */}
            <div className="absolute -top-6 right-4 keycap-glass-3d keycap-glass-3d-floating w-11 h-11 text-base shadow-xl hidden lg:flex pointer-events-none" style={{ animationDelay: '0.8s' }}>
              E
            </div>
            <div className="absolute top-1/3 -right-8 keycap-glass-3d keycap-glass-3d-floating w-10 h-10 text-sm shadow-xl hidden lg:flex pointer-events-none" style={{ animationDelay: '2.1s' }}>
              L
            </div>
            <div className="absolute -bottom-8 right-12 keycap-glass-3d keycap-glass-3d-floating w-12 h-12 text-lg shadow-xl hidden lg:flex pointer-events-none" style={{ animationDelay: '1.5s' }}>
              L
            </div>

          </div>

        </div>
      </section>

      {/* ── 5.2 PROOF & STATS STRIP (PART A: STATIC MARKETING CLAIMS + PART B: .SG-CARD) ── */}
      <section className="relative z-20 py-8 px-6 border-y border-white/10 bg-[#0F172A]/90 backdrop-blur-md">
        <div className="max-w-6xl mx-auto">
          <div className="sg-card grid grid-cols-2 md:grid-cols-4 gap-6 text-center shadow-2xl">
            <HudReticles />
            
            {[
              { val: '150+', label: 'Offline Word Banks' },
              { val: '3-Tier', label: 'Adaptive AI Cascade' },
              { val: '100%', label: 'Anti-Bypass Security' },
              { val: 'Zero-Lag', label: 'TTS Audio' }
            ].map((stat, idx) => (
              <div key={idx} className="flex flex-col items-center">
                <span className="font-display text-2xl sm:text-4xl font-extrabold text-white font-mono stat-number">
                  <CountUpNumber value={stat.val} />
                </span>
                <span className="text-arcade-green text-xs font-mono font-medium mt-1 uppercase tracking-wider stat-label">
                  {stat.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 5.3 CORE FEATURES GRID (PART B: LITERAL .SG-CARD MOTIF) ──────── */}
      <section id="features" className="relative z-10 py-24 px-6 bg-[#070A10]">
        <div className="max-w-6xl mx-auto">
          
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-mono text-arcade-green uppercase tracking-widest font-semibold block mb-3">
              // Core Capabilities
            </span>
            <h2 className="font-display text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
              Engineered For Learning. <br />
              Hardened For Security.
            </h2>
            <p className="text-white/90 text-sm sm:text-base mt-4">
              Every system component is calibrated to maximize spelling retention while enforcing strict system boundaries.
            </p>
          </div>

          {/* 3 Top Row + 2 Bottom Row Layout with .sg-card Motif */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            {FEATURES.slice(0, 3).map((feat, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.1 }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                whileHover={{ y: -4, scale: 1.01 }}
                className="sg-card flex flex-col justify-between group shadow-2xl transition-all duration-300"
              >
                <HudReticles />
                <div>
                  <div className="w-12 h-12 rounded-xl bg-arcade-green/15 border border-arcade-green/40 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform text-arcade-green shadow-md">
                    {feat.icon}
                  </div>
                  <h3 className="font-display text-xl font-bold text-white mb-2">{feat.title}</h3>
                  <p className="text-white/90 text-xs sm:text-sm leading-relaxed mb-6">{feat.body}</p>
                </div>
                <span className="inline-flex items-center text-[10px] font-mono font-semibold uppercase tracking-wider text-arcade-green bg-arcade-green/15 border border-arcade-green/30 px-3 py-1 rounded-full w-fit">
                  {feat.badge}
                </span>
              </motion.div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {FEATURES.slice(3, 5).map((feat, idx) => (
              <motion.div
                key={idx + 3}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.1 }}
                transition={{ duration: 0.5, delay: (idx + 3) * 0.1 }}
                whileHover={{ y: -4, scale: 1.01 }}
                className="sg-card flex flex-col justify-between group shadow-2xl transition-all duration-300"
              >
                <HudReticles />
                <div>
                  <div className="w-12 h-12 rounded-xl bg-arcade-green/15 border border-arcade-green/40 flex items-center justify-center mb-5 group-hover:scale-110 transition-transform text-arcade-green shadow-md">
                    {feat.icon}
                  </div>
                  <h3 className="font-display text-xl font-bold text-white mb-2">{feat.title}</h3>
                  <p className="text-white/90 text-xs sm:text-sm leading-relaxed mb-6">{feat.body}</p>
                </div>
                <span className="inline-flex items-center text-[10px] font-mono font-semibold uppercase tracking-wider text-arcade-green bg-arcade-green/15 border border-arcade-green/30 px-3 py-1 rounded-full w-fit">
                  {feat.badge}
                </span>
              </motion.div>
            ))}
          </div>

        </div>
      </section>

      {/* ── 5.4 HOW IT WORKS (PART B: ONBOARDING STEP CARDS WITH .SG-CARD) ── */}
      <section id="how-it-works" ref={howItWorksRef} className="relative z-10 py-24 px-6 bg-[#0B0F19]">
        <div className="max-w-6xl mx-auto">
          
          <div className="text-center max-w-2xl mx-auto mb-20">
            <span className="text-xs font-mono text-purple-400 uppercase tracking-widest font-semibold block mb-3">
              // Deployment Path
            </span>
            <h2 className="font-display text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
              Streamlined Onboarding
            </h2>
            <p className="text-white/90 text-sm sm:text-base mt-4">
              Set up the Windows lock app and pair your parent portal in under 5 minutes.
            </p>
          </div>

          {/* Laser Conduit Progress Bar Container */}
          <div className="relative">
            
            {/* Conduit Background Track Line */}
            <div className="hidden md:block absolute top-12 left-0 right-0 h-[3px] bg-white/10 z-0" />
            
            {/* Scroll-Linked Glowing Laser Conduit Line */}
            <motion.div 
              style={{ width: conduitWidth }}
              className="hidden md:block absolute top-12 left-0 h-[3px] bg-gradient-to-r from-arcade-green via-emerald-400 to-purple-500 shadow-[0_0_12px_#4ADE80] z-0"
            />

            {/* 4 Step Cards with .sg-card Motif */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 relative z-10">
              {STEPS.map((step, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, scale: 0.95 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  viewport={{ once: true, amount: 0.1 }}
                  transition={{ duration: 0.5, delay: idx * 0.12 }}
                  whileHover={{ y: -4 }}
                  className="sg-card flex flex-col justify-between shadow-2xl transition-all duration-300"
                >
                  <HudReticles />
                  <div>
                    {/* 3D Keycap Step Badge */}
                    <div className="keycap-glass-3d w-12 h-12 text-lg mb-6 shadow-lg">
                      {step.num}
                    </div>
                    <h3 className="font-display text-lg font-bold text-white mb-2">{step.title}</h3>
                    <p className="text-white/90 text-xs leading-relaxed">{step.body}</p>
                  </div>
                </motion.div>
              ))}
            </div>

          </div>

        </div>
      </section>

      {/* ── 5.5 SECURITY SHOWCASE (PART B: SECURITY PANEL WITH .SG-CARD) ── */}
      <section id="security" className="relative z-10 py-24 px-6 bg-[#070A10]">
        <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          
          {/* Left Column: Plain Language High-Contrast Verified Security Claims */}
          <motion.div 
            initial={{ opacity: 0, x: -24 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.1 }}
            transition={{ duration: 0.6 }}
          >
            <span className="text-xs font-mono text-arcade-green uppercase tracking-widest font-semibold block mb-3">
              // Anti-Bypass Architecture
            </span>
            <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-8">
              Zero-Bypass Kernel Protection
            </h2>

            <div className="space-y-6">
              {[
                {
                  title: 'OS Credential Manager Key Protection',
                  desc: 'API keys are never hardcoded or bundled. Security credentials are dynamically fetched via Windows Credential Manager at runtime.'
                },
                {
                  title: 'Strict Family Isolation Rules',
                  desc: 'Firestore security rules strictly isolate family data and enforce token authorization to prevent cross-tenant access.'
                },
                {
                  title: 'Background Daemon Watchdog',
                  desc: 'A low-level background watchdog daemon monitors OS system events to block Task Manager, Alt+Tab, and process termination attempts.'
                }
              ].map((claim, idx) => (
                <div key={idx} className="flex items-start gap-4">
                  <div className="w-8 h-8 rounded-lg bg-arcade-green/15 border border-arcade-green/40 text-arcade-green flex items-center justify-center flex-shrink-0 mt-1 shadow-md">
                    <Check size={16} />
                  </div>
                  <div>
                    <h3 className="font-display text-base font-bold text-white mb-1">{claim.title}</h3>
                    <p className="text-white/90 text-xs sm:text-sm leading-relaxed">{claim.desc}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-8 text-xs text-white/70 font-mono">
              Review full security frameworks in our{' '}
              <button onClick={() => setShowPrivacyModal(true)} className="text-arcade-green hover:underline font-bold cursor-pointer">
                Privacy Policy
              </button>{' '}
              and{' '}
              <button onClick={() => setShowTermsModal(true)} className="text-arcade-green hover:underline font-bold cursor-pointer">
                Terms of Service
              </button>.
            </div>
          </motion.div>

          {/* Right Column: Live Terminal Log Texture Stream with .sg-card */}
          <motion.div 
            initial={{ opacity: 0, x: 24 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.1 }}
            transition={{ duration: 0.6 }}
            className="sg-card terminal-panel font-mono text-xs text-left shadow-2xl"
          >
            <HudReticles />

            <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
              <div className="flex items-center gap-2">
                <Terminal size={14} className="text-arcade-green" />
                <span className="text-white/70 font-bold uppercase text-[10px]">Daemon Log Texture Stream</span>
              </div>
              <span className="flex items-center gap-1.5 text-[10px] text-arcade-green font-bold">
                <span className="w-2 h-2 rounded-full bg-arcade-green animate-pulse" /> LIVE
              </span>
            </div>

            <div className="space-y-2 h-64 overflow-hidden text-arcade-green text-[11px]">
              {terminalLogs.map((log, idx) => (
                <div key={idx} className="border-l-2 border-arcade-green/40 pl-3.5 py-0.5 truncate">
                  {log}
                </div>
              ))}
            </div>
          </motion.div>

        </div>
      </section>

      {/* ── 5.6 SYSTEM QUERIES (PART B: FAQ ACCORDION ITEMS WITH .SG-CARD) ────── */}
      <section id="faq" className="relative z-10 py-24 px-6 bg-[#0B0F19]">
        <div className="max-w-4xl mx-auto">
          
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-mono text-arcade-green uppercase tracking-widest font-semibold block mb-3">
              // Parent Questions
            </span>
            <h2 className="font-display text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
              System Queries
            </h2>
          </div>

          <div className="space-y-4">
            {FAQ_ITEMS.map((item, idx) => {
              const isOpen = activeFaq === idx;
              return (
                <motion.div 
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.1 }}
                  transition={{ duration: 0.4, delay: idx * 0.08 }}
                  className="sg-card overflow-hidden shadow-xl transition-all duration-300"
                >
                  <HudReticles />
                  <button 
                    onClick={() => setActiveFaq(isOpen ? null : idx)}
                    className="w-full p-6 text-left flex items-center justify-between gap-4 cursor-pointer"
                  >
                    <span className="font-display text-base sm:text-lg font-bold text-white">{item.q}</span>
                    <motion.div 
                      animate={{ rotate: isOpen ? 180 : 0 }}
                      transition={{ duration: 0.25 }}
                      className="text-arcade-green flex-shrink-0"
                    >
                      <ChevronDown size={20} />
                    </motion.div>
                  </button>

                  <AnimatePresence>
                    {isOpen && (
                      <motion.div 
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.25 }}
                        className="overflow-hidden"
                      >
                        <div className="px-6 pb-6 pt-0 text-xs sm:text-sm text-white/90 leading-relaxed border-t border-white/10 mt-1 pt-4">
                          {item.a}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              );
            })}
          </div>

        </div>
      </section>

      {/* ── 5.7 FOOTER ────────────────────────────────────────────────── */}
      <footer className="relative z-10 border-t border-white/10 pt-16 pb-12 px-6 bg-[#070A10]">
        <div className="max-w-6xl mx-auto">

          <div className="grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">

            {/* Branding */}
            <div className="md:col-span-2 space-y-4">
              <div className="flex items-center gap-3">
                <SpellGateLogo size={32} />
                <span className="font-display text-lg font-extrabold tracking-widest uppercase text-arcade-green">
                  SpellGate
                </span>
              </div>
              <p className="text-white/70 text-xs leading-relaxed max-w-sm">
                An educational screen-time management system that gamifies spelling challenges to unlock PC access.
              </p>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-arcade-green/10 border border-arcade-green/30 text-arcade-green text-[10px] font-mono">
                <span className="w-2 h-2 rounded-full bg-arcade-green animate-ping" />
                All Systems Operational
              </div>
            </div>

            {/* Quick Links */}
            <div>
              <h4 className="font-mono text-xs font-bold text-white/50 uppercase tracking-widest mb-4">Navigation</h4>
              <ul className="space-y-2 text-xs">
                {NAV_LINKS.map(link => (
                  <li key={link.href}>
                    <a href={link.href} className="text-white/80 hover:text-arcade-green transition-colors">
                      {link.label}
                    </a>
                  </li>
                ))}
                <li>
                  <Link to={user ? "/dashboard" : "/login"} className="text-white/80 hover:text-arcade-green transition-colors">
                    Parent Dashboard
                  </Link>
                </li>
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h4 className="font-mono text-xs font-bold text-white/50 uppercase tracking-widest mb-4">Legal Framework</h4>
              <ul className="space-y-2 text-xs">
                <li>
                  <button onClick={() => setShowPrivacyModal(true)} className="text-white/80 hover:text-arcade-green transition-colors cursor-pointer text-left">
                    Privacy Policy
                  </button>
                </li>
                <li>
                  <button onClick={() => setShowTermsModal(true)} className="text-white/80 hover:text-arcade-green transition-colors cursor-pointer text-left">
                    Terms of Service
                  </button>
                </li>
              </ul>
            </div>

          </div>

          <div className="border-t border-white/10 pt-8 flex flex-wrap items-center justify-between gap-4 text-xs text-white/65 font-mono">
            <div>
              © {new Date().getFullYear()} SpellGate Security System. Open source GPLv3.
            </div>
            <div>
              Engineered by{' '}
              <a
                href="https://github.com/Hazy019"
                target="_blank"
                rel="noopener noreferrer"
                className="text-arcade-green hover:underline font-semibold"
              >
                Kyrell Santillan / Hazy019
              </a>
            </div>
          </div>

        </div>
      </footer>

      {/* Legal Modals */}
      <LegalModal isOpen={showPrivacyModal} onClose={() => setShowPrivacyModal(false)} title="Privacy Policy">
        <h4 className="font-bold text-white">Our Privacy Promise</h4>
        <p>
          We built SpellGate because we believe technology should help kids learn, not track them.
          We do not sell, rent, share, or monetize your or your child's data. Ever.
        </p>
        <h4 className="font-bold text-white pt-2">What We Collect & Sync</h4>
        <ul className="list-disc pl-5 space-y-1">
          <li>
            <strong>Spelling Progress</strong>: We log words spelled correctly, accuracy rates, and session durations to your isolated Firestore database.
          </li>
          <li>
            <strong>Time Bank State</strong>: We sync earned PC screen time allowance to lock/unlock the child client.
          </li>
        </ul>
        <h4 className="font-bold text-white pt-2">Local Kiosk Security</h4>
        <p>
          Keyboard hooks (Alt+Tab, Task Manager) run entirely on your local PC. No keystrokes are ever recorded or transmitted.
        </p>
      </LegalModal>

      <LegalModal isOpen={showTermsModal} onClose={() => setShowTermsModal(false)} title="Terms of Service">
        <h4 className="font-bold text-white">1. Parental Supervision</h4>
        <p>
          SpellGate is a parental control tool. You determine multipliers and manage override passcodes.
        </p>
        <h4 className="font-bold text-white pt-2">2. System Access</h4>
        <p>
          The Windows desktop client requires system-level hooks to block shortcuts and manage screen lock states.
        </p>
        <h4 className="font-bold text-white pt-2">3. Emergency Override</h4>
        <p>
          Parents can bypass lock screens anytime using Ctrl+Shift+P and their master passcode.
        </p>
      </LegalModal>

    </div>
  );
}
