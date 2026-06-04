"""read_tool: Read file contents with optional line limits.

Used by LLM agent to inspect files, logs, configurations, and code.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool


@tool
def read_tool(
    path: Annotated[str, "Absolute or relative path to the file to read."],
    offset: Annotated[int, "Line offset to start reading from (0-indexed). Default 0."] = 0,
    limit: Annotated[int | None, "Maximum number of lines to read. None means no limit."] = None,
    encoding: Annotated[str, "File encoding. Default 'utf-8'."] = "utf-8",
) -> Annotated[str, "File contents or error message."]:
    """Read the contents of a file.

    Use this tool to read source code, configuration files, logs, or any text content.
    Supports line offset and limit for reading large files in chunks.

    Args:
        path: Path to file. Supports both absolute and relative paths.
        offset: Starting line number (0-indexed). Default 0.
        limit: Maximum number of lines to read. None reads entire file.
        encoding: Text encoding. Default utf-8.

    Returns:
        File contents up to limit, or error message if file cannot be read.

    Example:
        read_tool(path="README.md")
        read_tool(path="profiles/run_xxx/report.md", offset=10, limit=50)
        read_tool(path="logs/app.log", limit=100)  # last 100 lines
    """
    try:
        file_path = Path(path).expanduser().resolve()

        # Security: allow common safe directories
        # Security: allow current working directory and temp directories only
        safe_dirs = [os.getcwd(), "/tmp", "/var/tmp"]
        if not any(str(file_path).startswith(d) for d in safe_dirs):
            return f"[ERROR] Access denied: path '{path}' is outside allowed directories"

        if not file_path.exists():
            return f"[ERROR] File not found: {path}"

        if not file_path.is_file():
            return f"[ERROR] Not a file: {path}"

        # Check file size (max 100MB)
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > 100:
            return f"[ERROR] File too large: {size_mb:.1f}MB (max 100MB). Use blob_tool for large files."

        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            lines = f.readlines()

        # Apply offset
        if offset > 0:
            if offset >= len(lines):
                return "[ERROR] Offset exceeds file length"
            lines = lines[offset:]

        # Apply limit
        if limit is not None:
            lines = lines[:limit]

        content = "".join(lines)

        result = f"=== {path} (lines {offset}-{offset + len(lines) - 1}) ===\n{content}"

        # Add truncation indicator if file was truncated
        remaining = len(lines) if limit is None else (len(lines) - limit if len(lines) > limit else 0)
        total_lines = offset + len(lines)
        if offset == 0 and limit is not None and len(lines) == limit:
            result += f"\n... [{len(lines)} lines shown, use offset={total_lines} to read more]"

        return result

    except PermissionError:
        return f"[ERROR] Permission denied: {path}"
    except UnicodeDecodeError:
        return f"[ERROR] Cannot decode file as {encoding}. Use binary mode or different encoding."
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {str(e)}"