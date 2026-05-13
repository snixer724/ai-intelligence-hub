import express from 'express';
import dotenv from 'dotenv';
import analyzeRouter from './routes/analyze.js';
import queueRouter from './routes/queue.js';

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

// Seting up middleware to parse JSON bodies in requests. This is necessary to access req.body in our route handlers.
app.use(express.json());

// Use the route file: This makes your endpoint http://localhost:3000/api/analyze
app.use('/api/analyze', analyzeRouter);

// Use the queue routes: http://localhost:3000/api/queue
app.use('/api/queue', queueRouter);

// Start the server and listen on the specified port. The callback function logs a message to the console when the server is up and running.
app.listen(port, () => {
    console.log(`API Gateway listening at http://localhost:${port}`);
});