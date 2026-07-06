/**
 * Dashboard — main page for authenticated users
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { tracksApi, playlistsApi, adminApi } from '../services/api'
import TrackCard from '../components/TrackCard'
import PlaylistCard from '../components/PlaylistCard'
import StatsBar from '../components/StatsBar'
import MoodBadge from '../components/MoodBadge'

interface User {
  display_name: string | null
  email: string
  avatar_url: string | null
}

interface Props {
  user: User
  onLogout: () => void
}

const MOODS = ['All', 'Romantic', 'Happy', 'Energetic', 'Melancholic', 'Angry', 'Chill']

export default function Dashboard({ user, onLogout }: Props) {
  const [activeMood, setActiveMood] = useState('All')
  const [activeTab, setActiveTab] = useState<'tracks' | 'playlists'>('tracks')
  const [syncMessage, setSyncMessage] = useState('')

  const queryClient = useQueryClient()

  // ── Data Fetching ────────────────────────────────────────────────────────────
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: tracksApi.getStats,
    refetchInterval: 60_000,  // Refresh every minute
  })

  const { data: tracksData, isLoading: tracksLoading } = useQuery({
    queryKey: ['tracks', activeMood],
    queryFn: () => tracksApi.getTracks(1, 50, activeMood === 'All' ? undefined : activeMood),
  })

  const { data: playlistsData, isLoading: playlistsLoading } = useQuery({
    queryKey: ['playlists'],
    queryFn: playlistsApi.getPlaylists,
  })

  // ── Mutations ────────────────────────────────────────────────────────────────
  const importMutation = useMutation({
    mutationFn: tracksApi.importTracks,
    onSuccess: (data) => {
      setSyncMessage(`✅ Imported ${data.new_tracks_saved} new tracks`)
      queryClient.invalidateQueries({ queryKey: ['tracks'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
    onError: () => setSyncMessage('❌ Import failed'),
  })

  const categorizeMutation = useMutation({
    mutationFn: tracksApi.categorizeTracks,
    onSuccess: (data) => {
      setSyncMessage(`✅ Categorized ${data.categorized} tracks`)
      queryClient.invalidateQueries({ queryKey: ['tracks'] })
      queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
    onError: () => setSyncMessage('❌ Categorization failed'),
  })

  const syncPlaylistsMutation = useMutation({
    mutationFn: playlistsApi.syncPlaylists,
    onSuccess: (data) => {
      setSyncMessage(`✅ ${data.message}`)
      queryClient.invalidateQueries({ queryKey: ['playlists'] })
    },
    onError: () => setSyncMessage('❌ Playlist sync failed'),
  })

  const fullSyncMutation = useMutation({
    mutationFn: adminApi.syncMe,
    onSuccess: () => {
      setSyncMessage('✅ Full sync queued — check back in a moment')
      setTimeout(() => {
        queryClient.invalidateQueries()
      }, 5000)
    },
    onError: () => setSyncMessage('❌ Sync failed'),
  })

  const isSyncing =
    importMutation.isPending ||
    categorizeMutation.isPending ||
    syncPlaylistsMutation.isPending ||
    fullSyncMutation.isPending

  return (
    <div className="dashboard">
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <header className="header">
        <div className="header-left">
          <span className="header-logo">🎵</span>
          <span className="header-title">Moodify AI</span>
        </div>
        <div className="header-right">
          <span className="header-user">
            {user.display_name ?? user.email}
          </span>
          <button onClick={onLogout} className="btn-ghost">
            Logout
          </button>
        </div>
      </header>

      <main className="main">
        {/* ── Stats Section ───────────────────────────────────────────────── */}
        <section className="section">
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-number">{stats?.total_tracks ?? 0}</div>
              <div className="stat-label">Total Tracks</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">
                {Object.keys(stats?.mood_breakdown ?? {}).length}
              </div>
              <div className="stat-label">Mood Categories</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">
                {playlistsData?.total ?? 0}
              </div>
              <div className="stat-label">Playlists Created</div>
            </div>
            <div className="stat-card">
              <div className="stat-number">{stats?.uncategorized ?? 0}</div>
              <div className="stat-label">Uncategorized</div>
            </div>
          </div>

          {stats?.mood_breakdown && Object.keys(stats.mood_breakdown).length > 0 && (
            <StatsBar
              moodBreakdown={stats.mood_breakdown}
              total={stats.total_tracks}
            />
          )}
        </section>

        {/* ── Sync Controls ───────────────────────────────────────────────── */}
        <section className="section">
          <h2 className="section-title">Sync Controls</h2>
          <div className="sync-controls">
            <button
              className="btn-primary"
              onClick={() => importMutation.mutate()}
              disabled={isSyncing}
            >
              {importMutation.isPending ? '⏳ Importing...' : '📥 Import Tracks'}
            </button>
            <button
              className="btn-primary"
              onClick={() => categorizeMutation.mutate()}
              disabled={isSyncing}
            >
              {categorizeMutation.isPending ? '⏳ Categorizing...' : '🧠 Categorize Moods'}
            </button>
            <button
              className="btn-primary"
              onClick={() => syncPlaylistsMutation.mutate()}
              disabled={isSyncing}
            >
              {syncPlaylistsMutation.isPending ? '⏳ Syncing...' : '🎵 Sync Playlists'}
            </button>
            <button
              className="btn-spotify"
              onClick={() => fullSyncMutation.mutate()}
              disabled={isSyncing}
            >
              {fullSyncMutation.isPending ? '⏳ Queuing...' : '⚡ Full Auto Sync'}
            </button>
          </div>
          {syncMessage && (
            <div className="sync-message">{syncMessage}</div>
          )}
        </section>

        {/* ── Tabs ────────────────────────────────────────────────────────── */}
        <section className="section">
          <div className="tabs">
            <button
              className={`tab ${activeTab === 'tracks' ? 'tab-active' : ''}`}
              onClick={() => setActiveTab('tracks')}
            >
              Tracks ({stats?.total_tracks ?? 0})
            </button>
            <button
              className={`tab ${activeTab === 'playlists' ? 'tab-active' : ''}`}
              onClick={() => setActiveTab('playlists')}
            >
              Playlists ({playlistsData?.total ?? 0})
            </button>
          </div>

          {/* ── Tracks Tab ──────────────────────────────────────────────── */}
          {activeTab === 'tracks' && (
            <div>
              {/* Mood filter */}
              <div className="mood-filter">
                {MOODS.map((mood) => (
                  <button
                    key={mood}
                    onClick={() => setActiveMood(mood)}
                    className={`mood-filter-btn ${activeMood === mood ? 'mood-filter-active' : ''}`}
                  >
                    {mood === 'All' ? '🎵 All' : <MoodBadge mood={mood} size="sm" />}
                  </button>
                ))}
              </div>

              {/* Track list */}
              {tracksLoading ? (
                <div className="loading">Loading tracks...</div>
              ) : tracksData?.tracks?.length === 0 ? (
                <div className="empty-state">
                  <p>No tracks yet. Click "Import Tracks" to get started!</p>
                </div>
              ) : (
                <div className="track-list">
                  {tracksData?.tracks?.map((track: any) => (
                    <TrackCard key={track.id} track={track} />
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ── Playlists Tab ────────────────────────────────────────────── */}
          {activeTab === 'playlists' && (
            <div>
              {playlistsLoading ? (
                <div className="loading">Loading playlists...</div>
              ) : playlistsData?.playlists?.length === 0 ? (
                <div className="empty-state">
                  <p>No playlists yet.</p>
                  <p>Import tracks → Categorize → Sync Playlists to create them!</p>
                </div>
              ) : (
                <div className="playlist-grid">
                  {playlistsData?.playlists?.map((playlist: any) => (
                    <PlaylistCard key={playlist.id} playlist={playlist} />
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
