# FSN Local Backend for Mac

This is the **LOCAL** backend that runs on your Mac and connects to your frontend.

## 🎯 How It Works

1. **Frontend** (fsndevelopment.com) - You add devices and start them
2. **Local Backend** (your Mac) - Receives commands from frontend
3. **Appium** - Starts automatically when you click "Start Device" in frontend
4. **Your iPhone** - Gets controlled by the frontend through Appium

## 📁 Files

- `local-backend.py` - The main local backend server
- `register-device.py` - Register iPhone with local backend
- `START-FSN-LOCAL.command` - Easy startup script

## 🚀 Quick Start

### 1. Start the Local Backend

```bash
# Make the script executable
chmod +x START-FSN-LOCAL.command

# Start the local backend
./START-FSN-LOCAL.command
```

### 2. Add Your iPhone in Frontend

1. Go to **fsndevelopment.com**
2. Go to **Devices** page
3. Click **"Add Device"**
4. Add your iPhone details

### 3. Start Your Device

1. Go to **Running** page in frontend
2. Click **"Start Device"** for your iPhone
3. The local backend will start Appium automatically
4. Your iPhone is now controlled by the frontend!

## 🔧 Requirements

- Python 3 installed on your Mac
- Appium installed (`npm install -g appium`)
- iPhone connected via USB
- Developer Mode enabled on iPhone

## 📊 What Happens When You Start a Device

1. Frontend calls `http://localhost:8000/api/devices/{id}/start`
2. Local backend starts Appium on port 4720
3. Appium connects to your iPhone
4. Frontend can now control your iPhone

## 🛑 Stopping

- Click "Stop Device" in frontend
- Or press Ctrl+C in the terminal running the backend

## 🔍 Troubleshooting

- **Backend not starting**: Check if port 8000 is free
- **Appium not starting**: Make sure Appium is installed globally
- **iPhone not connecting**: Check USB connection and Developer Mode

## 📱 Perfect Setup!

This gives you exactly what you wanted:
- ✅ Local backend on your Mac
- ✅ Frontend controls your iPhone
- ✅ Appium starts automatically
- ✅ No cloud backend needed!
