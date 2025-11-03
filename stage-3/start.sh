#!/bin/bash

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
  echo "Installing requirements..."
  source venv/bin/activate
  pip install -r requirements.txt
else
  source venv/bin/activate
fi

# Run the Flask app
python3 main.py