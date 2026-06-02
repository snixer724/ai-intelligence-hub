import type { SyntheticEvent } from 'react'
import { Box, TextField, Button, Typography } from '@mui/material'

type AnalyzeFormProps = {
  url: string
  setUrl: (value: string) => void
  loading: boolean
  onSubmit: (e: SyntheticEvent<HTMLFormElement>) => Promise<void>
  message: string
}

export default function AnalyzeForm({ url, setUrl, loading, onSubmit, message}: AnalyzeFormProps) {
  return (
    <>
      <Typography variant="body1" gutterBottom>
        Enter a URL to analyze its content and extract insights using our AI-powered tools.
      </Typography>

      <Box
        component="form"
        onSubmit={onSubmit}
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
        <Button type="submit" variant="contained" disabled={loading || !url.trim()}>
          {loading ? 'Submitting...' : 'Analyze'}
        </Button>
      </Box>

      {message && (
        <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
          {message}
        </Typography>
      )}
    </>
  )
}
