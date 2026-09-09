import { useEffect, useState } from 'react'
import { fetchLesson } from '../api'
import MathText from './MathText'

export default function LessonPanel({ sessionId, topic }) {
  const [lesson, setLesson] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLesson(null)
    setError(null)
    fetchLesson(topic, sessionId).then(setLesson).catch((e) => setError(e.message))
  }, [topic, sessionId])

  if (error) return <p className="error">{error}</p>
  if (!lesson) return <p>Loading lesson...</p>

  return (
    <div className="lesson-panel">
      <MathText text={lesson.intro} />
      <pre className="lesson-content">{lesson.content}</pre>
    </div>
  )
}
