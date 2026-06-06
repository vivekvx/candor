import DebateTimeline from './DebateTimeline'
import AgentCard from './AgentCard'
import VerdictCard from './VerdictCard'

const LIVE_STATUSES = new Set(['round_1', 'cross_exam', 'arbitrating'])

export default function DebateArena({ state, currentQuery, onReset }) {
  const { status, advocateResearch, challengerResearch, advocateRebuttal, challengerRebuttal, verdict, metadata, error } = state

  const isLive = LIVE_STATUSES.has(status)
  const isComplete = status === 'complete'

  const advocateActive = (status === 'round_1' && !advocateResearch) || (status === 'cross_exam' && !advocateRebuttal)
  const challengerActive = (status === 'round_1' && !challengerResearch) || (status === 'cross_exam' && !challengerRebuttal)
  const arbitratorActive = status === 'arbitrating' && !verdict

  const query = currentQuery || state.query || ''

  return (
    <>
      <style>{`
        @keyframes pulse-live {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes dots {
          0%   { content: ''; }
          33%  { content: '.'; }
          66%  { content: '..'; }
          100% { content: '...'; }
        }
        .researching-dots::after {
          content: '';
          animation: dots 1.2s steps(3, end) infinite;
        }
      `}</style>

      <div style={{ minHeight: '100vh', backgroundColor: 'var(--bg-primary)' }}>
        {/* Header */}
        <div style={{
          backgroundColor: 'var(--bg-card)',
          borderBottom: '1px solid var(--border)',
          padding: '12px 24px',
          position: 'sticky',
          top: 0,
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
        }}>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '13px',
            color: 'var(--text-secondary)',
            maxWidth: '60%',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}>
            {query}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: 'var(--accent)',
                animation: isLive ? 'pulse-live 1.2s ease-in-out infinite' : 'none',
              }} />
              <span style={{
                fontFamily: 'var(--font-ui)',
                fontSize: '11px',
                fontWeight: 600,
                letterSpacing: '0.1em',
                color: isLive ? 'var(--accent)' : 'var(--text-dim)',
                textTransform: 'uppercase',
              }}>
                {isLive ? 'Live' : isComplete ? 'Complete' : status}
              </span>
            </div>
            <button
              onClick={onReset}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-dim)',
                cursor: 'pointer',
                fontSize: '18px',
                padding: '4px 8px',
                lineHeight: 1,
                transition: 'color 150ms ease',
              }}
              onMouseEnter={e => e.target.style.color = 'var(--text-secondary)'}
              onMouseLeave={e => e.target.style.color = 'var(--text-dim)'}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Timeline */}
        <DebateTimeline status={status} />

        {/* Error */}
        {status === 'error' && error && (
          <div style={{
            margin: '24px',
            padding: '16px',
            backgroundColor: 'var(--challenger-dim)',
            border: '1px solid var(--challenger)',
            borderRadius: 'var(--radius)',
            fontFamily: 'var(--font-mono)',
            fontSize: '13px',
            color: 'var(--challenger)',
          }}>
            {error}
          </div>
        )}

        {/* Main grid */}
        <div style={{ padding: '24px' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '16px',
            marginBottom: '16px',
          }}>
            <AgentCard
              agent="advocate"
              round1Data={advocateResearch}
              round2Data={advocateRebuttal}
              isActive={advocateActive}
              isComplete={isComplete}
            />
            <AgentCard
              agent="challenger"
              round1Data={challengerResearch}
              round2Data={challengerRebuttal}
              isActive={challengerActive}
              isComplete={isComplete}
            />
          </div>

          {(arbitratorActive || verdict) && (
            <div style={{ marginBottom: '16px' }}>
              <AgentCard
                agent="arbitrator"
                round1Data={verdict ? { headline_claim: verdict.verdict, confidence: verdict.confidence } : null}
                round2Data={null}
                isActive={arbitratorActive}
                isComplete={isComplete}
              />
            </div>
          )}

          <VerdictCard verdict={verdict} />

          {/* Footer metadata */}
          {isComplete && metadata && (
            <div style={{
              display: 'flex',
              gap: '24px',
              padding: '16px 0',
              marginTop: '16px',
              borderTop: '1px solid var(--border)',
              flexWrap: 'wrap',
            }}>
              {metadata.total_tokens !== undefined && (
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                  Tokens: <span style={{ color: 'var(--text-secondary)' }}>{metadata.total_tokens.toLocaleString()}</span>
                </div>
              )}
              {metadata.cost_usd !== undefined && (
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                  Cost: <span style={{ color: 'var(--text-secondary)' }}>${metadata.cost_usd.toFixed(4)}</span>
                </div>
              )}
              {metadata.duration_seconds !== undefined && (
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                  Time: <span style={{ color: 'var(--text-secondary)' }}>{(metadata.duration_seconds).toFixed(1)}s</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
