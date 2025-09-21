# Threads Working Tests

This directory contains working Threads automation tests that have been tested and verified on real devices.

## Login Functionality Tests

### 1. Basic Login Test
- **File**: `threads_login_test.py`
- **Description**: Complete Threads login flow with 8-checkpoint system
- **Features**:
  - Launch Threads app from desktop
  - Navigate to login screen
  - Enter username/email/mobile number
  - Enter password
  - Handle verification (2FA/email)
  - Verify login success
  - Return to safe state
- **Usage**: `python3 threads_login_test.py`

### 2. 2FA Login Test
- **File**: `threads_2fa_login_test.py`
- **Description**: Threads login with 2FA verification
- **Features**:
  - Complete login flow
  - 2FA code entry
  - Verification handling
- **Usage**: `python3 threads_2fa_login_test.py`

### 3. Complete 2FA Login Test
- **File**: `threads_complete_2fa_login_test.py`
- **Description**: Comprehensive 2FA login with email verification
- **Features**:
  - Gmail verification service integration
  - Complete 2FA flow
  - Error handling and recovery
- **Usage**: `python3 threads_complete_2fa_login_test.py`

## Supporting Files

### Action Classes
- **`login_action.py`**: Base login action class
- **`2fa_login_action.py`**: 2FA login action class
- **`base_action.py`**: Base action class with common functionality

### Services
- **`gmail_verification_service.py`**: Gmail email verification service
- **`logging_system.py`**: Comprehensive logging system

## Test Configuration

### Device Setup
- **Device UDID**: `ae6f609c40f74faeadc5a83c8c96bf8c6d0b3ccf`
- **Platform**: iOS
- **Appium Port**: 4741
- **WDA Port**: 8109

### Credentials
- **Test Username**: `nikita64712025c`
- **Test Password**: `datNe4zRS5qy`

## Features

### 8-Checkpoint System
1. **Launch Threads App**: Launch from desktop
2. **Navigate to Login**: Find and click login button
3. **Enter Username**: Enter username/email/mobile
4. **Enter Password**: Enter account password
5. **Click Login Button**: Submit login form
6. **Handle Verification**: Handle 2FA or email verification
7. **Verify Login Success**: Confirm successful login
8. **Return Safe State**: Navigate to main feed

### Evidence Collection
- Screenshots at each checkpoint
- XML page source dumps
- Comprehensive logging
- Error tracking and recovery

### Error Handling
- Element not found handling
- Timeout management
- Modal and popup handling
- Verification failure recovery

## Usage

1. **Start Appium Server**: Ensure Appium is running on port 4741
2. **Connect Device**: Connect your iOS device via USB
3. **Run Test**: Execute the desired test file
4. **Check Logs**: Review logs and evidence in the generated directories

## Logging

All tests generate comprehensive logs including:
- Action-level logging with timestamps
- Screenshot and XML capture
- Error tracking and recovery
- Performance metrics
- Session summaries

## Status

✅ **All tests are working and verified on real devices**
✅ **Comprehensive error handling implemented**
✅ **Evidence collection working**
✅ **Integration with backend appium service**
