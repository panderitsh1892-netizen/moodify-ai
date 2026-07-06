/**
 * MoodBadge — colored pill showing a mood category
 */

const MOOD_COLORS: Record<string, { bg: string; text: string }> = {
  Romantic:    { bg: '#ff6b9d22', text: '#ff6b9d' },
  Happy:       { bg: '#ffd93d22', text: '#ffd93d' },
  Energetic:   { bg: '#6bcb7722', text: '#6bcb77' },
  Melancholic: { bg: '#74b9ff22', text: '#74b9ff' },
  Angry:       { bg: '#ff767522', text: '#ff7675' },
  Chill:       { bg: '#a29bfe22', text: '#a29bfe' },
}

const MOOD_EMOJIS: Record<string, string> = {
  Romantic:    '🌹',
  Happy:       '⭐',
  Energetic:   '⚡',
  Melancholic: '🌧️',
  Angry:       '🔥',
  Chill:       '😌',
}

interface Props {
  mood: string
  size?: 'sm' | 'md'
}

export default function MoodBadge({ mood, size = 'md' }: Props) {
  const colors = MOOD_COLORS[mood] ?? { bg: '#ffffff22', text: '#ffffff' }
  const emoji = MOOD_EMOJIS[mood] ?? '🎵'

  return (
    <span
      style={{
        backgroundColor: colors.bg,
        color: colors.text,
        border: `1px solid ${colors.text}44`,
        padding: size === 'sm' ? '2px 8px' : '4px 12px',
        borderRadius: '999px',
        fontSize: size === 'sm' ? '11px' : '13px',
        fontWeight: 600,
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        whiteSpace: 'nowrap',
      }}
    >
      {emoji} {mood}
    </span>
  )
}
