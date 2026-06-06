import { useState, useEffect } from 'react'
import { useModels } from '../../hooks/useModels'

const EXAMPLES = [
  "Should I join Zepto as a backend engineer for 42 LPA?",
  "Is this ESOP offer from a Series A actually worth anything?",
  "Should I leave my FAANG job for a founder role at a seed startup?",
  "Swiggy vs Zepto — which offer should I take?",
]

export default function QueryInput({ onStart }) {
  const [query, setQuery] = useState('')
  const [selectedModel, setSelectedModel] = useState('')
  const [placeholderIndex, setPlaceholderIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const [focused, setFocused] = useState(false)
  const { models, loading: modelsLoading } = useModels()

  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholderIndex(i => (i + 1) % EXAMPLES.length)
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (models && models.length > 0 && !selectedModel) {
      const freeModel = models.find(m => m.free) || models[0]
      setSelectedModel(freeModel.id)
    }
  }, [models])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim() || loading) return
    setLoading(true)
    await onStart(query.trim(), selectedModel)
    setLoading(false)
  }

  return (
    <>
      <style>{`
        .candor-textarea::placeholder { color: var(--text-dim); }
        .candor-textarea:focus { outline: none; }
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-primary)',
        padding: '24px',
      }}>
        <div style={{ width: '100%', maxWidth: '680px' }}>
          <div style={{ textAlign: 'center', marginBottom: '48px' }}>
            <h1 style={{
              fontFamily: 'var(--font-display)',
              fontSize: '72px',
              fontWeight: 900,
              letterSpacing: '-0.03em',
              color: 'var(--text-primary)',
              margin: 0,
              lineHeight: 1,
            }}>
              CANDOR
            </h1>
            <p style={{
              fontFamily: 'var(--font-ui)',
              fontSize: '16px',
              color: 'var(--text-secondary)',
              marginTop: '12px',
              marginBottom: 0,
            }}>
              Three agents debate. One honest verdict.
            </p>
          </div>

          <form onSubmit={handleSubmit}>
            <textarea
              className="candor-textarea"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder={EXAMPLES[placeholderIndex]}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                backgroundColor: 'var(--bg-card)',
                border: `1px solid ${focused ? 'var(--accent)' : 'var(--border)'}`,
                boxShadow: focused ? '0 0 0 3px rgba(99,102,241,0.15)' : 'none',
                borderRadius: 'var(--radius)',
                padding: '16px',
                minHeight: '100px',
                maxHeight: '200px',
                resize: 'vertical',
                fontFamily: 'var(--font-mono)',
                fontSize: '15px',
                color: 'var(--text-primary)',
                display: 'block',
                transition: 'border-color 150ms ease, box-shadow 150ms ease',
              }}
            />

            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginTop: '12px',
              gap: '12px',
            }}>
              <select
                value={selectedModel}
                onChange={e => setSelectedModel(e.target.value)}
                disabled={modelsLoading}
                style={{
                  backgroundColor: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-secondary)',
                  padding: '10px 16px',
                  borderRadius: 'var(--radius)',
                  fontFamily: 'var(--font-ui)',
                  fontSize: '14px',
                  outline: 'none',
                  cursor: 'pointer',
                  flexShrink: 0,
                }}
              >
                {modelsLoading && <option value="">Loading models...</option>}
                {!modelsLoading && models && models.map(m => (
                  <option key={m.id} value={m.id}>
                    {m.name}{m.free ? ' (free)' : ''}
                  </option>
                ))}
              </select>

              <button
                type="submit"
                disabled={loading || !query.trim()}
                style={{
                  backgroundColor: 'var(--accent)',
                  color: 'white',
                  padding: '12px 28px',
                  borderRadius: 'var(--radius)',
                  fontFamily: 'var(--font-ui)',
                  fontWeight: 500,
                  fontSize: '15px',
                  border: 'none',
                  cursor: loading || !query.trim() ? 'not-allowed' : 'pointer',
                  minWidth: '120px',
                  opacity: loading ? 0.7 : 1,
                  transition: 'opacity 150ms ease',
                  flexShrink: 0,
                }}
              >
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
