#!/bin/bash

echo "Starting Morning Briefing Agent..."

# Check if ollama is already running
if ! curl -s http://localhost:11434 > /dev/null 2>&1; then
    echo "Starting Ollama..."
    ollama serve &
    OLLAMA_PID=$!
    sleep 3
else
    echo "Ollama already running."
fi

# Activate venv
source .venv/bin/activate

# Run the briefing
python agent/briefing_agent.py

# Clean up ollama if we started it
if [ ! -z "$OLLAMA_PID" ]; then
    kill $OLLAMA_PID 2>/dev/null
fi
