import { Router, type Request, type Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { analysisQueue } from '../queue.js';

const router = Router();
// const prisma = new PrismaClient();

router.post('/', async (req: Request, res: Response) => {
    const { url } = req.body;

    // Add the analysis job to the queue
    // await analysisQueue.add('analyze', { url });

    return res.status(202).json({ message: 'Analysis queued' });
});

export default router;
