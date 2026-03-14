import sys
import io
import traceback
import re
from typing import Any


# Blocked dangerous modules
BLOCKED_MODULES = [
    "os", "sys", "subprocess", "shutil", "socket",
    "requests", "urllib", "http", "ftplib", "smtplib",
    "pickle", "shelve", "importlib", "__import__",
    "open", "exec", "eval", "compile", "globals", "locals"
]


def is_safe_code(code: str) -> tuple[bool, str]:
    """
    Check if code is safe to execute.
    Returns (is_safe, reason)
    """
    code_lower = code.lower()

    dangerous_patterns = [
        (r"import\s+os", "os module not allowed"),
        (r"import\s+sys", "sys module not allowed"),
        (r"import\s+subprocess", "subprocess not allowed"),
        (r"import\s+shutil", "shutil not allowed"),
        (r"__import__", "__import__ not allowed"),
        (r"open\s*\(", "file open not allowed"),
        (r"exec\s*\(", "exec not allowed"),
        (r"eval\s*\(", "eval not allowed"),
        (r"import\s+socket", "socket not allowed"),
        (r"import\s+requests", "requests not allowed"),
    ]

    for pattern, reason in dangerous_patterns:
        if re.search(pattern, code_lower):
            return False, reason

    return True, "safe"


def execute_python(code: str) -> str:
    """
    Safely execute Python code in a sandboxed environment.
    Returns stdout output or error message.
    """
    # Safety check
    is_safe, reason = is_safe_code(code)
    if not is_safe:
        return f"Code blocked for safety: {reason}"

    # Capture stdout
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    try:
        # Safe builtins only
        safe_builtins = {
            "print": print,
            "len": len,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "round": round,
            "abs": abs,
            "max": max,
            "min": min,
            "sum": sum,
            "type": type,
            "isinstance": isinstance,
            "hasattr": hasattr,
            "getattr": getattr,
            "any": any,
            "all": all,
            "format": format,
        }

        # Available safe modules
        import math
        import json
        import re
        import statistics
        import datetime
        import pandas as pd
        import numpy as np

        safe_globals = {
            "__builtins__": safe_builtins,
            "math": math,
            "json": json,
            "re": re,
            "statistics": statistics,
            "datetime": datetime,
            "pd": pd,
            "np": np,
        }

        exec(code, safe_globals, {})

        output = sys.stdout.getvalue()
        error = sys.stderr.getvalue()

        if error:
            return f"Output:\n{output}\nWarnings:\n{error}"
        if output:
            return f"Output:\n{output}"
        return "Code executed successfully (no output)."

    except Exception as e:
        error_msg = traceback.format_exc()
        return f"Execution error:\n{error_msg}"

    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


def run_python_repl_tool(input: str) -> str:
    """
    Main entry point for the Python REPL tool.
    Cleans markdown code blocks if present.
    """
    code = input.strip()

    # Remove markdown code blocks if present
    if code.startswith("```python"):
        code = code[9:]
    elif code.startswith("```"):
        code = code[3:]
    if code.endswith("```"):
        code = code[:-3]

    code = code.strip()

    if not code:
        return "No code provided."

    return execute_python(code)