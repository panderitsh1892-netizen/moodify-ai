/**
 * App.tsx
 * ────────
 * Root component with OAuth callback handling.
 *
 * OAuth flow:
 * 1. User clicks "Connect Spotify" → redirected to /api/auth/login
 * 2. Spotify redirects to backend /api/auth/callback
 * 3. Backend redirects to frontend: http://localhost:3000/?token=eyJ...&user=...
 * 4. We extract token from URL, store it, redirect to clean URL
 */

import { useEffect, useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
})

interface User {
  id: number
  email: string
  display_name: string | null
  avatar_url: string | null
  spotify_id: string
  is_active: boolean
  created_at: string
}

function AppInner() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check for OAuth callback params first
    const params = new URLSearchParams(window.location.search)
    const token = params.get('token')
    const userParam = params.get('user')

    if (token && userParam) {
      try {
        const userData = JSON.parse(decodeURIComponent(userParam))
        localStorage.setItem('moodify_token', token)
        localStorage.setItem('moodify_user', JSON.stringify(userData))
        setUser(userData)
        // Clean URL without reloading
        window.history.replaceState({}, '', '/')
        setLoading(false)
        return
      } catch (e) {
        console.error('Failed to parse OAuth callback:', e)
      }
    }

    // No callback params — check localStorage for existing session
    const storedToken = localStorage.getItem('moodify_token')
    const storedUser = localStorage.getItem('moodify_user')

    if (storedToken && storedUser) {
      try {
        const userData = JSON.parse(storedUser)
        // Verify token is still valid by checking expiry
        setUser(userData)
      } catch (e) {
        localStorage.removeItem('moodify_token')
        localStorage.removeItem('moodify_user')
      }
    }

    setLoading(false)
  }, [])

  const login = () => {
    window.location.href = 'http://localhost:8000/api/auth/login'
  }

  const logout = () => {
    localStorage.removeItem('moodify_token')
    localStorage.removeItem('moodify_user')
    setUser(null)
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner">🎵</div>
        <p>Loading Moodify AI...</p>
      </div>
    )
  }

  if (!user) {
    return <Landing onLogin={login} />
  }

  return <Dashboard user={user} onLogout={logout} />
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppInner />
    </QueryClientProvider>
  )
}