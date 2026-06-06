import { useState, useEffect } from 'react'

function ScoreBar({ label, score, color }) {
  const [width, setWidth] = useState(0)
  useEffect(() => {
    const t = setTimeout(() => setWidth(score * 10), 100)
    return () => clearTimeout(t)
  }, [score])
  return (
    <div style={{ flex: 1 }}>
      <div style={{ fontFamily: 'var(--font-ui)', fontSize: '10px', fontWeight: 600, letterSpacing: '0.12em', color: 'var(--text-dim)', marginBottom: '8px' }}>
        {label}
      </div>
      <div style={{ height: '6px', backgroundColor: 'var(--border)', borderRadius: '3px', overflow: 'hidden', marginBottom: '6px' }}>
        <div style={{ height: '100%', width: `${width}%`, backgroundColor: color, borderRadius: '3px', transition: 'width 800ms ease' }} />
      </div>
      <div style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', fontWeight: 700, color: color }}>
        {score}<span style={{ fontSize: '12px', color: 'var(--text-dim)', fontWeight: 400 }}>/10</span>
      </div>
    </div>
  )
}

function CopyButton({ verdict }) {
  const [label, setLabel] = useState('Copy')

  function handleCopy() {
    const text = [
      'CANDOR VERDICT',
      '',
      `Bull Score: ${verdict.bull_score}/10`,
      `Bear Score: ${verdict.bear_score}/10`,
      '',
      `VERDICT: ${verdict.verdict}`,
      '',
      verdict.what_to_find_out?.length ? 'WHAT TO FIND OUT:' : null,
      verdict.what_to_find_out?.map((q, i) => `${i + 1}. ${q}`).join('\n'),
      '',
      verdict.if_i_were_you ? 'IF I WERE YOU:' : null,
      verdict.if_i_were_you,
      '',
      verdict.negotiation_tip ? 'NEGOTIATION TIP:' : null,
      verdict.negotiation_tip,
    ].filter(Boolean).join('\n')

    navigator.clipboard.writeText(text).then(() => {
      setLabel('Copied ✓')
      setTimeout(() => setLabel('Copy'), 2000)
    })
  }

  return (
    <button
      onClick={handleCopy}
      style={{
        background: 'transparent',
        border: 'none',
        color: label === 'Copy' ? 'var(--text-secondary)' : 'var(--advocate)',
        cursor: 'pointer',
        fontFamily: 'var(--font-mono)',
        fontSize: '12px',
        padding: '4px 8px',
        transition: 'color 150ms ease',
      }}
    >
      {label}
    </button>
  )
}

function ShareButton({ debateId }) {
  const [label, setLabel] = useState('Share')
  function handleShare() {
    const url = `${window.location.origin}/debate/${debateId}`
    navigator.clipboard.writeText(url).then(() => {
      setLabel('Link copied! ✓')
      setTimeout(() => setLabel('Share'), 2000)
    })
  }
  if (!debateId) return null
  return (
    <button onClick={handleShare} className="share-button" style={{
      background: 'transparent', border: 'none',
      color: label === 'Share' ? 'var(--text-secondary)' : 'var(--advocate)',
      cursor: 'pointer', fontFamily: 'var(--font-mono)', fontSize: '12px',
      padding: '4px 8px', transition: 'color 150ms ease',
    }}>{label}</button>
  )
}

function ExportButton() {
  return (
    <button onClick={() => window.print()} className="export-button" style={{
      background: 'transparent', border: 'none',
      color: 'var(--text-secondary)', cursor: 'pointer',
      fontFamily: 'var(--font-mono)', fontSize: '12px', padding: '4px 8px',
    }}>Export PDF</button>
  )
}

export default function VerdictCard({ verdict, debateId }) {
  if (!verdict) return null
  const v = verdict

  return (
    <div style={{
      backgroundColor: 'var(--bg-card)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--border)',
      padding: '32px',
      marginTop: '16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div style={{ fontFamily: 'var(--font-display)', fontSize: '24px', fontWeight: 700, color: 'var(--arbitrator)' }}>
          ⚖ VERDICT
        </div>
        <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
          <ShareButton debateId={debateId} />
          <ExportButton />
          <CopyButton verdict={v} />
        </div>
      </div>

      {(v.bull_score !== undefined || v.bear_score !== undefined) && (
        <div style={{ display: 'flex', gap: '24px', marginBottom: '24px' }}>
          <ScoreBar label="BULL CASE" score={v.bull_score ?? 0} color="var(--advocate)" />
          <div style={{ width: '1px', backgroundColor: 'var(--border)', flexShrink: 0 }} />
          <ScoreBar label="BEAR CASE" score={v.bear_score ?? 0} color="var(--challenger)" />
        </div>
      )}

      {v.verdict && (
        <div style={{
          fontFamily: 'var(--font-display)',
          fontSize: '20px',
          fontWeight: 700,
          color: 'var(--text-primary)',
          lineHeight: 1.5,
          borderLeft: '3px solid var(--arbitrator)',
          paddingLeft: '16px',
          marginBottom: '24px',
        }}>
          {v.verdict}
        </div>
      )}

      {v.what_to_find_out && v.what_to_find_out.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: '10px', fontWeight: 600, letterSpacing: '0.12em', color: 'var(--text-dim)', marginBottom: '12px' }}>
            WHAT TO FIND OUT BEFORE DECIDING
          </div>
          <ol style={{ margin: 0, padding: '0 0 0 20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {v.what_to_find_out.map((item, i) => (
              <li key={i} style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                {item}
              </li>
            ))}
          </ol>
        </div>
      )}

      {v.if_i_were_you && (
        <div style={{
          borderLeft: '3px solid var(--arbitrator)',
          backgroundColor: '#1a1a1f',
          padding: '16px',
          borderRadius: '0 var(--radius) var(--radius) 0',
          marginBottom: '16px',
        }}>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: '10px', fontWeight: 600, letterSpacing: '0.12em', color: 'var(--arbitrator)', marginBottom: '8px' }}>
            IF I WERE YOU
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            {v.if_i_were_you}
          </div>
        </div>
      )}

      {v.negotiation_tip && (
        <div style={{
          borderLeft: '3px solid var(--advocate)',
          backgroundColor: '#1a1a1f',
          padding: '16px',
          borderRadius: '0 var(--radius) var(--radius) 0',
        }}>
          <div style={{ fontFamily: 'var(--font-ui)', fontSize: '10px', fontWeight: 600, letterSpacing: '0.12em', color: 'var(--advocate)', marginBottom: '8px' }}>
            NEGOTIATION TIP
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            {v.negotiation_tip}
          </div>
        </div>
      )}
    </div>
  )
}
