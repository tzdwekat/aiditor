import { ScriptAnalysis } from '../types'

interface Annotation {
  start: number
  end: number
  type: 'broll' | 'edit' | 'cut' | 'expand'
  tool?: string
  tooltip: string
}

// All colours stay in the warm brown/amber family — no cool mauve or blue tones
const BROLL = {
  veo:          { bg: '#D8C8A8', border: '#7A5A20', emoji: '🎬' }, // warm parchment tan
  nano_banana:  { bg: '#E8D498', border: '#9A7010', emoji: '🍌' }, // honey gold
  stock:        { bg: '#C8D4B0', border: '#4A5E28', emoji: '📼' }, // muted olive
  'self-shot':  { bg: '#E0D0B0', border: '#8A6828', emoji: '🎥' }, // warm sand
} as Record<string, { bg: string; border: string; emoji: string }>

const ANNO = {
  edit:   { bg: '#F0E0A8', border: '#A86010', dashed: true,  emoji: '✏️' }, // amber
  cut:    { bg: '#E8C0B0', border: '#8B3820', dashed: false, emoji: '✂️' }, // dusty terracotta
  expand: { bg: '#C8D8B0', border: '#3A5A20', dashed: false, emoji: '➕' }, // sage
} as Record<string, { bg: string; border: string; dashed: boolean; emoji: string }>

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

export function buildAnnotatedHTML(scriptText: string, analysis: ScriptAnalysis): string {
  const anns: Annotation[] = []

  for (const shot of analysis.broll_opportunities) {
    const raw = shot.script_excerpt.trim()
    if (raw.length < 10) continue
    let idx = scriptText.indexOf(raw)
    let used = raw
    if (idx === -1 && raw.length > 60) { used = raw.slice(0, 70); idx = scriptText.indexOf(used) }
    if (idx === -1) continue
    const s = BROLL[shot.tool_recommendation]
    anns.push({ start: idx, end: idx + used.length, type: 'broll', tool: shot.tool_recommendation,
      tooltip: `${s?.emoji ?? '📹'} ${shot.tool_recommendation}: ${shot.suggested_visual}` })
  }

  for (const edit of analysis.line_edits) {
    const orig = edit.original.trim()
    if (orig.length < 10) continue
    const idx = scriptText.indexOf(orig)
    if (idx === -1) continue
    anns.push({ start: idx, end: idx + orig.length, type: 'edit',
      tooltip: `Suggested: ${edit.suggested}` })
  }

  for (const sugg of analysis.structural_suggestions) {
    if (sugg.type !== 'cut' && sugg.type !== 'expand') continue
    const m = sugg.section.match(/[''""«]([^''""\n»]{15,})[''""»]/)
    if (!m) continue
    const idx = scriptText.indexOf(m[1])
    if (idx === -1) continue
    const paraEnd = scriptText.indexOf('\n\n', idx + 30)
    const end = Math.min(idx + 250, paraEnd !== -1 ? paraEnd : idx + 250)
    anns.push({ start: idx, end, type: sugg.type as 'cut' | 'expand',
      tooltip: `${sugg.type === 'cut' ? '✂️ Cut' : '➕ Expand'}: ${sugg.rationale.slice(0, 120)}` })
  }

  anns.sort((a, b) => a.start - b.start)
  const clean: Annotation[] = []
  let cursor = 0
  for (const a of anns) { if (a.start >= cursor) { clean.push(a); cursor = a.end } }

  const parts: string[] = []
  let prev = 0
  for (const { start, end, type, tool, tooltip } of clean) {
    parts.push(esc(scriptText.slice(prev, start)))
    const content = esc(scriptText.slice(start, end))
    const tip = esc(tooltip)
    let style: string, emoji: string
    if (type === 'broll' && tool) {
      const s = BROLL[tool]
      style = `background:${s.bg};border-bottom:2px solid ${s.border}`
      emoji = s.emoji
    } else {
      const s = ANNO[type]
      style = `background:${s.bg};border-bottom:2px ${s.dashed ? 'dashed' : 'solid'} ${s.border}`
      emoji = s.emoji
    }
    parts.push(
      `<span style="${style};padding:1px 4px;border-radius:2px;cursor:help;" title="${tip}">${content}</span>` +
      `<sup style="font-size:0.65em;margin-left:1px">${emoji}</sup>`
    )
    prev = end
  }
  parts.push(esc(scriptText.slice(prev)))

  const body = parts.join('').replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>')

  const legendItems = [
    { ...BROLL.veo,          label: 'Veo' },
    { ...BROLL.nano_banana,  label: 'NanaBanana' },
    { ...BROLL.stock,        label: 'Stock' },
    { ...BROLL['self-shot'], label: 'Self-shot' },
    { ...ANNO.edit,          label: 'Line edit' },
    { ...ANNO.cut,           label: 'Cut' },
    { ...ANNO.expand,        label: 'Expand' },
  ]

  const legend = `
    <div style="margin-bottom:1.4rem;padding:.8rem 1rem;background:#F0E4C8;border:1px solid #8B6914;border-radius:3px;font-family:Georgia,serif;font-size:.81em;line-height:2.3;">
      <strong>Annotation key</strong> — hover any highlight for detail<br>
      ${legendItems.map(l =>
        `<span style="background:${l.bg};border-bottom:2px ${'dashed' in l && l.dashed ? 'dashed' : 'solid'} ${l.border};padding:1px 7px;margin-right:5px;border-radius:2px;">${l.emoji} ${l.label}</span>`
      ).join(' ')}
    </div>`

  return `<div style="font-family:Georgia,serif;line-height:2.1;font-size:.97em;max-width:860px;color:#2C1810;">${legend}${body}</div>`
}
