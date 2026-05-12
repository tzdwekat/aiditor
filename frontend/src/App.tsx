import { useState } from 'react'
import { AppStage, BrollOpportunity, GenerationResult, ScriptAnalysis, ShotList } from './types'
import { Stage1 } from './stages/Stage1'
import { Stage2 } from './stages/Stage2'
import { Stage3 } from './stages/Stage3'
import { Stage4 } from './stages/Stage4'
import { PencilLoader } from './components/PencilLoader'

async function readSSE(
  res: Response,
  onEvent: (data: Record<string, unknown>) => void,
): Promise<void> {
  const reader = res.body!.getReader()
  const dec = new TextDecoder()
  let buf = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += dec.decode(value, { stream: true })
    const lines = buf.split('\n')
    buf = lines.pop() ?? ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try { onEvent(JSON.parse(line.slice(6))) } catch {}
      }
    }
  }
}

export default function App() {
  const [stage, setStage]       = useState<AppStage>('input')
  const [scriptText, setScriptText]   = useState('')
  const [scriptName, setScriptName]   = useState('untitled')
  const [analysis, setAnalysis]       = useState<ScriptAnalysis | null>(null)
  const [shotList, setShotList]       = useState<ShotList | null>(null)
  const [genResults, setGenResults]   = useState<GenerationResult[]>([])
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState<string | null>(null)
  const [pageTurn, setPageTurn]       = useState<'out' | 'in' | null>(null)

  const reset = () => {
    setStage('input'); setScriptText(''); setScriptName('untitled')
    setAnalysis(null); setShotList(null); setGenResults([])
    setLoading(false); setError(null)
  }

  // ── Stage 1 → 2: stream analysis ─────────────────────────────────────────
  const handleAnalyze = async (text: string, name: string) => {
    setScriptText(text); setScriptName(name)
    setLoading(true); setError(null)
    let pending: ScriptAnalysis | null = null
    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ script_text: text }),
      })
      if (!res.ok) throw new Error(await res.text())
      await readSSE(res, ev => {
        if (ev.type === 'complete') {
          pending = ev.analysis as ScriptAnalysis
        } else if (ev.type === 'error') {
          setError(ev.message as string)
        }
      })
    } catch (e) {
      setError(String(e))
    }
    setLoading(false)
    if (pending) {
      setPageTurn('out')
      setTimeout(() => {
        setAnalysis(pending)
        setStage('analysis')
        setPageTurn('in')
        setTimeout(() => setPageTurn(null), 600)
      }, 600)
    }
  }

  // ── Stage 2 → 3: generate prompts ────────────────────────────────────────
  const handleGeneratePrompts = async (approved: BrollOpportunity[]) => {
    setLoading(true); setError(null)
    try {
      const res = await fetch('/api/shots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shots: approved }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setShotList(data)
      setStage('prompts')
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  // ── Stage 3 → 4: generate assets ─────────────────────────────────────────
  const handleGenerate = async () => {
    if (!shotList) return
    setStage('generating')
    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ shots: shotList.shots, script_name: scriptName }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setGenResults(data.results)
      setStage('results')
    } catch (e) {
      setError(String(e))
      setStage('prompts')
    }
  }

  return (
    <div className="min-h-screen bg-desk px-16">
      <div className="paper-stack">
        <div className={`paper${pageTurn === 'out' ? ' page-turn-out' : pageTurn === 'in' ? ' page-turn-in' : ''}`}>
        {/* Header */}
        <div className="flex justify-between items-start mb-6">
          <div>
            <h1 className="font-display text-4xl border-b-2 border-gold pb-1">
              <span className="text-gold-DEFAULT" style={{ color: '#8B6914' }}>AI</span>
              <span className="text-ink">ditor</span>
            </h1>
            <p className="font-serif text-sm text-ink-muted mt-1">
              AI-assisted video essay production pipeline
            </p>
          </div>
          {stage !== 'input' && (
            <button className="btn text-sm" onClick={reset}>Start Over</button>
          )}
        </div>

        <hr className="divider" />

        {/* Generating spinner */}
        {stage === 'generating' && (
          <div className="flex flex-col items-center justify-center py-20 gap-4">
            <div className="spinner w-10 h-10 border-4" />
            <p className="font-serif text-ink-muted">
              Generating assets… Veo shots may take 1–3 minutes each.
            </p>
          </div>
        )}

        {/* Analysis loading state */}
        {loading && stage === 'input' && <PencilLoader />}

        {/* Stages */}
        {stage === 'input' && !loading && (
          <Stage1 onAnalyze={handleAnalyze} loading={false} error={error} />
        )}
        {stage === 'analysis' && analysis && (
          <Stage2
            analysis={analysis}
            scriptText={scriptText}
            onGeneratePrompts={handleGeneratePrompts}
            loading={loading}
            error={error}
          />
        )}
        {stage === 'prompts' && shotList && (
          <Stage3
            shotList={shotList}
            onBack={() => setStage('analysis')}
            onGenerate={handleGenerate}
          />
        )}
        {stage === 'results' && analysis && (
          <Stage4
            results={genResults}
            analysis={analysis}
            scriptText={scriptText}
            onReset={reset}
          />
        )}

        {/* Footer */}
        <hr className="divider mt-16" />
        <p className="font-serif text-xs text-ink-muted">
          <strong>AIditor</strong> · AI-assisted video essay production ·{' '}
          <a href="https://github.com/tzdwekat/aiditor" className="underline hover:text-ink">
            GitHub
          </a>
        </p>
        </div>{/* end .paper */}
      </div>{/* end .paper-stack */}
    </div>
  )
}
