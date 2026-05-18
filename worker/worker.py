import json
import logging
import time
import uuid
from typing import Any

from db import AnalysisJob, save_record, session_scope
from job_status import JobStatus
from playwright_browser_scraper import scrape_with_browser
from playwright_mcp_scraper import scrape_with_mcp
from redis_client import redis_client

logger = logging.getLogger(__name__)

QUEUE_KEY = 'bull:analysis'


def get_next_job() -> tuple[str, dict] | None:
    """Pulls the next job ID from the wait queue and retrieves its data payload."""
    try:
        job_id = redis_client.lpop(f'{QUEUE_KEY}:wait')
        if not job_id:
            return None

        job_raw = redis_client.hget(f'{QUEUE_KEY}:{job_id}', 'data')
        return (job_id, json.loads(job_raw)) if job_raw else None
    except Exception as e:
        logger.error(f"Error retrieving next job from Redis: {e}")
        return None


def _update_job_state(job_record: AnalysisJob, status: JobStatus) -> None:
    """Helper to safely merge and update the DB status across transaction scopes."""
    with session_scope() as session:
        merged = session.merge(job_record)
        merged.status = status.name
        session.flush()
        session.refresh(merged)


def mark_job_complete(job_id: str, job_record: AnalysisJob) -> None:
    """Finalizes successful job tracking in both Redis and the primary database."""
    try:
        redis_client.zadd(f'{QUEUE_KEY}:completed', {job_id: time.time()})
        _update_job_state(job_record, JobStatus.COMPLETED)
        logger.info(f"Job {job_id} successfully marked as complete.")
    except Exception as e:
        logger.error(f"Error marking job {job_id} complete: {e}")


def mark_job_failed(job_id: str, job_record: AnalysisJob, error: str) -> None:
    """Tracks pipeline failure processing states across cache and persistence layers."""
    try:
        redis_client.zadd(f'{QUEUE_KEY}:failed', {job_id: time.time()})
        redis_client.hset(f'{QUEUE_KEY}:{job_id}', mapping={'state': 'failed', 'error': error})
        _update_job_state(job_record, JobStatus.FAILED)
        logger.warning(f"Job {job_id} marked as failed. Reason: {error}")
    except Exception as e:
        logger.error(f"Error marking job {job_id} as failed: {e}")


def execute_scrapers(url: str, db_job_id: str) -> bool:
    """Executes the dual browser and MCP collection layers for the target URL."""
    try:
        logger.info(f"Calling scraper routines for {url}")
        page_title = scrape_with_browser(url)
        llm_summary = scrape_with_mcp(url)

        if page_title:
            logger.info(f"Playwright check passed for Job {db_job_id}. Title: {page_title}")
        else:
            logger.warning(f"Playwright check returned empty for Job {db_job_id}")
            
        if llm_summary:
            logger.info(f"LLM summary successfully generated for Job {db_job_id}. Summary: {llm_summary[:1500]}...")
        else:
            logger.warning(f"Failed to generate LLM summary loop context for Job {db_job_id}")
            
        return True
    except Exception as e:
        logger.error(f"Critical error triggered during scraper execution for Job {db_job_id}: {e}")
        return False


def process_job(redis_job_id: str, job_data: dict[str, Any]) -> tuple[bool, AnalysisJob | None]:
    """
    Orchestrates database lifecycle setup and triggers the extraction pipeline.
    Returns a tuple indicating overall success and the updated job record for finalization steps.
    """
    logger.info(f"Processing job from Redis queue: {redis_job_id}")

    url = job_data.get('url')
    if not url:
        raise ValueError('Job data missing required url')

    # Initialize tracking entity
    job_id_uuid = str(uuid.uuid4())
    job_record = AnalysisJob(id=job_id_uuid, url=url, status=JobStatus.PROCESSING.name)
    job_record = save_record(job_record)
    logger.info(f"Saved DB AnalysisJob record with UUID: {job_id_uuid} for URL: {url}")

    success = execute_scrapers(url, job_id_uuid)
    return success, job_record


def run_worker() -> None:
    """
    Continuous polling loop processing incoming tasks from the message queue.
    Designed to run indefinitely until a graceful shutdown signal is received.
    """
    logger.info("Worker process has verified connection state and is now listening for jobs...")
    
    while True:
        try:
            job_payload = get_next_job()
            if not job_payload:
                time.sleep(1)
                continue

            job_id, job_data = job_payload
            success, job_record = process_job(job_id, job_data)

            if success:
                mark_job_complete(job_id, job_record)
            else:
                mark_job_failed(job_id, job_record, 'Job processing failed during scraping steps')
                
        except KeyboardInterrupt:
            logger.info("Graceful shutdown signal caught. Winding down worker...")
            break
        except Exception:
            logger.exception("Queue pipeline loop encountered an unexpected runtime failure")