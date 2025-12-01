import { useEffect, useRef, useState } from 'react'
import './App.css'

const MODEL_BACKEND_URL = '/api/chat'

function App() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "Hi, I'm your AI assistant. Ask me anything about your project, code, or ideas and I'll respond using the model behind this chat.",
      ts: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState('')
  const [modelStatus, setModelStatus] = useState('online')
  const [temperature, setTemperature] = useState(0.7)
  const [systemPrompt, setSystemPrompt] = useState(
    'You are a helpful AI assistant specialized in helping with university projects and coding.',
  )
  const messagesEndRef = useRef(null)

  useEffect(() => {
    if (!messagesEndRef.current) return
    messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, isSending])

  const handleSend = async () => {
    if (!input.trim() || isSending) return
    setError('')

    const userMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      ts: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsSending(true)

    try {
      const payload = {
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages.map(({ role, content }) => ({ role, content })),
          { role: 'user', content: userMessage.content },
        ],
        temperature,
      }

      const res = await fetch(MODEL_BACKEND_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        throw new Error(`Backend error: ${res.status}`)
      }

      const data = await res.json()

      const assistantText =
        data?.reply ??
        data?.content ??
        'The model responded, but the frontend could not understand the response shape. Please adjust the frontend parsing.'

      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: assistantText,
        ts: new Date().toISOString(),
      }

      setMessages((prev) => [...prev, assistantMessage])
      setModelStatus('online')
    } catch (err) {
      console.error(err)
      setError(
        'Could not reach the model backend. Check that your server is running and the URL in App.jsx matches it.',
      )
      setModelStatus('offline')

      const fallbackMessage = {
        id: `assistant-error-${Date.now()}`,
        role: 'assistant',
        content:
          "I'm having trouble reaching the model server. Once your backend is running, I will be able to respond normally.",
        ts: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, fallbackMessage])
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const clearChat = () => {
    setMessages((prev) => prev.slice(0, 1))
    setError('')
  }

  return (
    <div className="app-shell">
      <div className="app-gradient" />

      <div className="chat-layout">
        <aside className="sidebar">
          <div className="sidebar-header">
            <div className="brand-mark">
              <div className="brand-orbit" />
              <span className="brand-dot" />
            </div>
            <div>
              <div className="brand-title">FIEK AI Chatbot</div>
              <div className="brand-subtitle">Project assistant</div>
            </div>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-section-header">
              <span>Session</span>
              <button className="ghost-btn" onClick={clearChat}>
                Clear
              </button>
            </div>
            <div className="session-card">
              <div className="session-title">Current conversation</div>
              <div className="session-meta">
                <span className="pill pill-soft">Auto-saved</span>
                <span className={`pill pill-status ${modelStatus}`}>
                  <span className="status-dot" />
                  {modelStatus === 'online' ? 'Model online' : 'Model offline'}
                </span>
              </div>
            </div>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-section-header">
              <span>Model controls</span>
            </div>

            <div className="control-group">
              <label className="control-label">
                System behavior
                <span className="control-label-sub">
                  This instruction is sent as a system prompt.
                </span>
              </label>
              <textarea
                className="control-textarea"
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
              />
            </div>

            <div className="control-group">
              <label className="control-label">
                Temperature
                <span className="control-label-sub">
                  Lower is more focused, higher is more creative.
                </span>
              </label>
              <div className="control-row">
                <input
                  className="control-slider"
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(Number(e.target.value))}
                />
                <span className="slider-value">{temperature.toFixed(2)}</span>
              </div>
            </div>

            <div className="sidebar-footer">
              <div className="footer-chip">Frontend only • React + Vite</div>
              <div className="footer-chip">
                Set backend URL in <code>App.jsx</code>
              </div>
            </div>
          </div>
        </aside>

        <main className="chat-main">
          <header className="chat-header">
            <div>
              <div className="chat-title">AI chat workspace</div>
              <div className="chat-subtitle">
                Start by describing your assignment, then ask specific questions.
              </div>
            </div>
          </header>

          <section className="chat-stream">
            <div className="messages-scroll">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`message-row ${msg.role === 'user' ? 'user' : 'assistant'}`}
                >
                  <div className="avatar">
                    {msg.role === 'user' ? (
                      <span className="avatar-initial">You</span>
                    ) : (
                      <span className="avatar-initial">AI</span>
                    )}
                  </div>
                  <div className="bubble-column">
                    <div className="bubble-meta">
                      <span className="bubble-author">
                        {msg.role === 'user' ? 'You' : 'AI assistant'}
                      </span>
                    </div>
                    <div className="bubble">
                      <p>{msg.content}</p>
                    </div>
                  </div>
                </div>
              ))}

              {isSending && (
                <div className="message-row assistant">
                  <div className="avatar">
                    <span className="avatar-initial">AI</span>
                  </div>
                  <div className="bubble-column">
                    <div className="bubble-meta">
                      <span className="bubble-author">AI assistant</span>
                    </div>
                    <div className="bubble bubble-typing">
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                      <span className="typing-dot" />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          </section>

          <footer className="chat-input-shell">
            {error && <div className="error-banner">{error}</div>}
            <div className="chat-input-row">
              <textarea
                className="chat-input"
                placeholder="Ask anything about your project, e.g. “Explain how to structure my AI chatbot backend in Node.js.”"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
              />
              <div className="chat-actions">
                <button
                  className="secondary-btn"
                  type="button"
                  onClick={clearChat}
                  disabled={isSending}
                >
                  Clear
                </button>
                <button
                  className="primary-btn"
                  type="button"
                  onClick={handleSend}
                  disabled={isSending || !input.trim()}
                >
                  {isSending ? (
                    <span className="btn-loader">
                      <span className="loader-dot" />
                      <span className="loader-dot" />
                      <span className="loader-dot" />
                    </span>
                  ) : (
                    'Send'
                  )}
                </button>
              </div>
            </div>
            <div className="input-hint">
              Press <kbd>Enter</kbd> to send, <kbd>Shift</kbd> + <kbd>Enter</kbd> for a new line.
            </div>
          </footer>
        </main>
      </div>
    </div>
  )
}

export default App
