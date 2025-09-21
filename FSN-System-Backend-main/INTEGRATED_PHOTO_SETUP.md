# 🚀 Integrated Photo Posting Setup Guide

This system combines **photo cleaning**, **ngrok serving**, and **iPhone posting** into one seamless workflow using your template settings.

## 🎯 **How It Works**

When you set **Photo posts = 1** and select a **photos folder** in Templates:

1. **📸 Random Selection** - Picks random photo from your folder
2. **🧹 Photo Cleaning** - Uses your cleaner script to remove metadata
3. **🌐 ngrok Serving** - Creates tunnel to serve photo to iPhone  
4. **📱 iPhone Download** - iPhone downloads via Safari
5. **📲 Instagram Posting** - Posts with caption from your Excel file

## ⚙️ **Setup Requirements**

### 1. **ngrok Tokens Configuration**

Create `ngrok_tokens.json` in your project root:

```json
{
    "default": "YOUR_NGROK_TOKEN_HERE"
}
```

**Get your ngrok token:**
1. Go to https://dashboard.ngrok.com/get-started/your-authtoken
2. Copy your authtoken
3. Replace `YOUR_NGROK_TOKEN_HERE` with your token

### 2. **Photos Folder Structure**

```
/path/to/your/photos/
├── photo1.jpg
├── photo2.png
├── photo3.heic
└── photo4.jpeg
```

**Supported formats:** `.jpg`, `.jpeg`, `.png`, `.heic`

### 3. **Captions File (Optional)**

Excel file with captions in first column:

| Caption |
|---------|
| Living my best life! ✨ |
| Another day, another adventure 🌟 |
| Grateful for this moment 🙏 |

### 4. **Dependencies**

```bash
# Install required packages
pip install pandas pillow pillow-heif pyngrok

# Your cleaner script dependencies
cd CLEANER
pip install -r requirements.txt
```

## 🎮 **Usage in Templates**

### **Template Configuration:**

1. **Photos Posts per Day:** `1` (or any number)
2. **Photos Folder:** `/path/to/your/photos`  
3. **Captions File:** `/path/to/captions.xlsx` (optional)

### **When Template Runs:**

```
🚀 Starting integrated photo posting workflow
📸 Selected photo: /path/to/photos/photo3.jpg
🧹 Photo cleaned: /tmp/fsn_photos_device123/photo3_cleaned_5678.jpg
🌐 Photo served via ngrok: https://abc123.ngrok.io/photo3_cleaned_5678.jpg
📝 Using caption: Living my best life! ✨
📱 Instructing iPhone to download photo
🌐 Opening Safari to download photo
✅ Photo saved to iPhone Photos
📸 Opening Instagram to post photo
✅ Photo posted successfully!
```

## 🔧 **API Endpoints**

### **Test Workflow**
```bash
curl -X POST "http://localhost:8000/api/integrated-photo/test-workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "photos_folder": "/path/to/your/photos",
    "captions_file": "/path/to/captions.xlsx"
  }'
```

### **Process Photo Post**
```bash
curl -X POST "http://localhost:8000/api/integrated-photo/process-photo-post" \
  -H "Content-Type: application/json" \
  -d '{
    "photos_folder": "/path/to/your/photos",
    "captions_file": "/path/to/captions.xlsx",
    "device_udid": "your-iphone-udid"
  }'
```

### **Check Active Handlers**
```bash
curl -X GET "http://localhost:8000/api/integrated-photo/active-handlers"
```

### **Cleanup Resources**
```bash
curl -X POST "http://localhost:8000/api/integrated-photo/cleanup"
```

## 🐛 **Troubleshooting**

### **Common Issues:**

#### **"No photos found in folder"**
- Check folder path is correct
- Ensure photos have supported extensions
- Verify folder permissions

#### **"ngrok tunnel failed"**
- Check `ngrok_tokens.json` exists and has valid token
- Verify ngrok is installed: `pip install pyngrok`
- Check internet connection

#### **"Photo cleaning failed"**
- Verify CLEANER dependencies: `cd CLEANER && pip install -r requirements.txt`
- Check input photo format is supported
- Ensure sufficient disk space

#### **"iPhone download failed"**
- Verify iPhone is connected via Appium
- Check Safari app is available
- Ensure iPhone has internet access

### **Debug Mode:**

Enable detailed logging by setting environment variable:
```bash
export FSN_LOG_LEVEL=DEBUG
```

## 📊 **Monitoring**

### **Check Active Resources:**
```bash
curl -X GET "http://localhost:8000/api/integrated-photo/active-handlers"
```

**Response:**
```json
{
  "success": true,
  "handlers_info": {
    "active_handlers_count": 2,
    "active_devices": ["device123", "device456"],
    "temp_directories": ["device123", "device456"]
  }
}
```

### **Cleanup When Done:**
```bash
curl -X POST "http://localhost:8000/api/integrated-photo/cleanup"
```

## ✅ **Verification Steps**

1. **Test photo selection:**
   ```bash
   ls -la /path/to/your/photos
   ```

2. **Test ngrok token:**
   ```bash
   ngrok config check
   ```

3. **Test cleaner script:**
   ```bash
   cd CLEANER
   python cleaner.py
   ```

4. **Test full workflow:**
   ```bash
   curl -X POST "http://localhost:8000/api/integrated-photo/test-workflow" \
     -H "Content-Type: application/json" \
     -d '{"photos_folder": "/path/to/your/photos"}'
   ```

## 🎉 **You're All Set!**

Your integrated photo posting system is ready! When you:

1. **Set photo posts = 1** in template
2. **Select photos folder** 
3. **Run the template**

The system will automatically:
- ✅ Pick random photo
- ✅ Clean metadata  
- ✅ Serve via ngrok
- ✅ Download to iPhone
- ✅ Post to Instagram

**No manual photo transfers needed!** 🚀
