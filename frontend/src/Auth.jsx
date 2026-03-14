import { useState } from 'react'
import { auth, googleProvider } from './firebase'
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut
} from 'firebase/auth'

export default function Auth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleEmailAuth = async () => {
    if (!email || !password) {
      setError('Please enter email and password')
      return
    }
    setLoading(true)
    setError('')
    try {
      if (isLogin) {
        await signInWithEmailAndPassword(auth, email, password)
      } else {
        await createUserWithEmailAndPassword(auth, email, password)
      }
      onLogin()
    } catch (err) {
      setError(err.message.replace('Firebase: ', '').replace(/\(auth.*\)/, ''))
    }
    setLoading(false)
  }

  const handleGoogle = async () => {
    setLoading(true)
    setError('')
    try {
      await signInWithPopup(auth, googleProvider)
      onLogin()
    } catch (err) {
      setError(err.message.replace('Firebase: ', ''))
    }
    setLoading(false)
  }

  return (
    <div style={{
      display: 'flex', height: '100vh', background: '#0a0a0a',
      alignItems: 'center', justifyContent: 'center', fontFamily: 'system-ui'
    }}>
      <div style={{
        width: '400px', background: '#111', border: '1px solid #1a1a1a',
        borderRadius: '16px', padding: '40px', display: 'flex',
        flexDirection: 'column', gap: '20px'
      }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '8px' }}>
          <p style={{ fontSize: '32px', marginBottom: '8px' }}>⚡</p>
          <h1 style={{ fontSize: '22px', fontWeight: '700', color: '#6366f1', margin: 0 }}>
            NEXUS AGENT
          </h1>
          <p style={{ fontSize: '12px', color: '#444', marginTop: '4px' }}>
            Autonomous AI Platform
          </p>
        </div>

        {/* Toggle */}
        <div style={{
          display: 'flex', background: '#1a1a1a', borderRadius: '10px', padding: '4px'
        }}>
          {['Login', 'Register'].map((tab, i) => (
            <button
              key={tab}
              onClick={() => { setIsLogin(i === 0); setError('') }}
              style={{
                flex: 1, padding: '8px', border: 'none', borderRadius: '8px',
                background: isLogin === (i === 0) ? '#6366f1' : 'transparent',
                color: isLogin === (i === 0) ? '#fff' : '#666',
                cursor: 'pointer', fontSize: '13px', fontWeight: '600',
                transition: 'all 0.2s'
              }}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Email Input */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <input
            type="email"
            placeholder="Email address"
            value={email}
            onChange={e => setEmail(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleEmailAuth()}
            style={{
              padding: '12px 14px', background: '#1a1a1a', border: '1px solid #222',
              borderRadius: '8px', color: '#fff', fontSize: '14px', outline: 'none',
              fontFamily: 'inherit'
            }}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleEmailAuth()}
            style={{
              padding: '12px 14px', background: '#1a1a1a', border: '1px solid #222',
              borderRadius: '8px', color: '#fff', fontSize: '14px', outline: 'none',
              fontFamily: 'inherit'
            }}
          />
        </div>

        {/* Error */}
        {error && (
          <div style={{
            padding: '10px 14px', background: '#1a0a0a', border: '1px solid #3d1515',
            borderRadius: '8px', color: '#f87171', fontSize: '12px'
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Email Auth Button */}
        <button
          onClick={handleEmailAuth}
          disabled={loading}
          style={{
            padding: '12px', background: loading ? '#333' : '#6366f1',
            border: 'none', borderRadius: '8px', color: '#fff',
            fontSize: '14px', fontWeight: '600', cursor: loading ? 'not-allowed' : 'pointer',
            transition: 'all 0.2s'
          }}
        >
          {loading ? '...' : isLogin ? 'Sign In' : 'Create Account'}
        </button>

        {/* Divider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ flex: 1, height: '1px', background: '#1a1a1a' }} />
          <span style={{ fontSize: '12px', color: '#444' }}>or</span>
          <div style={{ flex: 1, height: '1px', background: '#1a1a1a' }} />
        </div>

        {/* Google Button */}
        <button
          onClick={handleGoogle}
          disabled={loading}
          style={{
            padding: '12px', background: '#1a1a1a', border: '1px solid #333',
            borderRadius: '8px', color: '#fff', fontSize: '14px',
            fontWeight: '600', cursor: loading ? 'not-allowed' : 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px',
            transition: 'all 0.2s'
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continue with Google
        </button>

        <p style={{ textAlign: 'center', fontSize: '11px', color: '#333', margin: 0 }}>
          NeuraX 2.0 Hackathon — NEXUS AGENT
        </p>
      </div>
    </div>
  )
}