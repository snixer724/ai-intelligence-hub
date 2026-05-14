# AI Project Context

## Overview
This repository implements an AI job queue system using a Node.js backend, a React frontend, Redis for queue state, a Python worker, Postgres database, Langchain used for summarizing urls, and docker for deploying.

## Goal
The goal of the project is for a user to submit a URL, have that URL summarized using AI (for example via LangChain), store the summary, and show the user the result and related information.

## Services
- `api/`: Express API backend in TypeScript
- `client-react/`: Vite-based React frontend
- `worker/`: Python worker that reads jobs from Redis and processes them
- `redis`: Queue store managed by Docker Compose
- `postgres`: Database service in Docker Compose (not directly required by the worker)

## Key Behavior
- Jobs are created by the API and stored in Bull-compatible Redis structures under `bull:analysis:*` keys.
- The worker reads from `bull:analysis:wait`, retrieves job details from `bull:analysis:<jobId>`, processes the job, and marks it complete or failed.
- The API exposes queue endpoints for status, delete, and reset operations.

## Important Files
- `docker-compose.yml`: Defines `worker`, `redis`, and `postgres` services.
- `api/src/routes/analyze.ts`: Adds analysis jobs to the queue.
- `api/src/routes/queue.ts`: Provides queue status and management endpoints.
- `worker/worker.py`: Current worker implementation using Redis client logic.
- `worker/requirements.txt`: Python requirements for the worker.



## Current Worker Logic
- Uses `redis-py` to connect to Redis
- Fetches next job with `lpop` from `bull:analysis:wait`
- Reads job data from the corresponding hash
- Processes the job and writes status to `bull:analysis:completed` or `bull:analysis:failed`

## Notes for AI
- Prefer working with current Redis client logic instead of `bullmq` Python library unless requested.
- Keep explanations focused on queue flow, key files, and Docker service interactions.
- Avoid assuming the worker uses BullMQ if the current code uses Redis directly.
