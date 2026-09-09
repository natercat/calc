import { useState } from 'react'
import { sendChatMessage } from '../api'
import MathInput from './MathInput'
import MathText from './MathText'

export default function ChatPanel({ sessionId, onProfileUpdate }) {
  const [messages, setMessages] = useState([
    { role: 'tutor', text: 'Ask me anything about calculus, or tell me what you want to focus on.' },
  ])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(text, imageBase64) {
    setMessages((m) => [...m, { role: 'student', text: text || '(photo)' }])
    setLoading(true)
    setError(null)
    try {
      const result = await sendChatMessage(sessionId, text, imageBase64)
      setMessages((m) => [...m, { role: 'tutor', text: result.reply }])
      onProfileUpdate(result.profile)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-panel">
      <div className="transcript">
        {messages.map((entry, i) => (
          <div key={i} className={`bubble ${entry.role}`}>
            {entry.role === 'tutor' ? <MathText text={entry.text} /> : <p>{entry.text}</p>}
          </div>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
      <MathInput
        onSubmit={handleSubmit}
        disabled={loading}
        placeholder="Ask a question or describe what you want to work on..."
      />
    </div>
  )
}
