import { useState, useEffect, type FormEvent } from 'react'
import { Container, Typography } from '@mui/material'
import AnalyzeForm from './components/AnalyzeForm'
import QueueStatus from './components/QueueStatus'
import type { QueueCounts, QueueJobs } from './types/queue'

function App() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [queueCounts, setQueueCounts] = useState<QueueCounts>({ active: 0, waiting: 0, total: 0 })
  const [queueJobs, setQueueJobs] = useState<QueueJobs>({ active: [], waiting: [], processedCount: 0 })

  const fetchQueueData = async () => {
    try {
      const res = await fetch('/api/queue/status')
      const data = await res.json()
      setQueueCounts(data.counts)
      setQueueJobs(data.jobs)
    } catch (error) {
      console.error('Failed to fetch queue data', error)
    }
  }

  useEffect(() => {
    fetchQueueData()
  }, [])

  const handleDelete = async (id: string) => {
    try {
      await fetch(`/api/queue/jobs/${id}`, { method: 'DELETE' })
      fetchQueueData()
    } catch (error) {
      console.error('Failed to delete job', error)
    }
  }

  const handleReset = async () => {
    if (window.confirm('Are you sure you want to reset the entire queue? This will delete all jobs.')) {
      try {
        await fetch('/api/queue/reset', { method: 'DELETE' })
        fetchQueueData()
      } catch (error) {
        console.error('Failed to reset queue', error)
      }
    }
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!url.trim()) return

    setLoading(true)
    setMessage('')

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      })

      const data = await response.json()

      if (response.ok) {
        setMessage(data.message || 'Analysis queued successfully!')
        setUrl('')
        fetchQueueData()
      } else {
        setMessage(data.message || 'Failed to queue analysis.')
      }
    } catch (error) {
      setMessage('Error: Could not connect to server.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxWidth="sm" sx={{ py: 6 }}>
      <Typography variant="h3" component="h1" gutterBottom>
        AI Intelligence Hub
      </Typography>

      <AnalyzeForm url={url} setUrl={setUrl} loading={loading} onSubmit={handleSubmit} message={message}/>
      <QueueStatus counts={queueCounts} jobs={queueJobs} onDelete={handleDelete} onReset={handleReset} />
    </Container>
  )
}

export default App