# 🤖 Complete FSN Workflow System

> **Complete Device-to-Template Automation System**  
> **Built for Threads automation with Crane container support**  
> **Status:** Production Ready

---

## 🎯 **SYSTEM OVERVIEW**

This system provides a complete workflow from frontend template selection to device automation execution. When you start a device with a template (e.g., "2 text posts per day"), the system:

1. **Initializes the phone** (starts Appium, connects to device)
2. **Handles jailbroken devices** (long-presses Threads icon, selects Crane container)
3. **Executes template actions** (runs existing Threads automation scripts)
4. **Provides real-time updates** (WebSocket status tracking)

---

## 🏗️ **SYSTEM ARCHITECTURE**

### **Core Components**

```
Frontend (React) 
    ↓ (HTTP/WebSocket)
Backend API (FastAPI)
    ↓
Job Execution Service
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│ Device Init     │ Container Switch│ Template Exec   │
│ (Appium Start)  │ (Crane)         │ (Threads Scripts)│
└─────────────────┴─────────────────┴─────────────────┘
    ↓
Real Device (iPhone)
```

### **File Structure**

```
api/
├── services/
│   ├── job_execution_service.py      # Main workflow orchestrator
│   ├── job_websocket_service.py      # Real-time updates
│   ├── template_action_mapper.py     # Maps templates to actions
│   ├── crane_account_switching.py    # Container switching
│   ├── crane_container_service.py    # Container management
│   └── appium_template_executor.py   # Script execution
├── routes/
│   ├── jobs.py                       # Job management API
│   └── job_websocket.py             # WebSocket endpoints
└── models/
    ├── device.py                     # Device model
    └── account.py                    # Account model
```

---

## 🚀 **COMPLETE WORKFLOW**

### **1. Frontend Template Execution**
When you click "Start Template" in the frontend:

```typescript
// Frontend sends job start request
const response = await fetch('/api/v1/jobs/start', {
  method: 'POST',
  body: JSON.stringify({
    template_id: "template_123",
    device_id: "device_4", 
    account_ids: ["account_1", "account_2"],
    execution_mode: "normal"
  })
})
```

### **2. Backend Job Creation**
The backend creates a job and starts execution:

```python
# Job Execution Service
job_id = f"job_{uuid.uuid4().hex[:8]}"
await job_execution_service.start_job(job_id, template, device, accounts)
```

### **3. Device Initialization**
```python
# Step 1: Start Appium server
await self._start_appium_server(device)

# Step 2: Connect to device
await self._connect_to_device(device)
```

### **4. Container Switching (Jailbroken Devices)**
```python
# Step 2: Long press Threads icon
await crane_threads_account_switching.complete_crane_account_switch_flow(
    device.udid, 
    account.container_id, 
    "threads"
)
```

### **5. Template Execution**
```python
# Step 3: Execute template actions
actions = template_action_mapper.map_template_to_actions(template)
await appium_template_executor.execute_template(template, device, accounts)
```

---

## 📋 **TEMPLATE MAPPING**

### **Template Settings → Actions**

| Template Setting | Action Generated | Script Used |
|------------------|------------------|-------------|
| `textPostsPerDay: 2` | 2x POST_THREAD | `06_post_thread_functionality_test.py` |
| `photosPostsPerDay: 1` | 1x POST_THREAD (with images) | `06_post_thread_functionality_test.py` |
| `likesPerDay: 10` | 10x LIKE_POST | `01_like_post_functionality_test.py` |
| `followsPerDay: 5` | 5x FOLLOW_USER | `03_search_profile_functionality_test.py` |
| `scrollingTimeMinutes: 30` | 60x VIEW_THREAD | `05_view_thread_functionality_test.py` |

### **Example Template Configuration**
```json
{
  "id": "template_123",
  "name": "Threads Daily Activity",
  "platform": "threads",
  "settings": {
    "textPostsPerDay": 2,
    "textPostsFile": "threads_posts.txt",
    "photosPostsPerDay": 1,
    "photosFolder": "threads_photos",
    "likesPerDay": 10,
    "followsPerDay": 5,
    "scrollingTimeMinutes": 30
  }
}
```

**Generated Actions:**
- 2x POST_THREAD (text posts)
- 1x POST_THREAD (photo post)
- 10x LIKE_POST
- 5x FOLLOW_USER
- 60x VIEW_THREAD (scrolling)

---

## 🔄 **REAL-TIME UPDATES**

### **WebSocket Connection**
```javascript
// Frontend connects to WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/jobs/ws?job_id=job_123')

ws.onmessage = (event) => {
  const update = JSON.parse(event.data)
  console.log(`Job ${update.job_id}: ${update.data.status} - ${update.data.progress}%`)
}
```

### **Status Updates**
```json
{
  "type": "job_update",
  "job_id": "job_123",
  "data": {
    "status": "executing",
    "progress": 75,
    "current_step": "executing_template"
  }
}
```

---

## 🛠️ **API ENDPOINTS**

### **Job Management**
- `POST /api/v1/jobs/start` - Start a new job
- `GET /api/v1/jobs/{job_id}/status` - Get job status
- `GET /api/v1/jobs` - Get all jobs
- `POST /api/v1/jobs/{job_id}/stop` - Stop a job
- `DELETE /api/v1/jobs/{job_id}` - Delete a job

### **WebSocket**
- `WS /api/v1/jobs/ws?job_id={job_id}` - Real-time job updates

---

## 📱 **DEVICE SUPPORT**

### **Jailbroken Devices**
- ✅ **Crane Container Support** - Automatic container switching
- ✅ **Account Isolation** - Each account uses its own container
- ✅ **Long Press Detection** - Automatically detects and handles Crane menu

### **Non-Jailbroken Devices**
- ✅ **Standard Appium** - Direct app control
- ✅ **Single Account** - One account per device

---

## 🧵 **THREADS AUTOMATION SCRIPTS**

### **Available Actions**
| Action | Script | Status | Description |
|--------|--------|--------|-------------|
| **POST_THREAD** | `06_post_thread_functionality_test.py` | ✅ Working | Create text/image threads |
| **LIKE_POST** | `01_like_post_functionality_test.py` | ✅ Working | Like/unlike threads |
| **COMMENT_POST** | `02_comment_post_functionality_test.py` | ✅ Working | Comment on threads |
| **SCAN_PROFILE** | `04_scan_profile_functionality_test.py` | ✅ Working | Profile data extraction |
| **SEARCH_PROFILE** | `03_search_profile_functionality_test.py` | ✅ Working | Search users |
| **VIEW_THREAD** | `05_view_thread_functionality_test.py` | ✅ Working | View/scroll threads |
| **REPLY_TO_THREAD** | `07_reply_to_thread_functionality_test.py` | ✅ Working | Reply to threads |
| **REPOST** | `08_repost_functionality_test.py` | ✅ Working | Repost content |
| **QUOTE_POST** | `09_quote_post_functionality_test.py` | ✅ Working | Quote with commentary |
| **EDIT_PROFILE** | `12_edit_profile_functionality_test.py` | ✅ Working | Profile customization |

---

## 🎯 **USAGE EXAMPLE**

### **Complete Workflow Example**

1. **Frontend**: User selects template "2 text posts per day" for device "iPhone7"
2. **Backend**: Creates job `job_abc123` and starts execution
3. **Device Init**: Starts Appium server on port 4741, connects to iPhone
4. **Container Switch**: Long-presses Threads icon, selects "Container 4" for account
5. **Template Exec**: Runs `06_post_thread_functionality_test.py` twice
6. **Real-time Updates**: Frontend receives progress updates via WebSocket
7. **Completion**: Job marked as completed, results logged

### **Expected Logs**
```
INFO: Job job_abc123 started successfully
INFO: Device iPhone7 initialized successfully  
INFO: Long pressed Threads icon successfully
INFO: Selected container Container 4 successfully
INFO: Launched Threads with selected container
INFO: Executing script: 06_post_thread_functionality_test.py
INFO: Thread posted successfully
INFO: Executing script: 06_post_thread_functionality_test.py  
INFO: Thread posted successfully
INFO: Job job_abc123 completed successfully
```

---

## 🔧 **CONFIGURATION**

### **Device Configuration**
```python
device = Device(
    id="device_4",
    udid="ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf",
    platform="iOS",
    name="iPhone7",
    jailbroken=True,  # Enable Crane support
    appium_port=4741,
    wda_port=8109,
    # ... other settings
)
```

### **Account Configuration**
```python
account = Account(
    id="account_1",
    username="test_user",
    platform="threads",
    container_id="container_4",  # Crane container ID
    # ... other settings
)
```

---

## 🚨 **ERROR HANDLING**

### **Common Issues & Solutions**

| Issue | Cause | Solution |
|-------|-------|----------|
| **Appium startup failed** | Port already in use | Kill existing process, restart |
| **Device connection failed** | WDA not running | Start WDA, check UDID |
| **Container switch failed** | Crane not installed | Install Crane on jailbroken device |
| **Script execution failed** | Missing dependencies | Install required Python packages |
| **WebSocket disconnected** | Network issue | Reconnect, check backend status |

---

## 📊 **MONITORING & LOGGING**

### **Job Status Tracking**
- ✅ **Real-time Progress** - WebSocket updates every step
- ✅ **Error Logging** - Detailed error messages and stack traces
- ✅ **Performance Metrics** - Execution time, success rates
- ✅ **Audit Trail** - Complete job history and results

### **Log Files**
- `job_execution.log` - Main execution logs
- `appium.log` - Appium server logs  
- `crane_switching.log` - Container switching logs
- `threads_automation.log` - Script execution logs

---

## 🎉 **READY TO USE!**

The complete workflow system is now ready! When you:

1. **Start a device** with a template in the frontend
2. **The system automatically**:
   - Initializes your iPhone
   - Handles Crane container switching (if jailbroken)
   - Executes the template actions using existing Threads scripts
   - Provides real-time updates via WebSocket

**Your 2 text posts per day template will now work end-to-end!** 🚀

---

*This system integrates all your existing Appium scripts with a complete job management and real-time monitoring system.*
