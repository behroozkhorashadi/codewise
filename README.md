# Codewise

## Project Dependencies

`Codewise` uses UV for package dependency management. Quick uv install instructions `curl -Ls https://astral.sh/uv/install.sh | sh`

## Project Setup

Clone the repo and cd into the directory.

```console
  $ uv python install 3.13
  $ uv python pin 3.13
  $ uv venv
  $ source .venv/bin/activate
  $ uv pip install .
  $ uv pip install . --group dev
  $ pre-commit install
```

## Run Project

From inside your virtual environment

```console
  $ python code_evaluator.py
```

## Tests & Linting
### Linting
We have built in black ruff and isort linters and formatting. To run them use the following commands:
```console
  $ ruff check . --fix
  $ black .
  $ isort .
```
Note: black and isort are built into the pre-commit hooks so they will run automatically

### Tests
From the root directory run:
```console
  $ pytest
```
