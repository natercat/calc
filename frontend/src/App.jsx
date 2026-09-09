import { useEffect, useState } from 'react'
import { createSession } from './api'
import LessonPanel from './components/LessonPanel'
import PracticePanel from './components/PracticePanel'
import ChatPanel from './components/ChatPanel'
import ProfilePanel from './components/ProfilePanel'

const TOPICS = [{ id: 'derivatives', label: 'Derivatives' }]
const MODES = [
  { id: 'lesson', label: 'Lesson' },
  { id: 'practice', label: 'Practice' },
  { id: 'chat', label: 'Chat' },
]

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [profile, setProfile] = useState({})
  const [topic, setTopic] = useState(TOPICS[0].id)
  const [mode, setMode] = useState('lesson')
  const [error, setError] = useState(null)

  useEffect(() => {
    createSession()
      .then((res) => {
        setSessionId(res.session_id)
        setProfile(res.profile)
      })
      .catch((e) => setError(e.message))
  }, [])

  if (error) {
    return <p className="error">Could not reach the backend: {error}</p>
  }

  if (!sessionId) {
    return <p>Starting your session...</p>
  }

  return (
    <div className="app">
      <header>
        <h1>CalcTutor</h1>
        <nav>
          {MODES.map((m) => (
            <button key={m.id} className={mode === m.id ? 'active' : ''} onClick={() => setMode(m.id)}>
              {m.label}
            </button>
          ))}
        </nav>
        <select value={topic} onChange={(e) => setTopic(e.target.value)}>
          {TOPICS.map((t) => (
            <option key={t.id} value={t.id}>
              {t.label}
            </option>
          ))}
        </select>
      </header>
      <main>
        <section className="content">
          {mode === 'lesson' && <LessonPanel sessionId={sessionId} topic={topic} />}
          {mode === 'practice' && (
            <PracticePanel sessionId={sessionId} topic={topic} onProfileUpdate={setProfile} />
          )}
          {mode === 'chat' && <ChatPanel sessionId={sessionId} onProfileUpdate={setProfile} />}
        </section>
        <ProfilePanel profile={profile} />
      </main>
    </div>
  )
}
