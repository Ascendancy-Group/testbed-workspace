#!/bin/bash
# Vera-M1 Tailscale Setup Script
# Run this on Vera-M1 after SSH access is established
# Created: 2026-07-31

set -e

echo "=== Vera-M1 Tailscale Setup ==="

# Install Tailscale
echo "Installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh

# Get auth key from 1Password (run this part locally, not on server)
# TAILSCALE_KEY=*** item get "krf7zcaqvgkgjm7jabvpiv3ibm" --vault AgentStack --fields authkey --reveal)

# Authenticate with Tailscale
echo "Authenticating with Tailscale..."
# Replace AUTH_KEY_HERE with actual key
tailscale up --authkey="AUTH_KEY_HERE" --hostname="vera-m1"

# Show status
echo "Tailscale status:"
tailscale status

echo "✅ Tailscale setup complete"
echo "Tailscale IP will be assigned automatically"
