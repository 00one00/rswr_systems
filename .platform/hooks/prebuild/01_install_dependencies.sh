#!/bin/bash

# Install Python dependencies
echo "Installing Python dependencies..."
source /var/app/venv/*/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Dependencies installed successfully"