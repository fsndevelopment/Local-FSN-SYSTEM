#!/usr/bin/env python3
"""
Gmail Email Verification Service
===============================

Service for handling Gmail email verification codes during Threads login.
Supports both Gmail API and IMAP access for retrieving verification codes.

Author: FSN Appium Team
Last Updated: January 15, 2025
Status: Production-ready
"""

import os
import re
import time
import logging
import imaplib
import email
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail API imports (optional)
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    GMAIL_API_AVAILABLE = True
except ImportError:
    GMAIL_API_AVAILABLE = False

logger = logging.getLogger(__name__)

class GmailVerificationService:
    """Service for retrieving Gmail verification codes"""
    
    def __init__(self, email_address: str, app_password: str = None, credentials_file: str = None):
        """
        Initialize Gmail verification service
        
        Args:
            email_address: Gmail email address
            app_password: Gmail app password for IMAP access
            credentials_file: Path to Gmail API credentials JSON file
        """
        self.email_address = email_address
        self.app_password = app_password
        self.credentials_file = credentials_file
        self.gmail_service = None
        
        # Initialize Gmail API if available
        if GMAIL_API_AVAILABLE and credentials_file:
            self._initialize_gmail_api()
    
    def _initialize_gmail_api(self):
        """Initialize Gmail API service"""
        try:
            if not os.path.exists(self.credentials_file):
                logger.warning(f"Gmail API credentials file not found: {self.credentials_file}")
                return
            
            # Gmail API scopes
            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
            
            creds = None
            token_file = 'token.json'
            
            # Load existing token
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            logger.info("✅ Gmail API initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gmail API: {str(e)}")
            self.gmail_service = None
    
    def get_verification_code_gmail_api(self, sender: str = "noreply@threads.net", 
                                      subject_contains: str = "verification", 
                                      max_attempts: int = 10, 
                                      wait_seconds: int = 5) -> Optional[str]:
        """
        Get verification code using Gmail API
        
        Args:
            sender: Email sender to filter by
            subject_contains: Text that should be in the subject
            max_attempts: Maximum number of attempts
            wait_seconds: Seconds to wait between attempts
            
        Returns:
            6-digit verification code or None
        """
        if not self.gmail_service:
            logger.error("❌ Gmail API not initialized")
            return None
        
        try:
            logger.info(f"🔍 Searching for verification email from {sender}...")
            
            for attempt in range(max_attempts):
                try:
                    # Search for emails
                    query = f'from:{sender} subject:{subject_contains} is:unread'
                    results = self.gmail_service.users().messages().list(
                        userId='me', q=query, maxResults=5
                    ).execute()
                    
                    messages = results.get('messages', [])
                    
                    if not messages:
                        logger.info(f"⏳ No verification emails found (attempt {attempt + 1}/{max_attempts})")
                        time.sleep(wait_seconds)
                        continue
                    
                    # Get the most recent message
                    message_id = messages[0]['id']
                    message = self.gmail_service.users().messages().get(
                        userId='me', id=message_id, format='full'
                    ).execute()
                    
                    # Extract verification code
                    code = self._extract_code_from_message(message)
                    if code:
                        logger.info(f"✅ Found verification code: {code}")
                        return code
                    
                    logger.info(f"⏳ No code found in email (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(wait_seconds)
                    
                except Exception as e:
                    logger.error(f"❌ Error searching emails (attempt {attempt + 1}): {str(e)}")
                    time.sleep(wait_seconds)
            
            logger.error("❌ No verification code found after all attempts")
            return None
            
        except Exception as e:
            logger.error(f"❌ Gmail API error: {str(e)}")
            return None
    
    def get_verification_code_imap(self, sender: str = "noreply@threads.net", 
                                 subject_contains: str = "verification", 
                                 max_attempts: int = 10, 
                                 wait_seconds: int = 5) -> Optional[str]:
        """
        Get verification code using IMAP
        
        Args:
            sender: Email sender to filter by
            subject_contains: Text that should be in the subject
            max_attempts: Maximum number of attempts
            wait_seconds: Seconds to wait between attempts
            
        Returns:
            6-digit verification code or None
        """
        if not self.app_password:
            logger.error("❌ Gmail app password not provided for IMAP access")
            return None
        
        try:
            logger.info(f"🔍 Connecting to Gmail IMAP...")
            
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.email_address, self.app_password)
            mail.select('inbox')
            
            for attempt in range(max_attempts):
                try:
                    # Search for unread emails from sender
                    search_criteria = f'(UNSEEN FROM "{sender}")'
                    status, messages = mail.search(None, search_criteria)
                    
                    if status != 'OK':
                        logger.error("❌ IMAP search failed")
                        time.sleep(wait_seconds)
                        continue
                    
                    email_ids = messages[0].split()
                    
                    if not email_ids:
                        logger.info(f"⏳ No unread emails from {sender} (attempt {attempt + 1}/{max_attempts})")
                        time.sleep(wait_seconds)
                        continue
                    
                    # Get the most recent email
                    latest_email_id = email_ids[-1]
                    status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
                    
                    if status != 'OK':
                        logger.error("❌ Failed to fetch email")
                        time.sleep(wait_seconds)
                        continue
                    
                    # Parse email
                    email_body = msg_data[0][1]
                    email_message = email.message_from_bytes(email_body)
                    
                    # Check subject
                    subject = email_message.get('Subject', '')
                    if subject_contains.lower() not in subject.lower():
                        logger.info(f"⏳ Subject doesn't contain '{subject_contains}' (attempt {attempt + 1}/{max_attempts})")
                        time.sleep(wait_seconds)
                        continue
                    
                    # Extract verification code
                    code = self._extract_code_from_email_message(email_message)
                    if code:
                        logger.info(f"✅ Found verification code: {code}")
                        mail.close()
                        mail.logout()
                        return code
                    
                    logger.info(f"⏳ No code found in email (attempt {attempt + 1}/{max_attempts})")
                    time.sleep(wait_seconds)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing email (attempt {attempt + 1}): {str(e)}")
                    time.sleep(wait_seconds)
            
            mail.close()
            mail.logout()
            logger.error("❌ No verification code found after all attempts")
            return None
            
        except Exception as e:
            logger.error(f"❌ IMAP error: {str(e)}")
            return None
    
    def _extract_code_from_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Extract verification code from Gmail API message"""
        try:
            # Get message body
            payload = message.get('payload', {})
            body = self._get_message_body(payload)
            
            if not body:
                return None
            
            # Extract 6-digit code
            code = self._extract_6_digit_code(body)
            return code
            
        except Exception as e:
            logger.error(f"❌ Error extracting code from message: {str(e)}")
            return None
    
    def _extract_code_from_email_message(self, email_message) -> Optional[str]:
        """Extract verification code from email message"""
        try:
            body = ""
            
            # Try to get text content
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            if not body:
                return None
            
            # Extract 6-digit code
            code = self._extract_6_digit_code(body)
            return code
            
        except Exception as e:
            logger.error(f"❌ Error extracting code from email: {str(e)}")
            return None
    
    def _get_message_body(self, payload: Dict[str, Any]) -> str:
        """Get message body from Gmail API payload"""
        try:
            if 'parts' in payload:
                # Multipart message
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body']['data']
                        return data.decode('base64').decode('utf-8', errors='ignore')
            else:
                # Single part message
                if payload['mimeType'] == 'text/plain':
                    data = payload['body']['data']
                    return data.decode('base64').decode('utf-8', errors='ignore')
            
            return ""
            
        except Exception as e:
            logger.error(f"❌ Error getting message body: {str(e)}")
            return ""
    
    def _extract_6_digit_code(self, text: str) -> Optional[str]:
        """Extract 6-digit verification code from text"""
        try:
            # Look for 6-digit codes
            patterns = [
                r'\b(\d{6})\b',  # 6 digits as word boundary
                r'code[:\s]*(\d{6})',  # "code: 123456"
                r'verification[:\s]*(\d{6})',  # "verification: 123456"
                r'(\d{6})',  # Any 6 digits
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    code = matches[0]
                    if len(code) == 6 and code.isdigit():
                        return code
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extracting 6-digit code: {str(e)}")
            return None
    
    def get_verification_code(self, sender: str = "noreply@threads.net", 
                            subject_contains: str = "verification", 
                            max_attempts: int = 10, 
                            wait_seconds: int = 5) -> Optional[str]:
        """
        Get verification code using the best available method
        
        Args:
            sender: Email sender to filter by
            subject_contains: Text that should be in the subject
            max_attempts: Maximum number of attempts
            wait_seconds: Seconds to wait between attempts
            
        Returns:
            6-digit verification code or None
        """
        logger.info(f"🔍 Getting verification code for {self.email_address}...")
        
        # Try Gmail API first if available
        if self.gmail_service:
            logger.info("📧 Trying Gmail API method...")
            code = self.get_verification_code_gmail_api(sender, subject_contains, max_attempts, wait_seconds)
            if code:
                return code
        
        # Fallback to IMAP
        if self.app_password:
            logger.info("📧 Trying IMAP method...")
            code = self.get_verification_code_imap(sender, subject_contains, max_attempts, wait_seconds)
            if code:
                return code
        
        logger.error("❌ All verification methods failed")
        return None

def create_gmail_verification_service(email_address: str, 
                                    app_password: str = None, 
                                    credentials_file: str = None) -> GmailVerificationService:
    """Factory function to create Gmail verification service"""
    return GmailVerificationService(email_address, app_password, credentials_file)
