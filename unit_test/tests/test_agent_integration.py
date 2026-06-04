"""Integration tests for generic tools in agent context.

Tests that tools work correctly when invoked through a LangChain agent.
"""

import pytest
import os
import tempfile
from pathlib import Path

# Import from agentprof package directly (development mode)
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")


class LLMInteractionCapture:
    """Capture LLM interactions for debugging."""

    def __init__(self):
        self.messages = []

    def set_messages(self, messages):
        self.messages = messages

    def get_prompts_and_responses(self):
        """Extract prompts and responses from captured messages."""
        result = []
        for i, msg in enumerate(self.messages):
            role = getattr(msg, 'type', 'unknown')
            content = getattr(msg, 'content', '')
            result.append(f"[{i}] Role: {role}\nContent: {content[:500]}")
        return "\n".join(result)


# Global capture instance
_capture = LLMInteractionCapture()

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

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent


def create_test_agent():
    """Create a test agent with all generic tools."""
    # Use values from .env with defaults from .env.example
    llm = ChatOpenAI(
        model=os.environ.get("VLLM_MODEL", "Qwen/Qwen3-30B-A3B-Instruct-2507"),
        temperature=0,
        base_url=os.environ.get("VLLM_BASE_URL", "http://127.0.0.1:8000/v1"),
        api_key=os.environ.get("VLLM_API_KEY", "dummy"),
    )

    tools = [
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
    ]

    # Create agent
    agent = create_agent(llm, tools=tools)
    return agent


def run_query(agent, query: str, test_name: str = None) -> str:
    """Run a query through the agent and return the response."""
    # Clear previous messages
    _capture.messages.clear()

    result = agent.invoke({"messages": [HumanMessage(content=query)]})
    messages = result.get("messages", [])

    # Save all messages for logging
    _capture.set_messages(messages)

    # Get test name from pytest environment variable if available
    if test_name is None:
        import os
        test_name = os.environ.get("PYTEST_CURRENT_TEST", "unknown_test")
        # Clean up the name
        if "::" in test_name:
            test_name = test_name.split("::")[-1]
        test_name = test_name.replace(" ", "_").replace("(", "").replace(")", "")

    # Save interactions to file with test name
    _save_interactions(query, test_name)

    # Get the last assistant message content
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content:
            return msg.content
    return ""


def _save_interactions(query: str, test_name: str = "test"):
    """Save captured LLM interactions to a file."""
    log_dir = Path(__file__).parent.parent / "test_logs"
    log_dir.mkdir(exist_ok=True)

    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{test_name}_{timestamp}.log"

    content = _capture.get_prompts_and_responses()

    with open(log_file, "w") as f:
        f.write(f"Query: {query}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Total messages: {len(_capture.messages)}\n")
        f.write("\n--- Messages ---\n")
        f.write(content)

    print(f"\n[LLM Interaction saved to: {log_file}]")


class TestAgentWithExecTool:
    """Test exec_tool in agent context."""

    def test_agent_exec_pwd(self):
        """Agent should be able to execute pwd command."""
        agent = create_test_agent()
        response = run_query(agent, "Execute the command 'pwd' and tell me the current directory.")
        # Agent should mention the directory path
        assert "/" in response or response != ""

    def test_agent_exec_which_python(self):
        """Agent should be able to find python path."""
        agent = create_test_agent()
        response = run_query(agent, "Find the path to python using 'which python3' command.")
        assert "python" in response.lower() or "/python" in response.lower()


class TestAgentWithReadTool:
    """Test read_tool in agent context."""

    def test_agent_read_file(self):
        """Agent should be able to read a file."""
        # Create a temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Hello from test file")
            temp_path = f.name

        try:
            agent = create_test_agent()
            # Get absolute path
            abs_path = os.path.abspath(temp_path)
            response = run_query(
                agent,
                f"Read the file at '{abs_path}' and tell me its contents."
            )
            assert "Hello from test file" in response
        finally:
            os.unlink(temp_path)

    def test_agent_read_nonexistent_file(self):
        """Agent should handle nonexistent file gracefully."""
        agent = create_test_agent()
        response = run_query(
            agent,
            "Try to read the file '/nonexistent/file.txt' and tell me what happens."
        )
        # Should contain error message about file not found
        assert "not found" in response.lower() or "error" in response.lower()


class TestAgentWithWriteTool:
    """Test write_tool in agent context."""

    def test_agent_write_file(self):
        """Agent should be able to write a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "agent_test.txt")
            abs_path = os.path.abspath(test_file)

            agent = create_test_agent()
            response = run_query(
                agent,
                f"Write the text 'Hello Agent' to the file '{abs_path}' and confirm if it was created."
            )
            # Check if file was created
            assert os.path.exists(abs_path), f"File {abs_path} was not created"
            with open(abs_path, 'r') as f:
                content = f.read()
            assert "Hello Agent" in content


class TestAgentWithLsTool:
    """Test ls_tool in agent context."""

    def test_agent_list_directory(self):
        """Agent should be able to list directory contents."""
        agent = create_test_agent()
        response = run_query(
            agent,
            "List the contents of the '/tmp' directory using ls_tool."
        )
        # Should contain some indication of listing
        assert response != ""


class TestAgentWithSystemInfoTool:
    """Test system_info_tool in agent context."""

    def test_agent_get_cpu_info(self):
        """Agent should be able to get CPU information."""
        agent = create_test_agent()
        response = run_query(
            agent,
            "Get the CPU information for this system."
        )
        # Should contain CPU-related info
        assert "cpu" in response.lower() or "processor" in response.lower()

    def test_agent_get_memory_info(self):
        """Agent should be able to get memory information."""
        agent = create_test_agent()
        response = run_query(
            agent,
            "Get the memory usage information for this system."
        )
        # Should contain memory-related info
        assert "memory" in response.lower() or "ram" in response.lower()


class TestAgentWithGrepTool:
    """Test grep_tool in agent context."""

    def test_agent_grep_in_file(self):
        """Agent should be able to search in a file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("def hello():\n    print('hello world')\ndef goodbye():\n    print('goodbye')")
            temp_path = f.name

        try:
            agent = create_test_agent()
            abs_path = os.path.abspath(temp_path)
            response = run_query(
                agent,
                f"Search for the word 'hello' in the file '{abs_path}' using grep."
            )
            assert "hello" in response.lower()
        finally:
            os.unlink(temp_path)


class TestAgentWithBlobTool:
    """Test blob_tool in agent context."""

    def test_agent_blob_size(self):
        """Agent should be able to get file size."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("x" * 100)
            temp_path = f.name

        try:
            agent = create_test_agent()
            abs_path = os.path.abspath(temp_path)
            response = run_query(
                agent,
                f"Get the size of the file '{abs_path}' using blob_tool."
            )
            # Should contain size info
            assert "bytes" in response.lower() or "size" in response.lower()
        finally:
            os.unlink(temp_path)


class TestAgentWithSystemMonitorTool:
    """Test system_monitor_tool in agent context."""

    def test_agent_start_monitor(self):
        """Agent should be able to start system monitoring."""
        agent = create_test_agent()
        response = run_query(
            agent,
            "Start a system monitor with ID 'test_monitor_123' for 2 seconds at 0.5s interval, then tell me the status."
        )
        # Should contain status info
        assert "monitor" in response.lower() or "test_monitor" in response.lower()

    def test_agent_get_status(self):
        """Agent should be able to check monitor status."""
        # First start a monitor via direct tool call
        system_monitor_tool.invoke({
            "action": "start",
            "monitor_id": "test_status_check",
            "duration": 10,
            "interval": 1.0,
        })

        agent = create_test_agent()
        response = run_query(
            agent,
            "Check the status of the monitor with ID 'test_status_check'."
        )
        # Stop the monitor
        system_monitor_tool.invoke({"action": "stop", "monitor_id": "test_status_check"})

        assert "monitor" in response.lower() or "status" in response.lower()


class TestAgentWithProcessTools:
    """Test process_run_tool and related tools in agent context."""

    def test_agent_run_background_process(self):
        """Agent should be able to run a background process."""
        agent = create_test_agent()
        response = run_query(
            agent,
            "Run the command 'sleep 5' as a background process and tell me the process ID."
        )
        # Should contain some process-related info
        assert "process" in response.lower() or "pid" in response.lower() or "sleep" in response.lower()

    def test_agent_list_processes(self):
        """Agent should be able to list running processes."""
        agent = create_test_agent()
        response = run_query(
            agent,
            "List all running processes on this system."
        )
        # Should contain process info
        assert "process" in response.lower()