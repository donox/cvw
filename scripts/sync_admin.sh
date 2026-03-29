#!/bin/bash
# Syncs scripts/admin/ to the server (gitignored — safe for passwords/secrets).
# Run from the project root on your local machine.
#
# Usage: ./scripts/sync_admin.sh

SERVER=root@cvwdev.org
REMOTE_DIR=/opt/cvwapp/admin

rsync -av --mkpath scripts/admin/ "$SERVER:$REMOTE_DIR/"
echo ""
echo "Synced to $SERVER:$REMOTE_DIR"
echo "On the server, run:  ./admin/run_admin.sh <script.py>"
