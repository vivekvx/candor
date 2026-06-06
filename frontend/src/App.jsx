import { useState, Component } from 'react'
import { useDebate } from './hooks/useDebate'
import QueryInput from './components/QueryInput'
import DebateArena from './components/DebateArena'

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
  const [currentQuery, setCurrentQuery] = useState('')
  const isDebating = state.status !== 'idle'

  const handleStart = (query, model) => {
    setCurrentQuery(query)
    startDebate(query, model)
  }

  const handleReset = () => {
    setCurrentQuery('')
    reset()
  }

  return (
    <ErrorBoundary onReset={handleReset}>
      <div style={{ minHeight: '100vh' }}>
        {!isDebating ? (
          <QueryInput onStart={handleStart} />
        ) : (
          <DebateArena state={state} currentQuery={currentQuery} onReset={handleReset} />
        )}
      </div>
    </ErrorBoundary>
  )
}
