from __future__ import annotations

import ast
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from strands import tool

WORKSPACE_ROOT = Path(
    os.getenv("WORKSPACE_ROOT", "/Users/tenonde/Projects/personal/multi-agent-strands")
)


@tool(description="Read the contents of a file from the workspace.")
def file_read(file_path: str) -> str:
    path = WORKSPACE_ROOT / file_path
    if not path.exists():
        return f"Error: File not found: {file_path}"
    if not path.is_file():
        return f"Error: Not a file: {file_path}"
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"


@tool(
    description="Write content to a file in the workspace. Creates parent directories if needed."
)
def file_write(file_path: str, content: str) -> str:
    path = WORKSPACE_ROOT / file_path
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file {file_path}: {str(e)}"


@tool(
    description="Edit a file by finding and replacing text. Returns error if pattern not found."
)
def editor(file_path: str, old_string: str, new_string: str) -> str:
    path = WORKSPACE_ROOT / file_path
    if not path.exists():
        return f"Error: File not found: {file_path}"
    try:
        content = path.read_text(encoding="utf-8")
        if old_string not in content:
            return f"Error: Pattern not found in {file_path}"
        new_content = content.replace(old_string, new_string, 1)
        path.write_text(new_content, encoding="utf-8")
        return f"Successfully edited {file_path}"
    except Exception as e:
        return f"Error editing file {file_path}: {str(e)}"


@tool(description="Execute a shell command and return the output.")
def shell(command: str, timeout: int = 60) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(WORKSPACE_ROOT),
        )
        output = f"Exit code: {result.returncode}\n"
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}\n"
        return output
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"


@tool(description="Execute Python code and return the output.")
def python_repl(code: str) -> str:
    try:
        tree = ast.parse(code)
        compiled = compile(tree, filename="<python_repl>")
        local_ns: dict[str, Any] = {}
        exec(compiled, local_ns)
        result_parts = []
        for key, value in local_ns.items():
            if not key.startswith("_"):
                result_parts.append(f"{key} = {repr(value)}")
        if result_parts:
            return "Variables:\n" + "\n".join(result_parts)
        return "Code executed successfully with no output"
    except SyntaxError as e:
        return f"Syntax Error: {str(e)}"
    except Exception as e:
        return f"Error executing code: {str(e)}"


@tool(description="Get the current datetime.")
def current_time() -> str:
    return datetime.now().isoformat()


strands_tools = [
    file_read,
    file_write,
    editor,
    shell,
    python_repl,
    current_time,
]

__all__ = [
    "strands_tools",
    "file_read",
    "file_write",
    "editor",
    "shell",
    "python_repl",
    "current_time",
]
