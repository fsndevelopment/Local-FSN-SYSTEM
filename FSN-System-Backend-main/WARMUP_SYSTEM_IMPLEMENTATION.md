# FSN Warmup System Implementation Guide

## Overview
The Warmup System is a comprehensive automation feature that allows accounts to perform engagement activities (scrolling, liking, following) without posting content. It works alongside the existing template system but focuses on building account credibility through organic engagement patterns.

## System Architecture

### Core Components
1. **Warmup Templates** - Multi-day configuration templates for engagement activities
2. **Account Phase Management** - Toggle between Warmup and Posting phases per account
3. **Warmup Execution Engine** - Automated engagement without posting
4. **Progress Tracking** - Daily completion tracking and statistics
5. **Device Integration** - Same device setup as templates (container switching, app launch)

## Database Schema

### Warmup Templates Table
```sql
CREATE TABLE warmup_templates (
    id INTEGER PRIMARY KEY,
    license_id VARCHAR(100) NOT NULL,
    platform VARCHAR(20) NOT NULL,  -- 'threads' or 'instagram'
    name VARCHAR(100) NOT NULL,
    total_days INTEGER DEFAULT 1,
    days_config JSON NOT NULL,  -- Configuration for each day
    scroll_minutes_per_day INTEGER DEFAULT 0,
    likes_per_day INTEGER DEFAULT 0,
    follows_per_day INTEGER DEFAULT 0,
    posting_interval_minutes INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

### Warmup Day Configs Table
```sql
CREATE TABLE warmup_day_configs (
    id INTEGER PRIMARY KEY,
    warmup_template_id INTEGER NOT NULL,
    day_number INTEGER NOT NULL,  -- 1, 2, 3, etc.
    scroll_minutes INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    follows_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Frontend Implementation

### 1. Warmup Template Editor Updates
**File**: `FSN-System-Frontend-main/app/(warmup)/warmup/page.tsx`

**Changes Required**:
- ✅ Remove Comments field from day configuration
- ✅ Remove Stories field from day configuration  
- ✅ Remove Posts field from day configuration
- ✅ Keep only: Scroll (min), Likes, Follows
- ✅ Multi-day configuration already implemented
- ✅ Copy settings from previous day when adding new day

### 2. Account Phase Selection
**File**: `FSN-System-Frontend-main/app/(accounts)/accounts/[id]/page.tsx`

**New Feature**:
- Add phase selector for each account: "Warmup" or "Posting"
- Store phase preference per account
- Show current phase status in account list

### 3. Device Assignment Updates
**File**: `FSN-System-Frontend-main/app/(devices)/devices/[id]/page.tsx`

**Changes Required**:
- Allow assignment of both Template AND Warmup Template to same device
- Show both assignments in device configuration
- Display which accounts use which template type

### 4. Running Page Integration
**File**: `FSN-System-Frontend-main/app/(running)/running/page.tsx`

**New Features**:
- Show warmup status alongside template status
- Display warmup progress: current day, completion status
- Show warmup statistics: likes today, follows today, scroll time remaining
- Account popup with warmup-specific information

## Backend Implementation

### 1. API Endpoints
**Files**: `FSN-System-Backend-main/api/routers/warmup_templates.py`

**Required Endpoints**:
- `GET /api/v1/warmup-templates` - List warmup templates
- `POST /api/v1/warmup-templates` - Create warmup template
- `PUT /api/v1/warmup-templates/{id}` - Update warmup template
- `DELETE /api/v1/warmup-templates/{id}` - Delete warmup template
- `GET /api/v1/warmup-templates/{id}` - Get specific template

### 2. Warmup Execution Engine
**File**: `FSN-System-Backend-main/FSN-MAC-AGENT/local-backend.py`

**New Functions**:
- `execute_warmup_session()` - Main warmup execution function
- `execute_warmup_scrolling()` - Handle scrolling activities
- `execute_warmup_likes()` - Handle liking activities  
- `execute_warmup_follows()` - Handle following activities
- `track_warmup_progress()` - Update warmup statistics

### 3. Warmup Tracking System
**File**: `FSN-System-Backend-main/FSN-MAC-AGENT/accounts_warmup_tracking_local_dev.json`

**JSON Structure**:
```json
{
  "license_dev": {
    "account_id": "1234567890": {
      "warmup_completed_today": true,
      "current_day": 3,
      "last_warmup_date": "2025-01-23",
      "warmup_stats": {
        "day_1": {
          "likes": 5,
          "follows": 2, 
          "scroll_minutes": 10,
          "completed_at": "2025-01-21T10:30:00Z"
        },
        "day_2": {
          "likes": 8,
          "follows": 3,
          "scroll_minutes": 15,
          "completed_at": "2025-01-22T14:20:00Z"
        },
        "day_3": {
          "likes": 12,
          "follows": 5,
          "scroll_minutes": 20,
          "completed_at": "2025-01-23T16:45:00Z"
        }
      },
      "next_warmup_day": 4,
      "warmup_template_id": "template_123"
    }
  }
}
```

## Automation Test Implementation

### 1. Warmup Test Classes
**Files**: 
- `FSN-System-Backend-main/platforms/threads/working_tests/warmup_scrolling_test.py`
- `FSN-System-Backend-main/platforms/threads/working_tests/warmup_likes_test.py`
- `FSN-System-Backend-main/platforms/threads/working_tests/warmup_follows_test.py`

**Test Structure**:
- Same checkpoint system as posting tests
- Focus on engagement activities only
- Profile verification and data extraction
- Evidence collection for warmup activities

### 2. Warmup Checkpoint Sequence
1. **Launch Threads App** - Same as posting
2. **Navigate to Feed** - Start scrolling area
3. **Execute Scrolling** - Scroll for specified minutes
4. **Execute Likes** - Like posts during scrolling
5. **Execute Follows** - Follow accounts during scrolling
6. **Navigate to Profile** - Verify account
7. **Extract Profile Data** - Username, name, followers
8. **Save Evidence** - Screenshots and logs
9. **Update Tracking** - Save warmup progress

## Execution Flow

### Daily Warmup Process
1. **Account Selection**: System identifies accounts in "Warmup" phase
2. **Cooldown Check**: Verify account hasn't completed warmup today
3. **Day Determination**: Check which warmup day to execute next
4. **Template Loading**: Load warmup template with day-specific settings
5. **Device Setup**: Same as posting (container switching, app launch)
6. **Activity Execution**: Execute scrolling, liking, following
7. **Progress Tracking**: Update JSON with completion status
8. **Next Day Setup**: Prepare for next warmup day tomorrow

### Account Phase Logic
- **Warmup Phase**: Execute warmup template activities only
- **Posting Phase**: Execute regular template activities (posts, etc.)
- **Mixed Phase**: Not supported - account must be in one phase at a time
- **Phase Switching**: Manual selection in accounts page

## Cooldown Management

### Warmup Cooldowns
- **Daily Limit**: 1 warmup session per account per day
- **Interval**: Respect `posting_interval_minutes` between warmup sessions
- **Tracking**: Separate from posting cooldowns
- **Reset**: Daily reset at midnight for warmup eligibility

### Integration with Existing Cooldown System
- Extend `LAST_ACCOUNT_SESSIONS` to track warmup vs posting
- Separate cooldown calculations for warmup activities
- Smart scheduling to avoid conflicts between warmup and posting

## User Interface Updates

### Running Page Enhancements
- **Account Status Display**:
  - Current phase: "Warmup" or "Posting"
  - Warmup progress: "Day 3/10" or "Completed"
  - Today's stats: Likes: 8, Follows: 3, Scroll: 15min
  - Cooldown: "Ready" or "2h 30m remaining"

### Device Configuration
- **Template Assignment**:
  - Regular Template: [Dropdown]
  - Warmup Template: [Dropdown]
  - Both can be assigned to same device
  - Account-level phase selection determines which executes

### Account Management
- **Phase Selector**:
  - Toggle between "Warmup" and "Posting"
  - Visual indicator of current phase
  - Bulk phase changes for multiple accounts

## Data Flow

### Template Creation Flow
1. User creates warmup template in `/warmup` page
2. Configures multiple days with different settings
3. Template saved to database with JSON day configurations
4. Template available for device assignment

### Execution Flow
1. User assigns warmup template to device
2. User sets account phase to "Warmup" in accounts page
3. User starts device from running page
4. System checks account phase and executes appropriate template
5. Warmup activities performed with progress tracking
6. Daily completion recorded in JSON file

### Progress Tracking Flow
1. Warmup session completes successfully
2. Statistics saved to JSON file
3. Current day incremented for next execution
4. Cooldown timer started
5. UI updated with new progress information

## Testing Strategy

### Unit Tests
- Warmup template creation and validation
- Day configuration management
- Progress tracking accuracy
- Cooldown calculation correctness

### Integration Tests
- End-to-end warmup execution
- Account phase switching
- Device assignment with both template types
- JSON file persistence and retrieval

### Manual Testing
- Create warmup template with multiple days
- Assign to device and set account phases
- Execute warmup sessions and verify progress
- Test cooldown and daily limits
- Verify UI updates and statistics display

## Implementation Checklist

### Backend Tasks
- [ ] Create warmup template database models
- [ ] Create database migration for warmup tables
- [ ] Implement warmup template API endpoints
- [ ] Create warmup execution engine in local-backend.py
- [ ] Implement warmup tracking JSON system
- [ ] Create warmup automation test classes
- [ ] Extend cooldown system for warmup activities

### Frontend Tasks
- [ ] Remove comments/stories/posts from warmup template editor
- [ ] Add account phase selection in accounts page
- [ ] Update device assignment for dual template support
- [ ] Enhance running page with warmup status display
- [ ] Add warmup statistics to account popups
- [ ] Implement warmup progress indicators

### Integration Tasks
- [ ] Test warmup template creation and saving
- [ ] Test account phase switching functionality
- [ ] Test warmup execution with real devices
- [ ] Test progress tracking and JSON persistence
- [ ] Test cooldown system integration
- [ ] Test UI updates and real-time statistics

### Documentation Tasks
- [ ] Update API documentation for warmup endpoints
- [ ] Create user guide for warmup template creation
- [ ] Document warmup execution process
- [ ] Create troubleshooting guide for warmup issues

## Success Criteria

### Functional Requirements
- ✅ Warmup templates can be created with multiple days
- ✅ Comments, stories, and posts fields removed from warmup editor
- ✅ Accounts can be set to Warmup or Posting phase
- ✅ Devices can have both template types assigned
- ✅ Warmup execution performs scrolling, liking, following only
- ✅ Daily progress tracking works correctly
- ✅ Cooldown system respects daily limits
- ✅ UI shows warmup progress and statistics

### Performance Requirements
- ✅ Warmup execution completes within reasonable time
- ✅ Progress tracking doesn't impact system performance
- ✅ UI updates in real-time during warmup execution
- ✅ JSON file operations are fast and reliable

### User Experience Requirements
- ✅ Intuitive warmup template creation process
- ✅ Clear account phase selection interface
- ✅ Comprehensive warmup progress visibility
- ✅ Easy switching between warmup and posting phases
- ✅ Accurate cooldown and completion status display

## Future Enhancements

### Advanced Features
- **Warmup Analytics**: Detailed statistics and progress charts
- **Bulk Operations**: Mass phase changes and template assignments
- **Warmup Scheduling**: Time-based warmup execution
- **Custom Warmup Patterns**: User-defined engagement sequences
- **Warmup Templates Library**: Pre-built templates for different account types

### Integration Improvements
- **Cross-Platform Support**: Extend to Instagram warmup
- **AI-Powered Optimization**: Smart warmup pattern recommendations
- **Advanced Cooldown Logic**: Machine learning-based timing optimization
- **Warmup Performance Metrics**: Success rate tracking and optimization

---

**Last Updated**: January 24, 2025
**Version**: 1.0
**Status**: Implementation in Progress
