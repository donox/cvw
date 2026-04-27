#!/usr/bin/env bash
# ------------------------------------------------------------------
# docker_power_up.sh  — power on the CVW production droplet
# ------------------------------------------------------------------
# Usage:
#   export DIGITALOCEAN_TOKEN=your_pat_here   # only once per shell
#   ./docker_power_up.sh                      # uses hardcoded droplet ID
#   ./docker_power_up.sh <other-id>           # override for a different droplet
# ------------------------------------------------------------------
set -euo pipefail

DROPLET_ID="${1:-560368862}"

echo "Powering UP Droplet $DROPLET_ID..."
doctl compute droplet-action power-on "$DROPLET_ID" --wait

echo "Droplet $DROPLET_ID is now on. Allow ~30 seconds for the app to start."
