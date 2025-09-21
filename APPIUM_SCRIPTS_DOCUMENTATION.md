# 🤖 FSN APPIUM SCRIPTS DOCUMENTATION

> **Complete Guide to All Appium Automation Scripts**  
> **Last Updated:** January 16, 2025  
> **Status:** Production Ready

---

## 📋 **OVERVIEW**

This document provides a comprehensive mapping of all Appium automation scripts in the FSN System Backend, organized by platform and functionality.

### **Platforms Supported**
- ✅ **Instagram** - 100% Complete (14/14 actions)
- 🔄 **Threads** - Phase 2 Development (Clean sheet)
- 🔧 **Shared Utilities** - Common Appium infrastructure

---

## 🏗️ **DIRECTORY STRUCTURE**

```
FSN-System-Backend-main/
├── platforms/
│   ├── config.py                           # Central platform configuration
│   ├── shared/                             # Shared utilities
│   │   └── utils/
│   │       ├── appium_driver.py           # Driver management
│   │       └── checkpoint_system.py       # 8-checkpoint verification system
│   ├── instagram/                          # Instagram automation (100% complete)
│   │   └── instagram_automation/
│   │       ├── actions/                    # Action implementations
│   │       └── tests/real_device/         # Real device tests
│   └── threads/                            # Threads automation (Phase 2)
│       ├── actions/                        # Action implementations
│       ├── tests/                          # Development tests
│       ├── working_tests/                  # Production-ready tests
│       └── threads_automation/            # Legacy tests
└── FSN-MAC-AGENT/                          # Local backend
    └── local-backend.py                   # Main backend server
```

---

## 🎯 **INSTAGRAM AUTOMATION (100% COMPLETE)**

### **Location:** `platforms/instagram/instagram_automation/`

#### **✅ CONFIRMED WORKING ACTIONS (14 Total)**

| Action | File | Status | Description |
|--------|------|--------|-------------|
| **LIKE_POST** | `tests/real_device/simple_like_test.py` | ✅ Production | Like/unlike posts |
| **COMMENT_POST** | `tests/real_device/comment_functionality_test.py` | ✅ Production | Comment on posts (7 checkpoints) |
| **FOLLOW_UNFOLLOW** | `tests/real_device/follow_unfollow_functionality_test.py` | ✅ Production | Follow/unfollow users |
| **SCAN_PROFILE** | `tests/real_device/simple_scan_profile_test.py` | ✅ Production | Profile data extraction |
| **POST_PICTURE** | `tests/real_device/post_picture_functionality_test.py` | ✅ Production | Upload pictures (8 checkpoints) |
| **POST_REEL** | `tests/real_device/post_reel_functionality_test.py` | ✅ Production | Upload reels |
| **POST_STORY** | `tests/real_device/post_story_functionality_test.py` | ✅ Production | Upload stories |
| **POST_CAROUSEL** | `tests/real_device/post_carousel_functionality_test.py` | ✅ Production | Upload carousel posts |
| **SEARCH_HASHTAG** | `tests/real_device/search_hashtag_functionality_test.py` | ✅ Production | Search hashtags |
| **SAVE_POST** | `tests/real_device/save_post_functionality_test.py` | ✅ Production | Save posts |
| **VIEW_STORY** | `tests/real_device/working_story_test.py` | ✅ Production | View stories |
| **EDIT_PROFILE** | `tests/real_device/edit_profile_functionality_test.py` | ✅ Production | Edit profile |
| **CAMERA_MODE_SWITCHING** | `actions/camera/mode_switcher.py` | ✅ Production | Camera mode switching (83.3% success) |
| **UNIVERSAL_AD_RECOVERY** | `tests/real_device/universal_ad_recovery.py` | ✅ Production | Ad recovery system |

#### **🔧 SUPPORTING FILES**

| File | Purpose | Location |
|------|---------|----------|
| `actions/confirmed_working/selectors_registry.py` | All confirmed selectors | `instagram_automation/actions/confirmed_working/` |
| `actions/confirmed_working/scroll_actions.py` | Scroll functionality | `instagram_automation/actions/confirmed_working/` |
| `actions/camera/mode_switcher_lib.py` | Camera library version | `instagram_automation/actions/camera/` |

#### **🧪 TEST UTILITIES**

| File | Purpose | Location |
|------|---------|----------|
| `tests/real_device/scroll_home_feed_test.py` | Home feed scrolling | `instagram_automation/tests/real_device/` |
| `tests/real_device/scroll_reels_test.py` | Reels scrolling | `instagram_automation/tests/real_device/` |
| `tests/real_device/find_ad_and_test_recovery.py` | Ad detection | `instagram_automation/tests/real_device/` |
| `tests/real_device/test_own_profile_only.py` | Profile testing | `instagram_automation/tests/real_device/` |
| `tests/working_tests/instagram_login_test.py` | Login functionality | `instagram_automation/tests/working_tests/` |

---

## 🧵 **THREADS AUTOMATION (PHASE 2 DEVELOPMENT)**

### **Location:** `platforms/threads/`

#### **🔄 DEVELOPMENT STATUS**
- **Status:** Phase 2 Development - Clean Sheet
- **Completion:** 0% (fresh start)
- **Architecture:** Reusing proven Instagram patterns

#### **📋 PLANNED ACTIONS (15 Total)**

| Phase | Action | File | Status | Description |
|-------|--------|------|--------|-------------|
| **2A** | LIKE_POST | `working_tests/01_like_post_functionality_test.py` | ✅ Working | Like/unlike threads |
| **2A** | COMMENT_POST | `working_tests/02_comment_post_functionality_test.py` | ✅ Working | Comment on threads |
| **2A** | SCAN_PROFILE | `working_tests/04_scan_profile_functionality_test.py` | ✅ Working | Profile scanning |
| **2A** | SEARCH_PROFILE | `working_tests/03_search_profile_functionality_test.py` | ✅ Working | Search users |
| **2A** | VIEW_THREAD | `working_tests/05_view_thread_functionality_test.py` | ✅ Working | Thread viewing |
| **2B** | POST_THREAD | `working_tests/06_post_thread_functionality_test.py` | ✅ Working | Create threads |
| **2B** | REPLY_TO_THREAD | `working_tests/07_reply_to_thread_functionality_test.py` | ✅ Working | Reply to threads |
| **2B** | REPOST | `working_tests/08_repost_functionality_test.py` | ✅ Working | Repost content |
| **2B** | QUOTE_POST | `working_tests/09_quote_post_functionality_test.py` | ✅ Working | Quote with commentary |
| **2C** | EDIT_PROFILE | `working_tests/12_edit_profile_functionality_test.py` | ✅ Working | Profile customization |
| **2C** | THREAD_ANALYTICS | `working_tests/13_thread_analytics_functionality_test.py` | ✅ Working | Engagement metrics |
| **2C** | NOTIFICATIONS | `working_tests/14_notifications_functionality_test.py` | ✅ Working | Notification handling |

#### **🔧 SUPPORTING FILES**

| File | Purpose | Location |
|------|---------|----------|
| `actions/login_action.py` | Login functionality | `threads/actions/` |
| `actions/scroll_actions.py` | Scroll functionality | `threads/actions/` |
| `base_action.py` | Base action class | `threads/` |
| `post_thread.py` | Thread posting | `threads/` |

#### **🧪 TEST FILES**

| File | Purpose | Location |
|------|---------|----------|
| `tests/app_launch_test.py` | App launch testing | `threads/tests/` |
| `working_tests/00_login_functionality_test.py` | Login testing | `threads/working_tests/` |
| `working_tests/scroll_home_feed_test.py` | Home feed scrolling | `threads/working_tests/` |
| `working_tests/threads_account_switching_test.py` | Account switching | `threads/working_tests/` |

#### **🔄 LEGACY TESTS**

| File | Purpose | Location |
|------|---------|----------|
| `threads_automation/tests/working_tests/threads_login_test.py` | Legacy login test | `threads/threads_automation/tests/working_tests/` |
| `threads_automation/tests/working_tests/threads_2fa_login_test.py` | 2FA login test | `threads/threads_automation/tests/working_tests/` |
| `threads_automation/tests/working_tests/threads_complete_2fa_login_test.py` | Complete 2FA test | `threads/threads_automation/tests/working_tests/` |
| `threads_automation/tests/working_tests/login_action.py` | Login action class | `threads/threads_automation/tests/working_tests/` |
| `threads_automation/tests/working_tests/2fa_login_action.py` | 2FA action class | `threads/threads_automation/tests/working_tests/` |
| `threads_automation/tests/working_tests/base_action.py` | Base action class | `threads/threads_automation/tests/working_tests/` |
| `threads_automation/tests/working_tests/gmail_verification_service.py` | Gmail service | `threads/threads_automation/tests/working_tests/` |
| `threads_automation/tests/working_tests/logging_system.py` | Logging system | `threads/threads_automation/tests/working_tests/` |

---

## 🔧 **SHARED UTILITIES**

### **Location:** `platforms/shared/utils/`

| File | Purpose | Description |
|------|---------|-------------|
| `appium_driver.py` | Driver management | AppiumDriverManager class for device connections |
| `checkpoint_system.py` | Verification system | 8-checkpoint verification system (ABC base class) |

---

## ⚙️ **CONFIGURATION FILES**

### **Location:** `platforms/`

| File | Purpose | Description |
|------|---------|-------------|
| `config.py` | Platform configuration | Central config for all platforms, device settings, and capabilities |

### **Device Configuration**
```python
DEVICE_CONFIG = {
    "udid": "f2fea37cddcf6e5c45862acfc98dd4a771a4c9f3",  # PhoneX
    "appium_port": 4735,
    "wda_port": 8100,
    "ios_version": "15.8.3"
}
```

---

## 🚀 **BACKEND INTEGRATION**

### **Location:** `FSN-MAC-AGENT/`

| File | Purpose | Description |
|------|---------|-------------|
| `local-backend.py` | Main backend server | FastAPI server with device management and Appium integration |

### **Key Features**
- ✅ Device management (start/stop)
- ✅ WebSocket support for real-time updates
- ✅ License validation system
- ✅ Appium process management
- ✅ CORS support for frontend integration

---

## 📊 **USAGE EXAMPLES**

### **Running Instagram Tests**
```bash
cd platforms/instagram/instagram_automation/tests/real_device/
python3 simple_like_test.py
python3 comment_functionality_test.py
python3 follow_unfollow_functionality_test.py
```

### **Running Threads Tests**
```bash
cd platforms/threads/working_tests/
python3 01_like_post_functionality_test.py
python3 02_comment_post_functionality_test.py
python3 03_search_profile_functionality_test.py
```

### **Starting Backend Server**
```bash
cd FSN-MAC-AGENT/
python3 local-backend.py
```

---

## 🎯 **DEVELOPMENT WORKFLOW**

### **1. Instagram (100% Complete)**
- All 14 actions are production-ready
- Tests verified on real devices
- No further development needed

### **2. Threads (Phase 2 Development)**
- Clean sheet implementation
- Reusing proven Instagram patterns
- 8-checkpoint verification system
- Real device testing required

### **3. Adding New Actions**
1. Create test file in appropriate platform directory
2. Implement 8-checkpoint verification system
3. Test on real device
4. Move to `working_tests/` when complete
5. Update documentation

---

## 🔍 **KEY FEATURES**

### **8-Checkpoint System**
Every automation script uses a standardized 8-checkpoint verification system:
1. **App Launch** - Verify app opens
2. **Navigation** - Navigate to target screen
3. **Element Detection** - Find target elements
4. **Action Execution** - Perform the action
5. **Verification** - Confirm action success
6. **Error Handling** - Handle failures gracefully
7. **Recovery** - Return to safe state
8. **Cleanup** - Proper session cleanup

### **Real Device Testing**
- All scripts tested on actual iOS devices
- Screenshots and XML dumps collected
- Production-ready with error handling

### **Modular Architecture**
- Shared utilities for common functionality
- Platform-specific implementations
- Easy to extend and maintain

---

## 📝 **NOTES**

- **Instagram**: 100% complete, production-ready
- **Threads**: Phase 2 development, clean sheet approach
- **Device UDID**: `ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf` (your iPhone)
- **Appium Port**: 4741
- **WDA Port**: 8109
- **Bundle IDs**: 
  - Instagram: `com.burbn.instagram`
  - Threads: `com.burbn.threads`

---

*This documentation is automatically generated and maintained by the FSN Appium Team.*
