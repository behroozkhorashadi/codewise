#!/bin/bash

set -e  # Exit on error

# Detect OS
OS="$(uname -s)"

echo "Detected OS: $OS"

# Define common steps
common_setup() {
  echo "🔧 Creating virtual environment..."
  uv venv

  echo "🐍 Activating virtual environment..."
  source .venv/bin/activate

  echo "📦 Installing main and dev dependencies with uv..."
  uv pip install .
  uv pip install . --group dev

  echo "✅ Installing pre-commit hooks..."
  pre-commit install

  echo "🎉 Setup complete!"
}

case "$OS" in
  Darwin)
    echo "Running macOS setup..."
    common_setup
    ;;
  Linux)
    echo "Running Linux setup..."
    common_setup
    ;;
  *)
    echo "❌ Unsupported OS: $OS"
    echo "Please run this script on macOS or Linux"
    exit 1
    ;;
esac
