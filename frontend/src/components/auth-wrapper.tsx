"use client"

import { useState, useEffect } from "react"
import { LoginForm } from "@/components/login-form"
import api from "@/lib/api"
import { Loader2 } from "lucide-react"

interface AuthWrapperProps {
  children: React.ReactNode
}

export function AuthWrapper({ children }: AuthWrapperProps) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    try {
      // Check if token exists in localStorage
      const token = localStorage.getItem('auth_token')
      if (!token) {
        setIsAuthenticated(false)
        setLoading(false)
        return
      }

      // Verify token by making a request to the API
      const result = await api.getCustomers()
      if (result.error && result.error.includes('401')) {
        // Token is invalid, remove it
        localStorage.removeItem('auth_token')
        setIsAuthenticated(false)
      } else {
        setIsAuthenticated(true)
      }
    } catch (err) {
      console.error('Auth check failed:', err)
      setIsAuthenticated(false)
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = () => {
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    api.logout()
    setIsAuthenticated(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex items-center gap-2">
          <Loader2 className="w-6 h-6 animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LoginForm onLogin={handleLogin} />
  }

  return <>{children}</>
}