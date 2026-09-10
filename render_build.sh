#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing uv..."
pip install uv

echo "Installing backend dependencies..."
uv pip install ".[server]"

echo "Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Build complete."
