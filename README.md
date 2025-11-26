# Autonomous Self-Improving Agent (ACE Framework)

> **Experiment based on "Agentic Context Engineering"**

This project implements an autonomous AI agent capable of **self-improvement** by evolving its own system prompt (context) rather than fine-tuning weights. This approach is inspired by the research concept that "Fine-tuning is Dead" (in favor of dynamic context engineering).

## 🧠 Core Concept: Agentic Context Engineering (ACE)

The agent operates on a loop designed to continuously refine its behavior:

1.  **Generator**: The main agent that performs tasks, answers questions, and executes tools.
2.  **Reflector**: A critique step that evaluates the Generator's output for quality, safety, and adherence to instructions.
3.  **Curator** (Planned): A mechanism to update the `system_prompt` based on the Reflector's insights, permanently "learning" from the interaction.

## ✨ Features

-   **Self-Reflection**: Every response is critiqued by a secondary LLM call to ensure high quality.
-   **Persistent Memory**: Uses **ChromaDB** to store and retrieve long-term memories across sessions.
-   **Tool Use**:
    -   **Web Search**: Real-time information via DuckDuckGo (Async).
    -   **File Management**: Read, write, and modify codebase files.
    -   **Code Execution**: Safe execution of Python scripts.
-   **Async Architecture**: Non-blocking I/O for smooth performance.

## 🚀 Quick Start

### Prerequisites

-   Python 3.10+
-   A Google Gemini API Key

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/adityasasidhar/_an_autonomous_agent.git
    cd _an_autonomous_agent
    ```

2.  **Install dependencies**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Setup API Key**:
    Create a file named `gemini_api_key.txt` in the root directory and paste your API key:
    ```text
    YOUR_GEMINI_API_KEY
    ```

### Running the Agent

```bash
python main.py
```

Interact with the agent in the terminal. After each response, you will see a `--- Reflector ---` block showing the critique.

## 📂 Project Structure

-   `main.py`: The entry point. Contains the main loop, agent initialization, and the **Reflector** logic.
-   `src/tools.py`: Definitions of all tools (Memory, File I/O, Calculator, etc.).
-   `src/search.py`: Asynchronous web search implementation using `crawl4ai` and `duckduckgo`.
-   `system_prompt`: The "brain" of the agent. This file is dynamically readable and writable by the agent itself.
-   `memories/`: Directory for ChromaDB persistence.

## 🔮 Future Roadmap

-   [ ] **Implement Curator**: Automate the update of `system_prompt` based on Reflector critiques.
-   [ ] **Multi-Turn Reflection**: Allow the agent to "think" and revise its answer *before* showing it to the user.
-   [ ] **Skill Library**: Allow the agent to write and save reusable Python functions.

## ⚠️ Disclaimer

This is an experimental research project. The agent has the capability to modify its own instructions and execute code. Run with caution and review the logs.
