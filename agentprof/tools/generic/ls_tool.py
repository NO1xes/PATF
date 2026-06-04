"""ls_tool: List directory contents with detailed information.

Used by LLM agent to explore file system structure and find files.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool


@tool
def ls_tool(
    path: Annotated[str, "Directory path to list. Default '.' (current directory)."] = ".",
    show_hidden: Annotated[bool, "Show hidden files (starting with .)."] = False,
    long_format: Annotated[bool, "Use long format with details (size, date, permissions)."] = True,
    max_items: Annotated[int, "Maximum number of items to show. 0 means no limit."] = 100,
    sort_by: Annotated[str, "Sort by: 'name', 'size', 'modified'. Default 'name'."] = "name",
) -> Annotated[str, "Directory listing or error message."]:
    """List contents of a directory.

    Use this tool to explore directory structure, find files, or check directory contents.
    Supports filtering, sorting, and detailed output format.

    Args:
        path: Directory path. Default is current directory.
        show_hidden: If True, show files starting with '.'. Default False.
        long_format: If True, show size, modification date, and permissions. Default True.
        max_items: Maximum number of items to show. 0 = no limit. Default 100.
        sort_by: Sort order: 'name', 'size', 'modified'. Default 'name'.

    Returns:
        Directory listing with optional details, or error message.

    Example:
        ls_tool(path=".")
        ls_tool(path="/home/zyc/workspace/PATF/agentprof", show_hidden=False)
        ls_tool(path="profiles", long_format=True, sort_by="modified")
        ls_tool(path=".", show_hidden=True, max_items=50)
    """
    try:
        dir_path = Path(path).expanduser().resolve()

        if not dir_path.exists():
            return f"[ERROR] Path not found: {path}"

        if not dir_path.is_dir():
            return f"[ERROR] Not a directory: {path}"

        # List entries
        try:
            entries = list(dir_path.iterdir())
        except PermissionError:
            return f"[ERROR] Permission denied: {path}"

        # Filter hidden files
        if not show_hidden:
            entries = [e for e in entries if not e.name.startswith(".")]

        # Sort entries
        if sort_by == "size":
            entries = sorted(entries, key=lambda e: e.stat().st_size if e.exists() else 0)
        elif sort_by == "modified":
            entries = sorted(entries, key=lambda e: e.stat().st_mtime if e.exists() else 0)
        else:  # name
            entries = sorted(entries, key=lambda e: e.name.lower())

        # Apply limit
        if max_items > 0 and len(entries) > max_items:
            entries = entries[:max_items]

        # Format output
        if not long_format:
            names = [e.name + ("/" if e.is_dir() else "") for e in entries]
            result = "\n".join(names)
            if max_items > 0 and len(entries) >= max_items:
                result += f"\n... [{max_items} items shown, use max_items=0 for all]"
            return result

        # Long format
        lines = []
        total_size = 0
        for entry in entries:
            try:
                stat = entry.stat()
                size = stat.st_size
                total_size += size

                # File type indicator
                if entry.is_dir():
                    kind = "d"
                    size_str = "-"
                elif entry.is_symlink():
                    kind = "l"
                    size_str = "-"
                else:
                    kind = "-"
                    size_str = format_size(size)

                # Permissions
                mode = oct(stat.st_mode)[-3:]
                perms = "".join(["r" if i in [4, 5, 6, 7] else "-" for i in [int(c) for c in str(mode)[-3:]]])

                # Date
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

                # Name
                name = entry.name + ("/" if entry.is_dir() else "")

                lines.append(f"{kind}{perms}  {size_str:>8}  {mtime}  {name}")

            except (PermissionError, OSError):
                # Skip entries we can't stat
                continue

        result = "\n".join(lines)
        result += f"\n\nTotal: {len(entries)} items, {format_size(total_size)}"

        if max_items > 0 and len(entries) >= max_items:
            result += f"\n... [max items {max_items} reached]"

        return result

    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {str(e)}"


def format_size(size: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}PB"