import React, { useEffect, useMemo, useState } from 'react'
import toast, { Toaster } from 'react-hot-toast'
import { Database, Play, Calendar, FileText, Trash2, Download, Mail, Sparkles, Server, Settings, Clock, LogOut } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { api, DbTestRequest, RunRequest, ScheduleJobRequest } from './api'
import { Card, CardHeader, CardContent, Input, TextArea, Select, Button, StatusBadge, Toggle, Tab } from './components'
import { useAuth } from './auth/AuthContext'

const toArtifactUrl = (path?: string) => {
  if (!path) return ''
  const normalized = path.replace(/\\/g, '/').replace(/^\.\//, '')
  return `${api.baseUrl}/${normalized}`
}

type Artifacts = {
  csv_path?: string
  pdf_path?: string
  [key: string]: string | undefined
}

export default function App() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<'query' | 'schedule' | 'jobs'>('query')
  
  // Data source
  const [useEnv, setUseEnv] = useState(true)
  const [connectMode, setConnectMode] = useState<'DSN' | 'Manual'>('DSN')
  const [dsn, setDsn] = useState('')
  const [host, setHost] = useState('')
  const [port, setPort] = useState('6543')
  const [name, setName] = useState('postgres')
  const [dbUser, setDbUser] = useState('')
  const [password, setPassword] = useState('')
  const [sslmode, setSslmode] = useState<'require' | 'prefer' | 'disable'>('require')
  const [table, setTable] = useState('')

  // Email
  const [emailOn, setEmailOn] = useState(false)
  const [emailFrom, setEmailFrom] = useState('')
  const [emailTo, setEmailTo] = useState('')
  const [emailKey, setEmailKey] = useState('')

  // Run
  const [question, setQuestion] = useState('')
  const [status, setStatus] = useState<'idle' | 'running' | 'success' | 'error'>('idle')
  const [errorMsg, setErrorMsg] = useState('')
  const [preview, setPreview] = useState<any[]>([])
  const [artifacts, setArtifacts] = useState<Artifacts>({})
  const [runId, setRunId] = useState<string>('')

  // Scheduler
  const [schedQuestion, setSchedQuestion] = useState('')
  const [frequency, setFrequency] = useState<'daily' | 'weekly' | 'monthly'>('daily')
  const [time, setTime] = useState('09:00')
  const [jobs, setJobs] = useState<any[]>([])

  const dsPayload = useMemo(() => ({
    db_type: 'postgres',
    use_env: useEnv,
    dsn: useEnv ? undefined : (connectMode === 'DSN' ? dsn : undefined),
    host: useEnv ? undefined : (connectMode === 'Manual' ? host : undefined),
    port: useEnv ? undefined : (connectMode === 'Manual' ? Number(port) : undefined),
    name: useEnv ? undefined : (connectMode === 'Manual' ? name : undefined),
    user: useEnv ? undefined : (connectMode === 'Manual' ? dbUser : undefined),
    password: useEnv ? undefined : (connectMode === 'Manual' ? password : undefined),
    table,
    sslmode: useEnv ? undefined : (connectMode === 'Manual' ? sslmode : undefined),
  }), [useEnv, connectMode, dsn, host, port, name, dbUser, password, table, sslmode])

  const emailOverrides = useMemo(() => emailOn ? ({
    // When using .env email (toggle ON), do not send overrides
  }) : ({
    // When toggle is OFF, use manual overrides from UI inputs
    email_from: emailFrom || undefined,
    email_to: emailTo || undefined,
    email_key: emailKey || undefined,
  }), [emailOn, emailFrom, emailTo, emailKey])

  async function testConnection() {
    if (!table) {
      toast.error('Please enter table name')
      return
    }
    const payload: DbTestRequest = dsPayload as any
    const toastId = toast.loading('Testing connection...')
    try {
      const res = await api.dbTest(payload)
      if (res.status !== 'success') throw new Error(res.error || 'Connection failed')
      toast.success(`Connected successfully · ${res.rows?.length || 0} rows sampled`, { id: toastId })
    } catch (e: any) {
      toast.error(e?.message || 'Connection failed', { id: toastId })
    }
  }

  async function runFlow() {
    if (!table) {
      toast.error('Please enter table name')
      return
    }
    // Validate email config when toggle is OFF (manual mode)
    if (!emailOn) {
      if (!emailFrom || !emailTo || !emailKey) {
        toast.error('Please provide all email fields (From, To, SendGrid API Key)')
        return
      }
    }
    setStatus('running')
    setErrorMsg('')
    setPreview([])
    setArtifacts({})
    try {
      const payload: RunRequest = {
        question: question || 'Show sample',
        user_id: 'default',
        ...dsPayload,
        ...emailOverrides,
      }
      const res = await api.run(payload)
      setStatus((res.status as any) || 'success')
      setPreview(res.preview || [])
      setArtifacts(res.artifacts || {})
      setRunId(res.run_id || '')
      if (res.status === 'success') {
        toast.success('Query completed successfully!')
      } else if (res.status === 'error') {
        toast.error('Query failed')
        setErrorMsg('Check logs for details')
      }
    } catch (e: any) {
      setStatus('error')
      setErrorMsg(e?.message || String(e))
      toast.error(e?.message || 'Request failed')
    }
  }

  async function addJob() {
    if (!schedQuestion) {
      toast.error('Enter scheduled question')
      return
    }
    if (!table) {
      toast.error('Please enter table name in data source')
      return
    }
    // Validate email config when toggle is OFF (manual mode)
    if (!emailOn) {
      if (!emailFrom || !emailTo || !emailKey) {
        toast.error('Please provide all email fields (From, To, SendGrid API Key)')
        return
      }
    }
    const toastId = toast.loading('Scheduling job...')
    try {
      const { db_type: _omit, ...dsOverrides } = dsPayload as any
      const payload: ScheduleJobRequest = {
        question: schedQuestion,
        frequency,
        time,
        user_id: 'scheduler',
        table,
        ...dsOverrides,
      }
      const res = await api.schedAdd(payload)
      if (res.status === 'success') {
        await refreshJobs()
        setSchedQuestion('')
        toast.success('Job scheduled successfully', { id: toastId })
        setActiveTab('jobs')
      } else {
        throw new Error('Failed to schedule job')
      }
    } catch (e: any) {
      toast.error(e?.message || 'Failed to schedule job', { id: toastId })
    }
  }

  async function refreshJobs() {
    const res = await api.schedList()
    setJobs(res.jobs || [])
  }

  async function deleteJob(id: string) {
    const toastId = toast.loading('Deleting job...')
    try {
      await api.schedDelete(id)
      await refreshJobs()
      toast.success('Job deleted', { id: toastId })
    } catch (e: any) {
      toast.error('Failed to delete job', { id: toastId })
    }
  }

  function filenameFromUrl(u: string): string {
    try {
      const p = new URL(u)
      const parts = p.pathname.split('/')
      const last = parts[parts.length - 1] || 'download'
      return decodeURIComponent(last)
    } catch {
      const parts = u.split('/')
      return decodeURIComponent(parts[parts.length - 1] || 'download')
    }
  }

  async function downloadAsset(url: string, name?: string) {
    try {
      const res = await fetch(url)
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
      const blob = await res.blob()
      const dl = document.createElement('a')
      const objectUrl = URL.createObjectURL(blob)
      dl.href = objectUrl
      dl.download = name || filenameFromUrl(url)
      document.body.appendChild(dl)
      dl.click()
      dl.remove()
      URL.revokeObjectURL(objectUrl)
    } catch (e: any) {
      toast.error(e?.message || 'Download failed')
    }
  }

  useEffect(() => { refreshJobs() }, [])

  const csvUrl = toArtifactUrl(artifacts?.csv_path)
  const pdfUrl = toArtifactUrl(artifacts?.pdf_path)

  function getInitials() {
    if (!user) return '?'
    const email = user.email || ''
    const username = user.user_metadata?.username || email.split('@')[0]
    return username.slice(0, 2).toUpperCase()
  }

  function getUserDisplayName() {
    if (!user) return 'User'
    return user.user_metadata?.username || user.email?.split('@')[0] || 'User'
  }

  async function handleLogout() {
    await signOut()
    toast.success('Signed out successfully')
    navigate('/sign-in')
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#211832' }}>
      <Toaster position="top-right" />
      
      {/* Header */}
      <div className="relative overflow-hidden border-b border-white/10">
        {/* Animated background gradient */}
        <div className="absolute inset-0 bg-gradient-to-r from-brand-primary/30 via-brand-deep/30 to-brand-primary/30"></div>
        
        <div className="relative w-full px-6 lg:px-12 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 rounded-2xl shadow-lg" style={{ background: '#F25912' }}>
                <Sparkles className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">MultiAgent</h1>
                <p className="text-white/70 text-sm mt-0.5">Ask anything. Get answers. Share results.</p>
              </div>
            </div>
            
            {/* User Profile */}
            <div className="flex items-center gap-4">
              <div className="text-right hidden md:block">
                <p className="text-white/90 font-medium text-sm">Welcome, {getUserDisplayName()}</p>
                <p className="text-white/60 text-xs">Let’s build your next report</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-xl" style={{ background: '#F25912' }}>
                  <div className="w-full h-full flex items-center justify-center text-white font-bold text-sm">
                  {getInitials()}
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2.5 bg-white/10 hover:bg-white/20 backdrop-blur-sm rounded-xl transition-all duration-200 hover:scale-105"
                  title="Sign out"
                >
                  <LogOut className="w-5 h-5 text-white" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full px-6 lg:px-12 py-8 max-w-[1800px] mx-auto">
        {/* New 3-panel layout */}
        <div className="grid grid-cols-12 gap-6">
          {/* Left: Navigation & status */}
          <aside className="col-span-12 md:col-span-3 lg:col-span-2 space-y-4">
            <div className="bg-slate-800/40 border border-white/10 rounded-2xl p-3">
              <nav className="flex flex-col gap-2">
                <button onClick={() => setActiveTab('query')} className={`w-full text-left px-4 py-3 rounded-xl transition-all ${activeTab==='query' ? 'bg-[color:#5C3E94] text-white shadow-glow' : 'text-slate-300 hover:bg-white/5'}`}>
                  <span className="inline-flex items-center gap-2"><Play className="w-4 h-4"/> Run Query</span>
                </button>
                <button onClick={() => setActiveTab('schedule')} className={`w-full text-left px-4 py-3 rounded-xl transition-all ${activeTab==='schedule' ? 'bg-[color:#5C3E94] text-white shadow-glow' : 'text-slate-300 hover:bg-white/5'}`}>
                  <span className="inline-flex items-center gap-2"><Clock className="w-4 h-4"/> Schedule</span>
                </button>
                <button onClick={() => setActiveTab('jobs')} className={`w-full text-left px-4 py-3 rounded-xl transition-all ${activeTab==='jobs' ? 'bg-[color:#5C3E94] text-white shadow-glow' : 'text-slate-300 hover:bg-white/5'}`}>
                  <span className="inline-flex items-center gap-2"><Calendar className="w-4 h-4"/> Active Jobs <span className="ml-2 px-2 py-0.5 bg-white/20 rounded-full text-xs">{jobs.length}</span></span>
                </button>
              </nav>
            </div>
            <div className="bg-slate-800/40 border border-white/10 rounded-2xl p-4">
              <div className="text-slate-300 text-sm mb-2">Status</div>
              <StatusBadge status={status} />
            </div>
          </aside>

          {/* Center: Main content */}
          <main className="col-span-12 md:col-span-6 lg:col-span-7 space-y-6">
            {/* Main Content with Tabs */}
            <div className="space-y-6">
            {/* The pills nav moved to the left sidebar for the new layout */}

            {/* Query Tab */}
            {activeTab === 'query' && (
              <div className="space-y-6 animate-fade-in">
                <div className="bg-slate-800/50 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl p-8">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-gradient-to-br from-teal-500 to-emerald-600 rounded-lg shadow-lg shadow-teal-500/20">
                      <Sparkles className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-xl font-semibold text-white">Ask a Question</h3>
                      <p className="text-sm text-slate-400">Natural language query analysis</p>
                    </div>
                  </div>
                  <div className="space-y-5">
                    <TextArea
                      label="Your Question"
                      placeholder="e.g., What is the most common employment type?"
                      value={question}
                      onChange={e => setQuestion(e.target.value)}
                      rows={4}
                    />
                    <Button
                      onClick={runFlow}
                      loading={status === 'running'}
                      icon={<Play className="w-4 h-4" />}
                    >
                      {status === 'running' ? 'Analyzing...' : 'Run Analysis'}
                    </Button>
                  </div>
                </div>

                {/* Status */}
                <div className="bg-slate-800/50 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="p-2 bg-blue-500/20 rounded-lg">
                      <Settings className="w-5 h-5 text-blue-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-white">Execution Status</h3>
                  </div>
                  <StatusBadge status={status} />
                  {errorMsg && <p className="mt-3 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg p-3">{errorMsg}</p>}
                </div>

                {/* Results */}
                {(preview.length > 0 || csvUrl || pdfUrl) && (
                  <div className="bg-slate-800/50 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl p-6">
                    <div className="flex items-center justify-between mb-6">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-emerald-500/20 rounded-lg">
                          <FileText className="w-5 h-5 text-emerald-400" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-white">Results</h3>
                          <p className="text-sm text-slate-400">{preview.length} rows preview</p>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {csvUrl && (
                          <button
                            onClick={() => downloadAsset(csvUrl)}
                            className="flex items-center gap-2 px-4 py-2 bg-teal-500/20 hover:bg-teal-500/30 text-teal-300 rounded-lg transition-all duration-200 border border-teal-500/30"
                          >
                            <Download className="w-4 h-4" />
                            CSV
                          </button>
                        )}
                        {pdfUrl && (
                          <button
                            onClick={() => downloadAsset(pdfUrl)}
                            className="flex items-center gap-2 px-4 py-2 bg-coral-500/20 hover:bg-coral-500/30 text-coral-300 rounded-lg transition-all duration-200 border border-coral-500/30"
                          >
                            <Download className="w-4 h-4" />
                            PDF Report
                          </button>
                        )}
                      </div>
                    </div>
                    {preview.length > 0 && (
                      <div className="overflow-x-auto rounded-xl border border-white/10">
                        <table className="min-w-full divide-y divide-white/10">
                          <thead className="bg-slate-900/50">
                            <tr>
                              {Object.keys(preview[0]).map((k) => (
                                <th key={k} className="px-6 py-4 text-left text-xs font-semibold text-teal-300 uppercase tracking-wider">
                                  {k}
                                </th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="bg-slate-800/30 divide-y divide-white/5">
                            {preview.map((row, i) => (
                              <tr key={i} className="hover:bg-slate-700/30 transition-colors">
                                {Object.keys(preview[0]).map((k) => (
                                  <td key={k} className="px-6 py-4 text-sm text-slate-200">
                                    {String(row[k])}
                                  </td>
                                ))}
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Schedule Tab */}
            {activeTab === 'schedule' && (
              <div className="bg-slate-800/50 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl p-8 animate-fade-in">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg shadow-lg shadow-purple-500/20">
                    <Clock className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-white">Schedule Recurring Query</h3>
                    <p className="text-sm text-slate-400">Automate your data analysis</p>
                  </div>
                </div>
                <div className="space-y-5">
                  <TextArea
                    label="Scheduled Question"
                    placeholder="e.g., Weekly employee satisfaction summary"
                    value={schedQuestion}
                    onChange={e => setSchedQuestion(e.target.value)}
                    rows={3}
                  />
                  <div className="grid grid-cols-2 gap-4">
                    <Select label="Frequency" value={frequency} onChange={e => setFrequency(e.target.value as any)}>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="monthly">Monthly</option>
                    </Select>
                    <Input label="Time (24h)" type="time" value={time} onChange={e => setTime(e.target.value)} />
                  </div>
                  <Button onClick={addJob} icon={<Calendar className="w-4 h-4" />}>
                    Schedule Job
                  </Button>
                </div>
              </div>
            )}

            {/* Jobs Tab */}
            {activeTab === 'jobs' && (
              <div className="bg-slate-800/50 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl p-6 animate-fade-in">
                <div className="flex items-center gap-3 mb-6">
                  <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-lg shadow-indigo-500/20">
                    <Calendar className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Active Scheduled Jobs</h3>
                    <p className="text-sm text-slate-400">{jobs.length} active job{jobs.length !== 1 ? 's' : ''}</p>
                  </div>
                </div>
                {jobs.length > 0 ? (
                  <div className="space-y-3">
                    {jobs.map((j) => (
                      <div
                        key={j.id}
                        className="flex items-start justify-between p-5 bg-slate-900/40 rounded-xl border border-white/10 hover:border-teal-500/30 transition-all"
                      >
                        <div className="flex-1">
                          <div className="font-medium text-white mb-2">{j.question}</div>
                          <div className="flex flex-wrap gap-3 text-sm text-slate-400">
                            <span className="px-3 py-1 bg-teal-500/20 text-teal-300 rounded-full border border-teal-500/30">
                              {j.frequency}
                            </span>
                            <span className="px-3 py-1 bg-blue-500/20 text-blue-300 rounded-full border border-blue-500/30">
                              {j.time}
                            </span>
                            <span className="px-3 py-1 bg-purple-500/20 text-purple-300 rounded-full border border-purple-500/30">
                              Next: {j.next_run || 'calculating...'}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() => deleteJob(j.id)}
                          className="flex items-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded-lg transition-all duration-200 border border-red-500/30"
                        >
                          <Trash2 className="w-4 h-4" />
                          Delete
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-16">
                    <div className="p-4 bg-slate-900/40 rounded-2xl w-fit mx-auto mb-4">
                      <Calendar className="w-16 h-16 text-slate-600" />
                    </div>
                    <p className="text-slate-300 font-medium mb-1">No scheduled jobs yet</p>
                    <p className="text-sm text-slate-500">Create one in the Schedule tab to automate your analysis</p>
                  </div>
                )}
              </div>
            )}
          </div>
          </main>

          {/* Right: Config panel */}
          <aside className="col-span-12 md:col-span-3 lg:col-span-3 space-y-6">
            {/* Data Source */}
            <div className="bg-slate-800/50 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl">
              <div className="p-6 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/10 rounded-lg">
                    <Database className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Data Source</h3>
                    <p className="text-sm text-slate-400">Configure database connection</p>
                  </div>
                </div>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  <Toggle
                    label="Use .env connection"
                    checked={useEnv}
                    onChange={setUseEnv}
                  />

                  {!useEnv && (
                    <div className="space-y-4 animate-fade-in">
                      <div className="flex gap-2">
                        <Button
                          variant={connectMode === 'DSN' ? 'primary' : 'ghost'}
                          size="sm"
                          onClick={() => setConnectMode('DSN')}
                        >
                          DSN
                        </Button>
                        <Button
                          variant={connectMode === 'Manual' ? 'primary' : 'ghost'}
                          size="sm"
                          onClick={() => setConnectMode('Manual')}
                        >
                          Manual
                        </Button>
                      </div>

                      {connectMode === 'DSN' ? (
                        <Input
                          label="PostgreSQL DSN"
                          placeholder="postgresql://user:pass@host:port/db"
                          value={dsn}
                          onChange={e => setDsn(e.target.value)}
                        />
                      ) : (
                        <>
                          <div className="grid grid-cols-2 gap-3">
                            <Input label="Host" value={host} onChange={e => setHost(e.target.value)} />
                            <Input label="Port" value={port} onChange={e => setPort(e.target.value)} />
                          </div>
                          <Input label="Database" value={name} onChange={e => setName(e.target.value)} />
                          <Input label="Username" value={dbUser} onChange={e => setDbUser(e.target.value)} />
                          <Input label="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
                          <Select label="SSL Mode" value={sslmode} onChange={e => setSslmode(e.target.value as any)}>
                            <option value="require">Require</option>
                            <option value="prefer">Prefer</option>
                            <option value="disable">Disable</option>
                          </Select>
                        </>
                      )}
                    </div>
                  )}

                  <Input
                    label="Table"
                    placeholder="public.my_table"
                    value={table}
                    onChange={e => setTable(e.target.value)}
                  />

                  <Button onClick={testConnection} icon={<Server className="w-4 h-4" />}>
                    Test Connection
                  </Button>
                </div>
              </div>
            </div>

            {/* Email Settings */}
            <div className="bg-slate-800/50 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl">
              <div className="p-6 border-b border-white/10">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-white/10 rounded-lg">
                    <Mail className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white">Email Delivery</h3>
                    <p className="text-sm text-slate-400">Required for all analysis runs</p>
                  </div>
                </div>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  <Toggle
                    label="Use .env email"
                    checked={emailOn}
                    onChange={setEmailOn}
                  />

                  {!emailOn && (
                    <div className="space-y-4 animate-fade-in">
                      <Input label="From Email *" value={emailFrom} onChange={e => setEmailFrom(e.target.value)} placeholder="sender@example.com" />
                      <Input label="To Email(s) *" placeholder="recipient@example.com, other@example.com" value={emailTo} onChange={e => setEmailTo(e.target.value)} />
                      <Input label="SendGrid API Key *" type="password" value={emailKey} onChange={e => setEmailKey(e.target.value)} placeholder="SG.xxxxxxxxx" />
                      <p className="text-xs text-slate-500">* All fields required when not using .env</p>
                    </div>
                  )}
                </div>
              </div>
                    </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
