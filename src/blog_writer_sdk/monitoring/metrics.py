"""
Comprehensive monitoring and metrics collection for BlogWriter SDK.

Provides detailed metrics, performance monitoring, and health checks.
"""

import time
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
import json
import psutil
import sys

from ..models.blog_models import BlogGenerationResult


logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""
    operation: str
    duration: float
    success: bool
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """
    Comprehensive metrics collector for the BlogWriter SDK.
    
    Collects and aggregates:
    - Request metrics (count, duration, success rate)
    - System metrics (CPU, memory, disk)
    - Business metrics (blogs generated, SEO scores, etc.)
    - Error metrics (error rates, types)
    - Cache metrics (hit rate, size)
    """
    
    def __init__(self, retention_hours: int = 24):
        """
        Initialize metrics collector.
        
        Args:
            retention_hours: How long to retain metrics in memory
        """
        self.retention_hours = retention_hours
        self.retention_seconds = retention_hours * 3600
        
        # Metrics storage
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[MetricPoint]] = defaultdict(list)
        self.performance_metrics: deque = deque()
        
        # Request tracking
        self.request_counts = defaultdict(int)
        self.request_durations = defaultdict(list)
        self.error_counts = defaultdict(int)
        
        # Business metrics
        self.blog_generation_stats = {
            'total_generated': 0,
            'total_words': 0,
            'avg_seo_score': 0.0,
            'avg_readability_score': 0.0,
            'success_rate': 0.0,
            'avg_generation_time': 0.0
        }
        
        # System metrics
        self.system_metrics = {}
        
        # Start background cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task to clean up old metrics."""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(300)  # Clean up every 5 minutes
                    self._cleanup_old_metrics()
                except Exception as e:
                    logger.error(f"Metrics cleanup error: {e}")
        
        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(cleanup_loop())
        except RuntimeError:
            # No event loop running, cleanup will happen manually
            pass
    
    def _cleanup_old_metrics(self):
        """Remove old metrics beyond retention period."""
        cutoff_time = time.time() - self.retention_seconds
        
        # Clean histograms
        for metric_name in self.histograms:
            self.histograms[metric_name] = [
                point for point in self.histograms[metric_name]
                if point.timestamp > cutoff_time
            ]
        
        # Clean performance metrics
        while self.performance_metrics and self.performance_metrics[0].timestamp < cutoff_time:
            self.performance_metrics.popleft()
        
        # Clean request durations
        for endpoint in self.request_durations:
            self.request_durations[endpoint] = [
                duration for duration in self.request_durations[endpoint]
                if duration > cutoff_time
            ]
    
    def increment_counter(self, name: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        key = name
        if labels:
            key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric."""
        key = name
        if labels:
            key = f"{name}:{json.dumps(labels, sort_keys=True)}"
        self.gauges[key] = value
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram value."""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {}
        )
        self.histograms[name].append(point)
    
    def record_request(self, endpoint: str, method: str, duration: float, status_code: int):
        """Record API request metrics."""
        # Count requests
        self.increment_counter('http_requests_total', labels={
            'endpoint': endpoint,
            'method': method,
            'status': str(status_code)
        })
        
        # Record duration
        self.record_histogram('http_request_duration_seconds', duration, labels={
            'endpoint': endpoint,
            'method': method
        })
        
        # Track errors
        if status_code >= 400:
            self.increment_counter('http_errors_total', labels={
                'endpoint': endpoint,
                'status': str(status_code)
            })
    
    def record_blog_generation(self, result: BlogGenerationResult, duration: float):
        """Record blog generation metrics."""
        self.blog_generation_stats['total_generated'] += 1
        
        if result.success and result.blog_post:
            self.blog_generation_stats['total_words'] += result.word_count or 0
            
            # Update averages
            total = self.blog_generation_stats['total_generated']
            
            if result.seo_score is not None:
                current_avg = self.blog_generation_stats['avg_seo_score']
                self.blog_generation_stats['avg_seo_score'] = (
                    (current_avg * (total - 1) + result.seo_score) / total
                )
            
            if result.readability_score is not None:
                current_avg = self.blog_generation_stats['avg_readability_score']
                self.blog_generation_stats['avg_readability_score'] = (
                    (current_avg * (total - 1) + result.readability_score) / total
                )
            
            current_avg = self.blog_generation_stats['avg_generation_time']
            self.blog_generation_stats['avg_generation_time'] = (
                (current_avg * (total - 1) + duration) / total
            )
        
        # Calculate success rate
        success_count = sum(1 for _ in range(total) if result.success)  # Simplified
        self.blog_generation_stats['success_rate'] = success_count / total if total > 0 else 0
        
        # Record individual metrics
        self.record_histogram('blog_generation_duration_seconds', duration)
        self.increment_counter('blog_generations_total', labels={
            'success': str(result.success)
        })
        
        if result.word_count:
            self.record_histogram('blog_word_count', result.word_count)
        
        if result.seo_score is not None:
            self.record_histogram('blog_seo_score', result.seo_score)
    
    def record_performance(self, operation: str, duration: float, success: bool, **metadata):
        """Record performance metrics for operations."""
        perf_metric = PerformanceMetrics(
            operation=operation,
            duration=duration,
            success=success,
            timestamp=time.time(),
            metadata=metadata
        )
        self.performance_metrics.append(perf_metric)
        
        # Also record as histogram
        self.record_histogram(f'{operation}_duration_seconds', duration, labels={
            'success': str(success)
        })
    
    def collect_system_metrics(self):
        """Collect system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.set_gauge('system_cpu_usage_percent', cpu_percent)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.set_gauge('system_memory_usage_percent', memory.percent)
            self.set_gauge('system_memory_used_bytes', memory.used)
            self.set_gauge('system_memory_available_bytes', memory.available)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.set_gauge('system_disk_usage_percent', disk.percent)
            self.set_gauge('system_disk_used_bytes', disk.used)
            self.set_gauge('system_disk_free_bytes', disk.free)
            
            # Process metrics
            process = psutil.Process()
            self.set_gauge('process_memory_rss_bytes', process.memory_info().rss)
            self.set_gauge('process_cpu_percent', process.cpu_percent())
            
            # Python metrics
            self.set_gauge('python_gc_objects_collected_total', len(sys.modules))
            
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        self.collect_system_metrics()
        
        # Calculate request statistics
        total_requests = sum(self.counters.get(k, 0) for k in self.counters if 'http_requests_total' in k)
        total_errors = sum(self.counters.get(k, 0) for k in self.counters if 'http_errors_total' in k)
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate average response times
        avg_response_times = {}
        for endpoint, durations in self.request_durations.items():
            if durations:
                avg_response_times[endpoint] = sum(durations) / len(durations)
        
        # Get recent performance metrics
        recent_performance = []
        cutoff_time = time.time() - 3600  # Last hour
        for perf in self.performance_metrics:
            if perf.timestamp > cutoff_time:
                recent_performance.append({
                    'operation': perf.operation,
                    'duration': perf.duration,
                    'success': perf.success,
                    'timestamp': perf.timestamp
                })
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': time.time() - (getattr(self, '_start_time', time.time())),
            
            # Request metrics
            'requests': {
                'total': total_requests,
                'errors': total_errors,
                'error_rate_percent': error_rate,
                'avg_response_times': avg_response_times
            },
            
            # Business metrics
            'blog_generation': self.blog_generation_stats,
            
            # System metrics
            'system': {
                'cpu_usage_percent': self.gauges.get('system_cpu_usage_percent', 0),
                'memory_usage_percent': self.gauges.get('system_memory_usage_percent', 0),
                'disk_usage_percent': self.gauges.get('system_disk_usage_percent', 0),
                'process_memory_mb': self.gauges.get('process_memory_rss_bytes', 0) / 1024 / 1024
            },
            
            # Performance metrics
            'performance': {
                'recent_operations': recent_performance[-10:],  # Last 10 operations
                'total_operations': len(self.performance_metrics)
            },
            
            # Counters and gauges
            'counters': dict(self.counters),
            'gauges': dict(self.gauges)
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        self.collect_system_metrics()
        
        # Determine health status
        cpu_usage = self.gauges.get('system_cpu_usage_percent', 0)
        memory_usage = self.gauges.get('system_memory_usage_percent', 0)
        disk_usage = self.gauges.get('system_disk_usage_percent', 0)
        
        # Calculate error rate
        total_requests = sum(self.counters.get(k, 0) for k in self.counters if 'http_requests_total' in k)
        total_errors = sum(self.counters.get(k, 0) for k in self.counters if 'http_errors_total' in k)
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        # Determine overall health
        health_issues = []
        
        if cpu_usage > 80:
            health_issues.append(f"High CPU usage: {cpu_usage:.1f}%")
        if memory_usage > 85:
            health_issues.append(f"High memory usage: {memory_usage:.1f}%")
        if disk_usage > 90:
            health_issues.append(f"High disk usage: {disk_usage:.1f}%")
        if error_rate > 5:
            health_issues.append(f"High error rate: {error_rate:.1f}%")
        
        if health_issues:
            status = "unhealthy"
        elif cpu_usage > 60 or memory_usage > 70 or error_rate > 1:
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            'status': status,
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {
                'cpu_usage': {'value': cpu_usage, 'threshold': 80, 'status': 'ok' if cpu_usage <= 80 else 'warning'},
                'memory_usage': {'value': memory_usage, 'threshold': 85, 'status': 'ok' if memory_usage <= 85 else 'warning'},
                'disk_usage': {'value': disk_usage, 'threshold': 90, 'status': 'ok' if disk_usage <= 90 else 'warning'},
                'error_rate': {'value': error_rate, 'threshold': 5, 'status': 'ok' if error_rate <= 5 else 'warning'}
            },
            'issues': health_issues,
            'uptime_seconds': time.time() - (getattr(self, '_start_time', time.time()))
        }


# Performance monitoring decorator
def monitor_performance(operation_name: str, metrics_collector: Optional[MetricsCollector] = None):
    """Decorator to monitor function performance."""
    def decorator(func: Callable):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error = None
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                duration = time.time() - start_time
                if metrics_collector:
                    metadata = {'error': error} if error else {}
                    metrics_collector.record_performance(
                        operation_name, duration, success, **metadata
                    )
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error = None
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                duration = time.time() - start_time
                if metrics_collector:
                    metadata = {'error': error} if error else {}
                    metrics_collector.record_performance(
                        operation_name, duration, success, **metadata
                    )
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# Global metrics collector instance
metrics_collector: Optional[MetricsCollector] = None


def initialize_metrics(retention_hours: int = 24) -> MetricsCollector:
    """Initialize global metrics collector."""
    global metrics_collector
    metrics_collector = MetricsCollector(retention_hours=retention_hours)
    metrics_collector._start_time = time.time()
    return metrics_collector


def get_metrics_collector() -> Optional[MetricsCollector]:
    """Get global metrics collector instance."""
    return metrics_collector
