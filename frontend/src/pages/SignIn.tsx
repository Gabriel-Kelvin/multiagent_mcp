import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuth } from '../auth/AuthContext'
import { Button, Card, CardContent, CardHeader, Input } from '../components'
import { Sparkles, LogIn } from 'lucide-react'

export default function SignInPage() {
  const { signIn } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const location = useLocation() as any
  const from = location.state?.from || '/app'

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    const { error } = await signIn(email.trim(), password)
    setLoading(false)
    if (error) return toast.error(error)
    toast.success('Signed in')
    navigate(from, { replace: true })
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#211832' }}>
      {/* Brand header */}
      <div className="relative overflow-hidden border-b border-white/10 bg-gradient-to-r from-brand-primary/30 via-brand-deep/30 to-brand-primary/30">
        <div className="relative w-full px-6 py-6">
          <div className="flex flex-col items-center justify-center text-center gap-2">
            <div className="p-2 rounded-xl" style={{ background: '#F25912' }}><Sparkles className="w-6 h-6 text-white" /></div>
            <div>
              <h1 className="text-2xl font-bold text-white">MultiAgent</h1>
              <p className="text-sm text-white/70 mt-0.5">Welcome back</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center min-h-[calc(100vh-10rem)] px-4 md:px-6 lg:px-8 py-10">
        <div className="w-full max-w-md">
          <Card>
            <CardHeader title="Sign in" subtitle="Use your email and password" />
            <CardContent>
              <form className="space-y-4" onSubmit={onSubmit}>
                <Input label="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} required />
                <Input label="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} required />
                <Button type="submit" loading={loading} icon={<LogIn className="w-4 h-4" />}>Sign In</Button>
              </form>
              <div className="flex items-center justify-between mt-4 text-sm">
                <Link to="/reset-password" className="text-brand-accent hover:underline">Forgot password?</Link>
                <Link to="/sign-up" className="text-brand-accent hover:underline">Create account</Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}