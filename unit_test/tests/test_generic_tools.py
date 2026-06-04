"""Unit tests for generic tools."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from agentprof.tools.generic import (
    exec_tool,
    read_tool,
    write_tool,
    grep_tool,
    blob_tool,
    ls_tool,
    system_info_tool,
    system_info_processes_tool,
    system_monitor_tool,
    process_run_tool,
    process_status_tool,
    process_list_tool,
)


class TestExecTool:
    """Tests for exec_tool."""

    def test_simple_command(self):
        result = exec_tool.invoke({"command": "echo hello"})
        assert "hello" in result

    def test_command_with_pipe(self):
        result = exec_tool.invoke({"command": "echo 'line1\\nline2' | head -1"})
        assert "line1" in result

    def test_nonexistent_command(self):
        result = exec_tool.invoke({"command": "nonexistent_cmd_xyz"})
        assert "[ERROR]" in result or "not found" in result.lower()

    def test_blocked_dangerous_command(self):
        with pytest.raises(ValueError, match="blocked pattern"):
            exec_tool.invoke({"command": "rm -rf /"})

    def test_timeout(self):
        result = exec_tool.invoke({"command": "sleep 10", "timeout": 1})
        assert "[TIMEOUT]" in result

    def test_check_mode_success(self):
        result = exec_tool.invoke({"command": "echo test", "check": False})
        assert "test" in result


class TestReadTool:
    """Tests for read_tool."""

    def test_read_file(self):
        # Create temp file
        fd, path = tempfile.mkstemp()
        try:
            os.write(fd, b"Line 1\nLine 2\nLine 3\n")
            os.close(fd)

            result = read_tool.invoke({"path": path})
            assert "Line 1" in result
            assert "Line 2" in result
        finally:
            os.unlink(path)

    def test_read_with_offset(self):
        fd, path = tempfile.mkstemp()
        try:
            os.write(fd, b"Line 1\nLine 2\nLine 3\n")
            os.close(fd)

            result = read_tool.invoke({"path": path, "offset": 1, "limit": 1})
            assert "Line 2" in result
        finally:
            os.unlink(path)

    def test_nonexistent_file(self):
        result = read_tool.invoke({"path": "/nonexistent/file_xyz.txt"})
        assert "[ERROR]" in result

    def test_outside_allowed_directory(self):
        result = read_tool.invoke({"path": "/etc/passwd"})
        assert "[ERROR]" in result or "Access denied" in result


class TestWriteTool:
    """Tests for write_tool."""

    def test_write_new_file(self):
        path = tempfile.mktemp(suffix=".txt")
        result = write_tool.invoke({"path": path, "content": "Hello World"})
        assert "[OK]" in result

        # Verify content
        with open(path) as f:
            assert f.read() == "Hello World"
        os.unlink(path)

    def test_overwrite_existing_file(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, b"Original")
        os.close(fd)

        result = write_tool.invoke({"path": path, "content": "New Content", "mode": "overwrite"})
        assert "[OK]" in result

        with open(path) as f:
            assert f.read() == "New Content"
        os.unlink(path)

    def test_append_to_file(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, b"Line 1\n")
        os.close(fd)

        result = write_tool.invoke({"path": path, "content": "Line 2\n", "mode": "append"})
        assert "[OK]" in result

        with open(path) as f:
            content = f.read()
        assert "Line 1" in content
        assert "Line 2" in content
        os.unlink(path)

    def test_create_mode_existing_file_fails(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, b"Existing")
        os.close(fd)

        result = write_tool.invoke({"path": path, "content": "New", "mode": "create"})
        assert "[ERROR]" in result
        os.unlink(path)

    def test_write_outside_allowed_directory(self):
        result = write_tool.invoke({"path": "/etc/test.txt", "content": "test"})
        assert "[ERROR]" in result


class TestGrepTool:
    """Tests for grep_tool."""

    def test_simple_pattern(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, b"def hello():\n    pass\ndef world():\n    pass\n")
        os.close(fd)

        result = grep_tool.invoke({"pattern": "def\\s+\\w+", "path": path})
        assert "hello" in result
        assert "world" in result
        os.unlink(path)

    def test_case_insensitive(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, b"HELLO\nhello\nHeLLo\n")
        os.close(fd)

        result = grep_tool.invoke({"pattern": "hello", "path": path, "case_sensitive": False})
        assert "HELLO" in result
        assert "hello" in result
        assert "HeLLo" in result
        os.unlink(path)

    def test_no_matches(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, b"hello world\n")
        os.close(fd)

        result = grep_tool.invoke({"pattern": "xyz123", "path": path})
        assert "No matches found" in result
        os.unlink(path)

    def test_nonexistent_file(self):
        result = grep_tool.invoke({"pattern": "test", "path": "/nonexistent/file.txt"})
        assert "[ERROR]" in result


class TestBlobTool:
    """Tests for blob_tool."""

    def test_size_operation(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, b"Hello World!")
        os.close(fd)

        result = blob_tool.invoke({"path": path, "operation": "size"})
        assert "[OK]" in result
        assert "bytes" in result
        os.unlink(path)

    def test_head_operation(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, b"Line 1\nLine 2\nLine 3\n")
        os.close(fd)

        result = blob_tool.invoke({"path": path, "operation": "head", "limit": 2})
        assert "Line 1" in result
        assert "Line 2" in result
        os.unlink(path)

    def test_tail_operation(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, b"Line 1\nLine 2\nLine 3\n")
        os.close(fd)

        result = blob_tool.invoke({"path": path, "operation": "tail", "limit": 2})
        assert "Line 2" in result
        assert "Line 3" in result
        os.unlink(path)

    def test_exists_operation(self):
        fd, path = tempfile.mkstemp()
        os.write(fd, b"test")
        os.close(fd)

        result = blob_tool.invoke({"path": path, "operation": "exists"})
        assert "[OK]" in result
        assert "bytes" in result
        os.unlink(path)

    def test_nonexistent_file(self):
        result = blob_tool.invoke({"path": "/nonexistent/file.txt", "operation": "size"})
        assert "[ERROR]" in result


class TestLsTool:
    """Tests for ls_tool."""

    def test_list_directory(self):
        result = ls_tool.invoke({"path": "/tmp", "max_items": 5, "long_format": True})
        assert "Total:" in result

    def test_nonexistent_directory(self):
        result = ls_tool.invoke({"path": "/nonexistent/directory_xyz"})
        assert "[ERROR]" in result


class TestSystemInfoTool:
    """Tests for system_info_tool."""

    def test_get_cpu_info(self):
        result = system_info_tool.invoke({"metrics": ["cpu"]})
        assert "=== CPU ===" in result
        assert "Logical CPUs:" in result

    def test_get_memory_info(self):
        result = system_info_tool.invoke({"metrics": ["memory"]})
        assert "=== Memory ===" in result
        assert "RAM:" in result

    def test_get_all_metrics(self):
        result = system_info_tool.invoke({"metrics": ["all"]})
        assert "=== CPU ===" in result
        assert "=== Memory ===" in result


class TestSystemInfoProcessesTool:
    """Tests for system_info_processes_tool."""

    def test_get_top_processes(self):
        result = system_info_processes_tool.invoke({"limit": 5, "sort_by": "cpu"})
        assert "=== Top Processes ===" in result


class TestSystemMonitorTool:
    """Tests for system_monitor_tool."""

    def test_start_monitoring(self):
        result = system_monitor_tool.invoke({
            "action": "start",
            "monitor_id": "test_monitor_unit",
            "duration": 2,
            "interval": 0.5,
        })
        assert "[OK]" in result
        assert "started" in result.lower()

    def test_get_status(self):
        # Start a monitor
        system_monitor_tool.invoke({
            "action": "start",
            "monitor_id": "test_status_unit",
            "duration": 5,
            "interval": 0.5,
        })

        # Get status
        result = system_monitor_tool.invoke({"action": "status", "monitor_id": "test_status_unit"})
        assert "[OK]" in result
        assert "Status:" in result

    def test_get_records_after_completion(self):
        # Start a short monitor
        system_monitor_tool.invoke({
            "action": "start",
            "monitor_id": "test_get_unit",
            "duration": 1,
            "interval": 0.2,
        })

        # Wait for completion
        time.sleep(2)

        # Get records
        result = system_monitor_tool.invoke({"action": "get", "monitor_id": "test_get_unit"})
        assert "=== System Monitor Records" in result
        assert "cpu_percent" in result
        assert "memory_percent" in result

    def test_stop_monitoring(self):
        # Start a monitor
        system_monitor_tool.invoke({
            "action": "start",
            "monitor_id": "test_stop_unit",
            "duration": 10,
            "interval": 0.5,
        })

        # Stop it
        result = system_monitor_tool.invoke({"action": "stop", "monitor_id": "test_stop_unit"})
        assert "[OK]" in result
        assert "stopped" in result.lower()

    def test_monitor_not_found(self):
        result = system_monitor_tool.invoke({"action": "status", "monitor_id": "nonexistent_monitor"})
        assert "[ERROR]" in result


class TestProcessTools:
    """Tests for process_run_tool, process_status_tool, process_list_tool."""

    def test_run_background_process(self):
        result = process_run_tool.invoke({
            "command": "sleep 3 && echo done",
            "label": "test_process_unit",
        })
        assert "[OK]" in result
        assert "Process started" in result

    def test_list_processes(self):
        # Run a process first
        process_run_tool.invoke({
            "command": "sleep 5",
            "label": "test_list_unit",
        })

        result = process_list_tool.invoke({})
        assert "[OK]" in result
        assert "test_list_unit" in result

    def test_status_nonexistent_process(self):
        result = process_status_tool.invoke({"pid": "nonexistent_pid_xyz"})
        assert "[ERROR]" in result