"""process_run_tool: Run commands as background processes.

Used by LLM agent to start long-running tasks without blocking.
"""

import os
import subprocess
import uuid
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool


# Global process registry (simplified, in-memory)
_PROCESS_REGISTRY: dict[str, dict] = {}


@tool
def process_run_tool(
    command: Annotated[str, "Command to execute in background."],
    cwd: Annotated[str | None, "Working directory. None uses current directory."] = None,
    label: Annotated[str | None, "Optional label to identify this process."] = None,
    detached: Annotated[bool, "If True, run fully detached (no output capture). Default True."] = True,
) -> Annotated[str, "Process ID and output file path, or error message."]:
    """Start a command as a background process.

    Use this tool to start long-running tasks (like profiling runs, servers)
    without blocking the agent. Process output is captured to a file.

    Args:
        command: Shell command to run in background.
        cwd: Working directory. None uses current directory.
        label: Optional human-readable label for this process.
        detached: If True, run fully detached (no output capture). Default True.

    Returns:
        Process ID (PID) and output file path, or error message.

    Example:
        process_run_tool(command="python -m agentprof.controller ...")
        process_run_tool(command="python -m http.server 8080", label="dev_server")
        process_run_tool(command="tail -f logs/app.log", detached=True)
    """
    try:
        # Generate process ID
        pid = str(uuid.uuid4())[:8]
        label = label or f"process_{pid}"

        # Output file
        output_dir = Path("/tmp/agentprof_processes")
        output_dir.mkdir(parents=True, exist_ok=True)
        stdout_file = output_dir / f"{pid}.stdout"
        stderr_file = output_dir / f"{pid}.stderr"

        # Sanitize command (basic check)
        if not command or not command.strip():
            return "[ERROR] Empty command"

        env = os.environ.copy()
        env["AGENTPROF_PROFILE_PID"] = pid

        if detached:
            # Fully detached process
            with open(stdout_file, "w") as stdout_f:
                with open(stderr_file, "w") as stderr_f:
                    proc = subprocess.Popen(
                        command,
                        shell=True,
                        cwd=cwd,
                        stdout=stdout_f,
                        stderr=stderr_f,
                        env=env,
                        start_new_session=True,
                    )

            process_info = {
                "pid": pid,
                "label": label,
                "real_pid": proc.pid,
                "command": command,
                "cwd": str(cwd) if cwd else os.getcwd(),
                "stdout": str(stdout_file),
                "stderr": str(stderr_file),
                "status": "running",
            }
        else:
            # Attached (capture output)
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )

            process_info = {
                "pid": pid,
                "label": label,
                "real_pid": proc.pid,
                "command": command,
                "cwd": str(cwd) if cwd else os.getcwd(),
                "stdout": str(stdout_file),
                "stderr": str(stderr_file),
                "status": "running",
                "attached": True,
            }

        _PROCESS_REGISTRY[pid] = process_info

        return (
            f"[OK] Process started: {label} (PID: {pid}, real PID: {proc.pid})\n"
            f"Output: {stdout_file}\n"
            f"Stderr: {stderr_file}\n"
            f"Status: running"
        )

    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {str(e)}"


@tool
def process_status_tool(
    pid: Annotated[str, "Process ID to check."],
) -> Annotated[str, "Process status and information, or error message."]:
    """Check status of a background process.

    Args:
        pid: Process ID returned from process_run_tool.

    Returns:
        Process status, or error if not found.
    """
    if pid not in _PROCESS_REGISTRY:
        return f"[ERROR] Process not found: {pid}"

    info = _PROCESS_REGISTRY[pid]

    # Check if real process is still alive
    try:
        real_pid = info.get("real_pid")
        if real_pid:
            os.kill(real_pid, 0)  # Signal 0 just checks existence
        info["status"] = "running"
    except OSError:
        info["status"] = "finished"

    # Read output if exists
    stdout_file = info.get("stdout")
    stderr_file = info.get("stderr")
    stdout_content = ""
    stderr_content = ""

    if stdout_file and Path(stdout_file).exists():
        with open(stdout_file, "r", errors="replace") as f:
            stdout_content = f.read(2000)
    if stderr_file and Path(stderr_file).exists():
        with open(stderr_file, "r", errors="replace") as f:
            stderr_content = f.read(500)

    return (
        f"[OK] Process: {info['label']} (PID: {pid})\n"
        f"Real PID: {info.get('real_pid', 'unknown')}\n"
        f"Status: {info['status']}\n"
        f"Command: {info['command']}\n"
        f"Working Dir: {info['cwd']}\n"
        f"--- Last stdout (2000 chars) ---\n{stdout_content}\n"
        f"--- Last stderr (500 chars) ---\n{stderr_content}"
    )


@tool
def process_list_tool() -> Annotated[str, "List of all managed background processes."]:
    """List all background processes started by this tool.

    Returns:
        List of all processes with their status.
    """
    if not _PROCESS_REGISTRY:
        return "[OK] No background processes"

    lines = []
    for pid, info in _PROCESS_REGISTRY.items():
        # Check alive status
        try:
            real_pid = info.get("real_pid")
            if real_pid:
                os.kill(real_pid, 0)
            status = "running"
        except OSError:
            status = "finished"

        lines.append(
            f"{pid} | {info['label']} | {status} | {info['command'][:50]}..."
        )

    return "[OK] Background processes:\n" + "\n".join(lines)