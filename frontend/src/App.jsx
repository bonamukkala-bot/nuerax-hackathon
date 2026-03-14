import { useState, useEffect, useRef } from 'react'
import { auth } from './firebase'
import { onAuthStateChanged, signOut } from 'firebase/auth'
import Auth from './Auth'

const API_URL = 'http://localhost:8000'

function App() {
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [sessionId] = useState(() => {
    const existing = localStorage.getItem('nexus_session_id')
    if (existing) return existing
    const newId = Math.random().toString(36).substring(7)
    localStorage.setItem('nexus_session_id', newId)
    return newId
  })
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [thoughts, setThoughts] = useState([])
  const [steps, setSteps] = useState([])
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [activeTab, setActiveTab] = useState('chat')
  const [history, setHistory] = useState([])
  const wsRef = useRef(null)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  // Auth state listener
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser)
      setAuthLoading(false)
    })
    return () => unsubscribe()
  }, [])

  useEffect(() => {
    if (user) connectWebSocket()
    return () => wsRef.current?.close()
  }, [user])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thoughts])

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`)
    ws.onopen = () => console.log('Connected to NEXUS AGENT')
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleWSMessage(data)
    }
    ws.onclose = () => setTimeout(connectWebSocket, 2000)
    wsRef.current = ws
  }

  const handleWSMessage = (data) => {
    if (data.type === 'thought') {
      setThoughts(prev => [...prev, data.content])
    } else if (data.type === 'step') {
      setSteps(prev => [...prev, data.content])
    } else if (data.type === 'answer') {
      setIsLoading(false)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.content.answer,
        confidence: data.content.confidence,
        tools_used: data.content.tools_used,
        steps_count: data.content.steps_count,
        thoughts: data.content.thoughts
      }])
    } else if (data.type === 'error') {
      setIsLoading(false)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${data.content}`,
        isError: true
      }])
    }
  }

  const sendMessage = () => {
    if (!input.trim() || isLoading) return
    const task = input.trim()
    setInput('')
    setThoughts([])
    setSteps([])
    setIsLoading(true)
    setMessages(prev => [...prev, { role: 'user', content: task }])
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ task }))
    } else {
      setIsLoading(false)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Connection lost. Please refresh.',
        isError: true
      }])
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData
      })
      const data = await res.json()
      if (data.success) {
        setUploadedFiles(prev => [...prev, {
          file_id: data.file_id,
          filename: data.filename,
          chunks: data.chunks
        }])
        setMessages(prev => [...prev, {
          role: 'system',
          content: `✅ File uploaded: ${data.filename} — ${data.chunks} chunks stored in memory.`
        }])
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'system',
        content: `❌ Upload failed: ${err.message}`,
        isError: true
      }])
    }
  }

  const loadHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/history`)
      const data = await res.json()
      if (data.success) setHistory(data.runs)
    } catch (err) {
      console.error('History load failed:', err)
    }
  }

  const renderMessage = (content) => {
    return content.split('\n').map((line, i) => {
      if (line.startsWith('## ')) {
        return <p key={i} style={{ fontWeight: '700', fontSize: '15px', color: '#a5b4fc', margin: '10px 0 4px' }}>{line.replace('## ', '')}</p>
      } else if (line.startsWith('# ')) {
        return <p key={i} style={{ fontWeight: '700', fontSize: '17px', color: '#6366f1', margin: '12px 0 6px' }}>{line.replace('# ', '')}</p>
      } else if (line.startsWith('- ') || line.startsWith('• ')) {
        return (
          <div key={i} style={{ display: 'flex', gap: '8px', margin: '3px 0' }}>
            <span style={{ color: '#6366f1', flexShrink: 0 }}>•</span>
            <p style={{ margin: 0 }}>{line.replace(/^[-•]\s/, '')}</p>
          </div>
        )
      } else if (line.startsWith('**') && line.endsWith('**')) {
        return <p key={i} style={{ fontWeight: '600', margin: '4px 0', color: '#e2e8f0' }}>{line.replace(/\*\*/g, '')}</p>
      } else if (line.trim() === '') {
        return <br key={i} />
      } else {
        return <p key={i} style={{ margin: '2px 0', lineHeight: '1.6' }}>{line}</p>
      }
    })
  }

  const suggestions = [
    'What is artificial intelligence?',
    'Search latest AI news today',
    'Calculate 15% of 85000',
    'Explain quantum computing simply'
  ]

  // ── LOADING SCREEN ─────────────────────────────────────
  if (authLoading) return (
    <div style={{
      display: 'flex', height: '100vh', background: '#0a0a0a',
      alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '16px'
    }}>
      <p style={{ fontSize: '32px' }}>⚡</p>
      <p style={{ color: '#6366f1', fontSize: '14px' }}>Loading NEXUS AGENT...</p>
    </div>
  )

  // ── AUTH SCREEN ────────────────────────────────────────
  if (!user) return <Auth onLogin={() => {}} />

  // ── MAIN APP ───────────────────────────────────────────
  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0a0a0a', color: '#fff', fontFamily: 'system-ui' }}>

      {/* Sidebar */}
      <div style={{ width: '240px', background: '#0f0f0f', borderRight: '1px solid #1a1a1a', display: 'flex', flexDirection: 'column', padding: '20px 14px' }}>
        <div style={{ marginBottom: '28px' }}>
          <h1 style={{ fontSize: '18px', fontWeight: '700', color: '#6366f1' }}>⚡ NEXUS AGENT</h1>
          <p style={{ fontSize: '11px', color: '#444', marginTop: '3px' }}>Autonomous AI Platform</p>
        </div>

        {['chat', 'files', 'history'].map(tab => (
          <button key={tab} onClick={() => { setActiveTab(tab); if (tab === 'history') loadHistory() }}
            style={{
              padding: '9px 12px', marginBottom: '4px', borderRadius: '8px', border: 'none',
              background: activeTab === tab ? '#6366f1' : 'transparent',
              color: activeTab === tab ? '#fff' : '#666',
              cursor: 'pointer', textAlign: 'left', fontSize: '13px',
              fontWeight: activeTab === tab ? '600' : '400'
            }}>
            {tab === 'chat' ? '💬 Chat' : tab === 'files' ? '📁 Files' : '📜 History'}
          </button>
        ))}

        {uploadedFiles.length > 0 && (
          <div style={{ marginTop: '20px' }}>
            <p style={{ fontSize: '10px', color: '#444', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Files in Memory</p>
            {uploadedFiles.map(f => (
              <div key={f.file_id} style={{ padding: '8px', background: '#1a1a1a', borderRadius: '6px', marginBottom: '4px' }}>
                <p style={{ fontSize: '11px', color: '#a5b4fc', fontWeight: '500', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.filename}</p>
                <p style={{ fontSize: '10px', color: '#444' }}>{f.chunks} chunks</p>
              </div>
            ))}
          </div>
        )}

        {/* User Info + Sign Out */}
        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ padding: '10px', background: '#1a1a1a', borderRadius: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              {user.photoURL ? (
                <img src={user.photoURL} alt="avatar" style={{ width: '24px', height: '24px', borderRadius: '50%' }} />
              ) : (
                <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', color: '#fff' }}>
                  {(user.email || 'U')[0].toUpperCase()}
                </div>
              )}
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <p style={{ fontSize: '11px', color: '#a5b4fc', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', margin: 0 }}>
                  {user.displayName || user.email}
                </p>
                <p style={{ fontSize: '10px', color: '#444', margin: 0 }}>Authenticated ✓</p>
              </div>
            </div>
          </div>
          <button
            onClick={() => signOut(auth)}
            style={{
              padding: '8px', background: 'transparent', border: '1px solid #222',
              borderRadius: '8px', color: '#666', fontSize: '12px', cursor: 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseEnter={e => e.currentTarget.style.borderColor = '#ef4444'}
            onMouseLeave={e => e.currentTarget.style.borderColor = '#222'}
          >
            Sign Out
          </button>
        </div>
      </div>

      {/* Main */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Header */}
        <div style={{ padding: '14px 24px', borderBottom: '1px solid #1a1a1a', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <p style={{ fontSize: '14px', fontWeight: '600' }}>
              {activeTab === 'chat' ? '💬 Chat' : activeTab === 'files' ? '📁 Uploaded Files' : '📜 Run History'}
            </p>
            <p style={{ fontSize: '11px', color: '#444' }}>
              {activeTab === 'chat' ? `Welcome back, ${user.displayName || user.email?.split('@')[0]}!` : ''}
            </p>
          </div>
          {isLoading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#6366f1', animation: 'pulse 1s infinite' }} />
              <p style={{ fontSize: '12px', color: '#6366f1' }}>Agent running...</p>
            </div>
          )}
        </div>

        {/* Chat Tab */}
        {activeTab === 'chat' && (
          <>
            <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>

              {messages.length === 0 && (
                <div style={{ textAlign: 'center', marginTop: '60px' }}>
                  <p style={{ fontSize: '40px', marginBottom: '10px' }}>🧠</p>
                  <h2 style={{ fontSize: '22px', fontWeight: '700', color: '#6366f1', marginBottom: '6px' }}>NEXUS AGENT</h2>
                  <p style={{ color: '#555', fontSize: '13px', marginBottom: '28px' }}>Upload any file or ask anything. I'll think, plan, and answer.</p>
                  <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
                    {suggestions.map(s => (
                      <button key={s} onClick={() => setInput(s)}
                        style={{ padding: '9px 14px', background: '#111', border: '1px solid #222', borderRadius: '8px', color: '#888', fontSize: '12px', cursor: 'pointer' }}>
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                  {msg.role !== 'user' && (
                    <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: msg.role === 'system' ? '#1a2a1a' : '#1e1e3f', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', marginRight: '8px', flexShrink: 0, marginTop: '4px' }}>
                      {msg.role === 'system' ? '📎' : '⚡'}
                    </div>
                  )}
                  <div style={{
                    maxWidth: '72%', padding: '12px 16px', borderRadius: '12px',
                    background: msg.role === 'user' ? '#6366f1' : msg.role === 'system' ? '#0d1f0d' : '#111',
                    border: msg.role === 'assistant' ? '1px solid #1a1a1a' : 'none',
                    color: msg.isError ? '#f87171' : '#e2e8f0'
                  }}>
                    <div style={{ fontSize: '14px' }}>
                      {renderMessage(msg.content)}
                    </div>
                    {msg.confidence && (
                      <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid #222', display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
                        <span style={{ fontSize: '11px', color: '#6366f1', background: '#1e1e3f', padding: '2px 8px', borderRadius: '4px' }}>
                          {msg.confidence}% confidence
                        </span>
                        {msg.tools_used?.map(t => (
                          <span key={t} style={{ fontSize: '11px', color: '#10b981', background: '#0a1f15', padding: '2px 8px', borderRadius: '4px' }}>
                            🔧 {t}
                          </span>
                        ))}
                        <span style={{ fontSize: '11px', color: '#444' }}>{msg.steps_count} steps</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                  <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#1e1e3f', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', flexShrink: 0 }}>⚡</div>
                  <div style={{ background: '#111', border: '1px solid #1a1a1a', borderRadius: '12px', padding: '14px 16px', maxWidth: '72%' }}>
                    <p style={{ fontSize: '12px', color: '#6366f1', marginBottom: '8px', fontWeight: '600' }}>Thinking...</p>
                    {thoughts.map((t, i) => (
                      <div key={i} style={{ display: 'flex', gap: '6px', marginBottom: '4px' }}>
                        <span style={{ color: '#6366f1', fontSize: '11px', marginTop: '2px', flexShrink: 0 }}>→</span>
                        <p style={{ fontSize: '12px', color: '#666', lineHeight: '1.5', margin: 0 }}>{t}</p>
                      </div>
                    ))}
                    {steps.map((s, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px', padding: '5px 8px', background: '#1a1a1a', borderRadius: '6px' }}>
                        <span style={{ fontSize: '11px', color: s.success ? '#10b981' : '#f87171' }}>{s.success ? '✓' : '✗'}</span>
                        <p style={{ fontSize: '11px', color: '#888', margin: 0, flex: 1 }}>Step {s.step}: {s.subtask?.substring(0, 50)}...</p>
                        <span style={{ fontSize: '10px', color: '#444' }}>{s.tool}</span>
                      </div>
                    ))}
                    <div style={{ display: 'flex', gap: '4px', marginTop: '8px' }}>
                      {[0, 1, 2].map(i => (
                        <div key={i} style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#6366f1', animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite` }} />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div style={{ padding: '14px 24px', borderTop: '1px solid #1a1a1a', background: '#0a0a0a' }}>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
                <input type="file" ref={fileInputRef} onChange={handleFileUpload} style={{ display: 'none' }} />
                <button onClick={() => fileInputRef.current?.click()}
                  title="Upload file"
                  style={{ padding: '11px', background: '#111', border: '1px solid #222', borderRadius: '8px', color: '#888', cursor: 'pointer', fontSize: '16px', flexShrink: 0 }}>
                  📎
                </button>
                <textarea
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
                  placeholder="Ask anything... (Enter to send)"
                  style={{
                    flex: 1, padding: '11px 14px', background: '#111', border: '1px solid #222',
                    borderRadius: '8px', color: '#fff', fontSize: '14px', resize: 'none',
                    minHeight: '44px', maxHeight: '120px', outline: 'none', fontFamily: 'inherit',
                    lineHeight: '1.5'
                  }} rows={1} />
                <button onClick={sendMessage} disabled={isLoading || !input.trim()}
                  style={{
                    padding: '11px 18px', background: isLoading || !input.trim() ? '#1a1a1a' : '#6366f1',
                    border: 'none', borderRadius: '8px', color: isLoading || !input.trim() ? '#444' : '#fff',
                    cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer',
                    fontSize: '14px', fontWeight: '600', flexShrink: 0
                  }}>
                  {isLoading ? '...' : 'Send ↑'}
                </button>
              </div>
            </div>
          </>
        )}

        {/* Files Tab */}
        {activeTab === 'files' && (
          <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
            {uploadedFiles.length === 0 ? (
              <div style={{ textAlign: 'center', marginTop: '80px' }}>
                <p style={{ fontSize: '48px', marginBottom: '12px' }}>📂</p>
                <p style={{ color: '#555', fontSize: '14px' }}>No files uploaded yet</p>
                <p style={{ color: '#333', fontSize: '12px', marginTop: '6px' }}>Use the 📎 button in chat to upload CSV, PDF, DOCX, images</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '10px' }}>
                {uploadedFiles.map(f => (
                  <div key={f.file_id} style={{ padding: '16px', background: '#111', border: '1px solid #1a1a1a', borderRadius: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <p style={{ fontWeight: '600', fontSize: '14px', marginBottom: '4px' }}>{f.filename}</p>
                      <p style={{ fontSize: '12px', color: '#555' }}>ID: {f.file_id} · {f.chunks} chunks in vector memory</p>
                    </div>
                    <button onClick={() => { setActiveTab('chat'); setInput(`Analyze the file ${f.filename}`) }}
                      style={{ padding: '8px 14px', background: '#6366f1', border: 'none', borderRadius: '6px', color: '#fff', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>
                      Analyze →
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
            {history.length === 0 ? (
              <div style={{ textAlign: 'center', marginTop: '80px' }}>
                <p style={{ fontSize: '48px', marginBottom: '12px' }}>📭</p>
                <p style={{ color: '#555', fontSize: '14px' }}>No history yet — start chatting!</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '10px' }}>
                {history.map((run, i) => (
                  <div key={i} style={{ padding: '16px', background: '#111', border: '1px solid #1a1a1a', borderRadius: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                      <p style={{ fontWeight: '600', fontSize: '14px', flex: 1, marginRight: '12px' }}>{run.task}</p>
                      <span style={{ fontSize: '12px', color: '#6366f1', background: '#1e1e3f', padding: '2px 8px', borderRadius: '4px', flexShrink: 0 }}>
                        {run.confidence}%
                      </span>
                    </div>
                    <p style={{ fontSize: '13px', color: '#666', marginBottom: '8px', lineHeight: '1.5' }}>
                      {run.final_answer?.substring(0, 120)}...
                    </p>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {run.tools_used?.map(t => (
                        <span key={t} style={{ fontSize: '11px', color: '#10b981', background: '#0a1f15', padding: '2px 6px', borderRadius: '4px' }}>
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 0.3; transform: scale(0.85); }
          50% { opacity: 1; transform: scale(1); }
        }
        textarea:focus { border-color: #6366f1 !important; }
        button:hover { opacity: 0.9; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #222; border-radius: 2px; }
      `}</style>
    </div>
  )
}

export default App