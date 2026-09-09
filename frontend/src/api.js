const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request to ${path} failed (${res.status})`)
  }
  return res.json()
}

export function createSession() {
  return request('/api/session', { method: 'POST' })
}

export function fetchLesson(topic, sessionId) {
  return request(`/api/lessons/${topic}?session_id=${sessionId}`)
}

export function startPractice(sessionId, topic) {
  return request('/api/practice/start', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, topic }),
  })
}

export function submitStep(sessionId, problemId, studentAnswer, imageBase64) {
  return request('/api/practice/step', {
    method: 'POST',
    body: JSON.stringify({
      session_id: sessionId,
      problem_id: problemId,
      student_answer: studentAnswer || null,
      image_base64: imageBase64 || null,
    }),
  })
}

export function sendChatMessage(sessionId, message, imageBase64) {
  return request('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ session_id: sessionId, message, image_base64: imageBase64 || null }),
  })
}
