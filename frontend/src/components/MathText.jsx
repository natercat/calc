import { useMemo } from 'react'
import katex from 'katex'

function renderSegment(segment, displayMode, key) {
  try {
    const html = katex.renderToString(segment, { throwOnError: false, displayMode })
    return <span key={key} dangerouslySetInnerHTML={{ __html: html }} />
  } catch {
    return <span key={key}>{segment}</span>
  }
}

export default function MathText({ text }) {
  const parts = useMemo(() => {
    if (!text) return []
    const pattern = /\$\$([^$]+)\$\$|\$([^$]+)\$/g
    const result = []
    let lastIndex = 0
    let match
    let key = 0
    while ((match = pattern.exec(text)) !== null) {
      if (match.index > lastIndex) {
        result.push(<span key={key++}>{text.slice(lastIndex, match.index)}</span>)
      }
      if (match[1] !== undefined) {
        result.push(renderSegment(match[1], true, key++))
      } else {
        result.push(renderSegment(match[2], false, key++))
      }
      lastIndex = pattern.lastIndex
    }
    if (lastIndex < text.length) {
      result.push(<span key={key++}>{text.slice(lastIndex)}</span>)
    }
    return result
  }, [text])

  return <p className="math-text">{parts}</p>
}
