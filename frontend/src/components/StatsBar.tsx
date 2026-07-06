/**
 * StatsBar — visual mood breakdown bar
 */

const MOOD_COLORS: Record<string, string> = {
  Romantic:    '#ff6b9d',
  Happy:       '#ffd93d',
  Energetic:   '#6bcb77',
  Melancholic: '#74b9ff',
  Angry:       '#ff7675',
  Chill:       '#a29bfe',
}

interface Props {
  moodBreakdown: Record<string, number>
  total: number
}

export default function StatsBar({ moodBreakdown, total }: Props) {
  if (total === 0) return null

  const moods = Object.entries(moodBreakdown).sort((a, b) => b[1] - a[1])

  return (
    <div className="stats-bar-container">
      {/* Stacked bar */}
      <div className="stats-bar">
        {moods.map(([mood, count]) => (
          <div
            key={mood}
            className="stats-bar-segment"
            style={{
              width: `${(count / total) * 100}%`,
              backgroundColor: MOOD_COLORS[mood] ?? '#888',
            }}
            title={`${mood}: ${count} tracks`}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="stats-legend">
        {moods.map(([mood, count]) => (
          <div key={mood} className="stats-legend-item">
            <span
              className="stats-legend-dot"
              style={{ backgroundColor: MOOD_COLORS[mood] ?? '#888' }}
            />
            <span className="stats-legend-label">{mood}</span>
            <span className="stats-legend-count">{count}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
