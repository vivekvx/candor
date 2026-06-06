import { useState, useEffect } from 'react'

const PROFILE_KEY = 'candor_profile'

function loadProfile() {
  try {
    return JSON.parse(localStorage.getItem(PROFILE_KEY) || 'null')
  } catch {
    return null
  }
}

function saveProfile(profile) {
  localStorage.setItem(PROFILE_KEY, JSON.stringify(profile))
}

export function useUserProfile() {
  const [profile, setProfile] = useState(() => loadProfile())

  function updateProfile(p) {
    setProfile(p)
    saveProfile(p)
  }

  function clearProfile() {
    setProfile(null)
    localStorage.removeItem(PROFILE_KEY)
  }

  return { profile, updateProfile, clearProfile }
}

export default function UserProfile({ onClose }) {
  const { profile, updateProfile } = useUserProfile()
  const [form, setForm] = useState({
    role: profile?.role || '',
    experience: profile?.experience || '',
    currentCtc: profile?.currentCtc != null ? String(profile.currentCtc) : '',
    riskAppetite: profile?.riskAppetite || 'Balanced',
  })

  function handleSave(e) {
    e.preventDefault()
    updateProfile({
      role: form.role.trim() || null,
      experience: form.experience || null,
      currentCtc: form.currentCtc ? parseFloat(form.currentCtc) : null,
      riskAppetite: form.riskAppetite,
    })
    onClose()
  }

  const inputStyle = {
    width: '100%',
    boxSizing: 'border-box',
    backgroundColor: '#1a1a2e',
    border: '1px solid var(--border)',
    borderRadius: '6px',
    padding: '10px 12px',
    fontFamily: 'var(--font-ui)',
    fontSize: '14px',
    color: 'var(--text-primary)',
    outline: 'none',
  }

  const labelStyle = {
    fontFamily: 'var(--font-ui)',
    fontSize: '12px',
    fontWeight: 600,
    letterSpacing: '0.06em',
    color: 'var(--text-dim)',
    textTransform: 'uppercase',
    marginBottom: '6px',
    display: 'block',
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0,0,0,0.7)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '24px',
      }}
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
    >
      <div style={{
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: '12px',
        padding: '28px',
        width: '100%',
        maxWidth: '400px',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '24px',
        }}>
          <h2 style={{
            fontFamily: 'var(--font-display)',
            fontSize: '18px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            margin: 0,
            letterSpacing: '-0.02em',
          }}>
            Your Profile
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-dim)',
              cursor: 'pointer',
              fontSize: '20px',
              padding: '0 4px',
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>

        <p style={{
          fontFamily: 'var(--font-ui)',
          fontSize: '13px',
          color: 'var(--text-secondary)',
          marginTop: 0,
          marginBottom: '24px',
          lineHeight: 1.6,
        }}>
          Optional — verdicts are personalized when you fill this in.
        </p>

        <form onSubmit={handleSave} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={labelStyle}>Current Role</label>
            <input
              type="text"
              value={form.role}
              onChange={e => setForm(f => ({ ...f, role: e.target.value }))}
              placeholder="e.g. Backend Engineer"
              style={inputStyle}
            />
          </div>

          <div>
            <label style={labelStyle}>Years of Experience</label>
            <select
              value={form.experience}
              onChange={e => setForm(f => ({ ...f, experience: e.target.value }))}
              style={{ ...inputStyle, cursor: 'pointer' }}
            >
              <option value="">Select…</option>
              <option value="0-1">0–1 years</option>
              <option value="1-3">1–3 years</option>
              <option value="3-5">3–5 years</option>
              <option value="5-10">5–10 years</option>
              <option value="10+">10+ years</option>
            </select>
          </div>

          <div>
            <label style={labelStyle}>Current CTC (LPA) — optional</label>
            <input
              type="number"
              value={form.currentCtc}
              onChange={e => setForm(f => ({ ...f, currentCtc: e.target.value }))}
              placeholder="e.g. 24"
              min={0}
              style={inputStyle}
            />
          </div>

          <div>
            <label style={labelStyle}>Risk Appetite</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              {['Conservative', 'Balanced', 'Aggressive'].map(opt => (
                <button
                  key={opt}
                  type="button"
                  onClick={() => setForm(f => ({ ...f, riskAppetite: opt }))}
                  style={{
                    flex: 1,
                    padding: '8px',
                    borderRadius: '6px',
                    border: `1px solid ${form.riskAppetite === opt ? 'var(--accent)' : 'var(--border)'}`,
                    backgroundColor: form.riskAppetite === opt ? 'rgba(99,102,241,0.15)' : 'transparent',
                    color: form.riskAppetite === opt ? 'var(--accent)' : 'var(--text-secondary)',
                    fontFamily: 'var(--font-ui)',
                    fontSize: '12px',
                    fontWeight: form.riskAppetite === opt ? 600 : 400,
                    cursor: 'pointer',
                    transition: 'all 150ms ease',
                  }}
                >
                  {opt}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            style={{
              backgroundColor: 'var(--accent)',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '12px',
              fontFamily: 'var(--font-ui)',
              fontSize: '14px',
              fontWeight: 600,
              cursor: 'pointer',
              marginTop: '8px',
            }}
          >
            Save Profile
          </button>
        </form>
      </div>
    </div>
  )
}
