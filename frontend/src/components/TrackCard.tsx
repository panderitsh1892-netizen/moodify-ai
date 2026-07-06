/**
 * TrackCard — displays a single track with mood badge
 */

import MoodBadge from './MoodBadge'

interface Track {
  id: number
  title: string
  artist: string
  album: string | null
  album_art_url: string | null
  mood_category: string | null
  played_at: string
  valence: number | null
  energy: number | null
}

interface Props {
  track: Track
}

function formatDate(dateStr: string) {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function TrackCard({ track }: Props) {
  return (
    <div className="track-card">
      {track.album_art_url ? (
        <img
          src={track.album_art_url}
          alt={track.album ?? ''}
          className="track-art"
        />
      ) : (
        <div className="track-art track-art-placeholder">🎵</div>
      )}

      <div className="track-info">
        <div className="track-title">{track.title}</div>
        <div className="track-artist">{track.artist}</div>
        {track.album && (
          <div className="track-album">{track.album}</div>
        )}
      </div>

      <div className="track-meta">
        {track.mood_category ? (
          <MoodBadge mood={track.mood_category} size="sm" />
        ) : (
          <span className="track-uncategorized">Uncategorized</span>
        )}
        <div className="track-date">{formatDate(track.played_at)}</div>
      </div>
    </div>
  )
}
