#!/usr/bin/env bash
# Render build script — installs system deps + Python deps

set -e

echo "==> Installing ffmpeg..."
apt-get update -qq && apt-get install -y -qq ffmpeg

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Build complete."
