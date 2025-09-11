"""
Batch processing capabilities for the BlogWriter SDK.

Enables efficient processing of multiple blog generation requests
with progress tracking, error handling, and result aggregation.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
from datetime import datetime
import uuid
from dataclasses import dataclass, field
from enum import Enum
import json

from ..models.blog_models import BlogRequest, BlogGenerationResult
from ..core.blog_writer import BlogWriter


logger = logging.getLogger(__name__)


class BatchStatus(str, Enum):
    """Batch processing status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchItem:
    """Individual item in a batch."""
    id: str
    request: BlogRequest
    status: BatchStatus = BatchStatus.PENDING
    result: Optional[BlogGenerationResult] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'request': self.request.model_dump(),
            'status': self.status.value,
            'result': self.result.model_dump() if self.result else None,
            'error': self.error,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class BatchJob:
    """Batch processing job."""
    id: str
    items: List[BatchItem]
    status: BatchStatus = BatchStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    total_items: int = 0
    completed_items: int = 0
    failed_items: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize computed fields."""
        self.total_items = len(self.items)
    
    def update_progress(self):
        """Update progress based on completed items."""
        if self.total_items > 0:
            self.progress = (self.completed_items + self.failed_items) / self.total_items * 100
        else:
            self.progress = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'progress': self.progress,
            'total_items': self.total_items,
            'completed_items': self.completed_items,
            'failed_items': self.failed_items,
            'metadata': self.metadata,
            'items': [item.to_dict() for item in self.items]
        }


class BatchProcessor:
    """
    Batch processor for blog generation requests.
    
    Features:
    - Concurrent processing with configurable limits
    - Progress tracking and status updates
    - Error handling and retry logic
    - Result aggregation and export
    - Real-time progress monitoring
    """
    
    def __init__(
        self,
        blog_writer: BlogWriter,
        max_concurrent: int = 5,
        max_retries: int = 2,
        retry_delay: float = 1.0,
        progress_callback: Optional[Callable[[BatchJob], None]] = None
    ):
        """
        Initialize batch processor.
        
        Args:
            blog_writer: BlogWriter instance for processing
            max_concurrent: Maximum concurrent processing jobs
            max_retries: Maximum retry attempts for failed items
            retry_delay: Delay between retries in seconds
            progress_callback: Optional callback for progress updates
        """
        self.blog_writer = blog_writer
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.progress_callback = progress_callback
        
        # Active jobs tracking
        self.active_jobs: Dict[str, BatchJob] = {}
        self.job_semaphore = asyncio.Semaphore(max_concurrent)
    
    def create_batch_job(
        self,
        requests: List[BlogRequest],
        job_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BatchJob:
        """
        Create a new batch job.
        
        Args:
            requests: List of blog generation requests
            job_id: Optional custom job ID
            metadata: Optional metadata for the job
            
        Returns:
            BatchJob instance
        """
        if not job_id:
            job_id = str(uuid.uuid4())
        
        # Create batch items
        items = []
        for i, request in enumerate(requests):
            item_id = f"{job_id}_{i}"
            items.append(BatchItem(id=item_id, request=request))
        
        # Create batch job
        job = BatchJob(
            id=job_id,
            items=items,
            metadata=metadata or {}
        )
        
        self.active_jobs[job_id] = job
        logger.info(f"Created batch job {job_id} with {len(items)} items")
        
        return job
    
    async def process_batch_item(
        self,
        item: BatchItem,
        job: BatchJob,
        retry_count: int = 0
    ) -> BatchItem:
        """
        Process a single batch item.
        
        Args:
            item: Batch item to process
            job: Parent batch job
            retry_count: Current retry attempt
            
        Returns:
            Updated batch item
        """
        async with self.job_semaphore:
            try:
                item.status = BatchStatus.RUNNING
                item.started_at = datetime.utcnow()
                
                logger.debug(f"Processing batch item {item.id}")
                
                # Generate blog content
                result = await self.blog_writer.generate(item.request)
                
                item.result = result
                item.status = BatchStatus.COMPLETED if result.success else BatchStatus.FAILED
                item.completed_at = datetime.utcnow()
                
                if result.success:
                    job.completed_items += 1
                    logger.debug(f"Batch item {item.id} completed successfully")
                else:
                    job.failed_items += 1
                    item.error = result.error_message
                    logger.warning(f"Batch item {item.id} failed: {result.error_message}")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Error processing batch item {item.id}: {error_msg}")
                
                # Retry logic
                if retry_count < self.max_retries:
                    logger.info(f"Retrying batch item {item.id} (attempt {retry_count + 1})")
                    await asyncio.sleep(self.retry_delay * (retry_count + 1))
                    return await self.process_batch_item(item, job, retry_count + 1)
                
                # Max retries exceeded
                item.status = BatchStatus.FAILED
                item.error = error_msg
                item.completed_at = datetime.utcnow()
                job.failed_items += 1
            
            # Update job progress
            job.update_progress()
            
            # Call progress callback if provided
            if self.progress_callback:
                try:
                    self.progress_callback(job)
                except Exception as e:
                    logger.warning(f"Progress callback error: {e}")
            
            return item
    
    async def process_batch(self, job_id: str) -> BatchJob:
        """
        Process a batch job.
        
        Args:
            job_id: ID of the batch job to process
            
        Returns:
            Completed batch job
        """
        if job_id not in self.active_jobs:
            raise ValueError(f"Batch job {job_id} not found")
        
        job = self.active_jobs[job_id]
        
        try:
            job.status = BatchStatus.RUNNING
            job.started_at = datetime.utcnow()
            
            logger.info(f"Starting batch processing for job {job_id} with {job.total_items} items")
            
            # Process items concurrently
            tasks = []
            for item in job.items:
                task = asyncio.create_task(self.process_batch_item(item, job))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update final status
            job.status = BatchStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.update_progress()
            
            logger.info(
                f"Batch job {job_id} completed: "
                f"{job.completed_items} successful, {job.failed_items} failed"
            )
            
        except Exception as e:
            job.status = BatchStatus.FAILED
            job.completed_at = datetime.utcnow()
            logger.error(f"Batch job {job_id} failed: {e}")
            raise
        
        return job
    
    async def process_batch_stream(self, job_id: str) -> AsyncGenerator[BatchItem, None]:
        """
        Process batch with streaming results.
        
        Args:
            job_id: ID of the batch job to process
            
        Yields:
            Completed batch items as they finish
        """
        if job_id not in self.active_jobs:
            raise ValueError(f"Batch job {job_id} not found")
        
        job = self.active_jobs[job_id]
        job.status = BatchStatus.RUNNING
        job.started_at = datetime.utcnow()
        
        # Create a queue for completed items
        completed_queue = asyncio.Queue()
        
        async def process_and_queue(item: BatchItem):
            """Process item and add to queue."""
            try:
                completed_item = await self.process_batch_item(item, job)
                await completed_queue.put(completed_item)
            except Exception as e:
                logger.error(f"Error processing item {item.id}: {e}")
                item.status = BatchStatus.FAILED
                item.error = str(e)
                await completed_queue.put(item)
        
        # Start processing tasks
        tasks = []
        for item in job.items:
            task = asyncio.create_task(process_and_queue(item))
            tasks.append(task)
        
        # Yield completed items as they finish
        completed_count = 0
        while completed_count < job.total_items:
            try:
                # Wait for next completed item with timeout
                item = await asyncio.wait_for(completed_queue.get(), timeout=30.0)
                completed_count += 1
                yield item
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for batch item completion")
                continue
        
        # Wait for all tasks to finish
        await asyncio.gather(*tasks, return_exceptions=True)
        
        job.status = BatchStatus.COMPLETED
        job.completed_at = datetime.utcnow()
    
    def get_batch_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch job."""
        if job_id not in self.active_jobs:
            return None
        
        job = self.active_jobs[job_id]
        return job.to_dict()
    
    def list_batch_jobs(self) -> List[Dict[str, Any]]:
        """List all batch jobs."""
        return [job.to_dict() for job in self.active_jobs.values()]
    
    def cancel_batch_job(self, job_id: str) -> bool:
        """Cancel a batch job."""
        if job_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[job_id]
        if job.status in [BatchStatus.PENDING, BatchStatus.RUNNING]:
            job.status = BatchStatus.CANCELLED
            job.completed_at = datetime.utcnow()
            logger.info(f"Cancelled batch job {job_id}")
            return True
        
        return False
    
    def delete_batch_job(self, job_id: str) -> bool:
        """Delete a batch job."""
        if job_id in self.active_jobs:
            del self.active_jobs[job_id]
            logger.info(f"Deleted batch job {job_id}")
            return True
        return False
    
    def export_batch_results(
        self,
        job_id: str,
        format: str = "json",
        include_failed: bool = True
    ) -> Optional[str]:
        """
        Export batch results.
        
        Args:
            job_id: Batch job ID
            format: Export format ('json', 'csv')
            include_failed: Whether to include failed items
            
        Returns:
            Exported data as string
        """
        if job_id not in self.active_jobs:
            return None
        
        job = self.active_jobs[job_id]
        
        if format == "json":
            export_data = {
                'job_id': job_id,
                'status': job.status.value,
                'summary': {
                    'total_items': job.total_items,
                    'completed_items': job.completed_items,
                    'failed_items': job.failed_items,
                    'progress': job.progress
                },
                'items': []
            }
            
            for item in job.items:
                if not include_failed and item.status == BatchStatus.FAILED:
                    continue
                export_data['items'].append(item.to_dict())
            
            return json.dumps(export_data, indent=2)
        
        elif format == "csv":
            # Simple CSV export
            lines = ["id,topic,status,word_count,seo_score,error"]
            
            for item in job.items:
                if not include_failed and item.status == BatchStatus.FAILED:
                    continue
                
                word_count = item.result.word_count if item.result else 0
                seo_score = item.result.seo_score if item.result else 0
                error = item.error or ""
                
                lines.append(
                    f"{item.id},{item.request.topic},{item.status.value},"
                    f"{word_count},{seo_score},\"{error}\""
                )
            
            return "\n".join(lines)
        
        return None
    
    def get_batch_statistics(self) -> Dict[str, Any]:
        """Get overall batch processing statistics."""
        total_jobs = len(self.active_jobs)
        running_jobs = sum(1 for job in self.active_jobs.values() if job.status == BatchStatus.RUNNING)
        completed_jobs = sum(1 for job in self.active_jobs.values() if job.status == BatchStatus.COMPLETED)
        failed_jobs = sum(1 for job in self.active_jobs.values() if job.status == BatchStatus.FAILED)
        
        total_items = sum(job.total_items for job in self.active_jobs.values())
        completed_items = sum(job.completed_items for job in self.active_jobs.values())
        failed_items = sum(job.failed_items for job in self.active_jobs.values())
        
        return {
            'jobs': {
                'total': total_jobs,
                'running': running_jobs,
                'completed': completed_jobs,
                'failed': failed_jobs
            },
            'items': {
                'total': total_items,
                'completed': completed_items,
                'failed': failed_items,
                'success_rate': (completed_items / total_items * 100) if total_items > 0 else 0
            },
            'settings': {
                'max_concurrent': self.max_concurrent,
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay
            }
        }
