import DeleteIcon from '@mui/icons-material/Delete'
import { Card, CardContent, Typography, List, ListItem, ListItemText, IconButton, Button } from '@mui/material'
import type { QueueCounts, QueueJobs } from '../types/queue'

type QueueStatusProps = {
  counts: QueueCounts
  jobs: QueueJobs
  onDelete: (id: string) => Promise<void>
  onReset: () => Promise<void>
}

export default function QueueStatus({ counts, jobs, onDelete, onReset }: QueueStatusProps) {
  return (
    <Card sx={{ mt: 4 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom>
          Queue Status
        </Typography>
        <Typography>Active: {counts.active}</Typography>
        <Typography>Waiting: {counts.waiting}</Typography>
        <Typography>Total: {counts.total}</Typography>
        <Typography>Processed: {jobs.processedCount}</Typography>
        <Button variant="outlined" color="secondary" onClick={onReset} sx={{ mt: 1 }}>
          Reset Queue
        </Button>

        <Typography variant="h6" sx={{ mt: 2 }}>
          Active Jobs
        </Typography>
        <List>
          {jobs.active.map((job) => (
            <ListItem
              key={job.id}
              secondaryAction={
                <IconButton edge="end" onClick={() => onDelete(job.id)}>
                  <DeleteIcon />
                </IconButton>
              }
            >
              <ListItemText
                primary={job.url}
                secondary={`ID: ${job.id}, Created: ${new Date(job.createdAt).toLocaleString()}`}
              />
            </ListItem>
          ))}
        </List>

        <Typography variant="h6" sx={{ mt: 2 }}>
          Waiting Jobs
        </Typography>
        <List>
          {jobs.waiting.map((job) => (
            <ListItem
              key={job.id}
              secondaryAction={
                <IconButton edge="end" onClick={() => onDelete(job.id)}>
                  <DeleteIcon />
                </IconButton>
              }
            >
              <ListItemText
                primary={job.url}
                secondary={`ID: ${job.id}, Created: ${new Date(job.createdAt).toLocaleString()}`}
              />
            </ListItem>
          ))}
        </List>
      </CardContent>
    </Card>
  )
}
