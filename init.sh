#!/bin/bash

# Check if the voices directory is empty
if [ -z "$(ls -A /app/voices)" ]; then
  echo "Voices directory is empty. Downloading voices..."
  bash /app/download_voices_tts-1.sh
  bash /app/download_voices_tts-1-hd.sh
else
  echo "Voices already exist. Skipping download."
fi

# Start the application
exec "$@"