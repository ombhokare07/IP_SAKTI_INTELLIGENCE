'use client';

import { type KeyboardEvent, useEffect, useState } from 'react';
import { CredentialResponse, GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';
import { BookOpen, CheckCircle2, Globe2, Languages, Leaf, LockKeyhole, Scale, ShieldAlert, ShieldCheck, Sparkles } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import DynamicIntelligenceVisual from '@/components/three/DynamicIntelligenceVisual';
import { API_BASE } from '@/services/api';
import { invalidateResource } from '@/services/resource-cache';

const capabilities = [
  [ShieldCheck, 'Patents'],
  [Leaf, 'Traditional Knowledge'],
  [Scale, 'Regulations'],
  [Sparkles, 'Responsible AI'],
  [Languages, 'Multilingual'],
  [BookOpen, 'Evidence Grounded'],
] as const;

export default function LoginPage() {
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [message, setMessage] = useState('');
  const [success, setSuccess] = useState('');
  const [signingIn, setSigningIn] = useState(false);
  const reduceMotion = useReducedMotion();
  const router = useRouter();
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  useEffect(() => {
    let active = true;
    fetch(`${API_BASE}/api/auth/me`, { credentials: 'include' })
      .then(async (response) => response.ok ? response.json() : { authenticated: false })
      .then((data) => { if (active && data?.authenticated) router.replace('/'); })
      .catch(() => undefined);
    return () => { active = false; };
  }, [router]);

  const selectMode = (next: 'signin' | 'signup') => {
    if (signingIn) return;
    setMode(next); setMessage(''); setSuccess('');
  };

  const navigateTabs = (event: KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      selectMode(mode === 'signin' ? 'signup' : 'signin');
      document.getElementById(mode === 'signin' ? 'signup-tab' : 'signin-tab')?.focus();
    }
  };

  const googleSuccess = async (credential: CredentialResponse) => {
    if (signingIn) return;
    if (!credential.credential) {
      setMessage('Google did not return a usable sign-in credential. Please try again.');
      return;
    }
    setSigningIn(true); setMessage(''); setSuccess('');
    try {
      const response = await fetch(`${API_BASE}/api/auth/google`, {
        method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: credential.credential, mode }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || 'Google sign-in could not be verified.');
      setSuccess(mode === 'signup' && data?.mode === 'signed_in'
        ? 'An account already exists. You are being signed in securely.'
        : data?.mode === 'account_created'
          ? 'Workspace account created. Opening your secure workspace…'
          : 'Identity verified. Opening your secure workspace…');
      invalidateResource('/auth/me');
      window.setTimeout(() => { router.replace('/'); router.refresh(); }, 280);
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'Google sign-in could not be verified.');
      setSigningIn(false);
    }
  };

  return <main className="login-page">
    <div className="login-aurora" aria-hidden="true"><i /><i /><i /></div>
    <motion.section className="login-story" initial={{ opacity: 0, x: -18 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: reduceMotion ? 0 : .42 }} aria-labelledby="login-story-title">
      <div className="login-story__brand"><span><Leaf size={22} /></span><div><strong>IP-SAKTI</strong><small>INTELLIGENCE</small></div></div>
      <div className="login-story__copy"><span className="eyebrow">AYUSH / RESPONSIBLE INTELLIGENCE</span><h1 id="login-story-title">Protect Innovation.<br /><em>Preserve Knowledge.</em></h1><p>Evidence-grounded IP &amp; Regulatory Intelligence for AYUSH Innovation</p></div>
      <div className="login-capabilities">{capabilities.map(([Icon, label]) => <span key={label}><Icon size={14} />{label}</span>)}</div>
      <div className="login-scene"><DynamicIntelligenceVisual /><div className="login-scene__legend"><span>Evidence nodes</span><span>Source-aware reasoning</span></div></div>
      <p className="login-story__quote">“Traditional wisdom deserves modern protection.”</p>
    </motion.section>

    <section className="login-auth-wrap">
      <motion.div className="login-card" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: reduceMotion ? 0 : .38, delay: reduceMotion ? 0 : .08 }} aria-labelledby="login-title">
        <div className="login-brand"><span><Leaf size={22} /></span><div><strong>IP-SAKTI</strong><small>Intelligence workspace</small></div></div>
        <div className="login-intro"><span><LockKeyhole size={13} /> SECURE WORKSPACE</span><h2 id="login-title">{mode === 'signin' ? 'Welcome back.' : 'Create your account.'}</h2><p>{mode === 'signin' ? 'Continue to your evidence-grounded IP and regulatory intelligence workspace.' : 'Start your evidence-grounded innovation journey with IP-SAKTI.'}</p></div>
        <div className="login-mode" role="tablist" aria-label="Account access mode">
          <button id="signin-tab" type="button" role="tab" aria-selected={mode === 'signin'} aria-controls="auth-panel" tabIndex={mode === 'signin' ? 0 : -1} disabled={signingIn} onKeyDown={navigateTabs} onClick={() => selectMode('signin')}>Sign In</button>
          <button id="signup-tab" type="button" role="tab" aria-selected={mode === 'signup'} aria-controls="auth-panel" tabIndex={mode === 'signup' ? 0 : -1} disabled={signingIn} onKeyDown={navigateTabs} onClick={() => selectMode('signup')}>Create Account</button>
        </div>
        <div id="auth-panel" role="tabpanel" aria-labelledby={mode === 'signin' ? 'signin-tab' : 'signup-tab'}>
          <div className="login-trust"><ShieldCheck size={18} /><div><strong>Google-verified access</strong><p>{mode === 'signin' ? 'Use the Google identity linked to your existing workspace.' : 'Your verified identity creates the local workspace account.'}</p></div></div>
          <div className={`login-google${signingIn ? ' busy' : ''}`} aria-busy={signingIn}>
            {googleClientId ? <GoogleOAuthProvider clientId={googleClientId}><GoogleLogin text="continue_with" onSuccess={googleSuccess} onError={() => !signingIn && setMessage('Google sign-in could not be started.')} useOneTap={false} /></GoogleOAuthProvider> : <p><ShieldAlert size={16} /> Google sign-in is not configured. Set <code>NEXT_PUBLIC_GOOGLE_CLIENT_ID</code>.</p>}
            {signingIn && !success && <small>Verifying your Google identity…</small>}
          </div>
          {success && <p className="login-success" role="status"><CheckCircle2 size={17} />{success}</p>}
          {message && <p className="login-message" role="alert"><ShieldAlert size={16} />{message}</p>}
        </div>
        <div className="login-disclaimer"><LockKeyhole size={15} /><p>Google verification is exchanged for a secure HttpOnly application session. IP-SAKTI does not store your Google password.</p></div>
        <p className="login-principle"><Globe2 size={14} /> Evidence before assertion. Human review remains essential.</p>
      </motion.div>
    </section>
  </main>;
}
