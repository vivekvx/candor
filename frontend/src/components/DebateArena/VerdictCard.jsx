import { useState, useEffect } from 'react'

const BADGE_CONFIG = {
  'HIGH':        { color: '#22c55e', bg: '#052e16', icon: '✓' },
  'MODERATE':    { color: '#f59e0b', bg: '#1c1400', icon: '~' },
  'LOW':         { color: '#ef4444', bg: '#1c0000', icon: '!' },
  'VERY LOW':    { color: '#ef4444', bg: '#1c0000', icon: '!!' },
  'NO DATA':     { color: '#6b7280', bg: '#111', icon: '?' },
}

function DataConfidenceBadge({ confidence }) {
  if (!confidence) return null
  const config = BADGE_CONFIG[confidence.label] || BADGE_CONFIG['NO DATA']
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: '6px',
      background: config.bg, border: `1px solid ${config.color}`,
      borderRadius: '6px', padding: '4px 10px', fontSize: '0.8rem',
      color: config.color, marginBottom: '1rem'
    }}>
      <span>{config.icon}</span>
      <span>Data confidence: {confidence.label}</span>
      <span style={{ color: '#666', fontSize: '0.75rem' }}>
        ({confidence.tools_summary})
      </span>
    </div>
  )
}

function ContradictionWarning({ disputes }) {
  if (!disputes || disputes.length === 0) return null
  return (
    <div style={{
      background: '#1c1000', border: '1px solid #f59e0b',
      borderRadius: '8px', padding: '0.75rem 1rem', margin: '0 0 1rem',
      fontSize: '0.85rem', color: '#f59e0b'
    }}>
      <strong>⚠ Factual disputes detected</strong>
      <p style={{ margin: '4px 0 0', color: '#d97706' }}>
        The agents gave contradictory information about:{' '}
        {disputes.join(', ')}.{' '}
        Verify these independently before deciding.
      </p>
    </div>
  )
}

function ReasoningTrail({ text }) {
  if (!text) return null
  return (
    <div style={{
      background: '#111', border: '1px solid #222',
      borderRadius: '8px', padding: '1rem', margin: '0 0 24px'
    }}>
      <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '6px',
                    textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Why this verdict
      </div>
      <p style={{ color: '#ccc', lineHeight: 1.6, margin: 0, fontSize: '0.9rem' }}>
        {text}
      </p>
    </div>
  )
}

const GLOSSARY = {
  'charge document': 'A record that the company has pledged its assets as loan collateral. High risk signal for employees.',
  'mca filing': 'Ministry of Corporate Affairs registration. Verifies the company is legally registered in India.',
  'esop': 'Employee Stock Ownership Plan. Shares the company grants you — only valuable if the company exits or IPOs.',
  'liquidation preference': 'Investors get paid before employees in an acquisition. 1x means they recover their investment first.',
  'burn rate': 'How fast the company spends money. High burn + low runway = layoff risk.',
  'series b': 'Second major funding round. Indicates investor confidence but also higher valuation pressure.',
  'ndr': 'Net Dollar Retention. How much revenue is retained from existing customers. Above 100% means customers expand.',
  'nbfc': 'Non-Banking Financial Company. Requires RBI license. Missing license = regulatory risk.',
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function GlossaryText({ text }) {
  if (!text) return null
  const escaped = escapeHtml(text)
  const html = Object.entries(GLOSSARY).reduce((acc, [term, def]) =>
    acc.replace(
      new RegExp(`\\b(${term})\\b`, 'gi'),
      `<span title="${escapeHtml(def)}" style="border-bottom:1px dotted #666;cursor:help">$1</span>`
    ), escaped)
  return <span dangerouslySetInnerHTML={{ __html: html }} />
}

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

      <DataConfidenceBadge confidence={v.data_confidence} />
      <ContradictionWarning disputes={v.unresolved_disputes} />

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
          <GlossaryText text={v.verdict} />
        </div>
      )}

      <ReasoningTrail text={v.reasoning_trail} />

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
            <GlossaryText text={v.if_i_were_you} />
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
