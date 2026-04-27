#!/usr/bin/env bash
# ------------------------------------------------------------------
# docker_power_down.sh  — power off the CVW production droplet
# ------------------------------------------------------------------
# Usage:
#   export DIGITALOCEAN_TOKEN=your_pat_here   # only once per shell
#   ./docker_power_down.sh                    # uses hardcoded droplet ID
#   ./docker_power_down.sh <other-id>         # override for a different droplet
# ------------------------------------------------------------------
set -euo pipefail

DROPLET_ID="${1:-560368862}"

echo "Powering DOWN Droplet $DROPLET_ID..."
doctl compute droplet-action power-off "$DROPLET_ID" --wait

echo "Droplet $DROPLET_ID is now powered off."
