from langchain.tools import tool
from pathlib import Path
import os

@tool
def change_your_behavior_tool(instruction: str):
    """
    A tool that allows you to change your behavior based on you altering your system prompt instructions.

    Args:
        instruction: A string containing the new behavior instructions for the AI.

    Returns:
        A confirmation message indicating the behavior has been changed.
    """

    with open('src/system_prompt', 'w') as f:
        f.write(instruction)
        print(f"change_your_behavior_tool() utilised : {instruction}")

@tool
def add_an_instruction_to_yourself(instruction: str) -> str:
    """
    A tool that allows you to add an instruction to your existing system prompt instructions.

    Args:
        instruction: A string containing the instruction to be added to the AI's behavior.

    Returns:
        A confirmation message indicating the instruction has been added.
    """

    with open('src/system_prompt', 'a') as f:
        f.write("\n" + instruction)
        print(f"add_an_instruction_to_yourself() utilised : {instruction}")

@tool
def read_your_code_base():
    """
    Reads the contents of the present codebase, where the logic and system functions are defined
    and returns the code for a better understanding of how the agent functions.

    Returns:
        The code of the agent and logic
    """
    file_paths = ['src/tools.py', 'src/search.py', 'src/system_prompt', 'app.py']
    file_contents = []
    for file_path in file_paths:
        file_path_obj = Path(file_path)
        if file_path_obj.exists() and file_path_obj.is_file():
            with open(file_path, 'r') as f:
                file_contents.append(file_path + f.read().strip())
        else:
            print(f"warning not a file or not found: {file_path}")
    return file_contents

@tool
def create_a_file(file_name : str, path : str):
    """
    Creates a new file at the specified path with the given filename.

    Args:
        file_name: Name of the file to create (e.g., 'example.txt')
        path: Directory path where the file should be created (e.g., '/home/user/documents')

    Returns:
        str: Success message with the full file path

    Raises:
        FileExistsError: If the file already exists
        PermissionError: If there are insufficient permissions
        OSError: For other OS-related errors
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

    full_path = os.path.join(path, file_name)

    if os.path.exists(full_path):
        raise FileExistsError(f"File already exists: {full_path}")

    with open(full_path, 'w') as f:
        pass

    return f"File created successfully: {full_path}"

@tool
def write_a_lines_in_a_file(filepath : str, line_start : int, line_end: int, text: str):
  """Writes a block of text to a file, starting at a specified line number.

  Args:
    filepath: The path to the file to write to.
    line_start: The line number in the file where the writing should start (1-based
index).
    line_end: The line number in the file where the writing should end (1-based index).
    text: The text to write.
  """
  try:
    with open(filepath, "a") as f:  # Use "a" to append to the file
      for i in range(line_start, line_end):
        f.write(text + "\n")
  except FileNotFoundError:
    print(f"File not found: {filepath}")
  except Exception as e:
    print(f"An error occurred: {e}")

@tool
def read_a_file(filepath : str):
    """
    Reads a file at the specified path and returns the contents.
    Args:
        filepath: The path to the file to read.
    Returns:
        The contents of the file.
    """
    with open(filepath, 'r') as f:
        return f.read()
