"""blob_tool: Handle binary or large file operations.

Used by LLM agent to inspect large files, binary data, or export specific chunks.
"""

import os
import base64
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool


@tool
def blob_tool(
    path: Annotated[str, "Absolute or relative path to the file."],
    operation: Annotated[str, "Operation: 'head' (first lines), 'tail' (last lines), 'size' (file size), 'exists' (check existence), 'encoding' (detect encoding), 'b64' (base64 encode)."],
    limit: Annotated[int, "Number of lines (head/tail) or bytes (b64) to read. Default 100."] = 100,
    offset: Annotated[int, "Byte offset for b64 encoding. Default 0."] = 0,
) -> Annotated[str, "Result of the operation or error message."]:
    """Perform operations on binary or large files.

    Use this tool to inspect large files, get file metadata, or encode binary content.
    Safer than read_tool for very large files or binary data.

    Args:
        path: Path to file.
        operation: Operation to perform.
            - 'head': Read first N lines (default 100).
            - 'tail': Read last N lines (default 100).
            - 'size': Get file size in bytes.
            - 'exists': Check if file exists and get metadata.
            - 'encoding': Detect text encoding.
            - 'b64': Base64 encode file content (limited by offset/limit).
        limit: Number of lines (head/tail) or bytes (b64) to process.
        offset: Byte offset for b64 operation.

    Returns:
        Result of operation or error message.

    Example:
        blob_tool(path="data/large_file.json", operation="size")
        blob_tool(path="logs/app.log", operation="tail", limit=50)
        blob_tool(path="images/photo.png", operation="b64", limit=1024)
        blob_tool(path="data.bin", operation="exists")
    """
    try:
        file_path = Path(path).expanduser().resolve()

        # Security: allow current working directory and temp directories only
        safe_dirs = [os.getcwd(), "/tmp", "/var/tmp"]
        if not any(str(file_path).startswith(d) for d in safe_dirs):
            return f"[ERROR] Access denied: path '{path}' is outside allowed directory"

        if not file_path.exists():
            return f"[ERROR] File not found: {path}"

        if operation == "exists":
            size = file_path.stat().st_size
            modified = file_path.stat().st_mtime
            return f"[OK] File exists: {path} ({size} bytes, modified {modified})"

        elif operation == "size":
            size = file_path.stat().st_size
            mb = size / (1024 * 1024)
            return f"[OK] {path}: {size} bytes ({mb:.2f} MB)"

        elif operation == "head":
            if not file_path.is_file():
                return f"[ERROR] Not a file: {path}"
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= limit:
                        break
                    lines.append(line.rstrip())
            result = "\n".join(lines[:limit])
            result += f"\n... [{limit} lines shown]"
            return result

        elif operation == "tail":
            if not file_path.is_file():
                return f"[ERROR] Not a file: {path}"
            # Efficient tail reading
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            tail_lines = lines[-limit:] if len(lines) > limit else lines
            result = "".join(line.rstrip() for line in tail_lines)
            result += f"\n... [{len(tail_lines)} lines shown]"
            return result

        elif operation == "encoding":
            # Detect encoding by reading first few KB
            with open(file_path, "rb") as f:
                raw = f.read(8192)
            # Try common encodings
            for enc in ["utf-8", "utf-16", "latin-1", "gbk", "shift_jis"]:
                try:
                    raw.decode(enc)
                    return f"[OK] Detected encoding: {enc}"
                except UnicodeDecodeError:
                    continue
            return "[WARN] Could not detect encoding, assuming utf-8"

        elif operation == "b64":
            # Base64 encode part of the file
            with open(file_path, "rb") as f:
                f.seek(offset)
                data = f.read(limit)
            encoded = base64.b64encode(data).decode("ascii")
            return f"[OK] Base64 ({len(data)} bytes -> {len(encoded)} chars):\n{encoded[:200]}..."

        else:
            return f"[ERROR] Unknown operation: '{operation}'. Use: head, tail, size, exists, encoding, b64"

    except PermissionError:
        return f"[ERROR] Permission denied: {path}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {str(e)}"