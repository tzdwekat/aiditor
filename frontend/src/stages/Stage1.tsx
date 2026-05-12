import { useState, useRef } from 'react'

interface Props {
  onAnalyze: (scriptText: string, scriptName: string) => void
  loading: boolean
  error: string | null
}

export function Stage1({ onAnalyze, loading, error }: Props) {
  const [mode, setMode] = useState<'paste' | 'upload'>('paste')
  const [text, setText] = useState('')
  const [uploadedText, setUploadedText] = useState('')
  const [uploadedName, setUploadedName] = useState('')
  const [uploadError, setUploadError] = useState('')
  const [uploading, setUploading] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const handleUpload = async (file: File) => {
    setUploading(true)
    setUploadError('')
    const form = new FormData()
    form.append('file', file)
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: form })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setUploadedText(data.text)
      setUploadedName(data.filename)
    } catch (e) {
      setUploadError(String(e))
    } finally {
      setUploading(false)
    }
  }

  const activeText  = mode === 'paste' ? text : uploadedText
  const activeName  = mode === 'paste' ? 'pasted_script' : uploadedName.replace(/\.[^.]+$/, '')
  const canSubmit   = activeText.trim().length > 0 && !loading && !uploading

  return (
    <div>
      <h2 className="section-title">I. Provide Your Script</h2>

      {/* Mode toggle */}
      <div className="flex gap-2 mb-5">
        {(['paste', 'upload'] as const).map(m => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={mode === m ? 'btn-primary' : 'btn'}
          >
            {m === 'paste' ? 'Paste text' : 'Upload file (PDF, DOCX, TXT, MD)'}
          </button>
        ))}
      </div>

      {mode === 'paste' ? (
        <form
          onSubmit={e => { e.preventDefault(); if (canSubmit) onAnalyze(text, activeName) }}
        >
          <textarea
            className="field h-80 resize-y leading-relaxed"
            placeholder="Paste the full text of your video essay script here…"
            value={text}
            onChange={e => setText(e.target.value)}
          />
          <button
            type="submit"
            className="btn-primary mt-4 w-full text-center"
            disabled={!canSubmit}
          >
            {loading ? <><span className="spinner mr-2" /> Analysing…</> : 'Analyse Script →'}
          </button>
        </form>
      ) : (
        <div>
          <div
            className="border border-dashed border-gold bg-paper-card rounded-sm p-8 text-center cursor-pointer hover:bg-tab-hover transition-colors"
            onClick={() => fileRef.current?.click()}
          >
            <p className="text-ink-muted font-serif">
              Click to select a file — PDF, DOCX, TXT, or MD
            </p>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.docx,.txt,.md"
              className="hidden"
              onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f) }}
            />
          </div>

          {uploading && (
            <p className="mt-3 font-serif text-ink-muted flex items-center gap-2">
              <span className="spinner" /> Extracting text…
            </p>
          )}
          {uploadError && <div className="alert-error mt-3">{uploadError}</div>}
          {uploadedText && (
            <div className="mt-4">
              <p className="font-serif text-ink-muted mb-2">
                ✓ Loaded <strong>{uploadedName}</strong> — {uploadedText.length.toLocaleString()} characters
              </p>
              <details className="card">
                <summary className="cursor-pointer font-serif text-ink-muted">Preview extracted text</summary>
                <pre className="mt-2 text-xs whitespace-pre-wrap font-serif text-ink leading-relaxed">
                  {uploadedText.slice(0, 1500)}{uploadedText.length > 1500 ? '…' : ''}
                </pre>
              </details>
              <button
                className="btn-primary mt-4 w-full"
                disabled={!canSubmit}
                onClick={() => onAnalyze(uploadedText, activeName)}
              >
                {loading ? <><span className="spinner mr-2" /> Analysing…</> : 'Analyse Script →'}
              </button>
            </div>
          )}
        </div>
      )}

      {error && <div className="alert-error mt-4">{error}</div>}
    </div>
  )
}
