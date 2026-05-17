export type Job = {
  id: string
  url: string
  createdAt: number
}

export type QueueCounts = {
  active: number
  waiting: number
  failed: number
  total: number
}

export type QueueJobs = {
  active: Job[]
  waiting: Job[]
  processedCount: number
}
