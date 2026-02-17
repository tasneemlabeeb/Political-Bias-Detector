export interface Article {
  id: string
  title: string
  link: string
  summary?: string
  content?: string
  published: string
  source_name: string
  political_bias: 'Left-Leaning' | 'Center-Left' | 'Centrist' | 'Center-Right' | 'Right-Leaning'
  ml_bias?: string
  ml_confidence?: number
  ml_explanation?: string
  bias_intensity?: number
  ml_direction_score?: number
  ml_lexical_left_hits?: number
  ml_lexical_right_hits?: number
  ml_loaded_language_hits?: number
}

export interface FilterState {
  sources: string[]
  biases: string[]
  keyword: string
  dateFrom: Date
  dateTo: Date
  sortBy: 'date-desc' | 'date-asc' | 'source' | 'confidence'
  minConfidence: number
}

export const BIAS_COLORS: Record<string, string> = {
  'Left-Leaning': '#1565C0',
  'Center-Left': '#42A5F5',
  'Centrist': '#78909C',
  'Center-Right': '#EF5350',
  'Right-Leaning': '#C62828',
}

export const BIAS_ORDER = ['Left-Leaning', 'Center-Left', 'Centrist', 'Center-Right', 'Right-Leaning']

export const BIAS_DISPLAY_NAMES: Record<string, string> = {
  'Left-Leaning': 'Far-Left',
  'Center-Left': 'Center-Left',
  'Centrist': 'Centrist',
  'Center-Right': 'Center-Right',
  'Right-Leaning': 'Far-Right',
}
