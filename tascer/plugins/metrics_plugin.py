"""Metrics Plugin for Tasc.

Provides observability via Prometheus-compatible metrics.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from . import Plugin, PluginInfo, PluginEvent, PluginStatus


@dataclass
class Metric:
    """A single metric."""
    
    name: str
    type: str  # counter, gauge, histogram
    help: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)
    buckets: List[float] = field(default_factory=list)  # For histograms
    observations: List[float] = field(default_factory=list)


class MetricsPlugin(Plugin):
    """Prometheus-compatible metrics for Tasc.
    
    Tracks:
    - tascer_actions_total: Total actions executed
    - tascer_action_duration_seconds: Action execution time
    - tascer_checkpoints_total: Checkpoints created
    - tascer_rollbacks_total: Rollbacks performed
    - tascer_errors_total: Errors encountered
    - tascer_legality_checks_total: Safety checks performed
    
    Exposes /metrics endpoint for Prometheus scraping.
    """
    
    def __init__(self, port: int = 9090):
        super().__init__()
        self.port = port
        self._metrics: Dict[str, Metric] = {}
        self._start_times: Dict[str, float] = {}
        self._init_metrics()
    
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="metrics",
            version="1.0.0",
            description="Prometheus metrics for observability",
            author="Tasc",
            requires=[],
            capabilities=["metrics", "prometheus", "observability"],
        )
    
    def _init_metrics(self):
        """Initialize default metrics."""
        self._metrics = {
            "tascer_actions_total": Metric(
                name="tascer_actions_total",
                type="counter",
                help="Total number of actions executed",
            ),
            "tascer_action_duration_seconds": Metric(
                name="tascer_action_duration_seconds",
                type="histogram",
                help="Action execution duration in seconds",
                buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
            ),
            "tascer_checkpoints_total": Metric(
                name="tascer_checkpoints_total",
                type="counter",
                help="Total checkpoints created",
            ),
            "tascer_rollbacks_total": Metric(
                name="tascer_rollbacks_total",
                type="counter",
                help="Total rollbacks performed",
            ),
            "tascer_errors_total": Metric(
                name="tascer_errors_total",
                type="counter",
                help="Total errors encountered",
            ),
            "tascer_legality_checks_total": Metric(
                name="tascer_legality_checks_total",
                type="counter",
                help="Total legality checks performed",
            ),
            "tascer_legality_blocked_total": Metric(
                name="tascer_legality_blocked_total",
                type="counter",
                help="Total actions blocked by safety checks",
            ),
            "tascer_active_runs": Metric(
                name="tascer_active_runs",
                type="gauge",
                help="Number of active Tasc runs",
            ),
        }
    
    async def initialize(self) -> bool:
        """Initialize metrics plugin."""
        self._status = PluginStatus.READY
        return True
    
    def get_actions(self) -> Dict[str, Callable]:
        """Return metrics actions."""
        return {
            "increment": self.increment,
            "observe": self.observe,
            "set_gauge": self.set_gauge,
            "get_metrics": self.get_metrics_text,
        }
    
    def get_context(self) -> Dict[str, Any]:
        """Return metrics context."""
        return {
            "metrics_count": len(self._metrics),
            "actions_total": self._metrics["tascer_actions_total"].value,
            "errors_total": self._metrics["tascer_errors_total"].value,
        }
    
    def increment(self, metric_name: str, value: float = 1.0) -> bool:
        """Increment a counter metric.
        
        ACTION: metrics.increment
        """
        if metric_name not in self._metrics:
            return False
        self._metrics[metric_name].value += value
        return True
    
    def observe(self, metric_name: str, value: float) -> bool:
        """Record an observation for a histogram.
        
        ACTION: metrics.observe
        """
        if metric_name not in self._metrics:
            return False
        metric = self._metrics[metric_name]
        metric.observations.append(value)
        return True
    
    def set_gauge(self, metric_name: str, value: float) -> bool:
        """Set a gauge value.
        
        ACTION: metrics.set_gauge
        """
        if metric_name not in self._metrics:
            return False
        self._metrics[metric_name].value = value
        return True
    
    def start_timer(self, action_id: str) -> None:
        """Start timing an action."""
        self._start_times[action_id] = time.perf_counter()
    
    def stop_timer(self, action_id: str) -> float:
        """Stop timing and record duration."""
        if action_id not in self._start_times:
            return 0.0
        duration = time.perf_counter() - self._start_times.pop(action_id)
        self.observe("tascer_action_duration_seconds", duration)
        return duration
    
    def get_metrics_text(self) -> str:
        """Get metrics in Prometheus text format.
        
        ACTION: metrics.get_metrics
        """
        lines = []
        
        for metric in self._metrics.values():
            lines.append(f"# HELP {metric.name} {metric.help}")
            lines.append(f"# TYPE {metric.name} {metric.type}")
            
            if metric.type == "histogram":
                # Output histogram buckets
                total = len(metric.observations)
                sum_val = sum(metric.observations) if metric.observations else 0
                
                for bucket in metric.buckets:
                    count = sum(1 for v in metric.observations if v <= bucket)
                    lines.append(f'{metric.name}_bucket{{le="{bucket}"}} {count}')
                lines.append(f'{metric.name}_bucket{{le="+Inf"}} {total}')
                lines.append(f"{metric.name}_sum {sum_val}")
                lines.append(f"{metric.name}_count {total}")
            else:
                lines.append(f"{metric.name} {metric.value}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def on_event(self, event: PluginEvent) -> Optional[Dict[str, Any]]:
        """Track events as metrics."""
        event_type = event.event_type
        
        if event_type == "action_start":
            action_id = event.data.get("action_id", "unknown")
            self.start_timer(action_id)
        
        elif event_type == "action_complete":
            action_id = event.data.get("action_id", "unknown")
            self.stop_timer(action_id)
            self.increment("tascer_actions_total")
        
        elif event_type == "checkpoint":
            self.increment("tascer_checkpoints_total")
        
        elif event_type == "rollback":
            self.increment("tascer_rollbacks_total")
        
        elif event_type == "error":
            self.increment("tascer_errors_total")
        
        elif event_type == "legality_check":
            self.increment("tascer_legality_checks_total")
            if not event.data.get("is_legal", True):
                self.increment("tascer_legality_blocked_total")
        
        elif event_type == "run_start":
            current = self._metrics["tascer_active_runs"].value
            self.set_gauge("tascer_active_runs", current + 1)
        
        elif event_type == "run_end":
            current = self._metrics["tascer_active_runs"].value
            self.set_gauge("tascer_active_runs", max(0, current - 1))
        
        return None
