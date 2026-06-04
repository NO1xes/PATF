"""system_info_tool: Collect system resource metrics.

Used by LLM agent to get CPU, memory, disk, and network information.
"""

import os
from typing import Annotated

from langchain_core.tools import tool

# Optional psutil import
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@tool
def system_info_tool(
    metrics: Annotated[list[str], "List of metrics to collect: 'cpu', 'memory', 'disk', 'network', 'all'. Default ['all']."] = None,
    interval: Annotated[float, "Measurement interval in seconds for CPU. Default 0.1."] = 0.1,
) -> Annotated[str, "System metrics or error message."]:
    """Collect system resource information.

    Use this tool to get CPU, memory, disk, and network metrics from the system.
    Essential for understanding resource usage during agent operations.

    Args:
        metrics: List of metrics to collect. Options:
            - 'cpu': CPU usage (per-core and average)
            - 'memory': RAM usage (used, free, percent)
            - 'disk': Disk usage (total, used, free, percent)
            - 'network': Network I/O (bytes sent/received)
            - 'all': All metrics (default)
        interval: Measurement interval for CPU percentage. Default 0.1s.

    Returns:
        Formatted system metrics or error message.

    Example:
        system_info_tool()
        system_info_tool(metrics=["cpu", "memory"])
        system_info_tool(metrics=["disk", "network"])
    """
    if not PSUTIL_AVAILABLE:
        return "[ERROR] psutil not installed. Install with: pip install psutil"

    if metrics is None:
        metrics = ["all"]

    # Normalize metrics
    if "all" in metrics:
        metrics = ["cpu", "memory", "disk", "network"]

    result_parts = []

    try:
        # CPU metrics
        if "cpu" in metrics:
            cpu_percent = psutil.cpu_percent(interval=interval, percpu=True)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            cpu_times = psutil.cpu_times()

            result_parts.append("=== CPU ===")
            result_parts.append(f"Logical CPUs: {cpu_count}")
            if cpu_freq:
                result_parts.append(f"Frequency: {cpu_freq.current:.0f} MHz")
            result_parts.append(f"Overall usage: {sum(cpu_percent)/len(cpu_percent):.1f}%")
            result_parts.append(f"Per-core: {', '.join(f'{p:.1f}%' for p in cpu_percent)}")
            result_parts.append(
                f"Times: user={cpu_times.user:.1f}s, system={cpu_times.system:.1f}s, "
                f"idle={cpu_times.idle:.1f}s"
            )

        # Memory metrics
        if "memory" in metrics:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            result_parts.append("\n=== Memory ===")
            result_parts.append(f"RAM: {mem.total / (1024**3):.1f} GB total")
            result_parts.append(f"Used: {mem.used / (1024**3):.1f} GB ({mem.percent}%)")
            result_parts.append(f"Available: {mem.available / (1024**3):.1f} GB")
            result_parts.append(f"Free: {mem.free / (1024**3):.1f} GB")
            if swap.total > 0:
                result_parts.append(f"Swap: {swap.total / (1024**3):.1f} GB total, "
                                   f"{swap.percent}% used")

        # Disk metrics
        if "disk" in metrics:
            partitions = psutil.disk_partitions()
            result_parts.append("\n=== Disk ===")
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    result_parts.append(
                        f"{partition.mountpoint} ({partition.fstype}): "
                        f"{usage.total / (1024**3):.1f} GB total, "
                        f"{usage.used / (1024**3):.1f} GB used ({usage.percent}%), "
                        f"{usage.free / (1024**3):.1f} GB free"
                    )
                except PermissionError:
                    continue

        # Network metrics
        if "network" in metrics:
            net_io = psutil.net_io_counters()
            net_connections = psutil.net_connections()

            result_parts.append("\n=== Network ===")
            result_parts.append(f"Bytes sent: {net_io.bytes_sent / (1024**2):.2f} MB")
            result_parts.append(f"Bytes received: {net_io.bytes_recv / (1024**2):.2f} MB")
            result_parts.append(f"Packets sent: {net_io.packets_sent}")
            result_parts.append(f"Packets received: {net_io.packets_recv}")
            result_parts.append(f"Active connections: {len(net_connections)}")

        return "\n".join(result_parts) if result_parts else "[ERROR] No metrics collected"

    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {str(e)}"


@tool
def system_info_processes_tool(
    limit: Annotated[int, "Maximum number of processes to show. Default 10."] = 10,
    sort_by: Annotated[str, "Sort by: 'cpu', 'memory', 'pid'. Default 'cpu'."] = "cpu",
) -> Annotated[str, "Top processes by resource usage."]:
    """List top processes by CPU or memory usage.

    Args:
        limit: Maximum number of processes to show. Default 10.
        sort_by: Sort by 'cpu', 'memory', or 'pid'. Default 'cpu'.

    Returns:
        Top processes with resource usage.
    """
    if not PSUTIL_AVAILABLE:
        return "[ERROR] psutil not installed"

    result_parts = ["=== Top Processes ==="]

    processes = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = proc.info
            if info["cpu_percent"] is None:
                info["cpu_percent"] = 0
            if info["memory_percent"] is None:
                info["memory_percent"] = 0
            processes.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Sort
    if sort_by == "memory":
        processes.sort(key=lambda p: p["memory_percent"] or 0, reverse=True)
    elif sort_by == "pid":
        processes.sort(key=lambda p: p["pid"], reverse=True)
    else:  # cpu
        processes.sort(key=lambda p: p["cpu_percent"] or 0, reverse=True)

    # Header
    result_parts.append(f"{'PID':>8} {'Name':<30} {'CPU%':>8} {'Memory%':>8}")
    result_parts.append("-" * 60)

    for proc_info in processes[:limit]:
        result_parts.append(
            f"{proc_info['pid']:>8} "
            f"{proc_info['name'][:30]:<30} "
            f"{proc_info['cpu_percent'] or 0:>7.1f}% "
            f"{proc_info['memory_percent'] or 0:>7.2f}%"
        )

    return "\n".join(result_parts)