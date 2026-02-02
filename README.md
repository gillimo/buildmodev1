# BuildMode v1 (Historical)

Mission Learning Statement
- Mission: Prototype a CLI-piped coding assistant for local development workflows.
- Learning focus: command synthesis, prompt orchestration, and early tool-loop design.
- Project start date: 2023-10-01 (original release window)

Early CLI-piped coding assistant with a Tkinter UI that generates Python code via the OpenAI API, runs it locally, and supports rollback/gold copies.

## Features

- GUI prompt entry with chat, code, and console panes
- OpenAI API-backed code generation with code-only extraction
- Auto-run of generated code with error-driven fix loop
- Working/rollback/gold file management under `Desktop/MartinCode`

## Installation

### Requirements

- Python 3.8+
- `requests` (install via `pip install requests`)
- Tkinter (bundled with standard Python on Windows)

### Setup

- Set `OPENAI_API_KEY` in your environment or create a local `env.txt` next to `buildmodev1.py`.

## Quick Start

```bash
python buildmodev1.py
```

## Usage

1. Enter a request in the prompt field (e.g., "calculator GUI").
2. The assistant generates Python code via OpenAI and saves it to `working_file.py`.
3. The code runs automatically; errors trigger an auto-fix loop.
4. Use the feedback window to save a gold copy or roll back.

## Architecture

```
User Prompt (GUI)
    |
    v
OpenAI API (chat completions)
    |
    v
Code Extraction -> working_file.py
    |
    v
Local Execution
    |
    +--> Error -> Fix Loop -> Update working_file.py
    |
    +--> Feedback -> Save Gold / Rollback
```

## Project Structure

```
buildmodev1.py   # Main GUI and orchestration
env.txt          # Local-only API key (gitignored)
Desktop/MartinCode/
  working_file.py
  rollback_file.py
  gold_copy.py
```

## Building

No build step required. Run directly with Python.

## Contributing

Historical artifact. If you want to experiment, fork the repo and make changes there.

## License

No license file is included in this repository.
