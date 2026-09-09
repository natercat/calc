import { useMemo } from 'react'
import katex from 'katex'

function renderMathSegment(segment, displayMode, key) {
  try {
    const html = katex.renderToString(segment, { throwOnError: false, displayMode })
    return <span key={key} dangerouslySetInnerHTML={{ __html: html }} />
  } catch {
    return <span key={key}>{segment}</span>
  }
}

// Splits text on $$...$$ (display math) and $...$ (inline math), rendering
// the math segments with KaTeX and leaving everything else as plain text.
// Exported separately from the MathText component so other renderers (e.g.
// lesson content, which also needs to handle **bold**/*italic* markdown
// around the math) can reuse the same math-splitting logic.
export function renderMathSegments(text, keyPrefix = '') {
  if (!text) return []
  const pattern = /\$\$([^$]+)\$\$|\$([^$]+)\$/g
  const result = []
  let lastIndex = 0
  let match
  let i = 0
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      result.push(<span key={`${keyPrefix}-${i++}`}>{text.slice(lastIndex, match.index)}</span>)
    }
    if (match[1] !== undefined) {
      result.push(renderMathSegment(match[1], true, `${keyPrefix}-${i++}`))
    } else {
      result.push(renderMathSegment(match[2], false, `${keyPrefix}-${i++}`))
    }
    lastIndex = pattern.lastIndex
  }
  if (lastIndex < text.length) {
    result.push(<span key={`${keyPrefix}-${i++}`}>{text.slice(lastIndex)}</span>)
  }
  return result
}

export default function MathText({ text }) {
  const parts = useMemo(() => renderMathSegments(text, 'm'), [text])
  return <p className="math-text">{parts}</p>
}
