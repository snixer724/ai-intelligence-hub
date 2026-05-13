import { useState } from 'react'
import { Container, Typography, Box, TextField, Button } from '@mui/material'

function App() {
    const [url, setUrl] = useState('')
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState('')

    const handleSubmit = async (e: React.SubmitEvent) => {
        e.preventDefault() // prevents browser from reloading on form submission
        if (!url.trim()) return // basic check to prevent empty submissions

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
            <Typography variant="body1" gutterBottom>
                Enter a URL to analyze its content and extract insights using our AI-powered tools.
            </Typography>

            <Box
                component="form"
                onSubmit={handleSubmit}
                sx={{ '& > :not(style)': { m: 1, width: '25ch' } }}
                noValidate
                autoComplete="off"
            >
                <TextField
                    id="url-input"
                    label="Enter URL"
                    variant="standard"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    required
                />
                <Button
                    type="submit"
                    variant="contained"
                    disabled={loading || !url.trim()}
                >
                    {loading ? 'Submitting...' : 'Analyze'}
                </Button>
            </Box>

            {message && (
                <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                    {message}
                </Typography>
            )}
        </Container>
    )
}

export default App