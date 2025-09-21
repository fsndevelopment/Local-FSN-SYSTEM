# 🔒 macOS Security Fix - Quick Guide

## The Problem
macOS blocks downloaded files for security. This is normal and expected!

## ✅ **3 Easy Solutions (Choose One):**

### **Option 1: Right-Click Method (Easiest)**
1. **Right-click** on `FSN-Agent-Simple.command`
2. **Select** "Open" (not double-click)
3. **Click** "Open" when macOS asks
4. **Done!** The agent will start

### **Option 2: Terminal Command (Quick)**
1. **Open Terminal** on your Mac
2. **Navigate** to the extracted folder:
   ```bash
   cd ~/Downloads/FSN-Agent-Mac-Complete
   ```
3. **Run this command:**
   ```bash
   xattr -d com.apple.quarantine FSN-Agent-Simple.command
   ```
4. **Now double-click** the file - it will work!

### **Option 3: Use the New App File**
1. **Use** `FSN-Agent-Mac-App.command` instead
2. **Right-click** and select "Open"
3. **Follow the same process**

## 🎯 **Why This Happens:**
- macOS protects you from potentially harmful files
- Downloaded files get "quarantined" automatically
- This is a **security feature**, not an error
- Once you allow it once, it will work normally

## 🚀 **After Fixing:**
- The agent will start normally
- You'll see pairing instructions
- Your iPhone will connect to the cloud
- Everything will work perfectly!

**This is completely normal and safe to fix!** 🎉
