import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity, Settings, User, LogOut, Clock, Award, AlertCircle,
  Save, Wifi, WifiOff, Link2, Unlock, RefreshCw, CheckCircle,
  Eye, EyeOff, Key, ShieldCheck, Laptop, Cpu, ShieldAlert, MonitorPlay,
  Sun, Moon, Brain, Menu, X, Mail
} from 'lucide-react';
import {
  doc, onSnapshot, updateDoc, serverTimestamp, setDoc, deleteDoc
} from 'firebase/firestore';
import { db } from './firebase';
import { useAuth } from './AuthContext';
import { useTheme } from './ThemeContext';

/* ─── StatCard Sub-Component ─────────────────────────────── */
const COLOR_MAP = {
  'cyber-blue':   { text: 'var(--neon)',    bg: 'rgba(0,229,255,0.08)',    border: 'rgba(0,229,255,0.18)' },
  'cyber-purple': { text: '#a78bfa',        bg: 'rgba(167,139,250,0.08)',   border: 'rgba(167,139,250,0.18)' },
  'cyber-pink':   { text: 'var(--crimson)', bg: 'rgba(255,56,100,0.08)',   border: 'rgba(255,56,100,0.18)' },
};
function StatCard({ icon, color, label, value, sub }) {
  const c = COLOR_MAP[color] ?? COLOR_MAP['cyber-blue'];
  return (
    <div
      className="flex items-start gap-3.5 p-4 rounded-2xl transition-all duration-300 group hover:scale-[1.01]"
      style={{ background: c.bg, border: `1px solid ${c.border}` }}
    >
      <div
        className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5"
        style={{ background: 'rgba(255,255,255,0.06)', color: c.text }}
      >
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-[0.625rem] font-bold uppercase tracking-widest mb-1" style={{ color: 'var(--text-dim)' }}>{label}</p>
        <p className="text-xl font-bold font-mono leading-none mb-1" style={{ color: c.text }}>{value}</p>
        <p className="text-[0.625rem] font-medium" style={{ color: 'var(--text-muted)', opacity: 0.7 }}>{sub}</p>
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

export default function Dashboard() {
  const { user, logout, resendVerification } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const uid = user?.uid;

  const [activeTab, setActiveTab]       = useState('analytics');
  const [sidebarOpen, setSidebarOpen]   = useState(false);
  const [multiplier, setMultiplier]     = useState(10);
  const [saveStatus, setSaveStatus]     = useState('idle'); // idle | saving | saved
  const [progressData, setProgressData] = useState(null);
  const [settingsData, setSettingsData] = useState(null);
  const [deviceData, setDeviceData]     = useState(null);
  const [isLive, setIsLive]             = useState(false);

  // ── PIN management state ────────────────────────────────────
  const [currentPin, setCurrentPin]       = useState('');
  const [newPin, setNewPin]               = useState('');
  const [confirmPin, setConfirmPin]       = useState('');
  const [pinVisible, setPinVisible]       = useState(false);
  const [pinSaveStatus, setPinSaveStatus] = useState('idle'); // idle | saving | saved | error
  const [pinError, setPinError]           = useState('');

  // ── Device pairing state ────────────────────────────────────
  const [pairingCode, setPairingCode]       = useState('');
  const [pairingLoading, setPairingLoading] = useState(false);
  const [pairedDeviceStatus, setPairedDeviceStatus] = useState('unpaired'); // unpaired | pairing | paired

  // ── Live listener: child progress ──────────────────────────
  useEffect(() => {
    if (!uid) return;
    const ref = doc(db, 'users', uid, 'child_data', 'progress');
    const unsub = onSnapshot(
      ref,
      (snap) => {
        setIsLive(true);
        if (snap.exists()) setProgressData(snap.data());
      },
      () => setIsLive(false)
    );
    return unsub;
  }, [uid]);

  // ── Live listener: settings (also loads PIN) ───────────────
  useEffect(() => {
    if (!uid) return;
    const ref = doc(db, 'users', uid, 'child_data', 'settings');
    const unsub = onSnapshot(ref, (snap) => {
      if (snap.exists()) {
        const data = snap.data();
        setSettingsData(data);
        setMultiplier(data.reward_multiplier ?? 10);
        setCurrentPin(data.parent_pin ?? '');
      }
    });
    return unsub;
  }, [uid]);

  // ── Live listener: device info ──────────────────────────────
  useEffect(() => {
    if (!uid) return;
    const ref = doc(db, 'users', uid, 'child_data', 'device');
    const unsub = onSnapshot(ref, (snap) => {
      if (snap.exists()) setDeviceData(snap.data());
    });
    return unsub;
  }, [uid]);

  // ── Save reward multiplier to Firestore ─────────────────────
  async function handleSaveSettings() {
    if (!uid) return;
    setSaveStatus('saving');
    try {
      await updateDoc(doc(db, 'users', uid, 'child_data', 'settings'), {
        reward_multiplier: multiplier,
        updated_at: serverTimestamp(),
      });
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 3000);
    } catch (e) {
      console.error(e);
      setSaveStatus('idle');
    }
  }

  // ── Force Unlock the child's PC remotely ────────────────────
  async function handleForceUnlock() {
    if (!uid) return;
    try {
      await updateDoc(doc(db, 'users', uid, 'child_data', 'settings'), {
        force_unlock: true,
      });
    } catch (e) {
      console.error("Force unlock failed:", e);
    }
  }

  // ── Save / change parent PIN ────────────────────────────────
  async function handleSavePin() {
    setPinError('');
    if (!newPin || newPin.length < 4) {
      setPinError('PIN must be at least 4 digits.');
      return;
    }
    if (newPin !== confirmPin) {
      setPinError('PINs do not match. Please try again.');
      return;
    }
    if (!/^\d+$/.test(newPin)) {
      setPinError('PIN must contain numbers only.');
      return;
    }
    setPinSaveStatus('saving');
    try {
      await updateDoc(doc(db, 'users', uid, 'child_data', 'settings'), {
        parent_pin: newPin,
      });
      setPinSaveStatus('saved');
      setNewPin('');
      setConfirmPin('');
      setTimeout(() => setPinSaveStatus('idle'), 3000);
    } catch (e) {
      console.error(e);
      setPinSaveStatus('error');
      setPinError('Failed to save PIN. Please try again.');
    }
  }

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  // ── Generate pairing code and listen for device intake ──────────
  async function handleGeneratePairingCode() {
    if (!uid) return;
    setPairingLoading(true);
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    setPairingCode(code);
    setPairedDeviceStatus('pairing');
    
    try {
      await setDoc(doc(db, 'pairing_codes', code), {
        parent_uid: uid,
        device_uid: '',
        created_at: serverTimestamp()
      });
      
      const unsub = onSnapshot(doc(db, 'pairing_codes', code), async (snap) => {
        if (snap.exists()) {
          const data = snap.data();
          if (data.device_uid) {
            // Child paired anonymously
            await updateDoc(doc(db, 'users', uid, 'child_data', 'settings'), {
              paired_device_uid: data.device_uid
            });
            await deleteDoc(doc(db, 'pairing_codes', code));
            setPairedDeviceStatus('paired');
            setPairingCode('');
            unsub();
          }
        }
      });
      
      // Auto-cleanup after 5 minutes
      setTimeout(async () => {
        try {
          unsub();
          await deleteDoc(doc(db, 'pairing_codes', code));
          setPairingCode('');
          setPairedDeviceStatus('unpaired');
        } catch (e) {}
      }, 300000);
      
    } catch (e) {
      console.error("Pairing code generation failed:", e);
      setPairedDeviceStatus('unpaired');
    } finally {
      setPairingLoading(false);
    }
  }

  // ── Derived stats from live data ────────────────────────────
  const sessions       = progressData?.sessions ?? [];
  const lastSession    = sessions[sessions.length - 1] ?? null;
  const masteredCount  = progressData?.mastered_words?.length ?? 0;
  const currentLevel   = progressData?.current_level ?? 'Novice';
  const struggleWords  = lastSession?.struggle_words ?? [];
  const accuracy       = lastSession?.accuracy ?? 0;
  const timeEarned     = lastSession?.time_earned_seconds ?? 0;

  // New analytics derivations
  const avgAccuracy = sessions.length 
    ? Math.round(sessions.reduce((acc, s) => acc + s.accuracy, 0) / sessions.length) 
    : 0;
  const accuracyDelta = sessions.length > 1 ? accuracy - avgAccuracy : 0;

  // Calculate online status (heartbeat active in last 3 minutes)
  const lastHeartbeat = deviceData?.last_heartbeat?.toDate() ?? null;
  const isDeviceOnline = lastHeartbeat && (new Date() - lastHeartbeat) < 180000;

  // If email verification is required by security rules, block dashboard access until verified
  if (user && !user.emailVerified) {
    return (
      <div className="min-h-screen bg-ink text-text-primary font-sans flex flex-col items-center justify-center p-6 relative overflow-hidden">
        {/* Subtle matrix background */}
        <div 
          className="absolute inset-0 pointer-events-none opacity-[0.03] z-0" 
          style={{ background: 'radial-gradient(rgba(255,255,255,0.8) 1px, transparent 1px) 0 0 / 24px 24px' }}
        />
        
        <div className="relative z-10 w-full max-w-md glass-hi rounded-2xl p-8 border border-white/5 text-center flex flex-col gap-6">
          <div className="w-16 h-16 rounded-2xl bg-cyber-purple/10 border border-cyber-purple/20 text-cyber-purple flex items-center justify-center mx-auto">
            <Mail className="w-8 h-8" />
          </div>
          
          <div>
            <h1 className="text-xl font-bold font-display tracking-tight text-white mb-2">Verify Your Email</h1>
            <p className="text-xs text-text-muted leading-relaxed">
              To secure your child's remote administration controls, we require a verified email address. 
              We've sent a verification link to:
            </p>
            <p className="text-xs font-semibold text-neon font-mono mt-1">{user.email}</p>
          </div>
          
          {pinSaveStatus === 'sending' && (
            <p className="text-xs text-mint">Verification link sent! Check your inbox.</p>
          )}
          {pinError && (
            <p className="text-xs text-crimson">{pinError}</p>
          )}

          <div className="flex flex-col gap-3">
            <button 
              onClick={async () => {
                setPinError('');
                setPinSaveStatus('idle');
                try {
                  await resendVerification();
                  setPinSaveStatus('sending');
                } catch (e) {
                  setPinError('Failed to send verification email. Try again shortly.');
                }
              }}
              className="btn-primary w-full py-2.5"
            >
              Resend Verification Link
            </button>
            
            <button 
              onClick={async () => {
                setPinError('');
                try {
                  // Reload the user profile from Firebase auth backend
                  await auth.currentUser.reload();
                  // Force React state update by reloading
                  window.location.reload(); 
                } catch (e) {
                  setPinError('Failed to refresh status. Try again.');
                }
              }}
              className="btn-ghost w-full py-2.5"
            >
              I have verified my email (Reload)
            </button>
          </div>
          
          <button 
            onClick={handleLogout}
            className="text-xs text-text-muted hover:text-white underline transition-colors"
          >
            Back to Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-ink text-text-primary font-sans flex flex-col md:flex-row relative overflow-hidden">
      
      {/* Visual Rhyming: Subtle dot-matrix background grid */}
      <div 
        className="absolute inset-0 pointer-events-none opacity-[0.03] z-0" 
        style={{ background: 'radial-gradient(rgba(255,255,255,0.8) 1px, transparent 1px) 0 0 / 24px 24px' }}
      />

      {/* Mobile Topbar */}
      <div className="md:hidden flex items-center justify-between px-4 py-3 glass-hi border-b border-white/5 z-30 relative">
        <div className="flex items-center gap-2">
          <SpellGateLogo size={28} />
          <span className="font-display text-sm font-bold tracking-widest uppercase text-brand">SpellGate</span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={toggleTheme} className="p-1.5 rounded-lg bg-white/5 text-text-muted" aria-label="Toggle theme">
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber" /> : <Moon className="w-4 h-4 text-neon" />}
          </button>
          <button onClick={() => setSidebarOpen(o => !o)} className="p-1.5 rounded-lg bg-white/5 text-text-muted" aria-label="Toggle sidebar">
            {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Sidebar Overlay (mobile) */}
      {sidebarOpen && (
        <div className="md:hidden fixed inset-0 z-20 bg-black/60 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
      )}

      {/* ── Sidebar ── */}
      <aside className={`
        fixed md:relative inset-y-0 left-0 z-20
        w-64 glass-hi border-r border-white/5 flex flex-col
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <div className="p-6 border-b border-white/5 flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <SpellGateLogo size={32} />
            <h2 className="text-lg font-bold tracking-widest font-display text-brand">
              SPELLGATE
            </h2>
          </div>
          <p className="text-[0.6875rem] font-semibold text-text-muted tracking-wider uppercase opacity-60">Parent Administration</p>

          {/* Sync status badge */}
          <div className={`mt-3 self-start inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
            isLive ? 'bg-mint/10 text-mint border border-mint/20'
                   : 'bg-white/5 text-text-muted border border-white/10'
          }`}>
            {isLive ? <Wifi className="w-3 h-3 animate-pulse" /> : <WifiOff className="w-3 h-3" />}
            {isLive ? 'Link Active' : 'Offline'}
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {[
            { id: 'analytics', label: 'Dashboard Activity', Icon: Activity  },
            { id: 'settings',  label: 'Control Settings',   Icon: Settings  },
          ].map(({ id, label, Icon }) => (
            <button
              key={id}
              onClick={() => { setActiveTab(id); setSidebarOpen(false); }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 text-left font-medium text-sm ${
                activeTab === id
                  ? 'bg-neon/10 text-neon'
                  : 'text-text-muted hover:bg-white/5 hover:text-text-primary'
              }`}
              style={activeTab === id ? { borderLeft: '3px solid var(--neon)' } : { borderLeft: '3px solid transparent' }}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-white/5">
          <div className="flex items-center justify-between mb-4 px-2">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center border border-white/10">
                <User className="w-5 h-5 text-neon" />
              </div>
              <div className="overflow-hidden">
                <p className="text-sm font-semibold truncate text-text-primary">Parent Portal</p>
                <p className="text-[0.6875rem] text-text-muted truncate opacity-70">{user?.email}</p>
              </div>
            </div>
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg bg-white/5 hover:bg-white/10 text-text-muted transition-colors press-effect"
              aria-label="Toggle Theme"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber" /> : <Moon className="w-4 h-4 text-neon" />}
            </button>
          </div>
          <button
            onClick={handleLogout}
            className="btn-danger w-full flex items-center justify-center gap-2 text-xs py-2.5"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* ── Main Content Area ── */}
      <main className="flex-1 min-w-0 p-4 md:p-6 lg:p-8 overflow-y-auto overflow-x-hidden relative z-10">
        <div className="absolute top-0 right-0 w-[400px] h-[400px] bg-radial-gradient(circle, rgba(139,92,246,0.04) 0%, transparent 70%) pointer-events-none" />

        {/* ── Dashboard Analytics Tab ── */}
        {activeTab === 'analytics' && (
          <div className="flex flex-col gap-4 animate-slide-up">
            
            {/* Top row: Title & Quick Stats */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2.5 flex-shrink-0">
              <div>
                <h1 className="text-2xl font-bold text-text-primary tracking-tight font-display">Dashboard Activity</h1>
                <p className="text-text-muted text-xs">Monitor child's real-time accuracy and game interactions.</p>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyber-purple/10 border border-cyber-purple/20 text-cyber-purple text-[0.6875rem] font-bold uppercase tracking-wider">
                  <Award className="w-3.5 h-3.5" />
                  Grade Level: <span className="text-text-primary ml-0.5">{currentLevel}</span>
                </div>
              </div>
            </div>

            {/* Bento Grid Body */}
            <div className="grid grid-cols-1 xl:grid-cols-4 gap-4 items-start">
              
              {/* Column 1 & 2 & 3: Spelling stats and curves (3/4 width) */}
              <div className="xl:col-span-3 flex flex-col gap-4">
                
                {/* Stats row */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 flex-shrink-0">
                  <StatCard 
                    icon={<Award className="w-4 h-4" />} 
                    color="cyber-blue" 
                    label="Mastered Words" 
                    value={masteredCount} 
                    sub="Cumulative database bank" 
                  />
                  <StatCard 
                    icon={<Activity className="w-4 h-4" />} 
                    color="cyber-purple" 
                    label="Session Accuracy" 
                    value={`${accuracy}%`} 
                    sub="Last practice rate" 
                  />
                  <StatCard 
                    icon={<Clock className="w-4 h-4" />} 
                    color="cyber-pink" 
                    label="Time Bank Earned"
                    value={`${Math.floor(timeEarned / 60)}m ${timeEarned % 60}s`} 
                    sub="Earned during last check" 
                  />
                </div>

                {/* Study baseline curve & Gemini Insights row */}
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                  
                  {/* Left curve (3/5 width) */}
                  <div className="md:col-span-3 glass rounded-2xl p-5 border border-white/5 flex flex-col justify-between">
                    <div className="flex-shrink-0">
                      <h3 className="text-xs font-bold text-text-primary uppercase tracking-wider mb-3 flex items-center gap-1.5">
                        <Activity className="w-4 h-4 text-cyber-purple" /> Spelling Curve
                      </h3>
                      <div className="grid grid-cols-2 gap-3 bg-ink/30 border border-white/5 p-3 rounded-lg text-[0.6875rem]">
                        <div>
                          <span className="text-text-dim block">Lifetime Average:</span>
                          <span className="font-mono font-bold text-text-primary text-sm mt-0.5">{avgAccuracy}%</span>
                        </div>
                        <div>
                          <span className="text-text-dim block">Deviation:</span>
                          <span className={`font-mono font-bold text-sm mt-0.5 ${accuracyDelta >= 0 ? 'text-mint' : 'text-red-400'}`}>
                            {accuracyDelta >= 0 ? `+${accuracyDelta}%` : `${accuracyDelta}%`}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* SVG Curve or bar elements */}
                    {sessions.length > 0 ? (
                      <div className="flex-1 flex items-end gap-1.5 h-full min-h-0 pt-3 relative overflow-hidden">
                        {sessions.slice(-7).map((s, idx) => (
                          <div key={idx} className="flex-1 flex flex-col justify-end h-full group/bar relative min-h-0">
                            <div 
                              className={`w-full rounded-t-[2px] transition-all duration-300 ${
                                s.accuracy >= 90 ? 'bg-mint animate-pulse' : s.accuracy >= 70 ? 'bg-neon' : 'bg-cyber-pink'
                              }`} 
                              style={{ height: `${s.accuracy}%`, opacity: idx === sessions.slice(-7).length - 1 ? 1 : 0.4 }} 
                            />
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-1 py-0.5 rounded bg-black/80 text-[0.5625rem] text-white font-mono opacity-0 group-hover/bar:opacity-100 transition-opacity pointer-events-none">
                              {s.accuracy}%
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-text-dim text-xs py-6">No historical sessions to chart.</p>
                    )}
                  </div>

                  {/* Right Gemini Advisor (2/5 width) */}
                  <div className="md:col-span-2 glass rounded-2xl p-5 border border-neon/15 bg-neon/5 flex flex-col justify-between">
                    <div className="flex-shrink-0 flex items-center gap-1.5 mb-2 pb-2 border-b border-neon/10">
                      <Brain className="w-3.5 h-3.5 text-neon" />
                      <span className="text-[0.625rem] font-bold text-neon uppercase tracking-wider font-mono">Gemini Advisor</span>
                    </div>
                    <div className="flex-1 overflow-y-auto pr-1 text-[0.725rem] text-text-muted leading-relaxed max-h-[140px] scrollbar-thin">
                      {sessions.length === 0 ? (
                        "Waiting for completed spelling sessions to compile diagnostics."
                      ) : accuracy >= 90 ? (
                        "Outstanding achievement! Learner demonstrates fluent spelling structures. Suggesting level promotion or multiplier increase."
                      ) : accuracy >= 70 ? (
                        "Healthy study progression. Monitor struggle words list regularly to reinforce correct letter pairings."
                      ) : (
                        "Child is experiencing blocks on recent tests. System recommends lowering playground exchange rates to prolong local study durations."
                      )}
                    </div>
                    <div className="flex-shrink-0 text-[0.5625rem] text-text-dim uppercase tracking-wider font-bold mt-2 pt-2 border-t border-neon/10 flex justify-between">
                      <span>Study Target</span>
                      <span className="text-neon">Grade 4 Level II</span>
                    </div>
                  </div>
                </div>
                {/* Bottom Row: Struggle Words & Session Logs (Side by Side Bento) */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  
                  {/* Struggle words */}
                  <div className="glass rounded-2xl p-4 border border-white/5 flex flex-col min-h-[120px]">
                    <span className="text-[0.625rem] font-bold text-text-dim uppercase tracking-wider mb-2 block">Struggle Words</span>
                    <div className="flex-1 overflow-y-auto pr-1 text-left">
                      {struggleWords.length > 0 ? (
                        <div className="flex flex-wrap gap-1.5">
                          {struggleWords.map((word, i) => (
                            <span key={i} className="font-mono text-[0.6875rem] text-text-primary px-2 py-0.5 rounded bg-white/5 border border-white/10 hover-amber transition-all">
                              {word}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <p className="text-text-dim text-[0.6875rem] leading-relaxed">
                          {progressData ? 'All words spelled correctly. Outstanding job!' : 'Waiting for completed sessions.'}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Recent sessions */}
                  <div className="glass rounded-2xl p-4 border border-white/5 flex flex-col min-h-[120px]">
                    <span className="text-[0.625rem] font-bold text-text-dim uppercase tracking-wider mb-2 block">Recent Session Logs</span>
                    <div className="flex-1 overflow-y-auto space-y-1.5 pr-1 text-left">
                      {sessions.length > 0 ? (
                        [...sessions].reverse().slice(0, 3).map((s, i) => (
                          <div key={i} className="flex justify-between bg-ink/30 border border-white/5 rounded px-2.5 py-1 text-[0.6875rem]">
                            <span className="text-text-muted">{s.date ?? `Session ${sessions.length - i}`}</span>
                            <span className="text-neon font-bold">{s.accuracy}% accuracy</span>
                            <span className="text-mint font-semibold bg-mint/5 border border-mint/10 px-1.5 py-0.25 rounded">{Math.floor((s.time_earned_seconds ?? 0) / 60)}m</span>
                          </div>
                        ))
                      ) : (
                        <p className="text-text-dim text-[0.6875rem]">No logs recorded yet.</p>
                      )}
                    </div>
                  </div>

                </div>

              </div>

              {/* Column 4: System Kiosk Monitor (1/4 width) */}
              <div className="xl:col-span-1 flex flex-col">
                <div className="glass rounded-2xl border border-neon/10 p-5 flex flex-col justify-between relative overflow-hidden group hover:border-neon/20 transition-all duration-300">
                  <div className="absolute top-0 right-0 w-44 h-44 bg-radial-gradient(circle, rgba(0,229,255,0.03) 0%, transparent 70%)" />
                  
                  {/* Header */}
                  <div className="flex-shrink-0 flex items-center justify-between pb-4 border-b border-white/5">
                    <div className="flex items-center gap-2">
                      <Laptop className="w-4.5 h-4.5 text-neon" />
                      <h2 className="text-xs font-bold tracking-tight text-text-primary font-display">Kiosk Status</h2>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className={`w-2.5 h-2.5 rounded-full ${
                        isDeviceOnline ? 'bg-mint animate-pulse shadow-[0_0_12px_rgba(61,255,160,0.8)]' : 'bg-text-dim'
                      }`} />
                      <span className="text-[0.625rem] font-bold uppercase tracking-wider text-text-muted">
                        {isDeviceOnline ? 'Connected' : 'Offline'}
                      </span>
                    </div>
                  </div>

                  {/* Laptop Mockup */}
                  <div className="flex-1 min-h-0 py-4 flex flex-col justify-center">
                    <div className="w-full bg-ink/80 rounded-lg border border-white/5 p-3 flex flex-col items-center justify-center gap-2 py-4 relative">
                      <div className="w-14 h-10 rounded border border-neon/20 flex items-center justify-center bg-neon/5 relative">
                        <Cpu className={`w-5 h-5 text-neon ${isDeviceOnline ? 'animate-pulse' : 'opacity-40'}`} />
                        <div className="absolute -bottom-1.5 w-6 h-1 bg-white/20 rounded" />
                      </div>
                      <div className="text-center overflow-hidden w-full">
                        <p className="text-xs font-bold tracking-wide text-text-primary truncate px-2">
                          {deviceData?.hostname ?? 'NO PAIRING'}
                        </p>
                        <p className="text-[0.5625rem] text-text-muted font-mono opacity-50">
                          {deviceData?.os_version ? `Win ${deviceData.os_version.split('.')[0]}` : 'Disconnected'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Details metadata */}
                  <div className="flex-shrink-0 space-y-2.5 text-[0.6875rem] border-b border-white/5 pb-4 mb-4">
                    <div className="flex justify-between">
                      <span className="text-text-muted">App Version:</span>
                      <span className="font-mono text-text-primary font-medium">{deviceData?.app_version ?? '--'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Install Date:</span>
                      <span className="text-text-primary font-medium">
                        {deviceData?.install_date ? new Date(deviceData.install_date).toLocaleDateString() : '--'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-muted">Last Ping:</span>
                      <span className="text-text-primary font-medium">
                        {lastHeartbeat ? lastHeartbeat.toLocaleTimeString() : 'Never'}
                      </span>
                    </div>
                  </div>

                  {/* Remote Action */}
                  <div className="flex-shrink-0 space-y-2">
                    <button
                      onClick={handleForceUnlock}
                      disabled={!isDeviceOnline}
                      className="w-full flex items-center justify-center gap-1.5 py-2.5 bg-red-500/10 border border-red-500/20 text-red-400 font-bold text-xs rounded-lg hover:bg-red-500/20 hover:border-red-500/40 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      <Unlock className="w-3.5 h-3.5" />
                      Force Unlock PC
                    </button>
                    <p className="text-[0.5625rem] text-text-dim text-center">
                      {!isDeviceOnline ? '⚠️ PC Offline' : 'Immediate remote override command.'}
                    </p>
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* ── Settings Tab ── */}
        {activeTab === 'settings' && (
          <div className="max-w-5xl space-y-6 animate-slide-up">
            <header>
              <h1 className="text-3xl font-bold text-text-primary tracking-tight font-display">System Controls</h1>
              <p className="text-text-muted text-sm mt-1">Configure screen time rates and override passcodes.</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch">
              
              {/* Left Column: Exchange rate rules */}
              <div className="glass rounded-xl p-6 border border-white/5 flex flex-col justify-between h-full">
                <div>
                  <h2 className="text-lg font-bold text-text-primary mb-2 flex items-center gap-2">
                    <Clock className="w-5 h-5 text-neon" />
                    Playtime Exchange Rate
                  </h2>
                  <p className="text-text-muted text-xs mb-5">
                    Specify the exact amount of computer access time awarded for every correct spelling response.
                  </p>

                  <div className="bg-ink/40 border border-white/5 rounded-xl p-5 mb-5">
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mb-5">
                      <div className="flex flex-col items-center bg-white/5 px-4 py-3 rounded-lg border border-white/10 w-full sm:w-[45%]">
                        <span className="text-3xl font-mono font-bold text-neon mb-0.5">1</span>
                        <span className="text-[0.625rem] text-text-muted uppercase tracking-wider font-semibold opacity-70">Correct Word</span>
                      </div>
                      <div className="text-sm text-text-dim font-bold font-mono">=</div>
                      <div className="flex flex-col items-center bg-neon/5 px-4 py-3 rounded-lg border border-neon/20 w-full sm:w-[45%]">
                        <span className="text-3xl font-mono font-bold text-neon mb-0.5">{multiplier}s</span>
                        <span className="text-[0.625rem] text-neon/80 uppercase tracking-wider font-semibold">Screen Time</span>
                      </div>
                    </div>

                    <input
                      type="range" min="5" max="60" step="5"
                      value={multiplier}
                      onChange={(e) => setMultiplier(parseInt(e.target.value))}
                      className="w-full accent-neon"
                    />
                    <div className="flex justify-between mt-2.5 text-[0.6875rem] font-semibold text-text-dim">
                      <span className="cursor-pointer hover:text-text-primary" onClick={() => setMultiplier(5)}>5s (Strict)</span>
                      <span className="cursor-pointer hover:text-text-primary" onClick={() => setMultiplier(30)}>30s (Balanced)</span>
                      <span className="cursor-pointer hover:text-text-primary" onClick={() => setMultiplier(60)}>60s (Generous)</span>
                    </div>
                  </div>

                  <div className="flex items-start gap-2.5 p-3.5 bg-neon/5 border border-neon/15 rounded-lg mb-5">
                    <Activity className="w-4 h-4 text-neon flex-shrink-0 mt-0.5" />
                    <p className="text-text-muted text-[0.6875rem] leading-relaxed">
                      Calculated projection: completing a standard <strong>10-word</strong> session will award exactly{' '}
                      <strong>{Math.floor((10 * multiplier) / 60)}m{' '}
                      {(10 * multiplier) % 60 > 0 ? `${(10 * multiplier) % 60}s` : ''}</strong> of computer time.
                    </p>
                  </div>
                </div>

                <button
                  onClick={handleSaveSettings}
                  disabled={saveStatus === 'saving'}
                  className="btn-primary press-effect w-full py-2.5 text-xs font-bold"
                >
                  {saveStatus === 'saving' ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                  {saveStatus === 'saved' ? 'Settings Saved!' : saveStatus === 'saving' ? 'Saving…' : 'Save Rules'}
                </button>
              </div>

              {/* Right Column: PIN configuration */}
              <div className="glass rounded-xl p-6 border border-white/5 flex flex-col justify-between h-full">
                <div>
                  <h2 className="text-lg font-bold text-text-primary mb-2 flex items-center gap-2">
                    <Key className="w-5 h-5 text-cyber-purple" />
                    Emergency Override PIN
                  </h2>
                  <p className="text-text-muted text-xs mb-5">
                    Required to exit Kiosk Lock mode on your child's PC via <strong>Ctrl+Shift+P</strong>. Keep it confidential.
                  </p>

                  {currentPin && (
                    <div className="bg-ink/40 border border-white/5 rounded-xl p-4 mb-5">
                      <p className="text-[0.625rem] text-text-dim uppercase tracking-widest mb-2 font-bold flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3 text-cyber-purple" /> Active Lock Passcode
                      </p>
                      <div className="flex items-center gap-3">
                        <span className="text-2xl font-mono font-black tracking-[0.25em] text-cyber-purple">
                          {pinVisible ? currentPin : '•'.repeat(currentPin.length)}
                        </span>
                        <button
                          onClick={() => setPinVisible(v => !v)}
                          className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-text-muted"
                        >
                          {pinVisible ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </div>
                  )}

                  <div className="space-y-3.5">
                    <div className="field-group">
                      <label className="text-[0.6875rem]">New 4-8 Digit PIN</label>
                      <input
                        type="password"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        value={newPin}
                        onChange={e => { setNewPin(e.target.value); setPinError(''); }}
                        placeholder="Enter numbers only"
                        className="input-base font-mono tracking-widest text-sm py-2 px-3"
                      />
                    </div>
                    <div className="field-group">
                      <label className="text-[0.6875rem]">Confirm New PIN</label>
                      <input
                        type="password"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        value={confirmPin}
                        onChange={e => { setConfirmPin(e.target.value); setPinError(''); }}
                        placeholder="Re-enter PIN"
                        className="input-base font-mono tracking-widest text-sm py-2 px-3"
                      />
                    </div>

                    {pinError && (
                      <p className="text-red-400 text-xs flex items-center gap-1 font-medium">
                        <AlertCircle className="w-3.5 h-3.5" /> {pinError}
                      </p>
                    )}
                  </div>
                </div>

                <button
                  onClick={handleSavePin}
                  disabled={pinSaveStatus === 'saving'}
                  className="btn-primary press-effect w-full py-2.5 text-xs font-bold bg-gradient-to-r from-cyber-purple to-neon text-white border-none shadow-sm mt-5"
                >
                  {pinSaveStatus === 'saving' && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  {pinSaveStatus === 'saved' ? 'PIN Configured!' : pinSaveStatus === 'saving' ? 'Processing…' : 'Set Override PIN'}
                </button>
              </div>

              {/* Secure Device Pairing Widget */}
              <div className="glass rounded-xl p-6 border border-white/5 flex flex-col md:flex-row items-center justify-between gap-6 col-span-1 lg:col-span-2">
                <div className="space-y-1.5 md:max-w-xl text-left">
                  <h2 className="text-lg font-bold text-text-primary flex items-center gap-2">
                    <Link2 className="w-5 h-5 text-neon" />
                    Device Pairing
                  </h2>
                  <p className="text-text-muted text-xs leading-relaxed">
                    Pair your child's PC client with this parent dashboard securely. 
                    This registers the child's PC client as an authorized companion device without exposing your account password.
                  </p>
                </div>
                
                <div className="flex-shrink-0 bg-ink/40 border border-white/5 rounded-xl p-5 min-w-[280px] text-center flex flex-col items-center justify-center">
                  {settingsData?.paired_device_uid ? (
                    <div className="space-y-3">
                      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-mint/10 border border-mint/20 text-mint text-xs font-bold uppercase tracking-wider">
                        <CheckCircle className="w-3.5 h-3.5" /> Paired Successfully
                      </div>
                      <p className="text-[0.625rem] text-text-dim uppercase tracking-wider font-semibold">
                        Device UID: {settingsData.paired_device_uid.slice(0, 12)}...
                      </p>
                      <button
                        onClick={async () => {
                          if (window.confirm("Are you sure you want to unpair this child device? The child's PC client will be locked out until re-paired.")) {
                            await updateDoc(doc(db, 'users', uid, 'child_data', 'settings'), {
                              paired_device_uid: null
                            });
                          }
                        }}
                        className="text-[0.6875rem] text-red-400 font-bold hover:underline cursor-pointer"
                      >
                        Unpair Device
                      </button>
                    </div>
                  ) : pairingCode ? (
                    <div className="space-y-2">
                      <p className="text-[0.625rem] text-neon uppercase tracking-wider font-bold animate-pulse">Pairing Code Active</p>
                      <span className="text-3xl font-mono font-black tracking-[0.25em] text-neon block">{pairingCode}</span>
                      <p className="text-[0.5625rem] text-text-muted leading-normal">
                        Enter this code on the child's PC client within 5 minutes.
                      </p>
                    </div>
                  ) : (
                    <button
                      onClick={handleGeneratePairingCode}
                      disabled={pairingLoading}
                      className="btn-primary press-effect w-full py-2.5 text-xs font-bold bg-gradient-to-r from-neon to-cyber-purple text-ink border-none shadow-sm cursor-pointer"
                    >
                      {pairingLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Link2 className="w-3.5 h-3.5" />}
                      Generate Pairing Code
                    </button>
                  )}
                </div>
              </div>

            </div>
          </div>
        )}
      </main>
    </div>
  );
}


