import { useState, useEffect } from 'react'

const AGENT_CONFIG = {
  advocate: {
    color: 'var(--advocate)',
    dimColor: 'var(--advocate-dim)',
    label: 'ADVOCATE',
    subtitle: 'Building the strongest case for',
    rebuttalLabel: '↩ REBUTTAL',
  },
  challenger: {
    color: 'var(--challenger)',
    dimColor: 'var(--challenger-dim)',
    label: 'CHALLENGER',
    subtitle: 'Attacking every claim',
    rebuttalLabel: '⚔ CROSS-EXAMINATION',
  },
  arbitrator: {
    color: 'var(--arbitrator)',
    dimColor: 'var(--arbitrator-dim)',
    label: 'ARBITRATOR',
    subtitle: 'Delivering the honest verdict',
    rebuttalLabel: null,
  },
}

function SkeletonBar({ width = '100%', height = '14px' }) {
  return (
    <div style={{
      width,
      height,
      borderRadius: '4px',
      background: 'linear-gradient(90deg, var(--border) 25%, var(--border-bright) 50%, var(--border) 75%)',
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.5s infinite',
    }} />
  )
}

function Label({ children, color }) {
  return (
    <div style={{
      fontFamily: 'var(--font-ui)',
      fontSize: '10px',
      fontWeight: 600,
      letterSpacing: '0.12em',
      color: color || 'var(--text-dim)',
      marginBottom: '6px',
      textTransform: 'uppercase',
    }}>
      {children}
    </div>
  )
}

function Section({ children }) {
  return (
    <div style={{ marginBottom: '16px' }}>
      {children}
    </div>
  )
}

function ConfidenceBar({ value, color }) {
  const [animatedWidth, setAnimatedWidth] = useState(0)

  useEffect(() => {
    const t = setTimeout(() => setAnimatedWidth((value || 0) * 100), 100)
    return () => clearTimeout(t)
  }, [value])

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
      <div style={{
        flex: 1,
        height: '6px',
        backgroundColor: 'var(--border)',
        borderRadius: '3px',
        overflow: 'hidden',
      }}>
        <div style={{
          height: '100%',
          width: `${animatedWidth}%`,
          backgroundColor: color,
          borderRadius: '3px',
          transition: 'width 800ms ease',
        }} />
      </div>
      <span style={{
        fontFamily: 'var(--font-mono)',
        fontSize: '12px',
        color: 'var(--text-secondary)',
        minWidth: '36px',
        textAlign: 'right',
      }}>
        {value}%
      </span>
    </div>
  )
}

export default function AgentCard({ agent, round1Data, round2Data, isActive, isComplete }) {
  const cfg = AGENT_CONFIG[agent]

  const cardStyle = {
    backgroundColor: 'var(--bg-card)',
    borderRadius: 'var(--radius-lg)',
    border: `1px solid ${isActive && !round1Data ? cfg.color : 'var(--border)'}`,
    boxShadow: isActive && !round1Data ? `0 0 0 1px ${cfg.color}, 0 0 24px ${cfg.color}22` : 'none',
    padding: '24px',
    transition: 'border-color 300ms ease, box-shadow 300ms ease',
    animation: round1Data ? 'slideUp 300ms ease' : 'none',
  }

  const header = (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
      <div style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        backgroundColor: cfg.color,
        flexShrink: 0,
      }} />
      <div>
        <div style={{
          fontFamily: 'var(--font-ui)',
          fontSize: '12px',
          fontWeight: 600,
          letterSpacing: '0.1em',
          color: cfg.color,
          textTransform: 'uppercase',
        }}>
          {cfg.label}
        </div>
        <div style={{
          fontFamily: 'var(--font-ui)',
          fontSize: '11px',
          color: 'var(--text-dim)',
          marginTop: '2px',
        }}>
          {cfg.subtitle}
        </div>
      </div>
    </div>
  )

  if (isActive && !round1Data) {
    return (
      <>
        <style>{`
          @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
          }
          @keyframes slideUp {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
          }
          .researching-dots::after {
            content: '';
            animation: dots 1.2s steps(3, end) infinite;
          }
          @keyframes dots {
            0%   { content: ''; }
            33%  { content: '.'; }
            66%  { content: '..'; }
            100% { content: '...'; }
          }
        `}</style>
        <div style={cardStyle}>
          {header}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '16px' }}>
            <SkeletonBar width="85%" />
            <SkeletonBar width="65%" />
            <SkeletonBar width="75%" />
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '12px',
            color: 'var(--text-dim)',
          }}>
            <span className="researching-dots">Researching</span>
          </div>
        </div>
      </>
    )
  }

  if (!round1Data) {
    return (
      <>
        <style>{`
          @keyframes slideUp {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}</style>
        <div style={{ ...cardStyle, opacity: 0.4 }}>
          {header}
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '12px',
            color: 'var(--text-dim)',
          }}>
            Waiting...
          </div>
        </div>
      </>
    )
  }

  const d = round1Data

  return (
    <>
      <style>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
      <div style={cardStyle}>
        {header}
        <div style={{ height: '1px', backgroundColor: 'var(--border)', marginBottom: '16px' }} />

        {d.headline_claim && (
          <Section>
            <Label>Position</Label>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '14px',
              color: 'var(--text-primary)',
              lineHeight: 1.5,
            }}>
              {d.headline_claim}
            </div>
          </Section>
        )}

        {d.headline_counter && (
          <Section>
            <Label>Counter</Label>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '14px',
              color: 'var(--text-primary)',
              lineHeight: 1.5,
            }}>
              {d.headline_counter}
            </div>
          </Section>
        )}

        {d.evidence && d.evidence.length > 0 && (
          <Section>
            <Label>Evidence</Label>
            <ul style={{ margin: 0, padding: '0 0 0 16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {d.evidence.map((item, i) => (
                <li key={i} style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.5,
                }}>
                  {typeof item === "string" ? item : item.advocate_claimed || item.point || item.text || JSON.stringify(item)}
                  {item.source && (
                    <span style={{ color: 'var(--text-dim)', marginLeft: '6px' }}>({item.source})</span>
                  )}
                </li>
              ))}
            </ul>
          </Section>
        )}

        {d.point_by_point && d.point_by_point.length > 0 && !round2Data && (
          <Section>
            <Label>Evidence</Label>
            <ul style={{ margin: 0, padding: '0 0 0 16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {d.point_by_point.map((item, i) => (
                <li key={i} style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.5,
                }}>
                  {item.advocate_claimed || item.point || item.claim || (typeof item === "string" ? item : JSON.stringify(item))}
                  {item.source && (
                    <span style={{ color: 'var(--text-dim)', marginLeft: '6px' }}>({item.source})</span>
                  )}
                </li>
              ))}
            </ul>
          </Section>
        )}

        {(d.strongest_point || d.strongest_counter) && (
          <Section>
            <Label>{d.strongest_counter ? 'Strongest Counter' : 'Strongest Point'}</Label>
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '13px',
              fontStyle: 'italic',
              color: 'var(--text-secondary)',
              lineHeight: 1.5,
              borderLeft: `2px solid ${cfg.color}`,
              paddingLeft: '10px',
            }}>
              {d.strongest_point || d.strongest_counter}
            </div>
          </Section>
        )}

        {d.confidence !== undefined && (
          <Section>
            <Label>Confidence</Label>
            <ConfidenceBar value={d.confidence} color={cfg.color} />
          </Section>
        )}

        {round2Data && (
          <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid var(--border)' }}>
            <Label color={agent === 'challenger' ? 'var(--challenger)' : 'var(--advocate)'}>
              {cfg.rebuttalLabel}
            </Label>

            {agent === 'challenger' && round2Data.point_by_point && round2Data.point_by_point.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {round2Data.point_by_point.map((item, i) => (
                  <div key={i}>
                    <div style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '12px',
                      fontStyle: 'italic',
                      color: 'var(--text-dim)',
                      lineHeight: 1.5,
                      marginBottom: '4px',
                    }}>
                      They claimed: {typeof item === "string" ? item : item.advocate_claimed || item.claim || item.point || JSON.stringify(item)}
                    </div>
                    {item.counter && (
                      <div style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '13px',
                        color: 'var(--text-secondary)',
                        lineHeight: 1.5,
                      }}>
                        Counter: {item.counter}
                        {item.source && (
                          <span style={{ color: 'var(--text-dim)', marginLeft: '6px' }}>[{item.source}]</span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {agent === 'advocate' && round2Data.evidence && round2Data.evidence.length > 0 && (
              <ul style={{ margin: 0, padding: '0 0 0 16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {round2Data.evidence.map((item, i) => (
                  <li key={i} style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.5,
                  }}>
                    {typeof item === "string" ? item : item.advocate_claimed || item.point || item.text || JSON.stringify(item)}
                    {item.source && (
                      <span style={{ color: 'var(--text-dim)', marginLeft: '6px' }}>({item.source})</span>
                    )}
                  </li>
                ))}
              </ul>
            )}

            {agent === 'advocate' && round2Data.point_by_point && round2Data.point_by_point.length > 0 && !round2Data.evidence && (
              <ul style={{ margin: 0, padding: '0 0 0 16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {round2Data.point_by_point.map((item, i) => (
                  <li key={i} style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '13px',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.5,
                  }}>
                    {item.advocate_claimed || item.point || item.claim || (typeof item === "string" ? item : JSON.stringify(item))}
                    {item.source && (
                      <span style={{ color: 'var(--text-dim)', marginLeft: '6px' }}>({item.source})</span>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </>
  )
}
