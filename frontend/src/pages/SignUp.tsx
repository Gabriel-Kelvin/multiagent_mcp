import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuth } from '../auth/AuthContext'
import { Button, Card, CardContent, CardHeader, Input } from '../components'
import { Sparkles, UserPlus } from 'lucide-react'

export default function SignUpPage() {
  const { signUp } = useAuth()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (password.length < 8) return toast.error('Password must be at least 8 characters')
    if (password !== confirm) return toast.error('Passwords do not match')
    setLoading(true)
    const { error, message } = await signUp(email.trim(), password, username.trim())
    setLoading(false)
    if (error) return toast.error(error)
    toast.success(message || 'Check your email to confirm your account')
    navigate('/sign-in')
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#211832' }}>
      <div className="relative overflow-hidden border-b border-white/10 bg-gradient-to-r from-brand-primary/30 via-brand-deep/30 to-brand-primary/30">
        <div className="relative w-full px-6 py-6">
          <div className="flex flex-col items-center justify-center text-center gap-2">
            <div className="p-2 rounded-xl" style={{ background: '#F25912' }}><Sparkles className="w-6 h-6 text-white" /></div>
            <div>
              <h1 className="text-2xl font-bold text-white">MultiAgent</h1>
              <p className="text-sm text-white/70 mt-0.5">Create your account</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center min-h-[calc(100vh-10rem)] px-4 md:px-6 lg:px-8 py-10">
        <div className="w-full max-w-md">
          <Card>
            <CardHeader title="Sign up" subtitle="We'll confirm via email" />
            <CardContent>
              <form className="space-y-4" onSubmit={onSubmit}>
                <Input label="Username" value={username} onChange={e => setUsername(e.target.value)} required />
                <Input label="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
                <Input label="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
                <Input label="Confirm Password" type="password" value={confirm} onChange={e => setConfirm(e.target.value)} required />
                <Button type="submit" loading={loading} icon={<UserPlus className="w-4 h-4" />}>Create Account</Button>
              </form>
              <div className="flex items-center justify-between mt-4 text-sm">
                <span className="text-gray-400">Already have an account?</span>
                <Link to="/sign-in" className="text-brand-accent hover:underline">Sign in</Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}