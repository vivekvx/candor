import { useState, useCallback, useRef } from 'react'
import { useDebateHistory } from './useDebateHistory'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''

function formatError(message) {
  if (!message) return 'Something went wrong. Please try again.'
  const msg = message.toLowerCase()
  if (msg.includes('rate limit') || msg.includes('ratelimit')) {
    const waitMatch = message.match(/try again in (\d+)m/i)
    if (waitMatch) return `Rate limited — Groq free tier limit reached. Try again in ${waitMatch[1]} minutes.`
    return 'Rate limited — Groq free tier limit reached. Try again in a few minutes.'
  }
  if (msg.includes('invalid api key') || msg.includes('invalid_api_key')) {
    return 'Invalid API key — check your GROQ_API_KEY in backend/.env'
  }
  if (msg.includes('connection') || msg.includes('network')) {
    return 'Connection error — make sure the backend is running on port 8000.'
  }
  return 'Something went wrong. Please try again.'
}

const INITIAL_STATE = {
  status: 'idle',
  advocateResearch: null,
  challengerResearch: null,
  advocateRebuttal: null,
  challengerRebuttal: null,
  verdict: null,
  metadata: null,
  error: null,
}

export function useDebate() {
  const [state, setState] = useState(INITIAL_STATE)
  const abortRef = useRef(null)
  const { saveDebate } = useDebateHistory()
  const queryRef = useRef('')

  const startDebate = useCallback(async (query, model) => {
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()
    queryRef.current = query
    setState({ ...INITIAL_STATE, status: 'connecting' })

    const profile = (() => {
      try { return JSON.parse(localStorage.getItem('candor_profile') || 'null') } catch { return null }
    })()

    try {
      const response = await fetch(`${API_BASE_URL}/api/debate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, model, user_profile: profile }),
        signal: abortRef.current.signal,
      })

      if (response.status === 429) {
        let message = 'High demand right now. Try again in a few minutes.'
        try {
          const data = await response.json()
          message = data.detail?.message || message
        } catch {}
        setState(s => ({ ...s, status: 'rate_limited', error: message }))
        return
      }

      if (!response.ok) {
        let message = `Request failed (HTTP ${response.status})`
        try {
          const data = await response.json()
          message = data.detail?.message || data.detail || message
        } catch {}
        setState(s => ({ ...s, status: 'error', error: formatError(message) }))
        return
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          try {
            const event = JSON.parse(line.slice(6))
            handleEvent(event, setState, (verdict, metadata, debateId) => {
              saveDebate(queryRef.current, verdict, metadata)
            })
          } catch {}
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setState(s => ({ ...s, status: 'error', error: formatError(err.message) }))
      }
    }
  }, [])

  const reset = useCallback(() => {
    if (abortRef.current) abortRef.current.abort()
    setState(INITIAL_STATE)
  }, [])

  return { state, startDebate, reset }
}

function handleEvent(event, setState, saveHistory) {
  switch (event.type) {
    case 'status':
      setState(s => ({
        ...s,
        status: event.stage === 'round_1_start' ? 'round_1'
              : event.stage === 'cross_examination_start' ? 'cross_exam'
              : event.stage === 'arbitration_start' ? 'arbitrating'
              : s.status
      }))
      break
    case 'advocate_research':
      setState(s => ({ ...s, advocateResearch: event.content }))
      break
    case 'challenger_research':
      setState(s => ({ ...s, challengerResearch: event.content }))
      break
    case 'advocate_rebuttal':
      setState(s => ({ ...s, advocateRebuttal: event.content }))
      break
    case 'challenger_rebuttal':
      setState(s => ({ ...s, challengerRebuttal: event.content }))
      break
    case 'verdict':
      setState(s => ({ ...s, verdict: event.content }))
      break
    case 'complete':
      setState(s => {
        if (s.verdict) saveHistory(s.verdict, event.metadata, event.debate_id)
        return { ...s, status: 'complete', metadata: { ...event.metadata, debate_id: event.debate_id } }
      })
      break
    case 'error':
      setState(s => ({ ...s, status: 'error', error: formatError(event.message) }))
      break
  }
}
