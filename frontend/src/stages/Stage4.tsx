import { GenerationResult, ScriptAnalysis } from '../types'
import { Tabs } from '../components/Tabs'
import { buildAnnotatedHTML } from '../utils/annotatedScript'

interface Props {
  results: GenerationResult[]
  analysis: ScriptAnalysis
  scriptText: string
  onReset: () => void
}

export function Stage4({ results, analysis, scriptText, onReset }: Props) {
  const successes = results.filter(r => r.success)
  const failures  = results.filter(r => !r.success)

  const byTool: Record<string, GenerationResult[]> = {}
  for (const r of successes) { (byTool[r.tool] ??= []).push(r) }

  const cuts    = analysis.structural_suggestions.filter(s => s.type === 'cut')
  const expands = analysis.structural_suggestions.filter(s => s.type === 'expand')
  const reorders= analysis.structural_suggestions.filter(s => s.type === 'reorder')

  const assetsTab = (
    <div>
      {byTool.nano_banana && (
        <div className="mb-6">
          <h3 className="font-display text-base text-ink mb-3">🍌 Generated Images</h3>
          <div className="grid grid-cols-3 gap-4">
            {byTool.nano_banana.map(r => (
              <div key={r.shot_index} className="card p-0 overflow-hidden">
                <img src={r.output_url!} alt={`Shot ${r.shot_index}`} className="w-full object-cover" />
                <p className="font-serif text-xs text-ink-muted p-2">Shot {r.shot_index}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {byTool.veo && (
        <div className="mb-6">
          <h3 className="font-display text-base text-ink mb-3">🎬 Generated Videos</h3>
          {byTool.veo.map(r => (
            <div key={r.shot_index} className="card">
              <p className="font-display font-semibold text-ink mb-2">Shot {r.shot_index}</p>
              <video src={r.output_url!} controls className="w-full rounded-sm" />
            </div>
          ))}
        </div>
      )}
      {byTool.stock && (
        <div className="mb-6">
          <h3 className="font-display text-base text-ink mb-3">📼 Stock Search Queries</h3>
          {byTool.stock.map(r => (
            <div key={r.shot_index} className="card">
              <p className="font-serif text-sm text-ink-muted">Shot {r.shot_index}</p>
            </div>
          ))}
        </div>
      )}
      {byTool['self-shot'] && (
        <div className="mb-6">
          <h3 className="font-display text-base text-ink mb-3">🎥 Shooting Notes</h3>
          {byTool['self-shot'].map(r => (
            <div key={r.shot_index} className="card">
              <p className="font-serif text-sm text-ink-muted">Shot {r.shot_index}</p>
            </div>
          ))}
        </div>
      )}
      {failures.length > 0 && (
        <details className="card border-red-300">
          <summary className="cursor-pointer font-serif text-red-700">
            ⚠️ {failures.length} failed shot{failures.length !== 1 ? 's' : ''}
          </summary>
          {failures.map(r => (
            <p key={r.shot_index} className="font-serif text-sm text-red-600 mt-1">
              Shot {r.shot_index} ({r.tool}): {r.error}
            </p>
          ))}
        </details>
      )}
    </div>
  )

  const scriptTab = (
    <div>
      <h3 className="font-display text-lg text-ink mb-2">The Script — Fully Annotated</h3>
      <p className="font-serif text-sm text-ink-muted mb-5">
        Hover any highlight to see the annotation detail.
      </p>
      <div dangerouslySetInnerHTML={{ __html: buildAnnotatedHTML(scriptText, analysis) }} />

      <hr className="divider" />

      <h3 className="font-display text-lg text-ink mb-4">🎵 Musical Score Guide</h3>
      {analysis.music_tone_per_section.map((m, i) => (
        <div key={i} className="card flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <p className="font-display font-semibold text-ink">{m.section}</p>
            <p className="font-serif text-sm italic text-ink-muted">{m.tone} · {m.tempo}</p>
          </div>
          <div className="flex-1">
            {m.suggested_track && <p className="font-serif text-sm text-ink mb-1">🎵 {m.suggested_track}</p>}
            <p className="font-serif text-xs text-ink-muted">{m.rationale}</p>
          </div>
        </div>
      ))}

      <hr className="divider" />

      <h3 className="font-display text-lg text-ink mb-4">🏗️ Structural Changes Reference</h3>
      {cuts.length > 0 && (
        <div className="mb-4">
          <p className="font-serif font-semibold text-ink mb-2">✂️ Cut</p>
          {cuts.map((s, i) => <p key={i} className="font-serif text-sm text-ink mb-1">— <em>{s.section}</em> — {s.rationale}</p>)}
        </div>
      )}
      {expands.length > 0 && (
        <div className="mb-4">
          <p className="font-serif font-semibold text-ink mb-2">➕ Expand</p>
          {expands.map((s, i) => <p key={i} className="font-serif text-sm text-ink mb-1">— <em>{s.section}</em> — {s.rationale}</p>)}
        </div>
      )}
      {reorders.length > 0 && (
        <div className="mb-4">
          <p className="font-serif font-semibold text-ink mb-2">🔀 Reorder</p>
          {reorders.map((s, i) => <p key={i} className="font-serif text-sm text-ink mb-1">— <em>{s.section}</em> — {s.rationale}</p>)}
        </div>
      )}
    </div>
  )

  return (
    <div>
      <h2 className="section-title">IV. Generated Assets & Annotated Script</h2>

      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="card text-center">
          <p className="font-display text-3xl text-ink">{successes.length}</p>
          <p className="font-serif text-sm text-ink-muted">Succeeded</p>
        </div>
        <div className="card text-center">
          <p className="font-display text-3xl text-ink">{failures.length}</p>
          <p className="font-serif text-sm text-ink-muted">Failed</p>
        </div>
      </div>

      <Tabs tabs={[
        { label: 'Generated Assets', content: assetsTab },
        { label: 'Annotated Script', content: scriptTab },
      ]} />

      <hr className="divider" />
      <button className="btn-primary" onClick={onReset}>Analyse Another Script</button>
    </div>
  )
}
