#!/usr/bin/env python3
"""
Clear scrolling tracking files to allow testing multiple times per day
"""

import os
import glob
import sys

def clear_tracking_files():
    """Clear all scrolling tracking files"""
    tracking_dir = "tracking_files"
    
    if not os.path.exists(tracking_dir):
        print("📁 No tracking directory found")
        return
    
    # Find all tracking files
    pattern = os.path.join(tracking_dir, "scroll_tracking_*.json")
    files = glob.glob(pattern)
    
    if not files:
        print("✅ No tracking files to clear")
        return
    
    # Remove files
    removed_count = 0
    for file_path in files:
        try:
            os.remove(file_path)
            print(f"🗑️  Removed: {os.path.basename(file_path)}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Failed to remove {file_path}: {e}")
    
    print(f"✅ Cleared {removed_count} tracking files")
    print("🚀 Scrolling and liking will run again!")

if __name__ == "__main__":
    clear_tracking_files()
