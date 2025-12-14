import { useEffect, useRef, useState } from 'react'
import './App.css'

// Use environment variable for API URL, fallback to relative path for same-domain or localhost for dev
const API_BASE_URL = "https://fiek-ai-chatbot.onrender.com"
const MODEL_BACKEND_URL = `${API_BASE_URL}/api/chat`
const MODEL_BACKEND_STREAM_URL = `${API_BASE_URL}/api/chat/stream`

function App() {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "Hi! I'm your FIEK AI chatbot. I'm here to help you find information about FIEK, answer questions about the faculty, assist with projects, and provide guidance on academic matters. How can I assist you today?",
      ts: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState('')
  const [modelStatus, setModelStatus] = useState('online')
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
    const currentInput = input.trim()
    setInput('')
    setIsSending(true)

    // Create assistant message placeholder for streaming
    const assistantMessageId = `assistant-${Date.now()}`
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      ts: new Date().toISOString(),
      isStreaming: true,
    }

    setMessages((prev) => [...prev, assistantMessage])

    try {
      // Build messages array with conversation history (excluding system prompt as backend handles it)
      const conversationMessages = messages
        .filter((msg) => msg.role !== 'system') // Remove any system messages from history
        .map(({ role, content }) => ({ role, content }))
      
      // Add the current user message
      conversationMessages.push({ role: 'user', content: currentInput })

      const payload = {
        messages: conversationMessages,
      }

      // Use streaming endpoint
      const res = await fetch(MODEL_BACKEND_STREAM_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(errorData.error || `Backend error: ${res.status}`)
      }

      // Handle streaming response
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let accumulatedContent = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              
              if (data.type === 'chunk') {
                accumulatedContent += data.content
                // Update the message in real-time
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: accumulatedContent }
                      : msg
                  )
                )
              } else if (data.type === 'sources') {
                accumulatedContent += data.content
                // Update the message with sources
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: accumulatedContent, isStreaming: false }
                      : msg
                  )
                )
              } else if (data.type === 'done') {
                // Final update to remove streaming flag
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, isStreaming: false }
                      : msg
                  )
                )
              } else if (data.type === 'error') {
                throw new Error(data.content)
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e)
            }
          }
        }
      }

      setModelStatus('online')
    } catch (err) {
      console.error(err)
      setError(
        err.message || 'Could not reach the model backend. Check that your server is running and the URL in App.jsx matches it.',
      )
      setModelStatus('offline')

      // Update the streaming message with error
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content:
                  "I'm having trouble reaching the model server. Once your backend is running, I will be able to respond normally.",
                isStreaming: false,
              }
            : msg
        )
      )
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

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      // You could add a toast notification here if desired
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="app-shell">
      <div className="app-gradient" />

      <div className="chat-layout">
        <aside className="sidebar">
          <div className="sidebar-header">
            <img src="/Up.png" alt="FIEK Logo" className="sidebar-logo" />
            <div>
              <div className="brand-title">FIEK AI Chatbot</div>
              <div className="brand-subtitle">Project assistant</div>
            </div>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-section-header">
              <span>About this assistant</span>
              <button className="ghost-btn" onClick={clearChat}>
                New chat
              </button>
            </div>

            <div className="info-card">
              <div className="info-title">FIEK-focused help</div>
              <p className="info-body">
                This chatbot is tailored for the Faculty of Electrical and Computer Engineering (FIEK).
                It uses retrieval-augmented generation to answer questions with up-to-date faculty
                information in English or Albanian.
              </p>
            </div>

            <div className="info-list">
              <div className="list-title">What it can do</div>
              <ul>
                <li>Explain academic programs and regulations (BSc, MSc, PhD).</li>
                <li>Share course schedules, notices, and scholarship details.</li>
                <li>Provide contacts for staff, offices, and student services.</li>
                <li>Summarize projects, collaborations, and infrastructure info.</li>
              </ul>
            </div>

            <div className="sidebar-footer">
              <div className="footer-chip">Bilingual (EN/AL)</div>
              <div className="footer-chip">RAG-powered answers</div>
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
            <div className="chat-header-logo">
              <img src="/Up.png" alt="FIEK Logo" className="logo-image" />
              <span className="logo-text">FIEK AI CHATBOT</span>
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
                      <div style={{ whiteSpace: 'pre-wrap' }}>
                        {msg.content ? (
                          msg.content.split('\n').map((line, idx) => (
                            <p key={idx} style={{ margin: idx > 0 ? '0.5em 0' : '0' }}>
                              {line}
                            </p>
                          ))
                        ) : msg.isStreaming ? (
                          <div className="bubble-typing">
                            <span className="typing-dot" />
                            <span className="typing-dot" />
                            <span className="typing-dot" />
                          </div>
                        ) : null}
                        {msg.isStreaming && msg.content && (
                          <span className="streaming-cursor">▊</span>
                        )}
                      </div>
                      {!msg.isStreaming && (
                        <button
                          className="copy-btn"
                          onClick={() => copyToClipboard(msg.content)}
                          title="Copy message"
                          aria-label="Copy message"
                        >
                          <svg
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}


              <div ref={messagesEndRef} />
            </div>
          </section>

          <footer className="chat-input-shell">
            {error && <div className="error-banner">{error}</div>}
            <div className="chat-input-row">
              <textarea
                className="chat-input"
                placeholder="Pyet rreth FIEK... (Ask about FIEK...)"
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
