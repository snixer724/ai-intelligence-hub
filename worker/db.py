import os
import logging
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import ARRAY, create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# Initialize module-level database logger
logger = logging.getLogger("database")

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/intelligence_db',
)

logger.info("Initializing SQLAlchemy database connection engine pool.")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AnalysisJob(Base):
    __tablename__ = 'AnalysisJob'

    id = Column(String, primary_key=True)
    url = Column(String, nullable=False)
    status = Column(String, default='PENDING')
    summary = Column(Text, nullable=True)
    keywords = Column(ARRAY(String), default=list)
    created_at = Column(
        'createdAt',
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        'updatedAt',
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


logger.info("Synchronizing data models with database schema definitions.")
Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.warning(f"Transaction failed. Rolling back active database session state: {e}")
        session.rollback()
        raise
    finally:
        logger.debug("Releasing transactional session pool assets back to engine.")
        session.close()


def save_record(job_record: AnalysisJob) -> AnalysisJob:
    logger.info(f"Upserting transactional entity entry: id={job_record.id} status={job_record.status}")
    try:
        with session_scope() as session:
            persisted = session.merge(job_record)
            session.flush()
            session.refresh(persisted)
            logger.info(f"Successfully committed database row changes: id={persisted.id}")
            return persisted
    except Exception as e:
        logger.error(f"Persist worker block aborted unexpectedly for job record '{job_record.id}': {e}", exc_info=True)
        raise