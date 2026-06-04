"""system_monitor_tool: Persistent system monitoring in background.

Records system metrics over time without blocking the agent.
LLM starts recording with duration/interval, then retrieves all records when complete.
"""

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated

from langchain_core.tools import tool

# Optional psutil import
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# Global monitor registry
_MONITORS: dict[str, "SystemMonitor"] = {}


@dataclass
class SystemMonitor:
    """Background system monitor."""
    monitor_id: str
    metrics: list
    interval: float
    duration: float
    start_time: float
    records: dict = field(default_factory=lambda: defaultdict(list))
    status: str = "pending"  # pending, running, completed, failed, stopped
    error: str | None = None
    thread: threading.Thread | None = None

    def add_record(self, metric_name: str, value):
        timestamp = time.time()
        self.records[metric_name].append({
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "value": value,
        })

    def is_complete(self) -> bool:
        elapsed = time.time() - self.start_time
        return elapsed >= self.duration


def _monitor_loop(monitor_id: str):
    """Background monitoring loop."""
    monitor = _MONITORS.get(monitor_id)
    if not monitor:
        return

    monitor.status = "running"

    try:
        while time.time() - monitor.start_time < monitor.duration:
            timestamp = time.time()

            # CPU
            if "cpu" in monitor.metrics:
                cpu_percent = psutil.cpu_percent(interval=None)
                monitor.records["cpu_percent"].append({
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                    "value": round(cpu_percent, 2),
                })

            # Memory
            if "memory" in monitor.metrics:
                mem = psutil.virtual_memory()
                monitor.records["memory_used_gb"].append({
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                    "value": round(mem.used / (1024**3), 2),
                })
                monitor.records["memory_percent"].append({
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                    "value": round(mem.percent, 2),
                })

            # Disk
            if "disk" in monitor.metrics:
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        key = f"disk_{partition.mountpoint.replace('/', '_').replace(':', '')}_percent"
                        monitor.records[key].append({
                            "timestamp": timestamp,
                            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                            "value": round(usage.percent, 2),
                        })
                    except PermissionError:
                        continue

            # Network
            if "network" in monitor.metrics:
                net = psutil.net_io_counters()
                monitor.records["network_sent_mb"].append({
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                    "value": round(net.bytes_sent / (1024**2), 2),
                })
                monitor.records["network_recv_mb"].append({
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp).isoformat(),
                    "value": round(net.bytes_recv / (1024**2), 2),
                })

            # Sleep until next interval
            sleep_time = monitor.interval - (time.time() - timestamp)
            if sleep_time > 0:
                time.sleep(sleep_time)

        monitor.status = "completed"

    except Exception as e:
        monitor.status = "failed"
        monitor.error = str(e)


@tool
def system_monitor_tool(
    action: Annotated[str, "Action: 'start' (begin recording), 'get' (retrieve records), 'status' (check progress), 'stop' (halt recording)."],
    monitor_id: Annotated[str, "Unique identifier for this monitoring session."],
    duration: Annotated[float, "Total recording duration in seconds. Default 60."] = 60.0,
    interval: Annotated[float, "Recording interval in seconds. Default 1.0."] = 1.0,
    metrics: Annotated[list[str] | None, "Metrics to record: 'cpu', 'memory', 'disk', 'network'. Default ['cpu', 'memory']."] = None,
) -> Annotated[str, "Result message with records or status information."]:
    """Start a background system monitoring session or retrieve recorded data.

    Use this tool to record system metrics over time without blocking the agent.
    The agent can start monitoring, perform other actions, then retrieve results later.

    Modes:
    - 'start': Begin background recording for specified duration
    - 'get': Retrieve all collected records (works after recording completes or during)
    - 'status': Check if recording is in progress or completed
    - 'stop': Halt an ongoing recording session

    Args:
        action: What to do ('start', 'get', 'status', 'stop')
        monitor_id: Unique name for this monitoring session (e.g., 'run_001_baseline')
        duration: Total recording duration in seconds (default 60)
        interval: Time between recordings in seconds (default 1.0)
        metrics: List of metrics to record (default ['cpu', 'memory'])

    Returns:
        For 'start': Confirmation that monitoring has begun
        For 'get': All collected records organized by metric
        For 'status': Current monitoring status and progress
        For 'stop': Confirmation that monitoring was halted

    Example:
        # Start monitoring for 60 seconds, record every 1 second
        system_monitor_tool(action="start", monitor_id="test_001", duration=60, interval=1.0)

        # After some time, check status
        system_monitor_tool(action="status", monitor_id="test_001")

        # Retrieve all recorded data
        system_monitor_tool(action="get", monitor_id="test_001")

        # Stop monitoring early
        system_monitor_tool(action="stop", monitor_id="test_001")
    """
    if not PSUTIL_AVAILABLE:
        return "[ERROR] psutil not installed. Install with: pip install psutil"

    if metrics is None:
        metrics = ["cpu", "memory"]

    if action == "start":
        # Create new monitor
        monitor = SystemMonitor(
            monitor_id=monitor_id,
            metrics=metrics,
            interval=interval,
            duration=duration,
            start_time=time.time(),
            records=defaultdict(list),
            status="pending",
        )
        _MONITORS[monitor_id] = monitor

        # Start background thread
        thread = threading.Thread(target=_monitor_loop, args=(monitor_id,), daemon=True)
        thread.start()
        monitor.thread = thread

        estimated_records = int(duration / interval)
        return (
            f"[OK] Monitoring started: {monitor_id}\n"
            f"Duration: {duration}s | Interval: {interval}s | Metrics: {', '.join(metrics)}\n"
            f"Estimated data points: ~{estimated_records}\n"
            f"Use action='status' to check progress, action='get' to retrieve results"
        )

    elif action == "get":
        if monitor_id not in _MONITORS:
            return f"[ERROR] Monitor not found: {monitor_id}. Use action='start' first."

        monitor = _MONITORS[monitor_id]

        if not monitor.records:
            return f"[INFO] No records collected yet for {monitor_id}. Recording may not have started."

        # Format records
        lines = [f"=== System Monitor Records: {monitor_id} ==="]
        lines.append(f"Status: {monitor.status}")
        lines.append(f"Duration: {monitor.duration}s | Interval: {monitor.interval}s")
        lines.append(f"Start: {datetime.fromtimestamp(monitor.start_time).isoformat()}")

        for metric_name, records in sorted(monitor.records.items()):
            lines.append(f"\n--- {metric_name} ({len(records)} records) ---")

            # Calculate statistics
            if records and isinstance(records[0]["value"], (int, float)):
                values = [r["value"] for r in records]
                avg = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)

                # Show sample records (first 5 and last 5)
                sample = records[:5]
                for r in sample:
                    lines.append(f"  {r['datetime']}: {r['value']}")

                if len(records) > 10:
                    lines.append(f"  ... ({len(records) - 10} more records) ...")
                    for r in records[-5:]:
                        lines.append(f"  {r['datetime']}: {r['value']}")

                lines.append(f"  Summary: avg={avg:.2f}, min={min_val:.2f}, max={max_val:.2f}")

        return "\n".join(lines)

    elif action == "status":
        if monitor_id not in _MONITORS:
            return f"[ERROR] Monitor not found: {monitor_id}. Use action='start' first."

        monitor = _MONITORS[monitor_id]
        elapsed = time.time() - monitor.start_time
        progress = min(100, (elapsed / monitor.duration) * 100)

        status_msg = (
            f"[OK] Monitor: {monitor_id}\n"
            f"Status: {monitor.status}\n"
            f"Progress: {progress:.1f}% ({elapsed:.1f}s / {monitor.duration}s)\n"
            f"Metrics: {', '.join(monitor.metrics)}\n"
            f"Interval: {monitor.interval}s\n"
        )

        if monitor.error:
            status_msg += f"Error: {monitor.error}\n"

        # Count records
        total_records = sum(len(v) for v in monitor.records.values())
        status_msg += f"Records collected: {total_records}\n"

        for metric_name, records in monitor.records.items():
            status_msg += f"  {metric_name}: {len(records)} records\n"

        return status_msg

    elif action == "stop":
        if monitor_id not in _MONITORS:
            return f"[ERROR] Monitor not found: {monitor_id}."

        monitor = _MONITORS[monitor_id]
        monitor.status = "stopped"
        elapsed = time.time() - monitor.start_time

        total_records = sum(len(v) for v in monitor.records.values())
        return (
            f"[OK] Monitoring stopped: {monitor_id}\n"
            f"Elapsed: {elapsed:.1f}s\n"
            f"Records collected: {total_records}\n"
            f"Use action='get' to retrieve results"
        )

    else:
        return f"[ERROR] Unknown action: '{action}'. Use 'start', 'get', 'status', or 'stop'."