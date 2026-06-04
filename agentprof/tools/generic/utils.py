"""Utility functions for generic tools.

Provides safety checks and environment setup for shell operations.
"""

import os
import re
from typing import Any


# Commands that are explicitly blocked for security
BLOCKED_PATTERNS = [
    r"rm\s+-rf\s+/",           # rm -rf / (dangerous)
    r"rm\s+-rf\s+\*",          # rm -rf * (dangerous)
    r"mkfs\b",                 # mkfs (destroy filesystem)
    r"dd\s+if=",               # dd with if (disk write)
    r":\(\)\{",                # Fork bomb pattern
    r"curl.*\|\s*sh",          # pipe curl to shell
    r"wget.*\|\s*sh",          # pipe wget to shell
]


def sanitize_command(command: str) -> str:
    """Validate and sanitize shell command.

    Args:
        command: Raw command string.

    Returns:
        Sanitized command string.

    Raises:
        ValueError: If command contains dangerous patterns.
    """
    if not command or not command.strip():
        raise ValueError("Empty command not allowed")

    # Check for blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command):
            raise ValueError(f"Command contains blocked pattern: {pattern}")

    # Limit command length to prevent abuse
    if len(command) > 10000:
        raise ValueError("Command too long (max 10000 chars)")

    return command


def build_env() -> dict[str, str]:
    """Build sanitized environment variables for subprocess.

    Returns:
        Dictionary of environment variables with minimal access.
    """
    # Start with current environment (filtered)
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
    }

    # Carry over safe variables
    safe_vars = ["AGENTPROF_PROFILE_DIR", "AGENTPROF_MACHINE", "VLLM_BASE_URL"]
    for key in safe_vars:
        if key in os.environ:
            env[key] = os.environ[key]

    return env


def parse_size_string(size_str: str) -> int:
    """Parse size string like '100KB', '5MB', '1GB' to bytes.

    Args:
        size_str: Size string (e.g., "100KB", "5MB", "1GB").

    Returns:
        Size in bytes.
    """
    units = {
        "B": 1,
        "KB": 1024,
        "MB": 1024 ** 2,
        "GB": 1024 ** 3,
        "TB": 1024 ** 4,
    }

    size_str = size_str.upper().strip()
    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            try:
                number = float(size_str[:-len(unit)])
                return int(number * multiplier)
            except ValueError:
                pass

    # Try parsing as plain number
    try:
        return int(size_str)
    except ValueError:
        return 0


def format_output(output: str, max_lines: int = 100, max_bytes: int = 50000) -> str:
    """Format command output to prevent overflow.

    Args:
        output: Raw output string.
        max_lines: Maximum lines to return.
        max_bytes: Maximum bytes to return.

    Returns:
        Truncated output with indicator if truncated.
    """
    lines = output.splitlines()
    if len(lines) > max_lines:
        output = "\n".join(lines[:max_lines])
        output += f"\n... [{len(lines) - max_lines} more lines truncated]"

    if len(output.encode()) > max_bytes:
        output = output[:max_bytes]
        output += f"\n... [output truncated at {max_bytes} bytes]"

    return output