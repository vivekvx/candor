const STAGES = ['round_1', 'cross_exam', 'arbitrating', 'complete']
const LABELS = ['Round 1 Research', 'Cross-Examination', 'Arbitration', 'Complete']

function getStageIndex(status) {
  const idx = STAGES.indexOf(status)
  return idx === -1 ? -1 : idx
}

export default function DebateTimeline({ status }) {
  const currentIndex = getStageIndex(status)

  return (
    <>
      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.3); }
        }
      `}</style>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px 24px',
        backgroundColor: 'var(--bg-card)',
        borderBottom: '1px solid var(--border)',
        overflowX: 'auto',
        gap: 0,
      }}>
        {STAGES.map((stage, i) => {
          const isCompleted = i < currentIndex
          const isActive = i === currentIndex
          const isPending = i > currentIndex

          return (
            <div key={stage} style={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
                <div style={{
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  backgroundColor: isCompleted ? 'var(--text-dim)' : isActive ? 'var(--accent)' : 'transparent',
                  border: isPending ? '1px solid var(--text-dim)' : isCompleted ? '1px solid var(--text-dim)' : 'none',
                  animation: isActive ? 'pulse-dot 1.5s ease-in-out infinite' : 'none',
                  transition: 'background-color 300ms ease',
                }} />
                <span style={{
                  fontFamily: 'var(--font-ui)',
                  fontSize: '11px',
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? 'var(--text-primary)' : 'var(--text-dim)',
                  whiteSpace: 'nowrap',
                  letterSpacing: '0.05em',
                }}>
                  {isCompleted ? '✓ ' : ''}{LABELS[i]}
                </span>
              </div>
              {i < STAGES.length - 1 && (
                <div style={{
                  width: '48px',
                  height: '1px',
                  backgroundColor: i < currentIndex ? 'var(--border-bright)' : 'var(--border)',
                  margin: '0 8px',
                  marginBottom: '16px',
                  transition: 'background-color 300ms ease',
                }} />
              )}
            </div>
          )
        })}
      </div>
    </>
  )
}
