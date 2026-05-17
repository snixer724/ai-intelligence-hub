import json
import time
import traceback
import uuid
from scraper import get_url_title

from typing import Any

from db import AnalysisJob, save_record, session_scope
from redis_client import redis_client
from job_status import JobStatus

QUEUE_KEY = 'bull:analysis'


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

        return job_id, json.loads(job_raw)
    except Exception as e:
        print(f'Error retrieving next job: {e}', flush=True)
        return None


def create_analysis_job(url: str) -> AnalysisJob:
    return AnalysisJob(
        id=str(uuid.uuid4()),
        url=url,
        status=JobStatus.PROCESSING.name,
    )


def mark_job_complete(job_id: str, job_record: AnalysisJob) -> None:
    try:
        completed_key = f'{QUEUE_KEY}:completed'
        redis_client.zadd(completed_key, {job_id: time.time()})

        with session_scope() as session:
            merged = session.merge(job_record)
            merged.status = JobStatus.COMPLETED.name
            session.flush()
            session.refresh(merged)

        print(f'Job {job_id} marked as complete', flush=True)
    except Exception as e:
        print(f'Error marking job complete: {e}', flush=True)


def mark_job_failed(job_id: str, job_record: AnalysisJob, error: str) -> None:
    try:
        failed_key = f'{QUEUE_KEY}:failed'
        redis_client.zadd(failed_key, {job_id: time.time()})
        job_key = f'{QUEUE_KEY}:{job_id}'
        redis_client.hset(job_key, mapping={'state': 'failed', 'error': error})

        with session_scope() as session:
            merged = session.merge(job_record)
            merged.status = JobStatus.FAILED.name
            session.flush()
            session.refresh(merged)

        print(f'Job {job_id} marked as failed: {error}', flush=True)
    except Exception as e:
        print(f'Error marking job as failed: {e}', flush=True)


def process_job(job_id: str, job_data: dict[str, Any]) -> tuple[bool, AnalysisJob | None]:
    print(f'[WORKER] Processing job {job_id}', flush=True)

    url = job_data.get('url')
    if not url:
        raise ValueError('Job data missing required url')

    print(f'[WORKER] Analyzing {url}...', flush=True)
    job_record = create_analysis_job(url)
    job_id = job_record.id  # Save before session closes
    job_record = save_record(job_record)
    print(f'[WORKER] Saved AnalysisJob {job_id} to DB', flush=True)

    # --- CALL THE EXTERNAL SCRAPER FILE ---
    try:
        # Call the synchronous wrapper from scraper.py
        print(f'[WORKER] Calling scraper for {url}', flush=True)
        page_title = get_url_title(url)
        
        if page_title:
            print(f'[WORKER] Playwright check passed for Job {job_id}', flush=True)
            # job_record.title = page_title
            # save_record(job_record)
        else:
            print(f'[WORKER] Playwright check failed or returned empty for Job {job_id}', flush=True)
            
    except Exception as e:
        print(f'[WORKER ERROR] Failed during scraper execution: {e}', flush=True)

    print(f'[WORKER] Job {job_id} completed successfully', flush=True)
    return True, job_record


def main() -> None:
    print('[WORKER] Starting worker...', flush=True)

    while True:
        try:
            result = get_next_job()
            if result is None:
                time.sleep(1)
                continue

            job_id, job_data = result
            success, job_record = process_job(job_id, job_data)

            if success:
                mark_job_complete(job_id, job_record)
            else:
                mark_job_failed(job_id, job_record, 'Job processing failed')
        except KeyboardInterrupt:
            print('\n[WORKER] Stopping worker...', flush=True)
            break
        except Exception as e:
            print(f'[WORKER] Unexpected error:\n{traceback.format_exc()}', flush=True)


if __name__ == '__main__':
    main()
