"""
Emergency fix for GEICO scanner getting stuck after login
This module forces Commercial Auto detection even if login detection fails
"""

import time
from selenium.webdriver.common.by import By

def force_commercial_auto_check(driver, status_message):
    """
    Force check for Commercial Auto tab regardless of login state
    Returns updated status message
    """
    
    # Check if we're stuck on "Login submitted - waiting for page load..."
    if "Login submitted" in status_message and "waiting" in status_message:
        # Check how long we've been waiting
        current_url = driver.current_url
        
        # If URL changed from login page, we're likely on dashboard
        if "gateway.geico.com" not in current_url or "login" not in current_url.lower():
            print("\n[FORCE FIX] Detected possible dashboard, forcing Commercial Auto check!")
            return "Checking for Commercial Auto tab..."
        
        # If still on login URL but page seems loaded
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            if len(body_text) > 100:  # Page has content
                print("\n[FORCE FIX] Page has content, forcing Commercial Auto check!")
                return "Page loaded - checking for Commercial Auto..."
        except:
            pass
    
    return status_message


def add_force_detection_to_scanner():
    """
    Code to add to the main scanner loop to force Commercial Auto detection
    """
    
    force_detection_code = '''
                # FORCE FIX: Add login timeout and force Commercial Auto check
                if "Login submitted" in current_status and "waiting" in current_status:
                    if not hasattr(driver, 'login_submit_time'):
                        driver.login_submit_time = time.time()
                    
                    # After 5 seconds, force check for Commercial Auto
                    if time.time() - driver.login_submit_time > 5:
                        print("\\n[TIMEOUT] Login wait timeout - forcing Commercial Auto check!")
                        current_status = "Forcing Commercial Auto detection..."
                        
                        # Force the commercial auto check
                        try:
                            from commercial_auto_force_click import ensure_commercial_auto_clicked
                            print("\\n[FORCE] Running Commercial Auto detection regardless of page state!")
                            success = ensure_commercial_auto_clicked(driver)
                            if success:
                                current_status = "Commercial Auto tab clicked!"
                                driver.login_submit_time = time.time() + 1000  # Prevent repeated attempts
                            else:
                                current_status = "Dashboard loaded - Commercial Auto not found"
                        except Exception as e:
                            print(f"[ERROR] Force detection failed: {e}")
                            current_status = "On dashboard"
    '''
    
    return force_detection_code