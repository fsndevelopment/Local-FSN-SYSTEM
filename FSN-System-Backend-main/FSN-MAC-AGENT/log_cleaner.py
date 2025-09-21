"""
Log Cleaner Utility
Prevents massive base64 content from appearing in logs
"""

def clean_template_data_for_logging(template_data):
    """
    Clean template data by removing large base64 file content
    
    Args:
        template_data: Template data dictionary that may contain base64 file content
        
    Returns:
        Cleaned template data safe for logging
    """
    if not template_data:
        return template_data
    
    # Create a copy to avoid modifying original
    cleaned_data = {}
    
    for key, value in template_data.items():
        if key == 'settings' and isinstance(value, dict):
            # Filter out FileContent keys from settings
            cleaned_settings = {}
            for setting_key, setting_value in value.items():
                if setting_key.endswith('FileContent'):
                    # Replace with summary instead of full content
                    if isinstance(setting_value, str) and len(setting_value) > 100:
                        cleaned_settings[setting_key] = f"[BASE64_CONTENT: {len(setting_value)} chars]"
                    else:
                        cleaned_settings[setting_key] = setting_value
                else:
                    cleaned_settings[setting_key] = setting_value
            cleaned_data[key] = cleaned_settings
        else:
            cleaned_data[key] = value
    
    return cleaned_data

def clean_job_info_for_history(job_info):
    """
    Clean job info by removing large base64 content before storing in history
    
    Args:
        job_info: Job information dictionary
        
    Returns:
        Cleaned job info safe for history storage
    """
    if not job_info:
        return job_info
    
    # Create a copy to avoid modifying original
    cleaned_job = job_info.copy()
    
    # Clean template data if present
    if 'template' in cleaned_job:
        cleaned_job['template'] = clean_template_data_for_logging(cleaned_job['template'])
    
    return cleaned_job

def format_template_summary(template_data):
    """
    Create a concise summary of template data for logging
    
    Args:
        template_data: Template data dictionary
        
    Returns:
        String summary of template settings
    """
    if not template_data:
        return "No template data"
    
    settings = template_data.get('settings', {})
    
    summary_parts = []
    
    # Add basic settings
    if settings.get('photosPostsPerDay', 0) > 0:
        summary_parts.append(f"Photos: {settings['photosPostsPerDay']}")
        if settings.get('photosFolder'):
            summary_parts.append(f"Folder: {settings['photosFolder']}")
        if settings.get('captionsFile'):
            summary_parts.append(f"Captions: {settings['captionsFile']}")
    
    if settings.get('textPostsPerDay', 0) > 0:
        summary_parts.append(f"Text: {settings['textPostsPerDay']}")
        if settings.get('textPostsFile'):
            summary_parts.append(f"TextFile: {settings['textPostsFile']}")
    
    if settings.get('followsPerDay', 0) > 0:
        summary_parts.append(f"Follows: {settings['followsPerDay']}")
    
    if settings.get('likesPerDay', 0) > 0:
        summary_parts.append(f"Likes: {settings['likesPerDay']}")
    
    return " | ".join(summary_parts) if summary_parts else "No actions configured"
