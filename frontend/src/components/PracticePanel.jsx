import { useEffect, useState } from 'react'
import { startPractice, submitStep } from '../api'
import MathInput from './MathInput'
import MathText from './MathText'

export default function PracticePanel({ sessionId, topic, onProfileUpdate }) {
  const [problem, setProblem] = useState(null)
  const [transcript, setTranscript] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    setProblem(null)
    setTranscript([])
    setError(null)
  }, [topic])

  async function newProblem() {
    setLoading(true)
    setTranscript([])
    setError(null)
    try {
      const p = await startPractice(sessionId, topic)
      setProblem(p)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit(text, imageBase64) {
    if (!problem) return
    setLoading(true)
    setError(null)
    try {
      const result = await submitStep(sessionId, problem.problem_id, text, imageBase64)
      setTranscript((t) => [
        ...t,
        { role: 'student', text: text || '(photo)' },
        { role: 'tutor', text: result.reply },
      ])
      onProfileUpdate(result.profile)
      if (result.solved) {
        setTranscript((t) => [...t, { role: 'system', text: 'Solved! Start a new problem when ready.' }])
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="practice-panel">
      {!problem && (
        <button onClick={newProblem} disabled={loading}>
          Start a practice problem
        </button>
      )}
      {problem && (
        <>
          <p className="prompt"><code>{problem.prompt}</code></p>
          <div className="transcript">
            {transcript.map((entry, i) => (
              <div key={i} className={`bubble ${entry.role}`}>
                {entry.role === 'tutor' ? <MathText text={entry.text} /> : <p>{entry.text}</p>}
              </div>
            ))}
          </div>
          {error && <p className="error">{error}</p>}
          <MathInput onSubmit={handleSubmit} disabled={loading} placeholder="Type your answer..." />
          <button className="secondary" onClick={newProblem} disabled={loading}>
            New problem
          </button>
        </>
      )}
      {!problem && error && <p className="error">{error}</p>}
    </div>
  )
}
