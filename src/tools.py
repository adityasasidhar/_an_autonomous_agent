from langchain.tools import tool
from pathlib import Path
import chromadb
import os
import hashlib
import requests
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import ast
import math
import operator
import subprocess
import tempfile
import sys
import textwrap

chroma_client = chromadb.PersistentClient(path="../memories")
collection = chroma_client.get_or_create_collection(name="my_collection")

@tool
def set_system_prompt(prompt: str):
    """
    Replace the system prompt with the given prompt text.
    Args:
        prompt: The new system prompt text.
    Returns:
        Confirmation message.
    """
    with open('system_prompt', 'w') as f:
        f.write(prompt)
    return "System prompt updated."

@tool
def add_system_instruction(instruction: str) -> str:
    """
    Add an instruction to the end of the system prompt.
    Args:
        instruction: The instruction to add.
    Returns:
        Confirmation message.
    """
    with open('system_prompt', 'a') as f:
        f.write("\n" + instruction)
    return "Instruction added to system prompt."

@tool
def get_codebase_files():
    """
    Get the contents of key codebase files for review.
    Returns:
        List of file contents.
    """
    file_paths = ['src/tools.py', 'src/search.py', 'system_prompt', 'app.py', 'main.py']
    files = []
    for file_path in file_paths:
        file_path_obj = Path(file_path)
        if file_path_obj.exists() and file_path_obj.is_file():
            with open(file_path, 'r') as f:
                files.append(file_path + f.read().strip())
    return files

@tool
def create_file(name: str, folder: str):
    """
    Create a new file in the given folder.
    Args:
        name: File name.
        folder: Folder path.
    Returns:
        Success message with file path.
    """
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    full_path = os.path.join(folder, name)
    if os.path.exists(full_path):
        raise FileExistsError(f"File already exists: {full_path}")
    with open(full_path, 'w') as f:
        pass
    return f"File created: {full_path}"

@tool
def add_lines_to_file(path: str, start_line: int, end_line: int, content: str):
    """
    Add lines of text to a file from start_line to end_line (1-based, inclusive start, exclusive end).
    Args:
        path: File path.
        start_line: Start line number.
        end_line: End line number.
        content: Text to add.
    """
    try:
        with open(path, "a") as f:
            for _ in range(start_line, end_line):
                f.write(content + "\n")
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Error: {e}"
    return "Lines added."

@tool
def read_file(path: str):
    """
    Read and return the contents of a file.
    Args:
        path: File path.
    Returns:
        File contents.
    """
    with open(path, 'r') as f:
        return f.read()

@tool
def save_memory(
    content: str,
    memory_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    overwrite: bool = True
) -> Dict[str, Any]:
    """
    Save or upsert a memory into the collection.

    Returns a dict with keys: 'id', 'status', and optionally 'message'.
    """
    if not content:
        return {"status": "error", "message": "Empty content not allowed."}

    # deterministic id if not provided
    mem_id = memory_id or hashlib.md5(content.encode("utf-8")).hexdigest()
    metadata = metadata or {}
    # use timezone-aware UTC timestamp
    metadata.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

    try:
        # if overwrite is False, check existence first
        if not overwrite:
            existing = collection.get(ids=[mem_id])
            if existing and existing.get("ids"):
                return {"id": mem_id, "status": "skipped", "message": "Memory already exists."}

        collection.upsert(
            ids=[mem_id],
            documents=[content],
            metadatas=[metadata],
        )
        return {"id": mem_id, "status": "ok"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@tool
def search_memories(
    query: str,
    top_k: int = 3,
    include_metadata: bool = True,
    min_distance: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Query the collection and return a list of results:
    Each result is a dict with keys: 'id', 'document', 'metadata' (optional), 'distance' (if available).
    """
    if not query:
        return []

    try:
        results = collection.query(query_texts=[query], n_results=top_k)
        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0] if include_metadata else [None] * len(ids)
        distances = results.get("distances", [[]])[0] if "distances" in results else [None] * len(ids)

        normalized: List[Dict[str, Any]] = []
        for i, _id in enumerate(ids):
            distance = distances[i] if i < len(distances) else None
            if min_distance is not None and distance is not None and distance > min_distance:
                continue
            normalized.append({
                "id": _id,
                "document": documents[i] if i < len(documents) else None,
                "metadata": metadatas[i] if include_metadata and i < len(metadatas) else None,
                "distance": distance,
            })
        return normalized
    except Exception:
        return []

@tool
def get_current_location():
    """
    Returns the current location of the user.
    Args: None
    Returns: Geographical location of the user.
    """
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        response.raise_for_status()
        data = response.json()
        city = data.get("city")
        region = data.get("region")
        country = data.get("country")
        if city:
            parts = [p for p in (city, region, country) if p]
            return ", ".join(parts)
        if region:
            parts = [p for p in (region, country) if p]
            return ", ".join(parts)
        loc = data.get("loc")
        if loc:
            return loc
        return None
    except Exception:
        return None

# Safe expression evaluator helpers
_allowed_math_funcs = {k: getattr(math, k) for k in dir(math) if not k.startswith("__")}
# allow a few builtins
_allowed_names = {
    **_allowed_math_funcs,
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'pow': pow,
}

_binops = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.LShift: operator.lshift,
    ast.RShift: operator.rshift,
    ast.BitOr: operator.or_,
    ast.BitAnd: operator.and_,
    ast.BitXor: operator.xor,
}

_unaryops = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Invert: operator.invert,
}


def _eval_node(node):
    """Recursively evaluate an AST node with a safe whitelist."""
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, complex)) or node.value is None:
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value)}")
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op_type = type(node.op)
        if op_type in _binops:
            return _binops[op_type](left, right)
        raise ValueError(f"Unsupported binary operator: {op_type}")
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        op_type = type(node.op)
        op = _unaryops.get(op_type)
        if op is not None:
            return op(operand)
        raise ValueError(f"Unsupported unary operator: {op_type}")
    if isinstance(node, ast.Call):
        # only allow simple function calls with Name as func
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct function calls are allowed")
        func_name = node.func.id
        if func_name not in _allowed_names:
            raise ValueError(f"Function '{func_name}' is not allowed")
        func = _allowed_names[func_name]
        args = [_eval_node(arg) for arg in node.args]
        # do not permit kwargs
        if node.keywords:
            raise ValueError("Keyword arguments are not allowed")
        return func(*args)
    if isinstance(node, ast.Name):
        if node.id in _allowed_names:
            return _allowed_names[node.id]
        raise ValueError(f"Use of name '{node.id}' is not allowed")
    if isinstance(node, ast.Tuple):
        return tuple(_eval_node(elt) for elt in node.elts)
    if isinstance(node, ast.List):
        return [_eval_node(elt) for elt in node.elts]
    raise ValueError(f"Unsupported expression: {type(node)}")


@tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression safely and return the result as a string.

    This uses the AST to whitelist nodes and allows math module functions and a
    few safe builtins (abs, round, min, max, pow). It does NOT allow attribute
    access, imports, or arbitrary code execution.
    """
    if not expression or not expression.strip():
        return "Error: empty expression"
    try:
        tree = ast.parse(expression, mode='eval')
        result = _eval_node(tree)
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@tool
def exec_python(code: str, timeout: int = 5, max_memory_mb: int = 256) -> Dict[str, Any]:
    """
    Execute Python code in a subprocess with resource limits and return a dict:
    { 'status': 'ok'|'error'|'timeout', 'stdout': str, 'stderr': str, 'returncode': int }

    Security notes:
    - This is not a perfect sandbox. It limits memory (RLIMIT_AS), CPU time (RLIMIT_CPU),
      and number of open files, but the executed code can still perform I/O, network calls,
      or try to fork processes. Use caution and prefer reviewing code before executing.
    - The runner writes a temporary wrapper file and invokes the same Python executable.
    """
    if not isinstance(code, str) or not code.strip():
        return {"status": "error", "message": "Empty code provided"}

    max_mem = int(max_memory_mb) * 1024 * 1024
    # Build wrapper that applies resource limits then executes the code
    wrapper = """
import resource, sys, traceback
# apply resource limits
resource.setrlimit(resource.RLIMIT_AS, ({max_mem}, {max_mem}))
resource.setrlimit(resource.RLIMIT_CPU, ({cpu_limit}, {cpu_limit}))
resource.setrlimit(resource.RLIMIT_NOFILE, (16, 16))
try:
{text}
except SystemExit as e:
    # preserve exit code
    sys.exit(e.code)
except Exception:
    traceback.print_exc()
""".format(
        max_mem=max_mem,
        cpu_limit=max(1, int(timeout) + 1),
        text=textwrap.indent(code, '    ')
    )

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.py') as tf:
            tf.write(wrapper)
            tmp_path = tf.name

        proc = subprocess.run([sys.executable, tmp_path], capture_output=True, text=True, timeout=timeout)
        return {
            "status": "ok" if proc.returncode == 0 else "error",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }
    except subprocess.TimeoutExpired as te:
        # subprocess will be killed; return timeout status
        return {
            "status": "timeout",
            "stdout": getattr(te, 'output', '') or '',
            "stderr": getattr(te, 'stderr', '') or '',
            "returncode": None,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass
