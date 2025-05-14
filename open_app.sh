#!/bin/bash

kill -9 $(lsof -ti :5000) 

# Activate conda environment
conda activate csc2529

# Change to project directory
cd ~/Desktop/LatexAnki

# Start Python app in background
python app.py &

# Wait a moment for the server to start
sleep 2

# Open browser
open http://127.0.0.1:5000/
