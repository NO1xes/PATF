"""exec_tool: Execute shell commands and return output.

Used by LLM agent to run system commands for profiling, analysis, and diagnostics.
"""

import subprocess
from typing import Annotated

from langchain_core.tools import tool

from agentprof.tools.generic.utils import sanitize_command, build_env


@tool
def exec_tool(
    command: Annotated[str, "The shell command to execute."],
    cwd: Annotated[str | None, "Working directory for the command. None uses current directory."] = None,
    timeout: Annotated[int, "Timeout in seconds. 0 means no timeout."] = 30,
    check: Annotated[bool, "If True, raise exception on non-zero exit code."] = False,
) -> Annotated[str, "Command output (stdout/stderr combined). Error details if failed."]:
    """Execute a shell command and return its output.

    Use this tool to run system commands, scripts, or any shell operations.
    The command runs in a sandboxed environment with limited permissions.

    Args:
        command: The shell command to execute (will be validated for safety).
        cwd: Working directory. None uses the current working directory.
        timeout: Maximum execution time in seconds. 0 = no limit.
        check: If True, raises ValueError on non-zero exit code.

    Returns:
        Combined stdout/stderr output, or error message if command fails.

    Example:
        exec_tool(command="ls -la")
        exec_tool(command="pytest tests/ -x -q", timeout=120)
        exec_tool(command="ps aux | grep python")
    """
    # Sanitize command for safety
    safe_command = sanitize_command(command)

    env = build_env()

    try:
        result = subprocess.run(
            safe_command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout if timeout > 0 else None,
            env=env,
        )

        output = result.stdout
        if result.stderr:
            output += "\n--- stderr ---\n" + result.stderr

        if check and result.returncode != 0:
            raise ValueError(
                f"Command failed with exit code {result.returncode}:\n{output}"
            )

        return output if output else "(no output)"

    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] Command exceeded {timeout} seconds"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {str(e)}"