import { useState, useEffect } from 'react'

export function useModels() {
  const [models, setModels] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('/api/models')
      .then(r => r.json())
      .then(d => { setModels(d.models || []); setLoading(false) })
      .catch(() => {
        setModels([{ id: 'groq/llama-3.3-70b-versatile', name: 'Llama 3.3 70B', provider: 'Groq', free: true }])
        setLoading(false)
      })
  }, [])

  return { models, loading }
}
