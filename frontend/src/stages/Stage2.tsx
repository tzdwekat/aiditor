import { useState } from 'react'
import { ScriptAnalysis, BrollOpportunity } from '../types'
import { Tabs } from '../components/Tabs'
import { buildAnnotatedHTML } from '../utils/annotatedScript'

interface Props {
  analysis: ScriptAnalysis
  scriptText: string
  onGeneratePrompts: (approved: BrollOpportunity[]) => void
  loading: boolean
  error: string | null
}

const PRIORITY_BADGE: Record<string, string> = {
  high: 'badge-high', medium: 'badge-medium', low: 'badge-low',
}
const TOOL_EMOJI: Record<string, string> = {
  veo: '🎬', nano_banana: '🍌', stock: '📼', 'self-shot': '🎥',
}
const GEN_LABEL: Record<string, string> = {
  veo: 'Generate this video?',
  nano_banana: 'Generate this image?',
  stock: 'Include stock query',
  'self-shot': 'Include shooting note',
}

export function Stage2({ analysis, scriptText, onGeneratePrompts, loading, error }: Props) {
  const [approved, setApproved] = useState<Set<number>>(new Set())

  const toggle = (i: number) =>
    setApproved(prev => { const s = new Set(prev); s.has(i) ? s.delete(i) : s.add(i); return s })

  const cuts     = analysis.structural_suggestions.filter(s => s.type === 'cut')
  const expands  = analysis.structural_suggestions.filter(s => s.type === 'expand')
  const reorders = analysis.structural_suggestions.filter(s => s.type === 'reorder')

  const tabs = [
    {
      label: 'Script Critique',
      content: (
        <div>
          <div className="grid grid-cols-2 gap-6 mb-6">
            <div>
              <h3 className="font-display text-lg text-ink mb-3">What's Working</h3>
              <ul className="space-y-1">
                {(analysis.strengths ?? []).map((s, i) => (
                  <li key={i} className="font-serif text-ink leading-relaxed">— {s}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="font-display text-lg text-ink mb-3">What Needs Work</h3>
              <ul className="space-y-1">
                {(analysis.weaknesses ?? []).map((w, i) => (
                  <li key={i} className="font-serif text-ink leading-relaxed">— {w}</li>
                ))}
              </ul>
            </div>
          </div>

          <hr className="divider" />

          {cuts.length > 0 && (
            <div className="mb-5">
              <h3 className="font-display text-base text-ink mb-3">✂️ Cut</h3>
              {cuts.map((s, i) => (
                <div key={i} className="card">
                  <p className="font-serif font-semibold text-ink">{s.section}</p>
                  <p className="font-serif text-ink-muted text-sm mt-1">{s.rationale}</p>
                </div>
              ))}
            </div>
          )}
          {expands.length > 0 && (
            <div className="mb-5">
              <h3 className="font-display text-base text-ink mb-3">➕ Expand</h3>
              {expands.map((s, i) => (
                <div key={i} className="card">
                  <p className="font-serif font-semibold text-ink">{s.section}</p>
                  <p className="font-serif text-ink-muted text-sm mt-1">{s.rationale}</p>
                </div>
              ))}
            </div>
          )}
          {reorders.length > 0 && (
            <div className="mb-5">
              <h3 className="font-display text-base text-ink mb-3">🔀 Reorder</h3>
              {reorders.map((s, i) => (
                <div key={i} className="card">
                  <p className="font-serif font-semibold text-ink">{s.section}</p>
                  <p className="font-serif text-ink-muted text-sm mt-1">{s.rationale}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      ),
    },
    {
      label: `B-roll (${analysis.broll_opportunities.length})`,
      content: (
        <div>
          <div className="grid grid-cols-4 gap-3 mb-4 text-sm font-serif text-ink-muted">
            <span>🎬 <strong>veo</strong> — AI video</span>
            <span>🍌 <strong>nano_banana</strong> — AI image</span>
            <span>📼 <strong>stock</strong> — search query</span>
            <span>🎥 <strong>self-shot</strong> — film yourself</span>
          </div>
          <hr className="divider" />
          {analysis.broll_opportunities.map((shot, i) => (
            <div key={i} className="card flex gap-4">
              <div className="pt-1">
                <input
                  type="checkbox"
                  id={`shot-${i}`}
                  checked={approved.has(i)}
                  onChange={() => toggle(i)}
                  className="w-4 h-4 accent-burgundy cursor-pointer"
                />
              </div>
              <div className="flex-1 min-w-0">
                <label htmlFor={`shot-${i}`} className="cursor-pointer">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="font-display font-semibold text-ink">
                      Shot {i + 1} {TOOL_EMOJI[shot.tool_recommendation]}
                    </span>
                    <code className="text-xs bg-tab-bar px-1.5 py-0.5 rounded font-mono text-ink-light">
                      {shot.tool_recommendation}
                    </code>
                    <span className={PRIORITY_BADGE[shot.priority]}>{shot.priority.toUpperCase()}</span>
                    <span className="text-xs text-ink-muted">{shot.timestamp_estimate}</span>
                  </div>
                  <p className="font-serif text-sm text-ink-muted italic border-l-2 border-gold pl-3 mb-2">
                    {shot.script_excerpt}
                  </p>
                  <p className="font-serif text-sm text-ink">
                    <strong>Visual:</strong> {shot.suggested_visual}
                  </p>
                  <p className="font-serif text-xs text-burgundy mt-1">{GEN_LABEL[shot.tool_recommendation]}</p>
                </label>
                <details className="mt-2">
                  <summary className="text-xs text-ink-muted cursor-pointer font-serif">
                    Why this visual?
                  </summary>
                  <p className="text-sm font-serif text-ink mt-1">{shot.rationale}</p>
                </details>
              </div>
            </div>
          ))}
        </div>
      ),
    },
    {
      label: `Structure (${analysis.structural_suggestions.length})`,
      content: (
        <div>
          {analysis.structural_suggestions.map((s, i) => {
            const label = s.type === 'cut' ? '✂️ CUT' : s.type === 'expand' ? '➕ EXPAND' : '🔀 REORDER'
            return (
              <div key={i} className="card">
                <p className="font-serif font-semibold text-ink mb-1">
                  <span className="text-burgundy">{label}</span> — {s.section}
                </p>
                <p className="font-serif text-sm text-ink">{s.rationale}</p>
              </div>
            )
          })}
        </div>
      ),
    },
    {
      label: `Line Edits (${analysis.line_edits.length})`,
      content: (
        <div>
          {analysis.line_edits.map((edit, i) => (
            <div key={i} className="card">
              <p className="font-serif text-sm text-ink mb-2">
                <span className="font-semibold text-ink-muted">Original:</span> {edit.original}
              </p>
              <p className="font-serif text-sm text-ink mb-2">
                <span className="font-semibold text-green-800">Suggested:</span> {edit.suggested}
              </p>
              <p className="font-serif text-xs text-ink-muted italic">Why: {edit.reason}</p>
            </div>
          ))}
        </div>
      ),
    },
    {
      label: `Music (${analysis.music_tone_per_section.length})`,
      content: (
        <div>
          {analysis.music_tone_per_section.map((m, i) => (
            <div key={i} className="card">
              <div className="flex flex-col sm:flex-row sm:items-start gap-3">
                <div className="flex-1">
                  <p className="font-display font-semibold text-ink">{m.section}</p>
                  <p className="font-serif text-sm text-ink-muted italic">{m.tone} · {m.tempo}</p>
                </div>
                <div className="flex-1">
                  {m.suggested_track && (
                    <p className="font-serif text-sm text-ink mb-1">🎵 {m.suggested_track}</p>
                  )}
                  <p className="font-serif text-xs text-ink-muted">{m.rationale}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      ),
    },
    {
      label: 'Annotated Script',
      content: (
        <div>
          <p className="font-serif text-sm text-ink-muted mb-4">
            Hover any highlight to read the annotation detail.
          </p>
          <div
            dangerouslySetInnerHTML={{ __html: buildAnnotatedHTML(scriptText, analysis) }}
          />
        </div>
      ),
    },
  ]

  return (
    <div>
      <h2 className="section-title">II. Script Analysis</h2>
      <div className="alert mb-5">
        <strong>Overall:</strong> {analysis.overall_assessment}
      </div>

      <Tabs tabs={tabs} />

      <hr className="divider" />

      <div className="flex items-center gap-4">
        {approved.size === 0 ? (
          <button className="btn-primary" disabled>
            Generate Production Prompts
          </button>
        ) : (
          <button
            className="btn-primary"
            disabled={loading}
            onClick={() => {
              const shots = [...approved].sort().map(i => analysis.broll_opportunities[i])
              onGeneratePrompts(shots)
            }}
          >
            {loading
              ? <><span className="spinner mr-2" /> Generating prompts…</>
              : `Generate Prompts for ${approved.size} Shot${approved.size !== 1 ? 's' : ''} →`}
          </button>
        )}
        {approved.size === 0 && (
          <p className="font-serif text-sm text-ink-muted">
            Check at least one shot in the B-roll tab to continue.
          </p>
        )}
      </div>
      {error && <div className="alert-error mt-4">{error}</div>}
    </div>
  )
}
