#!/bin/bash
# Disk Health Check Script
# Run with: sudo bash check_disk_health.sh

echo "=== NVMe Disk Health Check ==="
echo ""

# Check SMART status
if command -v smartctl &> /dev/null; then
    echo "1. SMART Status:"
    sudo smartctl -a /dev/nvme0n1
    echo ""
else
    echo "1. smartctl not found. Install with: sudo apt install smartmontools"
    echo ""
fi

# Check for recent disk errors
echo "2. Recent Disk Errors (last 24 hours):"
journalctl --since "24 hours ago" | grep -i "nvme.*error\|critical.*error\|medium.*error" | tail -20
echo ""

# Check filesystem
echo "3. Filesystem Check (read-only):"
sudo fsck -n /dev/nvme0n1p2
echo ""

# Check disk usage
echo "4. Disk Usage:"
df -h /dev/nvme0n1p2
echo ""

# Check for bad blocks (takes time)
echo "5. Bad Block Check (this may take a while):"
read -p "Run badblocks check? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running read-only badblocks check..."
    sudo badblocks -v -s /dev/nvme0n1p2 | head -100
fi

echo ""
echo "=== Check Complete ==="
echo ""
echo "If errors found, consider:"
echo "1. Backup important data immediately"
echo "2. Run full fsck on next boot: sudo touch /forcefsck && sudo reboot"
echo "3. Monitor SMART attributes for degradation"
