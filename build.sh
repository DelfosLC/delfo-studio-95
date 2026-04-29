#!/usr/bin/env bash
set -e

echo "==> Installing system dependencies..."
apt-get update -qq && apt-get install -y -qq ffmpeg nodejs

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Build complete."
