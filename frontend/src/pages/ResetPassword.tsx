import React, { useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuth } from '../auth/AuthContext'
import { Button, Card, CardContent, CardHeader, Input } from '../components'
import { Sparkles, KeyRound, Send } from 'lucide-react'

export default function ResetPasswordPage() {
  const { requestPasswordReset, updatePassword } = useAuth()
  const [email, setEmail] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [params] = useSearchParams()
  const navigate = useNavigate()

  const mode = params.get('mode') || 'request'

  async function submitRequest(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    const redirectTo = `${import.meta.env.VITE_APP_URL}/reset-password?mode=update`
    await requestPasswordReset(email.trim(), redirectTo)
    setLoading(false)
    toast.success('If an account exists, you will receive reset instructions')
  }

  async function submitUpdate(e: React.FormEvent) {
    e.preventDefault()
    if (newPassword.length < 8) return toast.error('Password must be at least 8 characters')
    if (newPassword !== confirm) return toast.error('Passwords do not match')
    setLoading(true)
    const { error } = await updatePassword(newPassword)
    setLoading(false)
    if (error) return toast.error(error)
    toast.success('Password updated. Please sign in')
    navigate('/sign-in', { replace: true })
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#211832' }}>
      <div className="relative overflow-hidden border-b border-white/10 bg-gradient-to-r from-brand-primary/30 via-brand-deep/30 to-brand-primary/30">
        <div className="relative w-full px-6 py-6">
          <div className="flex flex-col items-center justify-center text-center gap-2">
            <div className="p-2 rounded-xl" style={{ background: '#F25912' }}><Sparkles className="w-6 h-6 text-white" /></div>
            <div>
              <h1 className="text-2xl font-bold text-white">MultiAgent</h1>
              <p className="text-sm text-white/70 mt-0.5">{mode === 'update' ? 'Set a new password' : 'Reset your password'}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center min-h-[calc(100vh-10rem)] px-4 md:px-6 lg:px-8 py-10">
        <div className="w-full max-w-md">
          <Card>
            <CardHeader title={mode === 'update' ? 'Create a strong password' : 'We\'ll email you a link'} />
            <CardContent>
              {mode === 'update' ? (
                <form className="space-y-4" onSubmit={submitUpdate}>
                  <Input label="New Password" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} required />
                  <Input label="Confirm New Password" type="password" value={confirm} onChange={e => setConfirm(e.target.value)} required />
                  <Button type="submit" loading={loading} icon={<KeyRound className="w-4 h-4" />}>Update Password</Button>
                </form>
              ) : (
                <form className="space-y-4" onSubmit={submitRequest}>
                  <Input label="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
                  <Button type="submit" loading={loading} icon={<Send className="w-4 h-4" />}>Send Reset Link</Button>
                </form>
              )}

              {mode === 'request' && (
                <div className="flex items-center justify-between mt-4 text-sm">
                  <span className="text-gray-400">Remembered your password?</span>
                  <Link to="/sign-in" className="text-brand-accent hover:underline">Back to sign in</Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}