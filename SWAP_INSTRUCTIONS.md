# Increase Swap Space Instructions

## Current Status
- **Current swap**: 512MB (completely full!)
- **Memory**: 15GB total, ~10GB used
- **Problem**: Swap is exhausted, causing system slowdowns

## Quick Fix (Run These Commands)

```bash
# Create 4GB swap file
sudo fallocate -l 4G /swapfile

# Set secure permissions
sudo chmod 600 /swapfile

# Format as swap
sudo mkswap /swapfile

# Enable swap
sudo swapon /swapfile

# Make it permanent (add to /etc/fstab)
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## Or Use the Script

```bash
sudo bash increase_swap.sh
```

## Verify It Worked

```bash
# Check swap status
free -h

# Should show ~4.5GB total swap (512MB old + 4GB new)
# Or if you replaced it, should show 4GB

# Check swap files
swapon --show
```

## Recommended Swap Sizes

- **4GB**: Good for 15GB RAM system (what we're creating)
- **8GB**: If you do heavy development/work
- **2GB**: Minimum for stability

## After Increasing Swap

1. **Restart Cursor** - It will have more breathing room
2. **Monitor usage** - `free -h` to see if swap is being used
3. **If still slow** - May need to close applications or add more RAM

## Troubleshooting

### If swapfile already exists:
```bash
# Disable old swap
sudo swapoff /swapfile

# Remove old swapfile
sudo rm /swapfile

# Then run the creation commands above
```

### To remove swap later:
```bash
sudo swapoff /swapfile
sudo rm /swapfile
sudo sed -i '/\/swapfile/d' /etc/fstab
```

## Why This Helps Cursor

- **More memory headroom** - System won't run out of memory
- **Prevents crashes** - Swap gives buffer when RAM is full
- **Better performance** - System can swap out unused processes
