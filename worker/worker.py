import os
import sys
import redis
import json
import time

# Connect to Redis
redis_host = os.getenv('REDIS_HOST', '127.0.0.1')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)

QUEUE_NAME = 'analysis'
QUEUE_KEY = f'bull:{QUEUE_NAME}'

"""
Retrieve the next job from the queue.
"""
def get_next_job() -> tuple[str, dict] | None:

    try:
        wait_key = f'{QUEUE_KEY}:wait'
        job_id = redis_client.lpop(wait_key)

        if not job_id:
            return None

        job_key = f'{QUEUE_KEY}:{job_id}'
        job_raw = redis_client.hget(job_key, 'data')

        if not job_raw:
            return None

        job_data = json.loads(job_raw)
        return job_id, job_data
    except Exception as e:
        print(f"Error retrieving next job: {e}", flush=True)
        return None

"""
Mark a job as complete in the queue.
"""
def mark_job_complete(job_id):
    try:
        completed_key = f'{QUEUE_KEY}:completed'
        redis_client.zadd(completed_key, {job_id: time.time()})
        print(f"Job {job_id} marked as complete", flush=True)
    except Exception as e:
        print(f"Error marking job complete: {e}", flush=True)

"""
Mark a job as failed in the queue.
"""
def mark_job_failed(job_id, error):
    try:
        failed_key = f'{QUEUE_KEY}:failed'
        redis_client.zadd(failed_key, {job_id: time.time()})

        job_key = f'{QUEUE_KEY}:{job_id}'
        redis_client.hset(job_key, mapping={'state': 'failed', 'error': error})

        print(f"Job {job_id} marked as failed: {error}", flush=True)
    except Exception as e:
        print(f"Error marking job as failed: {e}", flush=True)

"""
Worker process that continuously polls the Redis queue for new jobs, processes them, and updates their status.
"""
def process_job(job_id, job_data):
    try:
        print(f"[WORKER] Processing job {job_id}", flush=True)
        url = job_data.get('url')
        print(f"[WORKER] Analyzing {url}...", flush=True)

        # TODO: Implement AI analysis logic here
        # For now, just a placeholder that simulates work
        time.sleep(2)  # Simulate work

        print(f"[WORKER] Job {job_id} completed successfully", flush=True)
        return True
    except Exception as e:
        print(f"[WORKER] Error processing job {job_id}: {e}", flush=True)
        raise  # Re-raise to mark job as failed

"""
Main worker loop using Redis client.
"""
def main():
    print("[WORKER] Starting worker with Redis client...", flush=True)

    while True:
        try:
            result = get_next_job()

            if result is None:
                time.sleep(1)
                continue

            job_id, job_data = result
            success = process_job(job_id, job_data)

            if success:
                mark_job_complete(job_id)
            else:
                mark_job_failed(job_id, "Job processing failed")
        except KeyboardInterrupt:
            print("\n[WORKER] Stopping worker...", flush=True)
            break
        except Exception as e:
            print(f"Unexpected error: {e}", flush=True)

if __name__ == '__main__':
    main()
