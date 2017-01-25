#!/bin/bash  
#  
# /etc/init.d/box 
#  
# Starts the at daemon  
#

# RAMDISK SETTINGS
RAMDISK_SIZE="200"
RAMDISK_PATH=/tmp/hls

PACKAGE_PATH= /root/live_platform


# Create ramdisk
mkdir -p RAMDISK_PATH
mount -t tmpfs -o size={$RAMDISK_SIZE}M tmpfs {$RAMDISK_PATH}

# Start redis-server





