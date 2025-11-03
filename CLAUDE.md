# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Codewise is a Python code quality analysis tool with a PySide6 GUI that uses OpenAI's GPT models to evaluate Python methods based on 16 quality criteria (separation of concerns, documentation, logic clarity, efficiency, etc.). It can analyze individual files or entire projects by collecting method definitions, finding their usage examples across the codebase, and sending them to LLMs for detailed evaluation.

## Development Setup

### Prerequisites
- Python 3.13
- UV package manager (`curl -Ls https://astral.sh/uv/install.sh | sh`)
- OpenAI API key (create `.env` file with `OPENAI_API_KEY=your_key_here`)

### Initial Setup
```bash
uv python install 3.13
uv python pin 3.13
uv venv
source .venv/bin/activate
uv pip install .
uv pip install . --group dev
pre-commit install
```

## Common Commands

### Running the Application
```bash
python code_evaluator.py
```
This launches the PySide6 GUI application.

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/gui/test_ui_utils.py

# Run specific test
pytest tests/gui/test_ui_utils.py::TestAnalysisWorker::test_worker_processes_all_methods_single_file

# Run with coverage
pytest --cov=code_wise --cov-report=html
```

### Linting and Formatting
```bash
# Check and fix linting issues
ruff check . --fix

# Format code (also runs via pre-commit)
black .

# Sort imports (also runs via pre-commit)
isort .
```

## Architecture

### Core Components

**AST-based Analysis Pipeline (`code_wise/logic/code_ast_parser.py`)**
- `MethodUsageCollector`: Main visitor class that walks Python AST to collect method definitions and their call sites
- Uses parent pointers in AST nodes to find enclosing functions for each method call
- Resolves module imports and method identifiers to track cross-file method usage
- Returns `MethodPointer` objects (method definition + file location) mapped to `CallSiteInfo` lists (usage examples with context)

**LLM Integration (`code_wise/llm/`)**
- `llm_integration.py`: OpenAI API wrapper with error handling
- `code_eval_prompt.py`: Prompt template defining 16 quality criteria for method evaluation
- Sends method body + up to 10 usage examples to GPT-4 for scoring (1-10) and feedback

**GUI Application (`code_wise/codewise_gui/codewise_ui_utils.py`)**
- `CodewiseApp`: Main Qt widget with two analysis modes:
  - Single File Mode: Analyzes all methods in one file
  - Entire Project Mode: Walks directory tree and analyzes all Python files
- `AnalysisWorker`: QThread that runs analysis off main thread to keep UI responsive
- `CancellableAPICall`: Thread-safe wrapper for API calls with proper cancellation support
- `LoadingSpinner`: Custom Qt widget showing animated spinner during analysis
- Split-pane UI: Left side shows progress logs, right side displays LLM responses

### Key Design Patterns

**Thread Safety for API Cancellation**
- `CancellableAPICall` uses threading locks to safely cancel in-flight API requests
- Worker thread checks `_is_cancelled` flag between operations to support immediate cancellation
- Critical: Always reset cancellation state (`_api_call.reset()`) before processing each method

**AST Parent Pointer Pattern**
- `set_parent_pointers()` adds `.parent` attribute to every AST node during parsing
- Enables `find_enclosing_function()` to walk up tree from Call node to find containing FunctionDef
- Required for extracting usage context (the function that calls a method)

**Progressive Processing**
- Methods are processed sequentially in a loop (NO break statements - see code_wise/codewise_gui/codewise_ui_utils.py:247-295)
- Each method emits separate signals: progress updates, API responses
- UI displays results incrementally rather than waiting for batch completion

## Testing Strategy

### GUI Testing
- Tests use a global QApplication instance (`get_qapp()`) shared across all tests to avoid crashes
- Mock `QMessageBox` calls to prevent popup dialogs during test runs
- Tests verify signal emissions, UI state changes, and thread cancellation

### Worker Thread Testing
- Extensive tests for the "process all methods" fix (tests/gui/test_ui_utils.py:310-709)
- Tests verify that ALL methods in a file are processed, not just the first one
- Includes tests for: multiple methods, class methods vs functions, error handling, cancellation mid-process

## Important Implementation Details

1. **Skip test files during analysis**: Both `code_ast_parser.py` and `analyze_cognitive_complexity.py` explicitly skip files starting with `test_` to avoid analyzing test code

2. **API call rate limiting**: Worker processes methods sequentially (not in parallel) to avoid overwhelming OpenAI API

3. **Usage example sampling**: `collect_method_usages()` randomly samples up to 10 usage examples per method (code_wise/logic/code_ast_parser.py:244)

4. **Mock QMessageBox in tests**: Always patch QMessageBox methods in GUI tests to prevent actual popup dialogs that would block pytest

5. **Environment configuration**: OpenAI API key is loaded from `.env` file via `python-dotenv`. The app displays helpful setup instructions if key is missing.

## File Structure

```
code_wise/
├── logic/              # AST parsing and cognitive complexity analysis
├── llm/                # LLM integration and prompt templates
├── codewise_gui/       # PySide6 GUI components
└── utils/              # Helper utilities for parsing

tests/
├── gui/                # GUI component tests (QApplication, signals, workers)
├── logic/              # AST parser tests
└── llm/                # LLM integration tests
```

## Code Style

- Line length: 120 characters (Black, Isort, Ruff configured)
- Python 3.13 features allowed
- String quotes: Skip string normalization (preserves single quotes)
- All code runs through pre-commit hooks (Black + Isort)
