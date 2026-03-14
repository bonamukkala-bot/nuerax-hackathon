import { useState, useEffect, useRef } from 'react'
import { auth } from './firebase'
import { onAuthStateChanged, signOut } from 'firebase/auth'
import Auth from './Auth'

const API_URL = 'https://nuerax-hackathon.onrender.com'

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
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [activeTab, setActiveTab] = useState('chat')
  const [history, setHistory] = useState([])
  const [uploadedFile, setUploadedFile] = useState(null)
  const [edaData, setEdaData] = useState(null)
  const [edaLoading, setEdaLoading] = useState(false)
  const [edaFile, setEdaFile] = useState(null)
  const wsRef = useRef(null)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

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
    try {
      const ws = new WebSocket(`wss://nuerax-hackathon.onrender.com/ws/${sessionId}`)
      ws.onopen = () => console.log('Connected to NEXUS AGENT')
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          handleWSMessage(data)
        } catch (e) {
          console.error('WS parse error:', e)
        }
      }
      ws.onclose = () => setTimeout(connectWebSocket, 2000)
      ws.onerror = (e) => console.error('WS error:', e)
      wsRef.current = ws
    } catch (e) {
      console.error('WS connect error:', e)
    }
  }

  const handleWSMessage = (data) => {
    if (!data) return
    if (data.type === 'thought') {
      setThoughts(prev => [...prev, String(data.content || '')])
    } else if (data.type === 'plan') {
      setThoughts(prev => [...prev, `📋 ${data.content || ''}`])
    } else if (data.type === 'tool_start') {
      setThoughts(prev => [...prev, String(data.content || '')])
    } else if (data.type === 'tool_result') {
      setThoughts(prev => [...prev, String(data.content || '')])
    } else if (data.type === 'answer') {
      setIsLoading(false)
      setThoughts([])
      let answerContent = ''
      if (typeof data.content === 'string') {
        answerContent = data.content
      } else if (data.content && typeof data.content === 'object') {
        answerContent = data.content.answer || data.content.content || JSON.stringify(data.content)
      } else {
        answerContent = 'No response generated'
      }
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: answerContent,
        confidence: data.confidence || 0,
        tools_used: data.tools_used || [],
        steps_count: data.steps || 0,
        youtube_url: data.youtube_url || '',
        youtube_label: data.youtube_label || '',
        images: data.images || [],
        topic: data.topic || '',
        bing_images_url: data.bing_images_url || ''
      }])
    } else if (data.type === 'error') {
      setIsLoading(false)
      setThoughts([])
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: String(data.content || 'An error occurred'),
        isError: true
      }])
    }
  }

  const sendMessage = () => {
    if (!input.trim() || isLoading) return
    const task = input.trim()
    setInput('')
    setThoughts([])
    setIsLoading(true)
    setMessages(prev => [...prev, { role: 'user', content: task }])
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        task,
        file_id: uploadedFile?.file_id || '',
        filename: uploadedFile?.filename || ''
      }))
    } else {
      setIsLoading(false)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Connection lost. Please refresh the page.',
        isError: true
      }])
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setMessages(prev => [...prev, {
      role: 'system',
      content: `⏳ Uploading ${file.name}...`
    }])

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: 'POST',
        body: formData
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Server error: ${res.status}`)
      }

      const data = await res.json()

      if (data.success) {
        const fileInfo = {
          file_id: data.file_id,
          filename: data.filename,
          chunks: data.chunks,
          extension: file.name.split('.').pop().toLowerCase()
        }
        setUploadedFile(fileInfo)
        setUploadedFiles(prev => [...prev, fileInfo])
        setMessages(prev => [...prev, {
          role: 'system',
          content: `✅ File uploaded: ${data.filename} — ${data.chunks} chunks stored in memory. You can now ask questions about it!`
        }])
      } else {
        throw new Error(data.detail || 'Upload failed')
      }
    } catch (err) {
      console.error('Upload error:', err)
      setMessages(prev => [...prev, {
        role: 'system',
        content: `❌ Upload failed: ${err.message}`,
        isError: true
      }])
    }

    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const runEDA = async (fileInfo) => {
    setEdaLoading(true)
    setEdaData(null)
    setEdaFile(fileInfo)
    setActiveTab('eda')

    try {
      const res = await fetch(`${API_URL}/eda/${fileInfo.file_id}`, {
        method: 'POST'
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `EDA failed: ${res.status}`)
      }

      const data = await res.json()
      if (data.success) {
        setEdaData(data)
      } else {
        throw new Error('EDA analysis failed')
      }
    } catch (err) {
      console.error('EDA error:', err)
      setEdaData({ error: err.message })
    }

    setEdaLoading(false)
  }

  const loadHistory = async () => {
    try {
      const res = await fetch(`${API_URL}/history`)
      const data = await res.json()
      if (data.runs) setHistory(data.runs)
    } catch (err) {
      console.error('History load failed:', err)
    }
  }

  const downloadReport = (report, filename) => {
    const blob = new Blob([report], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `EDA_Report_${filename}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const renderMessage = (content) => {
    if (!content) return null
    if (typeof content !== 'string') content = String(content)
    return content.split('\n').map((line, i) => {
      if (line.startsWith('### ')) {
        return <p key={i} style={{ fontWeight: '700', fontSize: '14px', color: '#c4b5fd', margin: '10px 0 4px' }}>{line.replace('### ', '')}</p>
      } else if (line.startsWith('## ')) {
        return <p key={i} style={{ fontWeight: '700', fontSize: '15px', color: '#a5b4fc', margin: '12px 0 4px' }}>{line.replace('## ', '')}</p>
      } else if (line.startsWith('# ')) {
        return <p key={i} style={{ fontWeight: '700', fontSize: '17px', color: '#6366f1', margin: '14px 0 6px' }}>{line.replace('# ', '')}</p>
      } else if (line.startsWith('- ') || line.startsWith('* ')) {
        return (
          <div key={i} style={{ display: 'flex', gap: '8px', margin: '3px 0' }}>
            <span style={{ color: '#6366f1', flexShrink: 0 }}>•</span>
            <p style={{ margin: 0, lineHeight: '1.6' }}>{line.replace(/^[-*]\s/, '')}</p>
          </div>
        )
      } else if (line.trim() === '') {
        return <br key={i} />
      } else {
        const parts = line.split(/(\*\*[^*]+\*\*)/)
        return (
          <p key={i} style={{ margin: '3px 0', lineHeight: '1.6' }}>
            {parts.map((part, j) => {
              if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={j}>{part.replace(/\*\*/g, '')}</strong>
              }
              return part
            })}
          </p>
        )
      }
    })
  }

  const suggestions = [
    'What is artificial intelligence?',
    'Search latest AI news in 2025',
    'Calculate compound interest: 50000 at 10% for 5 years',
    'Write Python code for bubble sort',
    'Explain how RAG works in AI',
    'Best practices for prompt engineering'
  ]

  const edaSupportedExts = ['csv', 'xlsx', 'xls', 'json']

  if (authLoading) return (
    <div style={{ display: 'flex', height: '100vh', background: '#0a0a0a', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '16px' }}>
      <p style={{ fontSize: '40px' }}>⚡</p>
      <p style={{ color: '#6366f1', fontSize: '14px' }}>Loading NEXUS AGENT...</p>
    </div>
  )

  if (!user) return <Auth onLogin={() => {}} />

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0a0a0a', color: '#e2e8f0', fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif' }}>

      {/* ── SIDEBAR ── */}
      <div style={{ width: '240px', background: '#0f0f0f', borderRight: '1px solid #1a1a1a', display: 'flex', flexDirection: 'column', padding: '20px 14px', gap: '6px' }}>
        <div style={{ marginBottom: '20px' }}>
          <h1 style={{ fontSize: '18px', fontWeight: '700', color: '#6366f1', margin: 0 }}>⚡ NEXUS AGENT</h1>
          <p style={{ fontSize: '11px', color: '#444', marginTop: '3px' }}>Autonomous AI Platform</p>
        </div>

        {[
          { id: 'chat', label: '💬 Chat' },
          { id: 'files', label: '📁 Files' },
          { id: 'eda', label: '📊 EDA Analysis' },
          { id: 'history', label: '📜 History' }
        ].map(tab => (
          <button key={tab.id}
            onClick={() => { setActiveTab(tab.id); if (tab.id === 'history') loadHistory() }}
            style={{ padding: '9px 12px', borderRadius: '8px', border: 'none', background: activeTab === tab.id ? '#6366f1' : 'transparent', color: activeTab === tab.id ? '#fff' : '#666', cursor: 'pointer', textAlign: 'left', fontSize: '13px', fontWeight: activeTab === tab.id ? '600' : '400' }}>
            {tab.label}
          </button>
        ))}

        {uploadedFiles.length > 0 && (
          <div style={{ marginTop: '16px' }}>
            <p style={{ fontSize: '10px', color: '#444', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Files in Memory</p>
            {uploadedFiles.map((f, i) => (
              <div key={i} style={{ padding: '8px', background: '#1a1a1a', borderRadius: '6px', marginBottom: '4px' }}>
                <p style={{ fontSize: '11px', color: '#a5b4fc', fontWeight: '500', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', margin: 0 }}>📄 {f.filename}</p>
                <p style={{ fontSize: '10px', color: '#444', margin: '2px 0 0' }}>{f.chunks} chunks</p>
              </div>
            ))}
          </div>
        )}

        <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ padding: '10px', background: '#1a1a1a', borderRadius: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {user.photoURL
                ? <img src={user.photoURL} alt="avatar" style={{ width: '24px', height: '24px', borderRadius: '50%' }} />
                : <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', color: '#fff', flexShrink: 0 }}>{(user.email || 'U')[0].toUpperCase()}</div>
              }
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <p style={{ fontSize: '11px', color: '#a5b4fc', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', margin: 0 }}>{user.displayName || user.email}</p>
                <p style={{ fontSize: '10px', color: '#10b981', margin: 0 }}>✓ Authenticated</p>
              </div>
            </div>
          </div>
          <button onClick={() => signOut(auth)}
            style={{ padding: '8px', background: 'transparent', border: '1px solid #222', borderRadius: '8px', color: '#666', fontSize: '12px', cursor: 'pointer' }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = '#ef4444'; e.currentTarget.style.color = '#ef4444' }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = '#222'; e.currentTarget.style.color = '#666' }}>
            Sign Out
          </button>
        </div>
      </div>

      {/* ── MAIN ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

        {/* Header */}
        <div style={{ padding: '14px 24px', borderBottom: '1px solid #1a1a1a', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#0f0f0f', flexShrink: 0 }}>
          <div>
            <p style={{ fontSize: '14px', fontWeight: '600', margin: 0 }}>
              {activeTab === 'chat' ? '💬 Chat with NEXUS'
                : activeTab === 'files' ? '📁 Uploaded Files'
                : activeTab === 'eda' ? '📊 AI EDA Analysis'
                : '📜 Run History'}
            </p>
            <p style={{ fontSize: '11px', color: '#444', margin: '2px 0 0' }}>
              {activeTab === 'chat' ? `Welcome, ${user.displayName || user.email?.split('@')[0]}!` : ''}
              {activeTab === 'eda' ? 'Agentic AI Exploratory Data Analysis' : ''}
            </p>
          </div>
          {isLoading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#6366f1', animation: 'pulse 1s infinite' }} />
              <p style={{ fontSize: '12px', color: '#6366f1', margin: 0 }}>Agent working...</p>
            </div>
          )}
        </div>

        {/* ── CHAT TAB ── */}
        {activeTab === 'chat' && (
          <>
            <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {messages.length === 0 && (
                <div style={{ textAlign: 'center', marginTop: '40px' }}>
                  <p style={{ fontSize: '48px', marginBottom: '12px' }}>🧠</p>
                  <h2 style={{ fontSize: '24px', fontWeight: '700', color: '#6366f1', marginBottom: '8px' }}>NEXUS Autonomous Agent</h2>
                  <p style={{ color: '#555', fontSize: '14px', marginBottom: '32px', lineHeight: '1.6' }}>
                    I can search the web, analyze data, write code, read files and much more.
                  </p>
                  <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap', maxWidth: '600px', margin: '0 auto' }}>
                    {suggestions.map((s, i) => (
                      <button key={i} onClick={() => setInput(s)}
                        style={{ padding: '9px 14px', background: '#111', border: '1px solid #222', borderRadius: '8px', color: '#888', fontSize: '12px', cursor: 'pointer' }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = '#6366f1'; e.currentTarget.style.color = '#a5b4fc' }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = '#222'; e.currentTarget.style.color = '#888' }}>
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start', animation: 'fadeIn 0.3s ease' }}>
                  {msg.role !== 'user' && (
                    <div style={{ width: '30px', height: '30px', borderRadius: '50%', background: msg.role === 'system' ? '#1a2a1a' : '#1e1e3f', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', marginRight: '10px', flexShrink: 0, marginTop: '4px' }}>
                      {msg.role === 'system' ? '📎' : '⚡'}
                    </div>
                  )}
                  <div style={{ maxWidth: '75%', padding: '12px 16px', borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '4px 16px 16px 16px', background: msg.role === 'user' ? '#6366f1' : msg.role === 'system' ? '#0d1f0d' : '#111', border: msg.role !== 'user' ? '1px solid #1a1a1a' : 'none', color: msg.isError ? '#f87171' : '#e2e8f0' }}>
                    <div style={{ fontSize: '14px', lineHeight: '1.6' }}>
                      {msg.content ? renderMessage(msg.content) : null}
                    </div>

                    {/* YouTube */}
                    {msg.role === 'assistant' && msg.youtube_url && (
                      <div style={{ marginTop: '14px', paddingTop: '12px', borderTop: '1px solid #222' }}>
                        <p style={{ fontSize: '11px', color: '#555', margin: '0 0 8px', fontWeight: '600' }}>📺 Watch and Learn</p>
                        <a href={msg.youtube_url} target="_blank" rel="noopener noreferrer"
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '8px 14px', background: '#1a0808', border: '1px solid #7f1d1d', borderRadius: '8px', color: '#fca5a5', fontSize: '13px', fontWeight: '600', textDecoration: 'none' }}
                          onMouseEnter={e => { e.currentTarget.style.background = '#2a0808'; e.currentTarget.style.borderColor = '#ef4444' }}
                          onMouseLeave={e => { e.currentTarget.style.background = '#1a0808'; e.currentTarget.style.borderColor = '#7f1d1d' }}>
                          ▶ {msg.youtube_label || 'Watch on YouTube'}
                        </a>
                      </div>
                    )}

                    {/* Bing Images */}
                    {msg.role === 'assistant' && msg.bing_images_url && (
                      <div style={{ marginTop: '8px' }}>
                        <a href={msg.bing_images_url} target="_blank" rel="noopener noreferrer"
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '7px 12px', background: '#0a1020', border: '1px solid #1e3a5f', borderRadius: '8px', color: '#93c5fd', fontSize: '12px', fontWeight: '600', textDecoration: 'none' }}
                          onMouseEnter={e => { e.currentTarget.style.background = '#0f1a30'; e.currentTarget.style.borderColor = '#3b82f6' }}
                          onMouseLeave={e => { e.currentTarget.style.background = '#0a1020'; e.currentTarget.style.borderColor = '#1e3a5f' }}>
                          🔍 Search Images on Bing
                        </a>
                      </div>
                    )}

                    {/* Placeholder Images */}
                    {msg.role === 'assistant' && msg.images && msg.images.length > 0 && (
                      <div style={{ marginTop: '14px' }}>
                        <p style={{ fontSize: '11px', color: '#555', marginBottom: '8px', fontWeight: '600' }}>🖼️ Visual Reference</p>
                        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                          {msg.images.map((url, idx) => (
                            <img key={idx} src={url} alt={msg.topic || 'related'}
                              style={{ width: '130px', height: '85px', objectFit: 'cover', borderRadius: '8px', border: '1px solid #222', cursor: 'pointer' }}
                              onClick={() => window.open(msg.bing_images_url || url, '_blank')}
                              onError={e => { e.target.style.display = 'none' }}
                              onMouseEnter={e => { e.target.style.border = '1px solid #6366f1' }}
                              onMouseLeave={e => { e.target.style.border = '1px solid #222' }}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Confidence */}
                    {msg.role === 'assistant' && msg.confidence > 0 && (
                      <div style={{ marginTop: '10px', paddingTop: '8px', borderTop: '1px solid #222', display: 'flex', gap: '6px', flexWrap: 'wrap', alignItems: 'center' }}>
                        <span style={{ fontSize: '11px', color: '#6366f1', background: '#1e1e3f', padding: '2px 8px', borderRadius: '4px' }}>
                          {Math.round(msg.confidence * 100)}% confidence
                        </span>
                        {msg.tools_used?.map((t, j) => (
                          <span key={j} style={{ fontSize: '11px', color: '#10b981', background: '#0a1f15', padding: '2px 8px', borderRadius: '4px' }}>🔧 {t}</span>
                        ))}
                        {msg.steps_count > 0 && (
                          <span style={{ fontSize: '11px', color: '#444' }}>{msg.steps_count} steps</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '10px' }}>
                  <div style={{ width: '30px', height: '30px', borderRadius: '50%', background: '#1e1e3f', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '14px', flexShrink: 0 }}>⚡</div>
                  <div style={{ background: '#111', border: '1px solid #1a1a1a', borderRadius: '4px 16px 16px 16px', padding: '14px 16px', maxWidth: '75%', minWidth: '200px' }}>
                    <p style={{ fontSize: '12px', color: '#6366f1', fontWeight: '600', margin: '0 0 8px' }}>Thinking...</p>
                    {thoughts.slice(-5).map((t, i) => (
                      <div key={i} style={{ display: 'flex', gap: '6px', marginBottom: '4px' }}>
                        <span style={{ color: '#6366f1', fontSize: '11px', marginTop: '2px', flexShrink: 0 }}>→</span>
                        <p style={{ fontSize: '12px', color: '#666', lineHeight: '1.5', margin: 0 }}>{t}</p>
                      </div>
                    ))}
                    <div style={{ display: 'flex', gap: '4px', marginTop: '10px' }}>
                      {[0, 1, 2].map(i => (
                        <div key={i} style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#6366f1', animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite` }} />
                      ))}
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div style={{ padding: '14px 24px', borderTop: '1px solid #1a1a1a', background: '#0f0f0f', flexShrink: 0 }}>
              {uploadedFile && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', background: '#1a0a2e', border: '1px solid #4a1d96', borderRadius: '6px', marginBottom: '8px' }}>
                  <span style={{ fontSize: '12px', color: '#a78bfa' }}>📎 {uploadedFile.filename} ready</span>
                  <button onClick={() => setUploadedFile(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: '14px' }}>×</button>
                </div>
              )}
              <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
                <input type="file" ref={fileInputRef} onChange={handleFileUpload} style={{ display: 'none' }}
                  accept=".pdf,.csv,.xlsx,.xls,.docx,.txt,.json,.png,.jpg,.jpeg" />
                <button onClick={() => fileInputRef.current?.click()}
                  style={{ padding: '11px 13px', background: '#111', border: '1px solid #222', borderRadius: '10px', color: '#888', cursor: 'pointer', fontSize: '16px', flexShrink: 0 }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = '#6366f1'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = '#222'}>
                  📎
                </button>
                <textarea value={input} onChange={e => setInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
                  placeholder="Ask anything... (Enter to send, Shift+Enter for new line)"
                  style={{ flex: 1, padding: '11px 14px', background: '#111', border: '1px solid #222', borderRadius: '10px', color: '#e2e8f0', fontSize: '14px', resize: 'none', minHeight: '44px', maxHeight: '120px', outline: 'none', fontFamily: 'inherit', lineHeight: '1.5' }}
                  rows={1}
                  onFocus={e => e.target.style.borderColor = '#6366f1'}
                  onBlur={e => e.target.style.borderColor = '#222'}
                />
                <button onClick={sendMessage} disabled={isLoading || !input.trim()}
                  style={{ padding: '11px 18px', background: isLoading || !input.trim() ? '#1a1a1a' : '#6366f1', border: 'none', borderRadius: '10px', color: isLoading || !input.trim() ? '#444' : '#fff', cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer', fontSize: '14px', fontWeight: '600', flexShrink: 0 }}>
                  {isLoading ? '...' : 'Send ↑'}
                </button>
              </div>
            </div>
          </>
        )}

        {/* ── FILES TAB ── */}
        {activeTab === 'files' && (
          <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
            {uploadedFiles.length === 0 ? (
              <div style={{ textAlign: 'center', marginTop: '80px' }}>
                <p style={{ fontSize: '48px', marginBottom: '12px' }}>📂</p>
                <p style={{ color: '#555', fontSize: '14px' }}>No files uploaded yet</p>
                <p style={{ color: '#333', fontSize: '12px', marginTop: '6px' }}>Use the 📎 button in chat to upload files</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '12px' }}>
                {uploadedFiles.map((f, i) => (
                  <div key={i} style={{ padding: '16px', background: '#111', border: '1px solid #1a1a1a', borderRadius: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <p style={{ fontWeight: '600', fontSize: '14px', marginBottom: '4px', color: '#e2e8f0' }}>📄 {f.filename}</p>
                      <p style={{ fontSize: '12px', color: '#555' }}>ID: {f.file_id} · {f.chunks} chunks</p>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button onClick={() => { setActiveTab('chat'); setInput(`Analyze the file ${f.filename} and give me key insights`) }}
                        style={{ padding: '8px 14px', background: '#6366f1', border: 'none', borderRadius: '6px', color: '#fff', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>
                        Chat →
                      </button>
                      {edaSupportedExts.includes(f.extension || '') && (
                        <button onClick={() => runEDA(f)}
                          style={{ padding: '8px 14px', background: '#10b981', border: 'none', borderRadius: '6px', color: '#fff', cursor: 'pointer', fontSize: '12px', fontWeight: '600' }}>
                          📊 EDA
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── EDA TAB ── */}
        {activeTab === 'eda' && (
          <div style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
            {!edaFile && !edaLoading && (
              <div style={{ textAlign: 'center', marginTop: '80px' }}>
                <p style={{ fontSize: '48px', marginBottom: '12px' }}>📊</p>
                <p style={{ color: '#e2e8f0', fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>Agentic AI EDA Pipeline</p>
                <p style={{ color: '#555', fontSize: '14px', marginBottom: '24px' }}>Upload a CSV, Excel, or JSON file then click the EDA button</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '400px', margin: '0 auto', background: '#111', border: '1px solid #1a1a1a', borderRadius: '12px', padding: '20px' }}>
                  <p style={{ color: '#a5b4fc', fontWeight: '600', fontSize: '14px', margin: 0 }}>What EDA does:</p>
                  {['🤖 Coder Agent writes Python EDA code automatically', '📊 Generates distribution charts for all columns', '🔥 Correlation heatmap', '❓ Missing values analysis', '🧠 Analyst Agent explains findings in plain English', '📄 Download full EDA report'].map((item, i) => (
                    <div key={i} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                      <p style={{ fontSize: '13px', color: '#888', margin: 0 }}>{item}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {edaLoading && (
              <div style={{ textAlign: 'center', marginTop: '80px' }}>
                <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', marginBottom: '20px' }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#6366f1', animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite` }} />
                  ))}
                </div>
                <p style={{ color: '#6366f1', fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>Running Agentic EDA Pipeline...</p>
                <p style={{ color: '#555', fontSize: '13px' }}>Coder Agent → Charts → Analyst Agent → Insights</p>
              </div>
            )}

            {edaData && !edaData.error && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>

                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <p style={{ fontSize: '20px', fontWeight: '700', color: '#6366f1', margin: 0 }}>📊 EDA Report: {edaFile?.filename}</p>
                    <p style={{ fontSize: '12px', color: '#555', margin: '4px 0 0' }}>Generated by Agentic AI Pipeline</p>
                  </div>
                  <button onClick={() => downloadReport(edaData.report, edaFile?.filename)}
                    style={{ padding: '10px 18px', background: '#10b981', border: 'none', borderRadius: '8px', color: '#fff', cursor: 'pointer', fontSize: '13px', fontWeight: '600' }}>
                    📄 Download Report
                  </button>
                </div>

                {/* Summary Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
                  {[
                    { label: 'Rows', value: edaData.summary?.rows, color: '#6366f1' },
                    { label: 'Columns', value: edaData.summary?.columns, color: '#10b981' },
                    { label: 'Duplicates', value: edaData.summary?.duplicates, color: '#f59e0b' },
                    { label: 'Memory', value: `${edaData.summary?.memory_kb} KB`, color: '#8b5cf6' }
                  ].map((card, i) => (
                    <div key={i} style={{ padding: '16px', background: '#111', border: `1px solid ${card.color}33`, borderRadius: '10px', textAlign: 'center' }}>
                      <p style={{ fontSize: '24px', fontWeight: '700', color: card.color, margin: 0 }}>{card.value}</p>
                      <p style={{ fontSize: '12px', color: '#555', margin: '4px 0 0' }}>{card.label}</p>
                    </div>
                  ))}
                </div>

                {/* Column Types */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div style={{ padding: '16px', background: '#111', border: '1px solid #1a1a1a', borderRadius: '10px' }}>
                    <p style={{ fontSize: '13px', fontWeight: '600', color: '#a5b4fc', marginBottom: '10px' }}>📈 Numeric Columns ({edaData.summary?.numeric_cols?.length})</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {edaData.summary?.numeric_cols?.map((col, i) => (
                        <span key={i} style={{ fontSize: '11px', padding: '3px 8px', background: '#1e1e3f', color: '#a5b4fc', borderRadius: '4px' }}>{col}</span>
                      ))}
                    </div>
                  </div>
                  <div style={{ padding: '16px', background: '#111', border: '1px solid #1a1a1a', borderRadius: '10px' }}>
                    <p style={{ fontSize: '13px', fontWeight: '600', color: '#10b981', marginBottom: '10px' }}>🏷️ Categorical Columns ({edaData.summary?.categorical_cols?.length})</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                      {edaData.summary?.categorical_cols?.map((col, i) => (
                        <span key={i} style={{ fontSize: '11px', padding: '3px 8px', background: '#0a1f15', color: '#10b981', borderRadius: '4px' }}>{col}</span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Missing Values */}
                {Object.keys(edaData.summary?.missing_values || {}).length > 0 && (
                  <div style={{ padding: '16px', background: '#1a0808', border: '1px solid #7f1d1d', borderRadius: '10px' }}>
                    <p style={{ fontSize: '13px', fontWeight: '600', color: '#fca5a5', marginBottom: '10px' }}>⚠️ Missing Values</p>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                      {Object.entries(edaData.summary?.missing_values || {}).map(([col, count], i) => (
                        <span key={i} style={{ fontSize: '12px', padding: '4px 10px', background: '#2a0808', color: '#fca5a5', borderRadius: '6px' }}>
                          {col}: {count} ({edaData.summary?.missing_pct?.[col]}%)
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Charts */}
                {edaData.charts && edaData.charts.length > 0 && (
                  <div>
                    <p style={{ fontSize: '16px', fontWeight: '600', color: '#e2e8f0', marginBottom: '16px' }}>📊 Generated Charts</p>
                    <div style={{ display: 'grid', gap: '16px' }}>
                      {edaData.charts.map((chart, i) => (
                        <div key={i} style={{ background: '#111', border: '1px solid #1a1a1a', borderRadius: '10px', overflow: 'hidden' }}>
                          <div style={{ padding: '12px 16px', borderBottom: '1px solid #1a1a1a' }}>
                            <p style={{ fontSize: '13px', fontWeight: '600', color: '#a5b4fc', margin: 0 }}>{chart.title}</p>
                          </div>
                          <div style={{ padding: '16px' }}>
                            <img src={`data:image/png;base64,${chart.image}`}
                              alt={chart.title}
                              style={{ width: '100%', borderRadius: '8px' }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI Insights */}
                {edaData.ai_insights && (
                  <div style={{ padding: '20px', background: '#0a1020', border: '1px solid #1e3a5f', borderRadius: '10px' }}>
                    <p style={{ fontSize: '16px', fontWeight: '600', color: '#93c5fd', marginBottom: '16px' }}>🧠 Analyst Agent Insights</p>
                    <div style={{ fontSize: '14px', lineHeight: '1.7', color: '#e2e8f0' }}>
                      {renderMessage(edaData.ai_insights)}
                    </div>
                  </div>
                )}

                {/* Coder Agent Output */}
                {edaData.stats_output && (
                  <div style={{ padding: '20px', background: '#0f1a0f', border: '1px solid #14532d', borderRadius: '10px' }}>
                    <p style={{ fontSize: '16px', fontWeight: '600', color: '#86efac', marginBottom: '16px' }}>🤖 Coder Agent Output</p>
                    <pre style={{ fontSize: '12px', color: '#4ade80', lineHeight: '1.6', overflowX: 'auto', whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'monospace' }}>
                      {edaData.stats_output}
                    </pre>
                  </div>
                )}

              </div>
            )}

            {edaData?.error && (
              <div style={{ padding: '20px', background: '#1a0808', border: '1px solid #7f1d1d', borderRadius: '10px', marginTop: '40px' }}>
                <p style={{ color: '#fca5a5', fontWeight: '600', marginBottom: '8px' }}>❌ EDA Error</p>
                <p style={{ color: '#888', fontSize: '13px' }}>{edaData.error}</p>
              </div>
            )}
          </div>
        )}

        {/* ── HISTORY TAB ── */}
        {activeTab === 'history' && (
          <div style={{ flex: 1, padding: '24px', overflowY: 'auto' }}>
            {history.length === 0 ? (
              <div style={{ textAlign: 'center', marginTop: '80px' }}>
                <p style={{ fontSize: '48px', marginBottom: '12px' }}>📭</p>
                <p style={{ color: '#555', fontSize: '14px' }}>No history yet — start chatting!</p>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: '12px' }}>
                {history.map((run, i) => (
                  <div key={i} style={{ padding: '16px', background: '#111', border: '1px solid #1a1a1a', borderRadius: '10px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                      <p style={{ fontWeight: '600', fontSize: '14px', flex: 1, marginRight: '12px', color: '#e2e8f0' }}>{run.task || 'Unknown task'}</p>
                      <span style={{ fontSize: '12px', color: '#6366f1', background: '#1e1e3f', padding: '2px 8px', borderRadius: '4px', flexShrink: 0 }}>
                        {Math.round((run.confidence || 0) * 100)}%
                      </span>
                    </div>
                    <p style={{ fontSize: '13px', color: '#555', marginBottom: '8px', lineHeight: '1.5' }}>
                      {(run.final_answer || '').substring(0, 120)}...
                    </p>
                    <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                      {(run.tools_used || []).map((t, j) => (
                        <span key={j} style={{ fontSize: '11px', color: '#10b981', background: '#0a1f15', padding: '2px 6px', borderRadius: '4px' }}>🔧 {t}</span>
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
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #222; border-radius: 2px; }
        textarea:focus { border-color: #6366f1 !important; }
      `}</style>
    </div>
  )
}

export default App