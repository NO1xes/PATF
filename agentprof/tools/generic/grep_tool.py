"""grep_tool: Search for patterns within files.

Used by LLM agent to search code, logs, and documents for specific content.
"""

import os
import re
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool


@tool
def grep_tool(
    pattern: Annotated[str, "Regular expression pattern to search for."],
    path: Annotated[str, "File or directory path to search in."],
    recursive: Annotated[bool, "Search recursively in subdirectories."] = False,
    case_sensitive: Annotated[bool, "Case sensitive matching."] = True,
    context_lines: Annotated[int, "Number of lines before/after match to show."] = 0,
    max_results: Annotated[int, "Maximum number of matching lines to return. 0 means no limit."] = 100,
    file_pattern: Annotated[str | None, "File name pattern to match (e.g., '*.py', '*.log'). None searches all files."] = None,
) -> Annotated[str, "Matching lines with context, or 'No matches'."]:
    """Search for a regular expression pattern in files or directories.

    Use this tool to find specific content in code, logs, or documents.
    Supports regular expressions, case sensitivity, and context display.

    Args:
        pattern: Regular expression pattern to search for.
        path: File or directory path to search. Use '.' for current directory.
        recursive: If True, search recursively in all subdirectories.
        case_sensitive: If True, match is case-sensitive. Default True.
        context_lines: Number of lines before/after match to include. Default 0.
        max_results: Maximum number of matching lines. 0 = no limit. Default 100.
        file_pattern: Glob pattern for files to search (e.g., "*.py", "*.log"). None searches all files.

    Returns:
        Matching lines with file:line:content format and context, or "No matches found".

    Example:
        grep_tool(pattern="def main", path="src/")
        grep_tool(pattern="ERROR", path="logs/app.log", context_lines=2)
        grep_tool(pattern="class\\s+\\w+", path=".", recursive=True, file_pattern="*.py")
    """
    try:
        search_path = Path(path).expanduser().resolve()

        if not search_path.exists():
            return f"[ERROR] Path not found: {path}"

        # Build grep pattern
        regex_flags = 0 if case_sensitive else re.IGNORECASE
        try:
            compiled_pattern = re.compile(pattern, regex_flags)
        except re.error as e:
            return f"[ERROR] Invalid regex pattern: {e}"

        matches = []
        results_count = 0

        # Determine files to search
        if search_path.is_file():
            files_to_search = [search_path]
        elif search_path.is_dir():
            if recursive:
                files_to_search = []
                for root, dirs, files in os.walk(search_path):
                    # Skip hidden directories and common non-source dirs
                    dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('__pycache__', 'node_modules', '.git')]
                    for file in files:
                        if file_pattern is None or file.endswith(file_pattern.lstrip('*')):
                            files_to_search.append(Path(root) / file)
            else:
                if file_pattern:
                    files_to_search = [f for f in search_path.iterdir() if f.is_file() and f.name.endswith(file_pattern.lstrip('*'))]
                else:
                    files_to_search = [f for f in search_path.iterdir() if f.is_file()]
        else:
            return f"[ERROR] Path is neither file nor directory: {path}"

        # Search each file
        for file_path in files_to_search:
            if results_count >= max_results and max_results > 0:
                break

            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    if compiled_pattern.search(line):
                        if results_count >= max_results and max_results > 0:
                            break

                        # Build context window
                        if context_lines > 0:
                            start = max(0, line_num - context_lines - 1)
                            end = min(len(lines), line_num + context_lines)
                            context = "".join(f"{i}: {lines[i]}" for i in range(start, end))
                            matches.append(f"--- {file_path}:{line_num} ---\n{context}")
                        else:
                            matches.append(f"{file_path}:{line_num}:{line.rstrip()}")

                        results_count += 1

            except (PermissionError, UnicodeDecodeError, OSError):
                # Skip files that can't be read
                continue

        if not matches:
            return "No matches found"

        result = f"[OK] Found {results_count} match(es):\n\n"
        result += "\n".join(matches)

        if max_results > 0 and results_count >= max_results:
            result += f"\n... [max results {max_results} reached]"

        return result

    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {str(e)}"