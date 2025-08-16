"""
Database module with PostgreSQL, SQLAlchemy async, and Redis support.
"""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

import redis.asyncio as redis
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, JSON, 
    Boolean, ForeignKey, Index, create_engine
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, selectinload
from sqlalchemy.sql import select, update, delete, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from config.config import get_settings
from backend.models.models import JobStatus, ProjectType, ComplexityLevel, AgentType


settings = get_settings()
Base = declarative_base()


# SQLAlchemy Models
class JobModel(Base):
    """SQLAlchemy model for jobs."""
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    project_type = Column(String(50), nullable=False)
    languages = Column(JSON, nullable=False, default=list)
    frameworks = Column(JSON, nullable=False, default=list)
    complexity = Column(String(50), nullable=False)
    features = Column(JSON, nullable=False, default=list)
    mode = Column(String(20), nullable=False, default="full")
    status = Column(String(20), nullable=False, default=JobStatus.PENDING)
    progress = Column(Float, nullable=False, default=0.0)
    current_step = Column(String(200), nullable=False, default="Initializing")
    step_number = Column(Integer, nullable=False, default=0)
    total_steps = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)
    estimated_duration = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    files = relationship("FileModel", back_populates="job", cascade="all, delete-orphan")
    logs = relationship("LogModel", back_populates="job", cascade="all, delete-orphan")
    tasks = relationship("TaskModel", back_populates="job", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_jobs_job_id", "job_id"),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_created_at", "created_at"),
    )


class FileModel(Base):
    """SQLAlchemy model for project files."""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False)
    filename = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    size = Column(Integer, nullable=False)
    hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job = relationship("JobModel", back_populates="files")
    
    # Indexes
    __table_args__ = (
        Index("idx_files_job_id", "job_id"),
        Index("idx_files_path", "path"),
        Index("idx_files_hash", "hash"),
    )


class LogModel(Base):
    """SQLAlchemy model for logs."""
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False)
    agent = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False, default="INFO")
    message = Column(Text, nullable=False)
    log_metadata = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    job = relationship("JobModel", back_populates="logs")
    
    # Indexes
    __table_args__ = (
        Index("idx_logs_job_id", "job_id"),
        Index("idx_logs_timestamp", "timestamp"),
    )


class TaskModel(Base):
    """SQLAlchemy model for agent tasks."""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(36), unique=True, index=True, nullable=False)
    job_id = Column(String(36), ForeignKey("jobs.job_id"), nullable=False)
    agent_type = Column(String(50), nullable=False)
    task_name = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default=JobStatus.PENDING)
    input_data = Column(JSON, nullable=False, default=dict)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    job = relationship("JobModel", back_populates="tasks")
    
    # Indexes
    __table_args__ = (
        Index("idx_tasks_job_id", "job_id"),
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_agent_type", "agent_type"),
    )


class StatsModel(Base):
    """SQLAlchemy model for system statistics."""
    __tablename__ = "stats"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_stats_metric_name", "metric_name"),
        Index("idx_stats_timestamp", "timestamp"),
    )


# Database Manager
class DatabaseManager:
    """Async database manager with PostgreSQL and Redis support."""
    
    def __init__(self):
        self.engine = None
        self.session_factory = None
        self.redis_client = None
        
    async def initialize(self):
        """Initialize database connections."""
        # PostgreSQL connection
        self.engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            pool_size=20,
            max_overflow=40,
            pool_timeout=30,
            pool_recycle=3600,
        )
        
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Redis connection
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            # Test Redis connection
            await self.redis_client.ping()
        except Exception as e:
            print(f"Warning: Redis connection failed: {e}")
            self.redis_client = None
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
        if self.redis_client:
            await self.redis_client.close()
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    # Cache methods
    async def get_cache(self, key: str) -> Optional[str]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        try:
            return await self.redis_client.get(key)
        except Exception:
            return None
    
    async def set_cache(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value in cache."""
        if not self.redis_client:
            return False
        try:
            ttl = ttl or settings.cache_ttl
            await self.redis_client.setex(key, ttl, value)
            return True
        except Exception:
            return False
    
    async def delete_cache(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.delete(key)
            return True
        except Exception:
            return False
    
    # Job methods
    async def create_job(
        self,
        job_id: str,
        name: str,
        description: str,
        project_type: ProjectType,
        languages: List[str],
        frameworks: List[str],
        complexity: ComplexityLevel,
        features: List[str],
        mode: str = "full"
    ) -> JobModel:
        """Create a new job."""
        async with self.get_session() as session:
            job = JobModel(
                job_id=job_id,
                name=name,
                description=description,
                project_type=project_type,
                languages=languages,
                frameworks=frameworks,
                complexity=complexity,
                features=features,
                mode=mode
            )
            session.add(job)
            await session.flush()
            return job
    
    async def get_job(self, job_id: str) -> Optional[JobModel]:
        """Get job by ID."""
        # Try cache first
        cache_key = f"job:{job_id}"
        cached = await self.get_cache(cache_key)
        if cached:
            return JobModel(**json.loads(cached))
        
        async with self.get_session() as session:
            result = await session.execute(
                select(JobModel).where(JobModel.job_id == job_id)
            )
            job = result.scalar_one_or_none()
            
            if job:
                # Cache the result
                job_dict = {
                    "job_id": job.job_id,
                    "name": job.name,
                    "status": job.status,
                    "progress": job.progress,
                    "current_step": job.current_step,
                    "step_number": job.step_number,
                    "total_steps": job.total_steps,
                    "created_at": job.created_at.isoformat(),
                    "updated_at": job.updated_at.isoformat(),
                }
                await self.set_cache(cache_key, json.dumps(job_dict, default=str))
            
            return job
    
    async def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        progress: float = None,
        current_step: str = None,
        step_number: int = None,
        error_message: str = None
    ) -> bool:
        """Update job status."""
        async with self.get_session() as session:
            values = {"status": status, "updated_at": datetime.utcnow()}
            
            if progress is not None:
                values["progress"] = progress
            if current_step is not None:
                values["current_step"] = current_step
            if step_number is not None:
                values["step_number"] = step_number
            if error_message is not None:
                values["error_message"] = error_message
            if status == JobStatus.COMPLETED:
                values["completed_at"] = datetime.utcnow()
            
            result = await session.execute(
                update(JobModel).where(JobModel.job_id == job_id).values(values)
            )
            
            # Invalidate cache
            await self.delete_cache(f"job:{job_id}")
            
            return result.rowcount > 0
    
    async def get_jobs(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[JobStatus] = None
    ) -> List[JobModel]:
        """Get jobs with pagination."""
        async with self.get_session() as session:
            query = select(JobModel).order_by(JobModel.created_at.desc())
            
            if status:
                query = query.where(JobModel.status == status)
            
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()
    
    # File methods
    async def create_file(
        self,
        job_id: str,
        filename: str,
        path: str,
        content: str,
        language: str
    ) -> FileModel:
        """Create a project file."""
        size = len(content.encode('utf-8'))
        file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        async with self.get_session() as session:
            file_model = FileModel(
                job_id=job_id,
                filename=filename,
                path=path,
                content=content,
                language=language,
                size=size,
                hash=file_hash
            )
            session.add(file_model)
            await session.flush()
            return file_model
    
    async def get_files(self, job_id: str) -> List[FileModel]:
        """Get all files for a job."""
        async with self.get_session() as session:
            result = await session.execute(
                select(FileModel).where(FileModel.job_id == job_id).order_by(FileModel.path)
            )
            return result.scalars().all()
    
    async def get_file(self, job_id: str, filename: str) -> Optional[FileModel]:
        """Get a specific file."""
        async with self.get_session() as session:
            result = await session.execute(
                select(FileModel).where(
                    FileModel.job_id == job_id,
                    FileModel.filename == filename
                )
            )
            return result.scalar_one_or_none()
    
    # Log methods
    async def create_log(
        self,
        job_id: str,
        agent: str,
        message: str,
        level: str = "INFO",
        metadata: Dict[str, Any] = None
    ) -> LogModel:
        """Create a log entry."""
        async with self.get_session() as session:
            log = LogModel(
                job_id=job_id,
                agent=agent,
                message=message,
                level=level,
                metadata=metadata or {}
            )
            session.add(log)
            await session.flush()
            return log
    
    async def get_logs(
        self,
        job_id: str,
        limit: int = 100,
        level: Optional[str] = None
    ) -> List[LogModel]:
        """Get logs for a job."""
        async with self.get_session() as session:
            query = select(LogModel).where(LogModel.job_id == job_id)
            
            if level:
                query = query.where(LogModel.level == level)
            
            query = query.order_by(LogModel.timestamp.desc()).limit(limit)
            result = await session.execute(query)
            return result.scalars().all()
    
    # Task methods
    async def create_task(
        self,
        task_id: str,
        job_id: str,
        agent_type: AgentType,
        task_name: str,
        input_data: Dict[str, Any]
    ) -> TaskModel:
        """Create an agent task."""
        async with self.get_session() as session:
            task = TaskModel(
                task_id=task_id,
                job_id=job_id,
                agent_type=agent_type,
                task_name=task_name,
                input_data=input_data
            )
            session.add(task)
            await session.flush()
            return task
    
    async def update_task_status(
        self,
        task_id: str,
        status: JobStatus,
        output_data: Dict[str, Any] = None,
        error_message: str = None
    ) -> bool:
        """Update task status."""
        async with self.get_session() as session:
            values = {"status": status}
            
            if status == JobStatus.RUNNING and not output_data:
                values["started_at"] = datetime.utcnow()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                values["completed_at"] = datetime.utcnow()
            
            if output_data is not None:
                values["output_data"] = output_data
            if error_message is not None:
                values["error_message"] = error_message
            
            result = await session.execute(
                update(TaskModel).where(TaskModel.task_id == task_id).values(values)
            )
            
            return result.rowcount > 0
    
    async def get_tasks(self, job_id: str) -> List[TaskModel]:
        """Get all tasks for a job."""
        async with self.get_session() as session:
            result = await session.execute(
                select(TaskModel).where(TaskModel.job_id == job_id).order_by(TaskModel.created_at)
            )
            return result.scalars().all()
    
    # Stats methods
    async def save_stat(self, metric_name: str, metric_value: float):
        """Save a system metric."""
        async with self.get_session() as session:
            stat = StatsModel(
                metric_name=metric_name,
                metric_value=metric_value
            )
            session.add(stat)
    
    async def get_stats(
        self,
        metric_name: str,
        hours: int = 24
    ) -> List[StatsModel]:
        """Get statistics for a metric."""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        async with self.get_session() as session:
            result = await session.execute(
                select(StatsModel).where(
                    StatsModel.metric_name == metric_name,
                    StatsModel.timestamp >= since
                ).order_by(StatsModel.timestamp)
            )
            return result.scalars().all()
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        async with self.get_session() as session:
            # Active jobs count
            active_jobs = await session.execute(
                select(func.count(JobModel.id)).where(
                    JobModel.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
                )
            )
            
            # Total jobs count
            total_jobs = await session.execute(select(func.count(JobModel.id)))
            
            # Average completion time
            avg_time = await session.execute(
                select(func.avg(
                    func.extract('epoch', JobModel.completed_at - JobModel.created_at)
                )).where(
                    JobModel.status == JobStatus.COMPLETED,
                    JobModel.completed_at.is_not(None)
                )
            )
            
            return {
                "active_jobs": active_jobs.scalar() or 0,
                "total_jobs": total_jobs.scalar() or 0,
                "avg_completion_time": avg_time.scalar() or 0,
            }
    
    async def get_job_count(self) -> int:
        """Get total number of jobs."""
        async with self.get_session() as session:
            result = await session.execute(select(func.count(JobModel.id)))
            return result.scalar() or 0
    
    async def get_completed_job_count(self) -> int:
        """Get number of completed jobs."""
        async with self.get_session() as session:
            result = await session.execute(
                select(func.count(JobModel.id)).where(JobModel.status == JobStatus.COMPLETED)
            )
            return result.scalar() or 0
    
    async def get_failed_job_count(self) -> int:
        """Get number of failed jobs."""
        async with self.get_session() as session:
            result = await session.execute(
                select(func.count(JobModel.id)).where(JobModel.status == JobStatus.FAILED)
            )
            return result.scalar() or 0


# Global database manager instance
db_manager = DatabaseManager()