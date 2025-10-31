# Autonomous Agent Experiment: Self-Evolving System Prompt

This repository contains an experimental research project that explores an autonomous agent built with a Large Language Model (LLM) which can analyze and suggest modifications to its own system prompt. The goal is to study self-modification, emergent behaviors, and safety/monitoring practices in AI systems.

> NOTE: This is an experimental research project. Do not run this in production or trust its behavior without thorough review and safeguards.

---

## Quick start

Prerequisites
- Python 3.10+ (the project was developed with Python 3.11)
- pip

Install dependencies (recommended in a virtual environment):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configuration
- The repository expects an API key file for generator models at `gemini_api_key.txt` (this project also references other providers; check `requirements.txt` and source files in `src/` for details).
- Do not commit secrets. Keep API keys outside version control.

Run the project
- A minimal run entrypoint exists at `main.py`. To run locally:

```bash
python main.py
```

Depending on your environment and available model providers (OpenAI, Google, Ollama, etc.), additional configuration may be required.

---

## What this project does

- Implements an LLM-driven agent that can observe its behavior, propose changes to its system prompt, and (in the experiment) apply those changes under controlled conditions.
- Logs and stores prompt edits and agent outputs for research and analysis.
- Includes tooling in `src/` for instantiation, searching, and helper utilities.

This project is intended for research and exploration of AI self-improvement concepts and is not production-ready.

---

## Project layout

- `main.py` — simple entrypoint to start the agent or demo logic.
- `src/` — core code for the agent: `instantiation.py`, `search.py`, `tools.py`, and related modules.
- `memories/` — local data used by the agent (vector DB files, sqlite DB for Chromadb, etc.).
- `gemini_api_key.txt` — optional file containing a model API key (not committed).
- `requirements.txt` — pinned dependencies used during development.

---

## Development notes

- Tests: None provided by default. If you add tests, follow standard pytest conventions and add a `tests/` folder.
- Linting / formatting: Use `black` / `ruff` if you want to apply formatting and linting.
- When editing core behavior (prompt mutation, persistence, model calls), add extensive logging and review logs to ensure safe changes.

Edge cases to watch for
- Unintended prompt changes that produce unsafe or secret-exposing behavior.
- Offline/limited model provider availability.
- Data corruption in the `memories/` folder if concurrent writes happen.

---

## Contributing

This is mainly a personal research project. If you'd like to contribute:
1. Open an issue to discuss proposed changes.
2. Send a pull request with a clear description, tests (where applicable), and a short rationale for prompt-related changes.

---

## License

Add your preferred license here (e.g., MIT, Apache-2.0). If you want, tell me which license and I can add a LICENSE file.

---

If you'd like, I can also:
- Add a short example or demo script that runs the agent in a safe, read-only mode.
- Create a CONTRIBUTING.md and a LICENSE file.
- Add a minimal `requirements-dev.txt` for linters and test tools.
