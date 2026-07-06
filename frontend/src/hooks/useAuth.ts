/**
 * hooks/useAuth.ts
 * ─────────────────
 * Authentication state management.
 *
 * Handles:
 * - Reading JWT token from localStorage
 * - Checking if user is logged in
 * - Handling OAuth callback (extracting token from URL)
 * - Logout
 */

import { useEffect, useState } from 'react'
import { authApi } from '../services/api'

interface User {
  id: number
  email: string
  display_name: string | null
  avatar_url: string | null
  spotify_id: string
  is_active: boolean
  created_at: string
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if this is an OAuth callback (URL has access_token in JSON body)
    // The backend returns JSON to the browser after callback
    checkAuthState()
  }, [])

  const checkAuthState = async () => {
    const token = localStorage.getItem('moodify_token')

    if (!token) {
      setLoading(false)
      return
    }

    try {
      const userData = await authApi.getMe()
      setUser(userData)
    } catch {
      // Token expired or invalid — clear it
      localStorage.removeItem('moodify_token')
      localStorage.removeItem('moodify_user')
    } finally {
      setLoading(false)
    }
  }

  const login = () => {
    // Redirect to backend OAuth login endpoint
    window.location.href = 'http://localhost:8000/api/auth/login'
  }

  const logout = () => {
    authApi.logout()
    setUser(null)
  }

  const setTokenAndUser = (token: string, userData: User) => {
    localStorage.setItem('moodify_token', token)
    localStorage.setItem('moodify_user', JSON.stringify(userData))
    setUser(userData)
  }

  return { user, loading, login, logout, setTokenAndUser }
}
