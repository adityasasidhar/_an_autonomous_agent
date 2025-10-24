from langchain.tools import tool

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
    return f"Behavior changed to: {instruction}"

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
    return f"Instruction added: {instruction}"
