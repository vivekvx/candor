import { useState, Component, useEffect } from 'react'
import { useDebate } from './hooks/useDebate'
import QueryInput from './components/QueryInput'
import DebateArena from './components/DebateArena'
import UserProfile, { useUserProfile } from './components/UserProfile'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { error: null } }
  static getDerivedStateFromError(error) { return { error } }
  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: '40px', fontFamily: 'monospace', color: '#F43F5E', backgroundColor: '#080809', minHeight: '100vh' }}>
          <div style={{ marginBottom: '8px', fontSize: '12px', letterSpacing: '0.1em' }}>RUNTIME ERROR</div>
          <div style={{ fontSize: '14px', color: '#F1F0EE', marginBottom: '16px' }}>{this.state.error.message}</div>
          <pre style={{ fontSize: '12px', color: '#8B8B99', whiteSpace: 'pre-wrap' }}>{this.state.error.stack}</pre>
          <button
            onClick={() => { this.setState({ error: null }); this.props.onReset?.() }}
            style={{ marginTop: '24px', padding: '10px 20px', background: '#6366F1', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontFamily: 'monospace' }}
          >
            Reset
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export default function App() {
  const { state, startDebate, reset } = useDebate()
  const { profile } = useUserProfile()
  const [currentQuery, setCurrentQuery] = useState('')
  const [showProfile, setShowProfile] = useState(false)
  const [sharedDebate, setSharedDebate] = useState(null)
  const isDebating = state.status !== 'idle'

  // Check for shared debate URL on mount
  useEffect(() => {
    const match = window.location.pathname.match(/^\/debate\/([a-f0-9]+)$/)
    if (match) {
      fetch(`${API_BASE_URL}/api/debate/${match[1]}`)
        .then(r => r.ok ? r.json() : null)
        .then(data => { if (data) setSharedDebate(data) })
        .catch(() => {})
    } else if (window.location.pathname === '/debate') {
      // Landed on /debate with no active debate — bounce back to landing page
      window.history.replaceState({}, '', '/')
    }
  }, [])

  // Back button on /debate returns to landing page
  useEffect(() => {
    const handlePopState = () => {
      if (window.location.pathname !== '/debate' && isDebating) {
        setCurrentQuery('')
        reset()
      }
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [isDebating, reset])

  const handleStart = (query, model) => {
    setCurrentQuery(query)
    window.history.pushState({}, '', '/debate')
    startDebate(query, model)
  }

  const handleReset = () => {
    setCurrentQuery('')
    reset()
    window.history.pushState({}, '', '/')
    // Clear shared debate URL
    if (sharedDebate) {
      setSharedDebate(null)
    }
  }

  // Shared debate read-only view
  if (sharedDebate) {
    const sharedState = {
      status: 'complete',
      advocateResearch: sharedDebate.advocate_research ? JSON.parse(sharedDebate.advocate_research) : null,
      challengerResearch: sharedDebate.challenger_research ? JSON.parse(sharedDebate.challenger_research) : null,
      advocateRebuttal: sharedDebate.advocate_rebuttal ? JSON.parse(sharedDebate.advocate_rebuttal) : null,
      challengerRebuttal: sharedDebate.challenger_rebuttal ? JSON.parse(sharedDebate.challenger_rebuttal) : null,
      verdict: sharedDebate.verdict,
      metadata: sharedDebate.metadata,
      error: null,
    }
    return (
      <ErrorBoundary onReset={handleReset}>
        <div style={{ minHeight: '100vh' }}>
          <div style={{
            backgroundColor: 'rgba(99,102,241,0.12)',
            borderBottom: '1px solid var(--border)',
            padding: '10px 24px',
            fontFamily: 'var(--font-ui)',
            fontSize: '13px',
            color: 'var(--text-secondary)',
            textAlign: 'center',
          }}>
            Shared debate · read-only ·{' '}
            <button onClick={handleReset} style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontFamily: 'inherit', fontSize: 'inherit' }}>
              Run your own →
            </button>
          </div>
          <DebateArena state={sharedState} currentQuery={sharedDebate.query} onReset={handleReset} />
        </div>
      </ErrorBoundary>
    )
  }

  return (
    <ErrorBoundary onReset={handleReset}>
      <div style={{ minHeight: '100vh', position: 'relative' }}>
        {/* Profile button — top right */}
        {!isDebating && (
          <button
            onClick={() => setShowProfile(true)}
            style={{
              position: 'fixed',
              top: '16px',
              right: '20px',
              background: 'transparent',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '6px 12px',
              fontFamily: 'var(--font-ui)',
              fontSize: '12px',
              color: profile ? 'var(--text-secondary)' : 'var(--text-dim)',
              cursor: 'pointer',
              zIndex: 100,
            }}
          >
            {profile?.role ? `${profile.role}` : 'Edit Profile'}
          </button>
        )}

        {!isDebating ? (
          <QueryInput onStart={handleStart} />
        ) : (
          <DebateArena state={state} currentQuery={currentQuery} onReset={handleReset} />
        )}

        {/* Profile modal */}
        {showProfile && <UserProfile onClose={() => setShowProfile(false)} />}

        {/* Subtle profile prompt if no profile set */}
        {!isDebating && !profile && (
          <div style={{
            position: 'fixed',
            bottom: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            fontFamily: 'var(--font-ui)',
            fontSize: '12px',
            color: 'var(--text-dim)',
            cursor: 'pointer',
          }}
            onClick={() => setShowProfile(true)}
          >
            Add your profile for personalized verdicts →
          </div>
        )}
      </div>
    </ErrorBoundary>
  )
}
