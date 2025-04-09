# Codewise

## Project Dependencies

`Codewise` uses UV for package dependency management. Quick uv install instructions `curl -Ls https://astral.sh/uv/install.sh | sh`  
Remember to open a new tab once you run curl so that uv shows up in your path

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
Put your OpenAPI api key in `.env_template` and rename it to `.env`  

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
For coverage use
```console
pytest --cov=code_wise --cov-report=term-missing
```
