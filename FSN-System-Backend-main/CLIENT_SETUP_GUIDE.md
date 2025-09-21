# 🍎 FSN Client Setup Guide

## **Super Simple Solution for Your Clients**

### **Option 1: One-Click Mac App (Recommended)**

1. **Download the installer script:**
   ```bash
   curl -O https://raw.githubusercontent.com/fsndevelopment/FSN-System-Backend/main/FSN-Client-Installer.sh
   ```

2. **Make it executable and run:**
   ```bash
   chmod +x FSN-Client-Installer.sh
   ./FSN-Client-Installer.sh
   ```

3. **That's it!** The script will:
   - ✅ Download the FSN backend
   - ✅ Install Python dependencies
   - ✅ Start the local server
   - ✅ Connect your iPhone to the cloud system

### **Option 2: Manual Setup (If Option 1 doesn't work)**

1. **Install Python 3:**
   ```bash
   brew install python3
   ```

2. **Download FSN backend:**
   ```bash
   git clone https://github.com/fsndevelopment/FSN-System-Backend.git
   cd FSN-System-Backend
   ```

3. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

4. **Start the server:**
   ```bash
   python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```

## **What Happens Next:**

1. **Your iPhone connects** to the local server on your Mac
2. **The local server** communicates with the cloud backend
3. **Your frontend** automatically detects the local server
4. **You can control your iPhone** through the website

## **For Your Clients:**

### **Step 1: Send them this link:**
```
https://github.com/fsndevelopment/FSN-System-Backend
```

### **Step 2: Tell them to run:**
```bash
curl -O https://raw.githubusercontent.com/fsndevelopment/FSN-System-Backend/main/FSN-Client-Installer.sh
chmod +x FSN-Client-Installer.sh
./FSN-Client-Installer.sh
```

### **Step 3: That's it!**
- The script does everything automatically
- Their iPhone will be connected
- They can use the website normally

## **Frontend Auto-Detection:**

The frontend will automatically detect if a client is running the local backend and use it instead of the cloud backend.

## **Troubleshooting:**

### **If Python is not installed:**
- Visit: https://www.python.org/downloads/
- Download and install Python 3

### **If the script fails:**
- Make sure your iPhone is connected via USB
- Trust this computer when prompted on your iPhone
- Check that port 8000 is not being used by another app

### **If the frontend doesn't connect:**
- Make sure the local server is running
- Check the terminal for any error messages
- Try refreshing the website

## **Benefits of This Approach:**

✅ **Super simple** - Clients just run one script
✅ **Automatic setup** - No manual configuration needed
✅ **Works immediately** - No complex tunneling
✅ **Easy to update** - Just re-run the script
✅ **Client-friendly** - No technical knowledge required

---

**This is the simplest solution for your clients!** 🚀
