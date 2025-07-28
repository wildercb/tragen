"""
Production Monitoring System
============================

Real-time monitoring and alerting for production trading operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class Alert:
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    component: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    acknowledged: bool = False
    resolved: bool = False
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Metric:
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    tags: Dict[str, str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

class MetricsCollector:
    """Collects and aggregates system metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        
    def increment_counter(self, name: str, value: float = 1.0, tags: Dict[str, str] = None):
        """Increment a counter metric."""
        self.counters[name] += value
        self._record_metric(name, MetricType.COUNTER, self.counters[name], tags)
        
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric."""
        self.gauges[name] = value
        self._record_metric(name, MetricType.GAUGE, value, tags)
        
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a value for histogram analysis."""
        self.histograms[name].append(value)
        # Keep only recent values
        if len(self.histograms[name]) > 1000:
            self.histograms[name] = self.histograms[name][-1000:]
        self._record_metric(name, MetricType.HISTOGRAM, value, tags)
        
    def time_operation(self, name: str, tags: Dict[str, str] = None):
        """Context manager for timing operations."""
        return TimerContext(self, name, tags)
        
    def _record_metric(self, name: str, metric_type: MetricType, value: float, tags: Dict[str, str] = None):
        """Record a metric."""
        metric = Metric(
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        self.metrics[name].append(metric)
        
    def get_metric_stats(self, name: str, window_minutes: int = 5) -> Dict[str, Any]:
        """Get statistics for a metric over a time window."""
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_metrics = [
            m for m in self.metrics[name] 
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
            
        values = [m.value for m in recent_metrics]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
            'latest': values[-1] if values else 0,
            'window_minutes': window_minutes
        }
        
    def get_histogram_percentiles(self, name: str) -> Dict[str, float]:
        """Get percentile statistics for histogram metrics."""
        if name not in self.histograms or not self.histograms[name]:
            return {}
            
        values = sorted(self.histograms[name])
        n = len(values)
        
        return {
            'p50': values[int(n * 0.5)] if n > 0 else 0,
            'p75': values[int(n * 0.75)] if n > 0 else 0,
            'p90': values[int(n * 0.9)] if n > 0 else 0,
            'p95': values[int(n * 0.95)] if n > 0 else 0,
            'p99': values[int(n * 0.99)] if n > 0 else 0,
            'count': n
        }

class TimerContext:
    """Context manager for timing operations."""
    
    def __init__(self, collector: MetricsCollector, name: str, tags: Dict[str, str] = None):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None
        
    def __enter__(self):
        self.start_time = datetime.now()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            self.collector.record_histogram(f"{self.name}_duration", duration, self.tags)

class HealthChecker:
    """System health monitoring."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.health_checks: Dict[str, Callable] = {}
        self.last_health_check = {}
        self.health_status = {}
        
    def register_health_check(self, name: str, check_function: Callable):
        """Register a health check function."""
        self.health_checks[name] = check_function
        
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        
        for name, check_func in self.health_checks.items():
            try:
                start_time = datetime.now()
                result = await check_func()
                duration = (datetime.now() - start_time).total_seconds()
                
                self.last_health_check[name] = datetime.now()
                self.health_status[name] = result
                
                results[name] = {
                    'status': 'healthy' if result.get('healthy', False) else 'unhealthy',
                    'duration_ms': duration * 1000,
                    'last_check': start_time.isoformat(),
                    **result
                }
                
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                results[name] = {
                    'status': 'error',
                    'error': str(e),
                    'last_check': datetime.now().isoformat()
                }
                
        return results
        
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        if not self.health_status:
            return {'status': 'unknown', 'checks': {}}
            
        healthy_count = sum(1 for status in self.health_status.values() 
                          if status.get('healthy', False))
        total_count = len(self.health_status)
        
        overall_status = 'healthy' if healthy_count == total_count else 'degraded'
        if healthy_count == 0:
            overall_status = 'critical'
            
        return {
            'status': overall_status,
            'healthy_checks': healthy_count,
            'total_checks': total_count,
            'last_update': max(self.last_health_check.values(), default=datetime.now()).isoformat(),
            'checks': self.health_status.copy()
        }

class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.alert_config = config.get('alerts', {})
        
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_handlers: List[Callable] = []
        
        # Alert rate limiting
        self.alert_counts: Dict[str, int] = defaultdict(int)
        self.last_alert_time: Dict[str, datetime] = {}
        
    def add_notification_handler(self, handler: Callable):
        """Add a notification handler."""
        self.notification_handlers.append(handler)
        
    async def create_alert(
        self, 
        level: AlertLevel, 
        title: str, 
        message: str, 
        component: str,
        metadata: Dict[str, Any] = None
    ) -> Alert:
        """Create and process a new alert."""
        
        alert_id = f"{component}_{title}_{datetime.now().timestamp()}"
        
        # Check rate limiting
        rate_limit_key = f"{component}_{title}"
        if self._is_rate_limited(rate_limit_key):
            logger.debug(f"Alert rate limited: {title}")
            return None
            
        alert = Alert(
            alert_id=alert_id,
            level=level,
            title=title,
            message=message,
            component=component,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        # Add to active alerts
        self.active_alerts[alert_id] = alert
        
        # Add to history
        self.alert_history.append(alert)
        
        # Keep history limited
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
            
        # Update rate limiting
        self.alert_counts[rate_limit_key] += 1
        self.last_alert_time[rate_limit_key] = datetime.now()
        
        # Send notifications
        await self._send_notifications(alert)
        
        logger.info(f"Alert created: {level.value} - {title}")
        
        return alert
        
    async def acknowledge_alert(self, alert_id: str, user: str = "system"):
        """Acknowledge an alert."""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            self.active_alerts[alert_id].metadata['acknowledged_by'] = user
            self.active_alerts[alert_id].metadata['acknowledged_at'] = datetime.now().isoformat()
            
            logger.info(f"Alert acknowledged: {alert_id} by {user}")
            
    async def resolve_alert(self, alert_id: str, user: str = "system"):
        """Resolve an alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts.pop(alert_id)
            alert.resolved = True
            alert.metadata['resolved_by'] = user
            alert.metadata['resolved_at'] = datetime.now().isoformat()
            
            logger.info(f"Alert resolved: {alert_id} by {user}")
            
    def _is_rate_limited(self, rate_limit_key: str) -> bool:
        """Check if alert should be rate limited."""
        max_alerts_per_hour = self.alert_config.get('max_alerts_per_hour', 10)
        
        # Clean old counts
        cutoff_time = datetime.now() - timedelta(hours=1)
        if (rate_limit_key in self.last_alert_time and 
            self.last_alert_time[rate_limit_key] < cutoff_time):
            self.alert_counts[rate_limit_key] = 0
            
        return self.alert_counts[rate_limit_key] >= max_alerts_per_hour
        
    async def _send_notifications(self, alert: Alert):
        """Send alert notifications."""
        for handler in self.notification_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error sending alert notification: {e}")
                
    def get_active_alerts(self, level: AlertLevel = None) -> List[Dict[str, Any]]:
        """Get active alerts."""
        alerts = list(self.active_alerts.values())
        
        if level:
            alerts = [a for a in alerts if a.level == level]
            
        return [asdict(alert) for alert in alerts]
        
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics."""
        active_by_level = defaultdict(int)
        for alert in self.active_alerts.values():
            active_by_level[alert.level.value] += 1
            
        return {
            'total_active': len(self.active_alerts),
            'by_level': dict(active_by_level),
            'total_history': len(self.alert_history),
            'last_alert': self.alert_history[-1].timestamp.isoformat() if self.alert_history else None
        }

class ProductionMonitor:
    """
    Comprehensive production monitoring system.
    
    Provides:
    - Real-time metrics collection
    - System health monitoring
    - Alert management
    - Performance tracking
    - Resource monitoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitoring_config = config.get('monitoring', {})
        
        # Core components
        self.metrics = MetricsCollector()
        self.health_checker = HealthChecker(config)
        self.alert_manager = AlertManager(config)
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task = None
        
        # Performance tracking
        self.performance_data = {
            'trades_per_minute': deque(maxlen=60),
            'api_response_times': deque(maxlen=1000),
            'error_rates': deque(maxlen=100),
            'memory_usage': deque(maxlen=100),
            'cpu_usage': deque(maxlen=100)
        }
        
        # Initialize health checks
        self._register_default_health_checks()
        
    async def initialize(self):
        """Initialize the monitoring system."""
        logger.info("Initializing production monitor...")
        
        # Setup default notification handlers
        await self._setup_notification_handlers()
        
        logger.info("Production monitor initialized")
        
    async def start_monitoring(self):
        """Start monitoring tasks."""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Production monitoring started")
        
    async def stop_monitoring(self):
        """Stop monitoring tasks."""
        if not self.is_monitoring:
            return
            
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Production monitoring stopped")
        
    async def record_execution(self, execution_result: Any):
        """Record trade execution metrics."""
        
        # Record execution metrics
        self.metrics.increment_counter('trades_executed_total')
        
        if hasattr(execution_result, 'execution_status'):
            self.metrics.increment_counter(
                f'trades_by_status_{execution_result.execution_status}',
                tags={'status': execution_result.execution_status}
            )
            
        if hasattr(execution_result, 'fees'):
            self.metrics.record_histogram('execution_fees', execution_result.fees)
            
        if hasattr(execution_result, 'slippage'):
            self.metrics.record_histogram('execution_slippage', execution_result.slippage)
            
        # Track trades per minute
        self.performance_data['trades_per_minute'].append(datetime.now())
        
        # Check for execution alerts
        await self._check_execution_alerts(execution_result)
        
    async def record_agent_performance(self, agent_id: str, performance_data: Dict[str, Any]):
        """Record agent performance metrics."""
        
        for metric_name, value in performance_data.items():
            if isinstance(value, (int, float)):
                self.metrics.set_gauge(f'agent_{metric_name}', value, tags={'agent_id': agent_id})
                
    async def record_api_call(self, endpoint: str, duration: float, status_code: int):
        """Record API call metrics."""
        
        self.metrics.increment_counter('api_calls_total', tags={'endpoint': endpoint})
        self.metrics.record_histogram('api_response_time', duration, tags={'endpoint': endpoint})
        
        if status_code >= 400:
            self.metrics.increment_counter('api_errors_total', tags={'endpoint': endpoint, 'status': str(status_code)})
            
        # Track response times
        self.performance_data['api_response_times'].append(duration)
        
    async def alert_emergency_halt(self, reason: str):
        """Create emergency halt alert."""
        await self.alert_manager.create_alert(
            AlertLevel.CRITICAL,
            "Emergency Trading Halt",
            f"Trading has been halted: {reason}",
            "production_controller",
            metadata={'reason': reason, 'halt_time': datetime.now().isoformat()}
        )
        
    async def alert_emergency_closure(self, reason: str, closed_positions: List[Dict[str, Any]]):
        """Create emergency position closure alert."""
        await self.alert_manager.create_alert(
            AlertLevel.CRITICAL,
            "Emergency Position Closure",
            f"All positions closed: {reason}",
            "production_controller",
            metadata={
                'reason': reason,
                'positions_closed': len(closed_positions),
                'closure_time': datetime.now().isoformat()
            }
        )
        
    async def alert_mode_change(self, old_mode: Any, new_mode: Any, reason: str):
        """Create trading mode change alert."""
        await self.alert_manager.create_alert(
            AlertLevel.WARNING,
            "Trading Mode Changed",
            f"Trading mode changed from {old_mode.value} to {new_mode.value}: {reason}",
            "production_controller",
            metadata={'old_mode': old_mode.value, 'new_mode': new_mode.value, 'reason': reason}
        )
        
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics."""
        
        # Calculate performance metrics
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        recent_trades = len([
            t for t in self.performance_data['trades_per_minute'] 
            if t > minute_ago
        ])
        
        avg_response_time = (
            statistics.mean(self.performance_data['api_response_times']) 
            if self.performance_data['api_response_times'] else 0
        )
        
        return {
            'timestamp': now.isoformat(),
            'trades_per_minute': recent_trades,
            'avg_api_response_time': avg_response_time,
            'total_trades': self.metrics.counters.get('trades_executed_total', 0),
            'total_api_calls': self.metrics.counters.get('api_calls_total', 0),
            'total_errors': self.metrics.counters.get('api_errors_total', 0),
            'active_alerts': len(self.alert_manager.active_alerts),
            'health_status': await self.health_checker.run_health_checks(),
            'performance_percentiles': {
                'api_response_time': self.metrics.get_histogram_percentiles('api_response_time'),
                'execution_fees': self.metrics.get_histogram_percentiles('execution_fees'),
                'execution_slippage': self.metrics.get_histogram_percentiles('execution_slippage')
            }
        }
        
    async def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get complete monitoring dashboard data."""
        
        system_metrics = await self.get_system_metrics()
        health_status = self.health_checker.get_overall_health()
        alert_summary = self.alert_manager.get_alert_summary()
        
        return {
            'system_metrics': system_metrics,
            'health_status': health_status,
            'alerts': {
                'summary': alert_summary,
                'active': self.alert_manager.get_active_alerts(),
                'critical': self.alert_manager.get_active_alerts(AlertLevel.CRITICAL)
            },
            'performance': {
                'trades_per_minute': len(self.performance_data['trades_per_minute']),
                'avg_response_time': statistics.mean(self.performance_data['api_response_times']) if self.performance_data['api_response_times'] else 0,
                'error_rate': len([e for e in self.performance_data['error_rates'] if e]) / max(len(self.performance_data['error_rates']), 1)
            }
        }
        
    def _register_default_health_checks(self):
        """Register default system health checks."""
        
        async def check_memory_usage():
            """Check system memory usage."""
            try:
                import psutil
                memory = psutil.virtual_memory()
                return {
                    'healthy': memory.percent < 90,
                    'memory_percent': memory.percent,
                    'available_gb': memory.available / (1024**3)
                }
            except ImportError:
                return {'healthy': True, 'note': 'psutil not available'}
                
        async def check_disk_usage():
            """Check disk usage."""
            try:
                import psutil
                disk = psutil.disk_usage('/')
                return {
                    'healthy': disk.percent < 90,
                    'disk_percent': disk.percent,
                    'available_gb': disk.free / (1024**3)
                }
            except ImportError:
                return {'healthy': True, 'note': 'psutil not available'}
                
        async def check_api_health():
            """Check API responsiveness."""
            response_times = list(self.performance_data['api_response_times'])
            if not response_times:
                return {'healthy': True, 'note': 'No API calls recorded'}
                
            avg_response = statistics.mean(response_times[-10:])  # Last 10 calls
            return {
                'healthy': avg_response < 5.0,  # 5 second threshold
                'avg_response_time': avg_response,
                'recent_calls': len(response_times)
            }
            
        self.health_checker.register_health_check('memory', check_memory_usage)
        self.health_checker.register_health_check('disk', check_disk_usage)
        self.health_checker.register_health_check('api', check_api_health)
        
    async def _setup_notification_handlers(self):
        """Setup default notification handlers."""
        
        async def log_notification_handler(alert: Alert):
            """Log alert notifications."""
            log_level = {
                AlertLevel.INFO: logging.INFO,
                AlertLevel.WARNING: logging.WARNING,
                AlertLevel.ERROR: logging.ERROR,
                AlertLevel.CRITICAL: logging.CRITICAL
            }.get(alert.level, logging.INFO)
            
            logger.log(log_level, f"ALERT [{alert.level.value}] {alert.title}: {alert.message}")
            
        self.alert_manager.add_notification_handler(log_notification_handler)
        
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        
        check_interval = self.monitoring_config.get('check_interval', 30)  # 30 seconds
        
        while self.is_monitoring:
            try:
                # Run health checks
                await self.health_checker.run_health_checks()
                
                # Update system metrics
                await self._update_system_metrics()
                
                # Check for threshold alerts
                await self._check_threshold_alerts()
                
                # Clean old data
                self._cleanup_old_data()
                
                await asyncio.sleep(check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(check_interval)
                
    async def _update_system_metrics(self):
        """Update system-level metrics."""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            self.metrics.set_gauge('system_cpu_percent', cpu_percent)
            self.performance_data['cpu_usage'].append(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics.set_gauge('system_memory_percent', memory.percent)
            self.performance_data['memory_usage'].append(memory.percent)
            
        except ImportError:
            # psutil not available
            pass
            
    async def _check_execution_alerts(self, execution_result: Any):
        """Check for execution-related alerts."""
        
        if hasattr(execution_result, 'execution_status'):
            if execution_result.execution_status == 'rejected':
                await self.alert_manager.create_alert(
                    AlertLevel.WARNING,
                    "Trade Execution Rejected",
                    f"Trade rejected for {execution_result.symbol}: {execution_result.error_message}",
                    "execution_engine",
                    metadata={'symbol': execution_result.symbol, 'reason': execution_result.error_message}
                )
                
    async def _check_threshold_alerts(self):
        """Check for threshold-based alerts."""
        
        # Check API response times
        response_times = list(self.performance_data['api_response_times'])
        if response_times:
            avg_response = statistics.mean(response_times[-10:])
            if avg_response > 10.0:  # 10 second threshold
                await self.alert_manager.create_alert(
                    AlertLevel.WARNING,
                    "High API Response Times",
                    f"Average API response time: {avg_response:.2f}s",
                    "api_monitoring",
                    metadata={'avg_response_time': avg_response}
                )
                
        # Check memory usage
        memory_usage = list(self.performance_data['memory_usage'])
        if memory_usage and memory_usage[-1] > 85:
            await self.alert_manager.create_alert(
                AlertLevel.WARNING,
                "High Memory Usage",
                f"Memory usage: {memory_usage[-1]:.1f}%",
                "system_monitoring",
                metadata={'memory_percent': memory_usage[-1]}
            )
            
    def _cleanup_old_data(self):
        """Clean up old performance data."""
        
        # Clean old trade timestamps (keep only last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.performance_data['trades_per_minute'] = deque([
            t for t in self.performance_data['trades_per_minute'] 
            if t > cutoff_time
        ], maxlen=60)
        
    async def cleanup(self):
        """Cleanup monitoring resources."""
        await self.stop_monitoring()
        
        # Clear data
        self.performance_data.clear()
        self.alert_manager.active_alerts.clear()
        self.alert_manager.alert_history.clear()
        
        logger.info("Production monitor cleanup complete")