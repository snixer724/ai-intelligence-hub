import { Queue } from 'bullmq';

// Using 127.0.0.1 because localhost can resolve to both IPv4 and IPv6 addresses
// which can cause connection issues with Redis.
// The port comes from the docker-compose.yml file where we expose Redis on port 6379.
export const analysisQueue = new Queue('analysis', {
    connection: {
        host: '127.0.0.1',
        port: 6379,
    },
});