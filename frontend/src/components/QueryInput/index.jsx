import { useState, useEffect } from 'react'
import { useModels } from '../../hooks/useModels'
import { useDebateHistory } from '../../hooks/useDebateHistory'

const CUSTOM_ID = '__custom__'

const EXAMPLES = [
  "Should I join Zepto as a backend engineer for 42 LPA?",
  "Is this ESOP offer from a Series A actually worth anything?",
  "Should I leave my FAANG job for a founder role at a seed startup?",
  "Swiggy vs Zepto — which offer should I take?",
]

const CHIPS = [
  "Should I join Zepto for 42 LPA?",
  "Is this ESOP offer worth taking?",
  "Leave TCS for a Series B startup?",
  "Is BYJU's still worth joining?",
  "Evaluate my offer: 28 LPA + ESOPs",
  "Switch from service to product company?",
]

const AGENTS = [
  {
    color: 'var(--advocate)',
    label: 'ADVOCATE',
    description: 'Builds the strongest case for the opportunity — funding signals, market timing, founder track record.',
  },
  {
    color: 'var(--challenger)',
    label: 'CHALLENGER',
    description: 'Attacks every claim with fresh eyes and hard evidence — red flags, market risks, compensation gaps.',
  },
  {
    color: 'var(--arbitrator)',
    label: 'ARBITRATOR',
    description: 'Delivers the honest verdict with no agenda — just the call you need to make a confident decision.',
  },
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
  const [hoveredChip, setHoveredChip] = useState(null)
  const [hoveredAgent, setHoveredAgent] = useState(null)
  const [mounted, setMounted] = useState(false)
  const { models, loading: modelsLoading } = useModels()
  const { getHistory, clearHistory } = useDebateHistory()
  const [history, setHistory] = useState(() => getHistory().slice(0, 5))

  useEffect(() => {
    const t = setTimeout(() => setMounted(true), 50)
    return () => clearTimeout(t)
  }, [])

  // Refresh history when window focused (debate may have completed in same tab)
  useEffect(() => {
    const refresh = () => setHistory(getHistory().slice(0, 5))
    window.addEventListener('focus', refresh)
    return () => window.removeEventListener('focus', refresh)
  }, [])

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
        @keyframes chipIn {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes agentIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes dotPulse {
          0%, 100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.6); opacity: 0.6; }
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

          {/* ── Example chips ── */}
          <div style={{ marginTop: '28px' }}>
            <div style={{
              fontFamily: 'var(--font-ui)',
              fontSize: '11px',
              fontWeight: 600,
              letterSpacing: '0.1em',
              color: 'var(--text-dim)',
              textTransform: 'uppercase',
              marginBottom: '10px',
            }}>
              Try an example
            </div>
            <div style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '8px',
            }}>
              {CHIPS.map((chip, i) => (
                <button
                  key={chip}
                  type="button"
                  onClick={() => setQuery(chip)}
                  onMouseEnter={() => setHoveredChip(i)}
                  onMouseLeave={() => setHoveredChip(null)}
                  style={{
                    background: 'transparent',
                    border: `1px solid ${hoveredChip === i ? 'var(--border-bright)' : 'var(--border)'}`,
                    borderRadius: '100px',
                    padding: '6px 14px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    color: hoveredChip === i ? 'var(--text-primary)' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    transition: 'border-color 150ms ease, color 150ms ease',
                    opacity: mounted ? 1 : 0,
                    animation: mounted ? `chipIn 300ms ease both` : 'none',
                    animationDelay: `${300 + i * 80}ms`,
                  }}
                >
                  {chip}
                </button>
              ))}
            </div>
          </div>

          {/* ── Divider + agent columns ── */}
          <div style={{
            marginTop: '32px',
            opacity: mounted ? 1 : 0,
            animation: mounted ? 'agentIn 400ms ease both' : 'none',
            animationDelay: '600ms',
          }}>
            <div style={{ height: '1px', backgroundColor: 'var(--border)', marginBottom: '28px' }} />

            <div style={{
              fontFamily: 'var(--font-ui)',
              fontSize: '11px',
              fontWeight: 600,
              letterSpacing: '0.1em',
              color: 'var(--text-dim)',
              textTransform: 'uppercase',
              marginBottom: '16px',
            }}>
              How it works
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '8px',
            }}>
              {AGENTS.map((agent, i) => (
                <div
                  key={agent.label}
                  onMouseEnter={() => setHoveredAgent(i)}
                  onMouseLeave={() => setHoveredAgent(null)}
                  style={{
                    padding: hoveredAgent === i ? '12px' : '12px',
                    borderRadius: '8px',
                    backgroundColor: hoveredAgent === i ? 'var(--bg-card)' : 'transparent',
                    border: `1px solid ${hoveredAgent === i ? 'var(--border)' : 'transparent'}`,
                    transition: 'background-color 200ms ease, border-color 200ms ease',
                    cursor: 'default',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    <div style={{
                      width: '7px',
                      height: '7px',
                      borderRadius: '50%',
                      backgroundColor: agent.color,
                      flexShrink: 0,
                      animation: mounted ? `dotPulse 600ms ease both` : 'none',
                      animationDelay: `${700 + i * 120}ms`,
                    }} />
                    <span style={{
                      fontFamily: 'var(--font-ui)',
                      fontSize: '11px',
                      fontWeight: 600,
                      letterSpacing: '0.12em',
                      color: agent.color,
                      textTransform: 'uppercase',
                    }}>
                      {agent.label}
                    </span>
                  </div>
                  <p style={{
                    fontFamily: 'var(--font-ui)',
                    fontSize: '13px',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.6,
                    margin: 0,
                  }}>
                    {agent.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* ── Recent debates ── */}
          {history.length > 0 && (
            <div style={{ marginTop: '32px', opacity: mounted ? 1 : 0, animation: mounted ? 'agentIn 400ms ease both' : 'none', animationDelay: '800ms' }}>
              <div style={{ height: '1px', backgroundColor: 'var(--border)', marginBottom: '20px' }} />
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                <div style={{ fontFamily: 'var(--font-ui)', fontSize: '11px', fontWeight: 600, letterSpacing: '0.1em', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                  Recent Debates
                </div>
                <button
                  type="button"
                  onClick={() => { clearHistory(); setHistory([]) }}
                  style={{ background: 'none', border: 'none', fontFamily: 'var(--font-ui)', fontSize: '11px', color: 'var(--text-dim)', cursor: 'pointer', padding: 0 }}
                >
                  Clear
                </button>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                {history.map(entry => {
                  const ago = (() => {
                    const diff = Date.now() - new Date(entry.timestamp).getTime()
                    const h = Math.floor(diff / 3600000)
                    if (h < 1) return 'just now'
                    if (h < 24) return `${h}h ago`
                    return `${Math.floor(h / 24)}d ago`
                  })()
                  return (
                    <button
                      key={entry.id}
                      type="button"
                      onClick={() => setQuery(entry.query)}
                      style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        background: 'transparent', border: '1px solid transparent',
                        borderRadius: '6px', padding: '8px 10px', cursor: 'pointer',
                        textAlign: 'left', transition: 'border-color 150ms ease, background-color 150ms ease',
                        width: '100%',
                      }}
                      onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.backgroundColor = 'var(--bg-card)' }}
                      onMouseLeave={e => { e.currentTarget.style.borderColor = 'transparent'; e.currentTarget.style.backgroundColor = 'transparent' }}
                    >
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginRight: '12px' }}>
                        {entry.query.length > 60 ? entry.query.slice(0, 60) + '…' : entry.query}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--advocate)' }}>● {entry.bull_score}</span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--challenger)' }}>● {entry.bear_score}</span>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>{ago}</span>
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>
          )}

        </div>
      </div>
    </>
  )
}
