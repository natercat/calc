import { useMemo } from 'react'
import { renderMathSegments } from './MathText'

// Lesson text uses a small fixed subset of markdown (## headings,
// **bold**, *italic*) around inline/display math ($...$, $$...$$). This
// renders all of it -- plain <pre> text would show '$\frac{x^2}{2}$'
// literally instead of a rendered fraction, which is exactly the kind of
// thing that makes a lesson unreadable to someone new to the notation.
function renderParagraph(text, key) {
  if (text.startsWith('## ')) {
    return (
      <h3 key={key} className="lesson-heading">
        {text.slice(3).trim()}
      </h3>
    )
  }

  const emphasisPattern = /\*\*([^*]+)\*\*|\*([^*]+)\*/g
  const pieces = []
  let lastIndex = 0
  let match
  let i = 0
  while ((match = emphasisPattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      pieces.push(...renderMathSegments(text.slice(lastIndex, match.index), `${key}-${i++}`))
    }
    if (match[1] !== undefined) {
      pieces.push(<strong key={`${key}-${i++}`}>{match[1]}</strong>)
    } else {
      pieces.push(<em key={`${key}-${i++}`}>{match[2]}</em>)
    }
    lastIndex = emphasisPattern.lastIndex
  }
  if (lastIndex < text.length) {
    pieces.push(...renderMathSegments(text.slice(lastIndex), `${key}-${i++}`))
  }
  return (
    <p key={key} className="lesson-paragraph">
      {pieces}
    </p>
  )
}

export default function LessonContent({ text }) {
  const paragraphs = useMemo(() => (text || '').split(/\n\n+/).map((p) => p.trim()).filter(Boolean), [text])
  return <div className="lesson-content">{paragraphs.map((p, i) => renderParagraph(p, i))}</div>
}
