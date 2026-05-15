import os
from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import ARRAY, create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/intelligence_db',
)
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


Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def save_record(job_record: AnalysisJob) -> AnalysisJob:
    print(f'[DB] save_record id={job_record.id} url={job_record.url} status={job_record.status}', flush=True)
    try:
        with session_scope() as session:
            persisted = session.merge(job_record)
            session.flush()
            session.refresh(persisted)
            print(f'[DB] Saved successfully id={persisted.id}', flush=True)
            return persisted
    except Exception as e:
        print(f'[DB] save_record FAILED: {e}', flush=True)
        raise