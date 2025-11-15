"""
Cloud Tasks service for async blog generation.

This service handles enqueueing blog generation jobs to Cloud Tasks,
enabling better autoscaling and cost optimization for long-running tasks.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

try:
    from google.cloud import tasks_v2
    from google.protobuf import duration_pb2
    CLOUD_TASKS_AVAILABLE = True
except ImportError:
    # Cloud Tasks not available - will use in-memory processing
    CLOUD_TASKS_AVAILABLE = False
    tasks_v2 = None
    duration_pb2 = None

logger = logging.getLogger(__name__)


class CloudTasksService:
    """Service for managing Cloud Tasks for blog generation."""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        queue_name: Optional[str] = None
    ):
        """
        Initialize Cloud Tasks service.
        
        Args:
            project_id: GCP project ID (defaults to env var)
            location: GCP location (defaults to env var or 'europe-west1')
            queue_name: Cloud Tasks queue name (defaults to env var or 'blog-generation-queue')
        """
        if not CLOUD_TASKS_AVAILABLE:
            logger.warning("Cloud Tasks library not available. Async processing will use in-memory queue.")
            self.client = None
            return
            
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT_ID")
        self.location = location or os.getenv("GCP_LOCATION", "europe-west1")
        self.queue_name = queue_name or os.getenv("CLOUD_TASKS_QUEUE_NAME", "blog-generation-queue")
        
        if not self.project_id:
            raise ValueError("Project ID must be provided or set in GOOGLE_CLOUD_PROJECT env var")
        
        self.client = tasks_v2.CloudTasksClient()
        self.queue_path = self.client.queue_path(self.project_id, self.location, self.queue_name)
    
    def create_blog_generation_task(
        self,
        request_data: Dict[str, Any],
        worker_url: str,
        schedule_time: Optional[int] = None
    ) -> str:
        """
        Create a Cloud Task for blog generation.
        
        Args:
            request_data: Blog generation request data
            worker_url: URL of the worker service endpoint
            schedule_time: Optional Unix timestamp to schedule the task
            
        Returns:
            Task name/ID
        """
        if not CLOUD_TASKS_AVAILABLE or self.client is None:
            logger.warning("Cloud Tasks not available, returning placeholder task name")
            return "in-memory-task-placeholder"
            
        try:
            # Prepare HTTP request
            http_request = tasks_v2.HttpRequest(
                http_method=tasks_v2.HttpMethod.POST,
                url=worker_url,
                headers={"Content-Type": "application/json"},
                body=json.dumps(request_data).encode()
            )
            
            # Create task
            task = tasks_v2.Task(
                http_request=http_request,
                schedule_time=schedule_time if schedule_time else None
            )
            
            # Create the task
            response = self.client.create_task(
                request={"parent": self.queue_path, "task": task}
            )
            
            logger.info(f"Created Cloud Task: {response.name}")
            return response.name
            
        except Exception as e:
            logger.error(f"Failed to create Cloud Task: {e}")
            raise
    
    def get_task_status(self, task_name: str) -> Dict[str, Any]:
        """
        Get task status (requires Cloud Tasks API v2beta3 or monitoring).
        
        Note: Cloud Tasks doesn't provide direct status API.
        Use Cloud Monitoring or store status in database.
        """
        # This would require Cloud Monitoring integration
        # For now, return task name
        return {"task_name": task_name, "status": "queued"}
    
    def create_queue_if_not_exists(self) -> None:
        """Create Cloud Tasks queue if it doesn't exist."""
        if not CLOUD_TASKS_AVAILABLE or self.client is None:
            logger.warning("Cloud Tasks not available, skipping queue creation")
            return
            
        try:
            queue = tasks_v2.Queue(
                name=self.queue_path,
                rate_limits=tasks_v2.RateLimits(
                    max_dispatches_per_second=100,  # 100 tasks/second
                    max_concurrent_dispatches=500   # 500 concurrent workers
                ),
                retry_config=tasks_v2.RetryConfig(
                    max_attempts=3,
                    max_retry_duration=duration_pb2.Duration(seconds=3600)  # 1 hour
                )
            )
            
            try:
                self.client.create_queue(
                    request={"parent": self.client.common_location_path(self.project_id, self.location), "queue": queue}
                )
                logger.info(f"Created Cloud Tasks queue: {self.queue_name}")
            except Exception as e:
                if "already exists" in str(e).lower():
                    logger.info(f"Queue {self.queue_name} already exists")
                else:
                    raise
                    
        except Exception as e:
            logger.warning(f"Failed to create queue (may already exist): {e}")


# Global instance
_cloud_tasks_service: Optional[CloudTasksService] = None


def get_cloud_tasks_service() -> CloudTasksService:
    """Get or create global Cloud Tasks service instance."""
    global _cloud_tasks_service
    if _cloud_tasks_service is None:
        _cloud_tasks_service = CloudTasksService()
    return _cloud_tasks_service

