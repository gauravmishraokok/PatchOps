#!/bin/bash
# run_local.sh
# Export your keys before running
# export GROQ_API_KEY=your_key
# export GITHUB_TOKEN=your_token

echo "Starting PatchOps Pipeline API..."
uvicorn pipeline_api:app --host 0.0.0.0 --port 8000
