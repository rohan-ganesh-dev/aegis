"""Monitoring package for proactive customer intelligence."""

from aegis.monitors.proactive_monitor import (
    ProactiveMonitor,
    get_monitor,
    start_monitoring,
    stop_monitoring
)

__all__ = [
    'ProactiveMonitor',
    'get_monitor',
    'start_monitoring',
    'stop_monitoring'
]
