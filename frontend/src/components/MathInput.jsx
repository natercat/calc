import { useRef, useState } from 'react'

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result.split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export default function MathInput({ onSubmit, placeholder, disabled }) {
  const [text, setText] = useState('')
  const [imagePreview, setImagePreview] = useState(null)
  const [imageBase64, setImageBase64] = useState(null)
  const fileInputRef = useRef(null)

  async function handleFile(e) {
    const file = e.target.files?.[0]
    if (!file) return
    const base64 = await fileToBase64(file)
    setImageBase64(base64)
    setImagePreview(URL.createObjectURL(file))
  }

  function clearImage() {
    setImageBase64(null)
    setImagePreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (!text.trim() && !imageBase64) return
    onSubmit(text.trim(), imageBase64)
    setText('')
    clearImage()
  }

  return (
    <form className="math-input" onSubmit={handleSubmit}>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        rows={2}
      />
      <div className="math-input-controls">
        <label className="upload-button">
          Upload photo
          <input type="file" accept="image/*" ref={fileInputRef} onChange={handleFile} hidden />
        </label>
        {imagePreview && (
          <span className="image-preview">
            <img src={imagePreview} alt="upload preview" />
            <button type="button" onClick={clearImage}>x</button>
          </span>
        )}
        <button type="submit" disabled={disabled}>Send</button>
      </div>
    </form>
  )
}
