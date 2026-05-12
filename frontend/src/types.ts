export interface BrollOpportunity {
  timestamp_estimate: string
  script_excerpt: string
  suggested_visual: string
  priority: 'high' | 'medium' | 'low'
  tool_recommendation: 'veo' | 'nano_banana' | 'stock' | 'self-shot'
  rationale: string
}

export interface StructuralSuggestion {
  type: 'reorder' | 'cut' | 'expand'
  section: string
  rationale: string
}

export interface LineEdit {
  original: string
  suggested: string
  reason: string
}

export interface MusicTone {
  section: string
  tone: string
  tempo: string
  rationale: string
  suggested_track?: string
}

export interface ScriptAnalysis {
  overall_assessment: string
  strengths: string[]
  weaknesses: string[]
  structural_suggestions: StructuralSuggestion[]
  line_edits: LineEdit[]
  broll_opportunities: BrollOpportunity[]
  music_tone_per_section: MusicTone[]
}

export interface ProductionShot {
  shot_index: number
  tool: string
  production_prompt: string
  alternates: string[]
}

export interface ShotList {
  shots: ProductionShot[]
}

export interface GenerationResult {
  shot_index: number
  tool: string
  success: boolean
  error?: string
  output_url?: string
}

export type AppStage = 'input' | 'analysis' | 'prompts' | 'generating' | 'results'
