import React from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function ProtectedRoute() {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin h-6 w-6 rounded-full border-2 border-primary-600 border-t-transparent" />
      </div>
    )
  }
  if (!user) return <Navigate to="/sign-in" state={{ from: location.pathname }} replace />
  return <Outlet />
}