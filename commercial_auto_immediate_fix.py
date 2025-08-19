"""
Immediate Commercial Auto detection after login
This runs as soon as the login button is clicked
"""

import time
import threading
from commercial_auto_force_click import ensure_commercial_auto_clicked

def start_commercial_auto_monitor(driver):
    """
    Start monitoring for Commercial Auto tab in a separate thread
    This runs immediately after login and keeps checking
    """
    
    def monitor_and_click():
        print("\n[MONITOR] Starting Commercial Auto tab monitor thread...")
        start_time = time.time()
        checked_urls = set()
        
        while time.time() - start_time < 60:  # Monitor for up to 60 seconds
            try:
                current_url = driver.current_url
                
                # Check if URL changed (indicates navigation)
                if current_url not in checked_urls:
                    checked_urls.add(current_url)
                    print(f"\n[MONITOR] New URL detected: {current_url}")
                    
                    # Wait a bit for page to load
                    time.sleep(2)
                    
                    # Check if we're past login page
                    if "login" not in current_url.lower() or len(checked_urls) > 1:
                        print("[MONITOR] Appears to be past login, checking for Commercial Auto...")
                        
                        # Check if already clicked
                        try:
                            already_clicked = driver.execute_script("return window.commercialAutoClicked || false")
                            if already_clicked:
                                print("[MONITOR] Commercial Auto already clicked, stopping monitor")
                                return
                        except:
                            pass
                        
                        # Try to click Commercial Auto
                        try:
                            success = ensure_commercial_auto_clicked(driver)
                            if success:
                                print("[MONITOR] Successfully clicked Commercial Auto tab!")
                                return
                            else:
                                print("[MONITOR] Commercial Auto tab not found yet...")
                        except Exception as e:
                            print(f"[MONITOR] Error during Commercial Auto click: {e}")
                
                # Check every 2 seconds
                time.sleep(2)
                
            except Exception as e:
                print(f"[MONITOR] Monitor error: {e}")
                time.sleep(2)
        
        print("[MONITOR] Monitor timeout after 60 seconds")
    
    # Start monitor thread
    monitor_thread = threading.Thread(target=monitor_and_click, daemon=True)
    monitor_thread.start()
    print("[MONITOR] Commercial Auto monitor thread started")


# Code to add right after login button click
monitor_integration_code = '''
# Add this right after the login button is clicked (around line 1260):

# Start Commercial Auto monitor immediately after login
try:
    from commercial_auto_immediate_fix import start_commercial_auto_monitor
    start_commercial_auto_monitor(driver)
    print("[INFO] Commercial Auto monitor started - will detect and click tab automatically")
except Exception as e:
    print(f"[WARNING] Could not start Commercial Auto monitor: {e}")
'''