import express from 'express';
import dotenv from 'dotenv';
import analyzeRouter from './routes/analyze.js';

dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

// Seting up middleware to parse JSON bodies in requests. This is necessary to access req.body in our route handlers.
app.use(express.json());

// Use the route file: This makes your endpoint http://localhost:3000/analyze
app.use('/analyze', analyzeRouter);

// Start the server and listen on the specified port. The callback function logs a message to the console when the server is up and running.
app.listen(port, () => {
    console.log(`API Gateway listening at http://localhost:${port}`);
});