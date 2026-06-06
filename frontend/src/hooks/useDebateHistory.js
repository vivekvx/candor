const HISTORY_KEY = 'candor_debate_history'
const MAX_HISTORY = 10

export function useDebateHistory() {
  function getHistory() {
    try {
      return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]')
    } catch {
      return []
    }
  }

  function saveDebate(query, verdict, metadata) {
    const history = getHistory()
    const entry = {
      id: Date.now().toString(),
      query,
      verdict_summary: verdict?.verdict || '',
      bull_score: verdict?.bull_score || 0,
      bear_score: verdict?.bear_score || 0,
      cost_usd: metadata?.cost_usd || 0,
      timestamp: new Date().toISOString(),
    }
    const updated = [entry, ...history].slice(0, MAX_HISTORY)
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated))
    return entry
  }

  function clearHistory() {
    localStorage.removeItem(HISTORY_KEY)
  }

  return { saveDebate, getHistory, clearHistory }
}
