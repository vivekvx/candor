import { useState, useEffect } from 'react'
import { useModels } from '../../hooks/useModels'

const CUSTOM_ID = '__custom__'

const EXAMPLES = [
  "Should I join Zepto as a backend engineer for 42 LPA?",
  "Is this ESOP offer from a Series A actually worth anything?",
  "Should I leave my FAANG job for a founder role at a seed startup?",
  "Swiggy vs Zepto — which offer should I take?",
]

export default function QueryInput({ onStart }) {
  const [query, setQuery] = useState('')
  const [selectedModel, setSelectedModel] = useState('')
  const [customModel, setCustomModel] = useState('')
  const [isCustom, setIsCustom] = useState(false)
  const [placeholderIndex, setPlaceholderIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const [focused, setFocused] = useState(false)
  const [customFocused, setCustomFocused] = useState(false)
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

  const handleSelectChange = (e) => {
    const val = e.target.value
    if (val === CUSTOM_ID) {
      setIsCustom(true)
      setSelectedModel(CUSTOM_ID)
    } else {
      setIsCustom(false)
      setSelectedModel(val)
    }
  }

  const activeModel = isCustom ? customModel.trim() : selectedModel
  const customValid = !isCustom || customModel.trim().includes('/')

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim() || loading || !activeModel || !customValid) return
    setLoading(true)
    await onStart(query.trim(), activeModel)
    setLoading(false)
  }

  return (
    <>
      <style>{`
        .candor-textarea::placeholder { color: var(--text-dim); }
        .candor-textarea:focus { outline: none; }
        .custom-model-input::placeholder { color: var(--text-dim); }
        .custom-model-input:focus { outline: none; }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-4px); }
          to { opacity: 1; transform: translateY(0); }
        }
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
              alignItems: 'flex-start',
              justifyContent: 'space-between',
              marginTop: '12px',
              gap: '12px',
            }}>
              {/* Model selector + custom input */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', minWidth: 0, flex: 1 }}>
                <select
                  value={selectedModel}
                  onChange={handleSelectChange}
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
                    width: '100%',
                  }}
                >
                  {modelsLoading && <option value="">Loading models...</option>}
                  {!modelsLoading && models && models.map(m => (
                    <option key={m.id} value={m.id}>
                      {m.name}{m.free ? ' (free)' : ''}
                    </option>
                  ))}
                  <option value={CUSTOM_ID}>Custom model…</option>
                </select>

                {isCustom && (
                  <div style={{ animation: 'fadeIn 150ms ease' }}>
                    <input
                      className="custom-model-input"
                      type="text"
                      value={customModel}
                      onChange={e => setCustomModel(e.target.value)}
                      onFocus={() => setCustomFocused(true)}
                      onBlur={() => setCustomFocused(false)}
                      placeholder="provider/model-name"
                      autoFocus
                      style={{
                        width: '100%',
                        boxSizing: 'border-box',
                        backgroundColor: 'var(--bg-card)',
                        border: `1px solid ${customFocused ? 'var(--accent)' : customValid ? 'var(--border)' : 'var(--challenger)'}`,
                        color: 'var(--text-primary)',
                        padding: '8px 12px',
                        borderRadius: 'var(--radius)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '13px',
                        transition: 'border-color 150ms ease',
                      }}
                    />
                    <div style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '11px',
                      color: 'var(--text-dim)',
                      marginTop: '5px',
                      lineHeight: 1.6,
                    }}>
                      groq/llama-3.1-8b-instant · anthropic/claude-opus-4-5 · gemini/gemini-2.0-flash
                    </div>
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={loading || !query.trim() || !customValid || (isCustom && !customModel.trim())}
                style={{
                  backgroundColor: 'var(--accent)',
                  color: 'white',
                  padding: '12px 28px',
                  borderRadius: 'var(--radius)',
                  fontFamily: 'var(--font-ui)',
                  fontWeight: 500,
                  fontSize: '15px',
                  border: 'none',
                  cursor: (loading || !query.trim()) ? 'not-allowed' : 'pointer',
                  minWidth: '120px',
                  opacity: (loading || (isCustom && !customModel.trim())) ? 0.7 : 1,
                  transition: 'opacity 150ms ease',
                  flexShrink: 0,
                  alignSelf: 'flex-start',
                  marginTop: '1px',
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
