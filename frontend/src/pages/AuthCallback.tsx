import React, { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'

export default function AuthCallbackPage() {
  const navigate = useNavigate()

  useEffect(() => {
    const t = setTimeout(async () => {
      const { data } = await supabase.auth.getSession()
      if (data.session) navigate('/app', { replace: true })
      else navigate('/sign-in', { replace: true })
    }, 300)
    return () => clearTimeout(t)
  }, [navigate])

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#211832' }}>
      <div className="flex items-center gap-3 text-white/80">
        <div className="animate-spin h-6 w-6 rounded-full border-2 border-[color:#F25912] border-t-transparent" />
        <span>Signing you in...</span>
      </div>
    </div>
  )
}