/**
 * PlaylistCard — displays a Spotify mood playlist
 */

import MoodBadge from './MoodBadge'

interface Playlist {
  id: number
  name: string
  mood_category: string
  spotify_url: string | null
  track_count: number
  last_synced_at: string | null
}

interface Props {
  playlist: Playlist
}

function formatDate(dateStr: string | null) {
  if (!dateStr) return 'Never'
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function PlaylistCard({ playlist }: Props) {
  return (
    <div className="playlist-card">
      <div className="playlist-header">
        <MoodBadge mood={playlist.mood_category} />
        <span className="playlist-track-count">
          {playlist.track_count} tracks
        </span>
      </div>

      <div className="playlist-name">{playlist.name}</div>

      <div className="playlist-footer">
        <span className="playlist-synced">
          Synced: {formatDate(playlist.last_synced_at)}
        </span>

        {playlist.spotify_url && (
          <a
            href={playlist.spotify_url}
            target="_blank"
            rel="noreferrer"
            className="spotify-link"
          >
            Open in Spotify ↗
          </a>
        )}
      </div>
    </div>
  )
}
