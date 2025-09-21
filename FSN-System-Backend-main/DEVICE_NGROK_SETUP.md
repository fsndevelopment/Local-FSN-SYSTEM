# 🔑 Device-Specific ngrok Token Setup

Your photo posting system now uses **device-specific ngrok tokens** instead of a global configuration file!

## ✅ **Benefits**

- **🔒 Per-device tokens** - Each device can have its own ngrok token
- **📸 Optional photo posting** - Only devices with tokens can post photos
- **📝 Text posting still works** - No ngrok token needed for text posts
- **🎯 Flexible setup** - Some devices can post photos, others just text

## 🚀 **How to Set Up**

### **Step 1: Get Your ngrok Token**
1. Go to https://dashboard.ngrok.com/get-started/your-authtoken
2. Copy your authtoken (looks like: `2abc123def456_your_token_here`)

### **Step 2: Add Token to Device**
1. **Go to Devices page** in your frontend
2. **Click on a device** to open device details
3. **Scroll to "Device Information"** section
4. **Find "ngrok Token (Optional)"** field
5. **Paste your token** in the password field
6. **Click "Save"**

### **Step 3: Use Photo Posting**
1. **Create template** with `photosPostsPerDay > 0`
2. **Select photos folder** (like "PFP")
3. **Select captions file** (optional)
4. **Run template** - photos will be automatically processed and posted!

## 🎯 **How It Works**

### **With ngrok Token:**
```
✅ Device has ngrok token
📸 Photo posting enabled
🚀 Full workflow: select → clean → serve → download → post
```

### **Without ngrok Token:**
```
⚠️ Device has no ngrok token  
📝 Text posting only
🚀 Text workflow: select caption → post text
```

## 🔧 **Device Settings UI**

The device detail page now shows:

```
Device Information
├── Model: iPhone 7
├── Appium Port: 4741
├── WDA Port: 8109
└── ngrok Token (Optional) [password field] [Save button]
    💡 Photo posting: Only needed for Mac → iPhone photo transfers
```

## 📊 **Template Behavior**

### **Photo Posts with Token:**
- ✅ Selects random photo from folder
- ✅ Cleans metadata using your cleaner script
- ✅ Creates device-specific ngrok tunnel
- ✅ Downloads photo to iPhone via Safari
- ✅ Posts to Threads with caption

### **Photo Posts without Token:**
- ⚠️ Skips photo posts with helpful message:
  ```
  ⚠️ No ngrok token set for device 4 - skipping photo post 1
  💡 Set ngrok token in device settings to enable photo posting
  ```

### **Text Posts:**
- ✅ Always work regardless of ngrok token
- ✅ Uses captions/text from Excel files
- ✅ No photo download needed

## 🎉 **Ready to Use!**

1. **✅ Add ngrok token** to any device that needs photo posting
2. **✅ Leave empty** for devices that only do text posting  
3. **✅ Mix and match** - some devices photos, others text only
4. **✅ Fully flexible** photo posting system!

Your photo posting is now **completely optional and device-specific**! 🚀📸
