"""write_tool: Write content to files with create/overwrite/append modes.

Used by LLM agent to save analysis results, reports, and generated content.
"""

import os
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool


@tool
def write_tool(
    path: Annotated[str, "Absolute or relative path to the file to write."],
    content: Annotated[str, "Content to write to the file."],
    mode: Annotated[str, "Write mode: 'overwrite' (default), 'append', 'create'."] = "overwrite",
    encoding: Annotated[str, "File encoding. Default 'utf-8'."] = "utf-8",
) -> Annotated[str, "Success message with bytes written, or error message."]:
    """Write content to a file.

    Use this tool to save reports, analysis results, logs, or any generated content.
    Supports three modes: overwrite (replace content), append (add to end), create (new file only).

    Args:
        path: Path to file. Supports both absolute and relative paths.
        content: Content to write. Can be multi-line text.
        mode: Write mode.
            - 'overwrite': Replace existing file or create new (default).
            - 'append': Add content to end of existing file.
            - 'create': Create new file only; fails if file exists.
        encoding: Text encoding. Default utf-8.

    Returns:
        Success message with bytes written, or error message.

    Example:
        write_tool(path="output/result.txt", content="Analysis complete")
        write_tool(path="logs/app.log", content="New entry\\n", mode="append")
        write_tool(path="report.md", content="# Report\\n\\nResults...", mode="overwrite")
    """
    try:
        file_path = Path(path).expanduser().resolve()

        # Security: allow current working directory and temp directories only
        safe_dirs = [os.getcwd(), "/tmp", "/var/tmp"]
        if not any(str(file_path).startswith(d) for d in safe_dirs):
            return f"[ERROR] Access denied: cannot write to '{path}' outside allowed directories"

        # Create parent directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle mode
        if mode == "create":
            if file_path.exists():
                return f"[ERROR] File already exists: {path}. Use 'overwrite' to replace."
            file_path.touch(exist_ok=False)
        elif mode == "append":
            if not file_path.exists():
                # Append to non-existing file = create + write
                pass
        elif mode != "overwrite":
            return f"[ERROR] Invalid mode: '{mode}'. Use 'overwrite', 'append', or 'create'."

        # Write content
        write_mode = "a" if mode == "append" else "w"
        with open(file_path, write_mode, encoding=encoding) as f:
            bytes_written = f.write(content)
            f.flush()
            os.fsync(f.fileno())

        return f"[OK] Written {bytes_written} bytes to {path}"

    except FileExistsError:
        return f"[ERROR] File already exists: {path}. Use mode='overwrite' or 'append'."
    except PermissionError:
        return f"[ERROR] Permission denied: {path}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {str(e)}"