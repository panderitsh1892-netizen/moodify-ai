/**
 * services/api.ts
 * ───────────────
 * Centralized API client.
 *
 * All backend calls go through this file.
 * Axios interceptors automatically attach the JWT token to every request.
 */

import axios from 'axios'

// ── Axios Instance ─────────────────────────────────────────────────────────────
const api = axios.create({
  baseURL: '/api',   // Vite proxy forwards /api → http://backend:8000/api
  headers: { 'Content-Type': 'application/json' },
})

// Attach JWT token to every request automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('moodify_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── Auth ───────────────────────────────────────────────────────────────────────
export const authApi = {
  /** Get current logged-in user */
  getMe: () => api.get('/auth/me').then(r => r.data),

  /** Refresh Spotify token */
  refresh: () => api.post('/auth/refresh').then(r => r.data),

  /** Logout */
  logout: () => {
    localStorage.removeItem('moodify_token')
    localStorage.removeItem('moodify_user')
    window.location.href = '/'
  },
}

// ── Tracks ─────────────────────────────────────────────────────────────────────
export const tracksApi = {
  /** Import recent listening history from Spotify */
  importTracks: () => api.post('/tracks/import').then(r => r.data),

  /** Categorize tracks by mood */
  categorizeTracks: () => api.post('/tracks/categorize').then(r => r.data),

  /** Get paginated track list, optionally filtered by mood */
  getTracks: (page = 1, pageSize = 20, mood?: string) =>
    api.get('/tracks/', {
      params: { page, page_size: pageSize, ...(mood && { mood }) },
    }).then(r => r.data),

  /** Get listening stats and mood breakdown */
  getStats: () => api.get('/tracks/stats').then(r => r.data),
}

// ── Playlists ──────────────────────────────────────────────────────────────────
export const playlistsApi = {
  /** Create or update all mood playlists in Spotify */
  syncPlaylists: () => api.post('/playlists/sync').then(r => r.data),

  /** Get all playlists from our database */
  getPlaylists: () => api.get('/playlists/').then(r => r.data),
}

// ── Admin ──────────────────────────────────────────────────────────────────────
export const adminApi = {
  /** Trigger full sync for current user */
  syncMe: () => api.post('/admin/sync/me').then(r => r.data),

  /** Check task status */
  getTaskStatus: (taskId: string) =>
    api.get(`/admin/task/${taskId}`).then(r => r.data),
}

export default api
