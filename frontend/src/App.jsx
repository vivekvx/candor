import { useDebate } from './hooks/useDebate'
import QueryInput from './components/QueryInput'
import DebateArena from './components/DebateArena'

export default function App() {
  const { state, startDebate, reset } = useDebate()
  const isDebating = state.status !== 'idle'

  return (
    <div style={{ minHeight: '100vh' }}>
      {!isDebating ? (
        <QueryInput onStart={startDebate} />
      ) : (
        <DebateArena state={state} onReset={reset} />
      )}
    </div>
  )
}
