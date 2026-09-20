'use client';

import { FormEvent, useEffect, useState } from 'react';
import { CredentialResponse, GoogleLogin, GoogleOAuthProvider } from '@react-oauth/google';
import { Eye, EyeOff, Leaf, LockKeyhole, Mail, ShieldAlert, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { API_BASE } from '@/services/api';

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [message, setMessage] = useState('');
  const [signingIn, setSigningIn] = useState(false);
  const router = useRouter();
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  useEffect(() => {
    let active = true;
    fetch(`${API_BASE}/api/auth/me`, {credentials:'include'})
      .then(async response => response.ok ? response.json() : {authenticated:false})
      .then(data => { if (active && data?.authenticated) router.replace('/'); })
      .catch(() => undefined);
    return () => { active = false; };
  }, [router]);

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage('Use Google sign-in to access this workspace.');
  };

  const googleSuccess = async (credential: CredentialResponse) => {
    if (!credential.credential) {
      setMessage('Google did not return a usable sign-in credential. Please try again.');
      return;
    }
    setSigningIn(true);
    setMessage('');
    try {
      const response = await fetch(`${API_BASE}/api/auth/google`, {
        method:'POST',
        credentials:'include',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({token:credential.credential}),
      });
      if (!response.ok) throw new Error('verification_failed');
      router.replace('/');
      router.refresh();
    } catch {
      setMessage('Google sign-in could not be verified. Check the configured client and try again.');
    } finally {
      setSigningIn(false);
    }
  };

  return <main className="login-page">
    <div className="login-page__aurora" aria-hidden="true"><i/><i/><i/></div>
    <motion.section className="login-card" initial={{opacity:0,y:18}} animate={{opacity:1,y:0}} transition={{duration:.36,ease:'easeOut'}} aria-labelledby="login-title">
      <div className="login-brand"><span><Leaf size={24}/></span><div><strong>IP-SAKTI</strong><small>Intelligence</small></div></div>
      <div className="login-intro"><span>SECURE WORKSPACE</span><h1 id="login-title">Welcome back.</h1><p>Continue evidence-grounded IP and regulatory research for AYUSH innovation.</p></div>
      <form onSubmit={submit} noValidate>
        <label><span>Email or username</span><div><Mail size={17}/><input name="identity" autoComplete="username" placeholder="you@example.org" aria-label="Email or username"/></div></label>
        <label><span>Password</span><div><LockKeyhole size={17}/><input name="password" type={showPassword?'text':'password'} autoComplete="current-password" placeholder="Enter your password" aria-label="Password"/><button type="button" onClick={()=>setShowPassword(value=>!value)} aria-label={showPassword?'Hide password':'Show password'}>{showPassword?<EyeOff size={17}/>:<Eye size={17}/>}</button></div></label>
        <label className="login-remember"><input type="checkbox"/> <span>Remember this device</span></label>
        <button className="login-submit" type="submit">Use Google sign-in</button>
      </form>
      <div className="login-google">
        {googleClientId ? <GoogleOAuthProvider clientId={googleClientId}><GoogleLogin onSuccess={googleSuccess} onError={()=>setMessage('Google sign-in could not be started.')} useOneTap={false} /></GoogleOAuthProvider> : <p><ShieldAlert size={16}/> Google sign-in is not configured. Set <code>NEXT_PUBLIC_GOOGLE_CLIENT_ID</code>.</p>}
        {signingIn&&<small>Verifying your Google account…</small>}
      </div>
      {message&&<p className="login-message" role="status"><ShieldCheck size={16}/>{message}</p>}
      <p className="login-disclaimer">Google verifies identity with the configured client. The application stores only an HttpOnly session cookie.</p>
    </motion.section>
  </main>;
}
