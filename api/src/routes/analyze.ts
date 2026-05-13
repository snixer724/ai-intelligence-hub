import { Router, type Request, type Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { analysisQueue } from '../queue.js';

const router = Router();
// const prisma = new PrismaClient();

router.post('/', async (req: Request, res: Response) => {
    const { url } = req.body;

    if (!url) {
        return res.status(400).json({ message: 'URL is required' });
    }

    if (!isValidUrl(url)) {
        return res.status(400).json({ message: 'Invalid URL format' });
    }

    // Add the analysis job to the queue
    await analysisQueue.add('analyze', { 
        url, 
        removeOnComplete: {
            age: 3600, // Keep completed jobs for 1 hour
            count: 1000, // Or keep the last 1000 jobs
        },
        removeOnFail: {
            age: 86400, // Keep failed jobs for 24 hours for debugging
        }
    });

    return res.status(202).json({ message: 'Analysis queued' });
});

// Simple check for valid URL format. This can be enhanced with more specific checks if needed.
const isValidUrl = (urlString: string): boolean => {
    try {
        const url = new URL(urlString);
        if (!['http:', 'https:'].includes(url.protocol)) {
            return false;
        }
        return true;
    } catch (error) {
        return false;
    }
};

export default router;
