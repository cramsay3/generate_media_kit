#!/bin/bash
# Increase Swap Space Script
# Run with: sudo bash increase_swap.sh

set -e

echo "Current swap status:"
free -h
echo ""

# Check if swapfile already exists
if [ -f /swapfile ]; then
    echo "⚠️  /swapfile already exists"
    read -p "Remove existing swapfile and create new 4GB one? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Disabling swap..."
        swapoff /swapfile 2>/dev/null || true
        echo "Removing old swapfile..."
        rm -f /swapfile
    else
        echo "Exiting. Keeping existing swapfile."
        exit 0
    fi
fi

echo "Creating 4GB swap file..."
fallocate -l 4G /swapfile

echo "Setting permissions..."
chmod 600 /swapfile

echo "Formatting as swap..."
mkswap /swapfile

echo "Enabling swap..."
swapon /swapfile

echo ""
echo "✅ Swap file created and activated!"
echo ""
free -h
echo ""

# Check if already in fstab
if grep -q "/swapfile" /etc/fstab; then
    echo "✅ Swap already in /etc/fstab (will persist after reboot)"
else
    echo "Adding swap to /etc/fstab for persistence..."
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "✅ Added to /etc/fstab"
fi

echo ""
echo "Swap configuration complete!"
echo "New swap size: 4GB"
swapon --show
