import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { Session, User } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'

export type AuthContextType = {
  session: Session | null
  user: User | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<{ error?: string }>
  signUp: (email: string, password: string, username: string) => Promise<{ error?: string; message?: string }>
  signOut: () => Promise<void>
  requestPasswordReset: (email: string, redirectTo: string) => Promise<void>
  updatePassword: (newPassword: string) => Promise<{ error?: string }>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(res => {
      const data = res.data
      setSession(data.session)
      setUser(data.session?.user ?? null)
      setLoading(false)
      if (data.session?.user) ensureProfileOnLogin(data.session.user)
    })

    const { data: sub } = supabase.auth.onAuthStateChange((_event, sess) => {
      setSession(sess)
      setUser(sess?.user ?? null)
      setLoading(false)
      if (sess?.user) ensureProfileOnLogin(sess.user)
    })

    return () => {
      sub.subscription.unsubscribe()
    }
  }, [])

  async function ensureProfileOnLogin(u: User) {
    const pendingKey = `pending_username_${u.email}`
    const username = localStorage.getItem(pendingKey)
    if (!username) return
    try {
      await supabase.from('profiles').upsert({ id: u.id, username }, { onConflict: 'id' })
      localStorage.removeItem(pendingKey)
    } catch {}
  }

  async function signIn(email: string, password: string) {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) return { error: error.message }
    return {}
  }

  async function signUp(email: string, password: string, username: string) {
    const redirectTo = `${import.meta.env.VITE_APP_URL}/auth/callback`
    const { error, data } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: redirectTo,
        data: { username },
      },
    })
    if (error) return { error: error.message }
    if (data.user?.email) {
      localStorage.setItem(`pending_username_${data.user.email}`, username)
    }
    return { message: 'Check your email to confirm your account' }
  }

  async function signOut() { await supabase.auth.signOut() }

  async function requestPasswordReset(email: string, redirectTo: string) {
    await supabase.auth.resetPasswordForEmail(email, { redirectTo })
  }

  async function updatePassword(newPassword: string) {
    const { error } = await supabase.auth.updateUser({ password: newPassword })
    if (error) return { error: error.message }
    return {}
  }

  const value = useMemo<AuthContextType>(() => ({
    session, user, loading, signIn, signUp, signOut, requestPasswordReset, updatePassword
  }), [session, user, loading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}