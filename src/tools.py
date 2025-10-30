from langchain.tools import tool
from pathlib import Path
import os

@tool
def set_system_prompt(prompt: str):
    """
    Replace the system prompt with the given prompt text.
    Args:
        prompt: The new system prompt text.
    Returns:
        Confirmation message.
    """
    with open('src/system_prompt', 'w') as f:
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
    with open('src/system_prompt', 'a') as f:
        f.write("\n" + instruction)
    return "Instruction added to system prompt."

@tool
def get_codebase_files():
    """
    Get the contents of key codebase files for review.
    Returns:
        List of file contents.
    """
    file_paths = ['src/tools.py', 'src/search.py', 'src/system_prompt', 'app.py', 'main.py']
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
