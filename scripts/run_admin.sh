#!/bin/bash
# Copies an admin Python script into the web container and runs it from /app.
# Run from /opt/cvwapp on the server.
#
# Usage: ./admin/run_admin.sh <script.py>

set -e

SCRIPT=$1
if [ -z "$SCRIPT" ]; then
    echo "Usage: $0 <script.py>"
    exit 1
fi

ADMIN_DIR="$(dirname "$0")"
SCRIPT_PATH="$ADMIN_DIR/$SCRIPT"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Script not found: $SCRIPT_PATH"
    exit 1
fi

echo "Copying $SCRIPT into container..."
docker compose cp "$SCRIPT_PATH" web:/app/_admin_script.py

echo "Running..."
docker compose exec web bash -c "cd /app && python _admin_script.py; rm -f _admin_script.py"
