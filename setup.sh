#!/bin/bash

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dev dependencies with uv..."
uv pip install . --group dev

echo "Installing pre-commit hooks..."
pre-commit install

echo "✅ Setup complete!"
