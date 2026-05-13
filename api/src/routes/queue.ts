import { Router, type Request, type Response } from 'express';
import { analysisQueue } from '../queue.js';

const router = Router();

/**
 * Endpoint to get the current status of the analysis queue, including counts of active and waiting jobs,
 * as well as details of each job.
 * @route GET /api/queue/status
 * @returns {object} 200 - Queue status with counts and job details
 * @returns {object} 500 - Internal server error
 */
router.get('/status', async (req: Request, res: Response) => {
    try {
        const activeJobs = await analysisQueue.getActive();
        const waitingJobs = await analysisQueue.getWaiting();
        const completedCount = await analysisQueue.getCompletedCount();
        const failedCount = await analysisQueue.getFailedCount();
        const processedCount = completedCount + failedCount;

        const activeCount = activeJobs.length;
        const waitingCount = waitingJobs.length;
        const total = activeCount + waitingCount;

        const active = activeJobs.map(job => ({
            id: job.id,
            url: job.data.url,
            createdAt: job.opts.timestamp
        }));

        const waiting = waitingJobs.map(job => ({
            id: job.id,
            url: job.data.url,
            createdAt: job.opts.timestamp
        }));

        res.json({ 
            counts: { active: activeCount, waiting: waitingCount, total },
            jobs: { active, waiting, processedCount }
        });
    } catch (error) {
        res.status(500).json({ message: 'Error fetching queue status' });
    }
});

/**
 * Endpoint to reset the analysis queue, removing all jobs.
 * @route DELETE /api/queue/reset
 * @returns {object} 200 - Queue reset successfully
 * @returns {object} 500 - Internal server error
 */
router.delete('/reset', async (req: Request, res: Response) => {
    try {
        await analysisQueue.obliterate({ force: true });
        res.json({ message: 'Queue reset successfully' });
    } catch (error) {
        res.status(500).json({ message: 'Error resetting queue' });
    }
});

/**
 * Endpoint to delete a specific job from the analysis queue by its ID. This allows for manual removal of jobs 
 * that may be stuck or no longer needed.
 * @route DELETE /api/queue/jobs/:id
 * @param {string} id - The ID of the job to be deleted, provided as a URL parameter.
 */
router.delete('/jobs/:id', async (req: Request, res: Response) => {
    try {
        const { id } = req.params;
        if (!id || typeof id !== 'string') {
            return res.status(400).json({ message: 'Valid job ID required' });
        }
        await analysisQueue.remove(id);
        res.status(204).send(); // No content
    } catch (error) {
        res.status(500).json({ message: 'Error deleting job' });
    }
});

export default router;