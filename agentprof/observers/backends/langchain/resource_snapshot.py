"""Resource snapshot observer (Hardware/Resource Layer).

Low-cost coarse-grained snapshot: CPU, memory, GPU (if available), disk, network.
Runs alongside baseline trace — not deferred to the end.
Used for early USE health check, not root cause attribution.

Output: resource_snapshot.csv
"""

from __future__ import annotations

import csv
import threading
import time
import uuid
from pathlib import Path

import psutil

from agentprof.observers.base import BaseObserver
from agentprof.schema.events import AgentEvent


class ResourceSnapshotObserver(BaseObserver):
    name = "resource_snapshot"
    layer = "hardware_resource"

    def __init__(self, run_id: str, interval_s: float = 1.0) -> None:
        self._run_id = run_id
        self._interval_s = interval_s
        self._rows: list[dict] = []
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def attach(self, target: object = None) -> None:
        """Start background sampling thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._thread.start()

    def detach(self) -> None:
        """Stop sampling thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self._interval_s * 3)

    def flush(self, state=None) -> list[AgentEvent]:
        # ResourceSnapshot writes CSV directly; no AgentEvents emitted
        return []

    def write_csv(self, output_dir: Path) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "resource_snapshot.csv"
        if not self._rows:
            return out_path
        fieldnames = list(self._rows[0].keys())
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self._rows)
        return out_path

    def _sample_loop(self) -> None:
        net_before = psutil.net_io_counters()
        disk_before = psutil.disk_io_counters()
        while not self._stop_event.is_set():
            ts = time.time()
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()
            net_after = psutil.net_io_counters()
            disk_after = psutil.disk_io_counters()

            self._rows.append({
                "ts": round(ts, 3),
                "cpu_pct": cpu,
                "mem_used_mb": round(mem.used / 1024 / 1024, 1),
                "mem_total_mb": round(mem.total / 1024 / 1024, 1),
                "mem_pct": mem.percent,
                "net_sent_kb": round((net_after.bytes_sent - net_before.bytes_sent) / 1024, 2),
                "net_recv_kb": round((net_after.bytes_recv - net_before.bytes_recv) / 1024, 2),
                "disk_read_kb": round((disk_after.read_bytes - disk_before.read_bytes) / 1024, 2) if disk_after else 0,
                "disk_write_kb": round((disk_after.write_bytes - disk_before.write_bytes) / 1024, 2) if disk_after else 0,
            })
            net_before = net_after
            disk_before = disk_after
            self._stop_event.wait(self._interval_s)

