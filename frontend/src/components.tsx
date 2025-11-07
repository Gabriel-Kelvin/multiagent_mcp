import React from 'react'
import { CheckCircle2, XCircle, Loader2, AlertCircle } from 'lucide-react'

export function Card({ children, className = '', gradient = false }: { children: React.ReactNode; className?: string; gradient?: boolean }) {
  return (
    <div className={`w-full bg-white dark:bg-[color:var(--brand-panel,#2a2144)] rounded-2xl shadow-soft border border-white/10 overflow-hidden transition-all hover:shadow-lg ${gradient ? 'bg-gradient-to-br from-white to-[rgba(92,62,148,0.08)] dark:from-[rgba(65,43,107,0.4)] dark:to-[rgba(33,24,50,0.6)]' : ''} ${className}`}>
      {children}
    </div>
  )
}

export function CardHeader({ title, subtitle, icon }: { title: string; subtitle?: string; icon?: React.ReactNode }) {
  return (
    <div className="px-6 py-5 border-b border-white/10 bg-gradient-to-r from-brand-primary/15 to-brand-deep/15">
      <div className="flex items-center gap-3">
        {icon && <div className="text-brand-accent">{icon}</div>}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
          {subtitle && <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">{subtitle}</p>}
        </div>
      </div>
    </div>
  )
}

export function CardContent({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return <div className={`p-6 ${className}`}>{children}</div>
}

export function Input({ label, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { label?: string }) {
  return (
    <div className="space-y-2">
      {label && <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>}
      <input
        className="w-full px-4 py-2.5 bg-white dark:bg-[color:var(--brand-input,#2b2246)] border border-gray-300/60 dark:border-white/10 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 outline-none focus:ring-2 focus:ring-brand-accent focus:border-transparent transition-all shadow-sm hover:border-gray-400/80 dark:hover:border-white/20"
        {...props}
      />
    </div>
  )
}

export function TextArea({ label, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string }) {
  return (
    <div className="space-y-2">
      {label && <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>}
      <textarea
        className="w-full px-4 py-2.5 bg-white dark:bg-[color:var(--brand-input,#2b2246)] border border-gray-300/60 dark:border-white/10 rounded-xl text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 outline-none focus:ring-2 focus:ring-brand-accent focus:border-transparent transition-all shadow-sm hover:border-gray-400/80 dark:hover:border-white/20 resize-none"
        {...props}
      />
    </div>
  )
}

export function Select({ label, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { label?: string }) {
  return (
    <div className="space-y-2">
      {label && <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>}
      <select
        className="w-full px-4 py-2.5 bg-white dark:bg-[color:var(--brand-input,#2b2246)] border border-gray-300/60 dark:border-white/10 rounded-xl text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-brand-accent focus:border-transparent transition-all shadow-sm hover:border-gray-400/80 dark:hover:border-white/20"
        {...props}
      >
        {children}
      </select>
    </div>
  )
}

export function Button({ children, variant = 'primary', size = 'md', loading = false, icon, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  icon?: React.ReactNode
}) {
  const baseClasses = 'inline-flex items-center justify-center font-medium rounded-xl transition-all duration-200 shadow-sm hover:shadow-md active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100'
  
  const variants = {
    primary: 'bg-gradient-to-r from-brand-accent to-[color:#e04a0a] hover:from-[color:#ff6b24] hover:to-brand-accent text-white shadow-glow-accent border border-brand-accent/30',
    secondary: 'bg-gradient-to-r from-brand-primary to-brand-deep hover:from-brand-deep hover:to-brand-primary text-white shadow-glow border border-brand-primary/30',
    danger: 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white',
    ghost: 'bg-gray-100 dark:bg-dark-700 hover:bg-gray-200 dark:hover:bg-dark-600 text-gray-700 dark:text-gray-300',
  }
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-5 py-2.5 text-sm',
    lg: 'px-6 py-3 text-base',
  }
  
  return (
    <button
      className={`${baseClasses} ${variants[variant]} ${sizes[size]}`}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? (
        <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Processing...</>
      ) : (
        <>{icon && <span className="mr-2">{icon}</span>}{children}</>
      )}
    </button>
  )
}

export function StatusBadge({ status, message }: { status: 'idle' | 'running' | 'success' | 'error'; message?: string }) {
  const variants = {
    idle: { bg: 'bg-gray-100 dark:bg-dark-700', text: 'text-gray-700 dark:text-gray-300', icon: AlertCircle },
    running: { bg: 'bg-blue-100 dark:bg-blue-950', text: 'text-blue-700 dark:text-blue-300', icon: Loader2 },
    success: { bg: 'bg-emerald-100 dark:bg-emerald-950', text: 'text-emerald-700 dark:text-emerald-300', icon: CheckCircle2 },
    error: { bg: 'bg-red-100 dark:bg-red-950', text: 'text-red-700 dark:text-red-300', icon: XCircle },
  }
  
  const variant = variants[status]
  const Icon = variant.icon
  
  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${variant.bg} ${variant.text} text-sm font-medium`}>
      <Icon className={`w-4 h-4 ${status === 'running' ? 'animate-spin' : ''}`} />
      <span>{message || status.charAt(0).toUpperCase() + status.slice(1)}</span>
    </div>
  )
}

export function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!checked)}
      className="flex items-center gap-3 group"
    >
      <div className={`relative w-11 h-6 rounded-full transition-colors ${checked ? 'bg-brand-accent' : 'bg-gray-300 dark:bg-dark-600'}`}>
        <div className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform ${checked ? 'translate-x-5' : 'translate-x-0'}`} />
      </div>
      <span className="text-sm font-medium text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-white transition-colors">{label}</span>
    </button>
  )
}

export function Tab({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className={`px-5 py-3 font-medium text-sm rounded-lg transition-all ${
        active
          ? 'bg-brand-primary text-white shadow-md'
          : 'bg-gray-100 dark:bg-dark-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-dark-600'
      }`}
    >
      {children}
    </button>
  )
}
