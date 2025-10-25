from langchain.tools import tool
from pathlib import Path
import os

from litellm.files.main import file_content


@tool
def change_your_behavior_tool(instruction: str) -> str:
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
