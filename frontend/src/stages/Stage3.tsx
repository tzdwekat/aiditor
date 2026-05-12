import { ShotList } from '../types'

interface Props {
  shotList: ShotList
  onBack: () => void
  onGenerate: () => void
}

export function Stage3({ shotList, onBack, onGenerate }: Props) {
  const byTool: Record<string, typeof shotList.shots> = {}
  for (const s of shotList.shots) {
    ;(byTool[s.tool] ??= []).push(s)
  }

  return (
    <div>
      <h2 className="section-title">III. Review Production Prompts</h2>
      <p className="font-serif text-ink-muted mb-5">
        Review each prompt before sending to the generators. These go directly to Veo and NanaBanana.
      </p>

      {byTool.veo && (
        <div className="alert-warn mb-5">
          ⚠️ {byTool.veo.length} Veo generation{byTool.veo.length !== 1 ? 's' : ''} will run.
          Each takes 1–3 minutes and costs API credits (~$0.50–3.00 per clip).
        </div>
      )}

      {Object.entries(byTool).map(([tool, shots]) => (
        <div key={tool} className="mb-6">
          <h3 className="font-display text-base text-ink mb-3">
            <code className="bg-tab-bar px-2 py-0.5 rounded text-sm font-mono">{tool}</code>
            {' '}— {shots.length} shot{shots.length !== 1 ? 's' : ''}
          </h3>
          {shots.map(shot => (
            <div key={shot.shot_index} className="card">
              <p className="font-display font-semibold text-ink mb-2">Shot {shot.shot_index}</p>
              <pre className="bg-tab-bar border border-gold rounded-sm p-3 text-sm font-mono text-ink whitespace-pre-wrap leading-relaxed">
                {shot.production_prompt}
              </pre>
              {shot.alternates.length > 0 && (
                <details className="mt-2">
                  <summary className="text-xs text-ink-muted cursor-pointer font-serif">
                    Alternate phrasings ({shot.alternates.length})
                  </summary>
                  <div className="mt-2 space-y-2">
                    {shot.alternates.map((alt, i) => (
                      <pre key={i} className="bg-tab-bar border border-gold-border rounded-sm p-2 text-xs font-mono text-ink whitespace-pre-wrap">
                        {alt}
                      </pre>
                    ))}
                  </div>
                </details>
              )}
            </div>
          ))}
        </div>
      ))}

      <hr className="divider" />
      <div className="flex gap-3">
        <button className="btn" onClick={onBack}>← Back to Analysis</button>
        <button className="btn-primary" onClick={onGenerate}>Generate All Assets →</button>
      </div>
    </div>
  )
}
