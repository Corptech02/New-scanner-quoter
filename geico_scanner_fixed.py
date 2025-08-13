#!/usr/bin/env python3
"""
Geico Auto Quota Scanner - Web Interface
A web-based scanner that captures screenshots and detects elements on Geico's website
"""

from flask import Flask, render_template_string, jsonify, Response
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import base64
import io
import time
import threading
import json
import subprocess
from PIL import Image

app = Flask(__name__)

# Global variables
driver = None
is_scanning = False
scan_thread = None
current_screenshot = None
detected_elements = []
fps_counter = 0
last_fps_time = time.time()
current_status = "Ready to scan"  # New status variable

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Geico Auto Quota Scanner</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        
        .controls {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .start-button {
            background-color: #0066cc;
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        
        .start-button:hover {
            background-color: #0052a3;
        }
        
        .start-button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        
        .screenshot-container {
            position: relative;
            background: #f0f0f0;
            border: 2px solid #ddd;
            border-radius: 5px;
            min-height: 600px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }
        
        #screenshotImage {
            max-width: 100%;
            height: auto;
            display: block;
        }
        
        .overlay-container {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
        }
        
        .element-overlay {
            position: absolute;
            border: 3px solid red;
            background-color: rgba(255, 0, 0, 0.2);
            pointer-events: none;
            transition: all 0.1s ease;
        }
        
        .element-label {
            position: absolute;
            background-color: red;
            color: white;
            padding: 4px 8px;
            font-size: 12px;
            font-weight: bold;
            top: -25px;
            left: 0;
            white-space: nowrap;
            border-radius: 3px;
        }
        
        .fps-counter {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(0,0,0,0.7);
            color: #0ff;
            padding: 5px 10px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 14px;
            z-index: 1000;
        }
        
        .status-message {
            text-align: center;
            margin-top: 20px;
            font-size: 16px;
            color: #666;
        }
        
        .placeholder-message {
            color: #999;
            font-size: 18px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Geico Auto Quota Scanner</h1>
        
        <div class="controls">
            <button class="start-button" onclick="startScanning()">Start Quote</button>
        </div>
        
        <div class="screenshot-container">
            <div class="fps-counter" id="fpsCounter" style="display: none;">FPS: 0</div>
            <div id="screenshotDisplay">
                <p class="placeholder-message">Click "Start Quote" to begin scanning</p>
            </div>
            <div class="overlay-container" id="overlayContainer"></div>
        </div>
        
        <div class="status-message" id="statusMessage"></div>
    </div>

    <script>
        let isScanning = false;
        let updateInterval = null;
        
        function startScanning() {
            if (isScanning) return;
            
            isScanning = true;
            const button = document.querySelector('.start-button');
            button.disabled = true;
            button.textContent = 'Scanning...';
            
            document.getElementById('fpsCounter').style.display = 'block';
            document.getElementById('statusMessage').textContent = 'Initializing scanner...';
            
            fetch('/start-scan', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'started') {
                        document.getElementById('statusMessage').textContent = 'Scanner started. Loading Geico website...';
                        startUpdating();
                    }
                })
                .catch(error => {
                    console.error('Error starting scan:', error);
                    document.getElementById('statusMessage').textContent = 'Error starting scanner';
                    resetButton();
                });
        }
        
        function startUpdating() {
            updateInterval = setInterval(() => {
                fetch('/get-screenshot')
                    .then(response => response.json())
                    .then(data => {
                        if (data.screenshot) {
                            updateScreenshot(data.screenshot, data.elements);
                            document.getElementById('fpsCounter').textContent = `FPS: ${data.fps || 0}`;
                        }
                    })
                    .catch(error => {
                        console.error('Error getting screenshot:', error);
                    });
            }, 100); // Update every 100ms for ~10 FPS
        }
        
        function updateScreenshot(screenshotData, elements) {
            const display = document.getElementById('screenshotDisplay');
            const overlayContainer = document.getElementById('overlayContainer');
            
            // Update screenshot
            display.innerHTML = `<img id="screenshotImage" src="data:image/png;base64,${screenshotData}" alt="Screenshot">`;
            
            // Wait for image to load before adding overlays
            const img = document.getElementById('screenshotImage');
            img.onload = function() {
                // Clear previous overlays
                overlayContainer.innerHTML = '';
                
                // Get image dimensions for scaling
                const imgRect = img.getBoundingClientRect();
                const container = document.querySelector('.screenshot-container');
                const containerRect = container.getBoundingClientRect();
                
                // Calculate offset
                const offsetX = (containerRect.width - imgRect.width) / 2;
                const offsetY = (containerRect.height - imgRect.height) / 2;
                
                // Add element overlays
                if (elements && elements.length > 0) {
                    elements.forEach(element => {
                        const overlay = document.createElement('div');
                        overlay.className = 'element-overlay';
                        
                        // Scale coordinates to match displayed image size
                        const scaleX = imgRect.width / img.naturalWidth;
                        const scaleY = imgRect.height / img.naturalHeight;
                        
                        // Position relative to the image element inside the container
                        const imgOffsetLeft = img.offsetLeft;
                        const imgOffsetTop = img.offsetTop;
                        
                        overlay.style.left = (imgOffsetLeft + element.x * scaleX) + 'px';
                        overlay.style.top = (imgOffsetTop + element.y * scaleY) + 'px';
                        overlay.style.width = (element.width * scaleX) + 'px';
                        overlay.style.height = (element.height * scaleY) + 'px';
                        
                        const label = document.createElement('div');
                        label.className = 'element-label';
                        label.textContent = element.label;
                        overlay.appendChild(label);
                        
                        overlayContainer.appendChild(overlay);
                    });
                }
                
                // Update status message with current action
                fetch('/get-status')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('statusMessage').textContent = data.status || `Scanning... Found ${elements ? elements.length : 0} elements`;
                    })
                    .catch(error => {
                        document.getElementById('statusMessage').textContent = `Scanning... Found ${elements ? elements.length : 0} elements`;
                    });
            };
        }
        
        function resetButton() {
            isScanning = false;
            const button = document.querySelector('.start-button');
            button.disabled = false;
            button.textContent = 'Start Quote';
            
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
        }
        
        // Stop scanning when page is closed
        window.addEventListener('beforeunload', function() {
            if (isScanning) {
                fetch('/stop-scan', { method: 'POST' });
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start-scan', methods=['POST'])
def start_scan():
    global driver, is_scanning, scan_thread
    
    # Clean up any existing browser instance first
    if driver:
        try:
            driver.quit()
        except:
            pass
        driver = None
    
    # Wait a bit for any existing scan to fully stop
    if is_scanning:
        is_scanning = False
        time.sleep(0.5)
    
    is_scanning = True
    scan_thread = threading.Thread(target=scan_geico_site)
    scan_thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/stop-scan', methods=['POST'])
def stop_scan():
    global is_scanning, driver
    
    is_scanning = False
    if driver:
        driver.quit()
        driver = None
    
    return jsonify({'status': 'stopped'})

@app.route('/get-screenshot')
def get_screenshot():
    global current_screenshot, detected_elements, fps_counter
    
    if current_screenshot:
        return jsonify({
            'screenshot': current_screenshot,
            'elements': detected_elements,
            'fps': fps_counter
        })
    else:
        return jsonify({'screenshot': None, 'elements': [], 'fps': 0})

@app.route('/get-status')
def get_status():
    global current_status
    return jsonify({'status': current_status})

def scan_geico_site():
    global driver, is_scanning, current_screenshot, detected_elements, fps_counter, last_fps_time, current_status
    
    # Kill any existing Chrome processes first - more aggressive
    import subprocess
    import os
    import tempfile
    import shutil
    
    print("[DEBUG] Killing existing Chrome processes...")
    subprocess.run(['pkill', '-9', '-f', 'chrome'], capture_output=True)
    subprocess.run(['pkill', '-9', '-f', 'chromium'], capture_output=True)
    subprocess.run(['pkill', '-9', '-f', 'chromedriver'], capture_output=True)
    time.sleep(1)  # Give time for processes to die
    
    # Write debug to file
    with open('scanner_debug_thread.log', 'a') as f:
        f.write(f"[DEBUG] {time.strftime('%Y-%m-%d %H:%M:%S')} Starting scan_geico_site function\n")
        f.flush()
    
    print("[DEBUG] Starting scan_geico_site function")
    temp_dir = None
    try:
        # Set up Chrome options
        current_status = "Setting up Chrome browser..."
        with open('scanner_debug_thread.log', 'a') as f:
            f.write(f"[DEBUG] {time.strftime('%Y-%m-%d %H:%M:%S')} Setting up Chrome options\n")
            f.flush()
        print("[DEBUG] Setting up Chrome options")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        # Re-enable headless for server environment
        chrome_options.add_argument('--headless=new')
        print("[DEBUG] Running in headless mode for server environment")
        
        # Try to create a unique user data directory
        try:
            # Create a unique temporary directory with timestamp
            temp_dir = tempfile.mkdtemp(prefix=f'geico_scanner_{int(time.time())}_')
            chrome_options.add_argument(f'--user-data-dir={temp_dir}')
            print(f"[DEBUG] Using temporary profile directory: {temp_dir}")
        except Exception as e:
            print(f"[DEBUG] Could not create temp directory, running without user-data-dir: {e}")
            # Don't use user-data-dir if we can't create temp dir
        
        # Add more options to prevent conflicts
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize driver
        print("[DEBUG] Initializing Chrome driver")
        current_status = "Starting Chrome browser..."
        try:
            print("[DEBUG] Creating Chrome webdriver with options...")
            driver = webdriver.Chrome(options=chrome_options)
            print("[DEBUG] Chrome driver initialized successfully")
            driver.set_window_size(1920, 1080)
            current_status = "Chrome browser started"
            
            # Test that driver is working
            print("[DEBUG] Testing driver - getting window handles...")
            handles = driver.window_handles
            print(f"[DEBUG] Window handles: {handles}")
            print(f"[DEBUG] Current URL: {driver.current_url}")
        except Exception as chrome_error:
            print(f"[ERROR] Failed to initialize Chrome driver: {chrome_error}")
            current_status = f"Failed to start Chrome: {str(chrome_error)[:50]}"
            # Write detailed error to log
            with open('scanner_debug_thread.log', 'a') as f:
                f.write(f"[ERROR] {time.strftime('%Y-%m-%d %H:%M:%S')} Chrome init error: {chrome_error}\n")
                import traceback
                f.write(traceback.format_exc())
                f.flush()
            # Clean up temp directory if it exists
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
            raise
        
        # Execute script to mask webdriver detection
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            '''
        })
        
        print("[DEBUG] Navigating to Geico gateway page")
        current_status = "Loading Geico website..."
        driver.get('https://gateway.geico.com/')
        print("[DEBUG] Successfully loaded Geico gateway page")
        current_status = "Geico website loaded"
        
        # Wait for page to load
        time.sleep(2)
        
        # Check if we need to go to the login page directly
        # Sometimes the gateway redirects to login, sometimes we need to navigate there
        try:
            # Look for "Manage My Policy" link which usually leads to login
            manage_policy_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Manage') and contains(text(), 'Policy')]")
            if manage_policy_links:
                print("[DEBUG] Found 'Manage My Policy' link, clicking it")
                manage_policy_links[0].click()
                time.sleep(3)  # Wait for redirect
        except Exception as e:
            print(f"[DEBUG] No manage policy link found or error clicking: {e}")
        
        frame_count = 0
        last_time = time.time()
        
        # Take an initial screenshot to verify everything is working
        try:
            print("[DEBUG] Taking initial screenshot...")
            current_status = "Taking initial screenshot..."
            screenshot = driver.get_screenshot_as_png()
            img = Image.open(io.BytesIO(screenshot))
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            current_screenshot = base64.b64encode(buffered.getvalue()).decode()
            print("[DEBUG] Initial screenshot successful")
            current_status = "Scanner ready"
        except Exception as e:
            print(f"[ERROR] Failed to take initial screenshot: {e}")
            current_status = f"Screenshot error: {str(e)[:50]}"
        
        while is_scanning:
            try:
                # Take screenshot
                screenshot = driver.get_screenshot_as_png()
                img = Image.open(io.BytesIO(screenshot))
                
                with open('scanner_debug_thread.log', 'a') as f:
                    f.write(f"[DEBUG] {time.strftime('%Y-%m-%d %H:%M:%S')} Screenshot captured, size: {len(screenshot)} bytes\n")
                    f.flush()
                print(f"[DEBUG] Screenshot captured, size: {len(screenshot)} bytes")
                
                # Convert to base64
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                current_screenshot = base64.b64encode(buffered.getvalue()).decode()
                
                with open('scanner_debug_thread.log', 'a') as f:
                    f.write(f"[DEBUG] {time.strftime('%Y-%m-%d %H:%M:%S')} Screenshot converted to base64, length: {len(current_screenshot)}\n")
                    f.flush()
                
                # Detect elements
                elements_found = []
                
                # Check for login fields on ANY page (not just login pages)
                # First, detect if we have username/password fields visible
                has_username_field = False
                has_password_field = False
                username_element = None
                password_element = None
                
                # Check for username field
                try:
                    username_fields = driver.find_elements(By.XPATH, "//input[@type='text' or @type='email' or @name='username' or @name='j_username' or @id='username' or contains(@placeholder, 'username') or contains(@placeholder, 'Username') or contains(@aria-label, 'username') or contains(@aria-label, 'Username')]")
                    for field in username_fields:
                        if field.is_displayed():
                            has_username_field = True
                            username_element = field
                            break
                except:
                    pass
                
                # Check for password field
                try:
                    password_fields = driver.find_elements(By.XPATH, "//input[@type='password' or @name='password' or @name='j_password' or @id='password']")
                    for field in password_fields:
                        if field.is_displayed():
                            has_password_field = True
                            password_element = field
                            break
                except:
                    pass
                
                # If we found both username and password fields, try to auto-fill them
                if has_username_field and has_password_field and not driver.execute_script("return window.geicoLoginAttempted || false"):
                    # Mark that we've attempted login to avoid repeated attempts
                    driver.execute_script("window.geicoLoginAttempted = true;")
                    
                    print(f"[DEBUG] Found login fields on page: {driver.current_url}")
                    print("[DEBUG] Attempting to auto-fill login credentials...")
                    current_status = "Login detected - Starting auto-fill..."
                    
                    # Perform automatic login - Use detected elements directly
                    try:
                        # Simple, direct approach - just click and type
                        print("[DEBUG] Using direct Selenium interaction...")
                        current_status = "Clicking username field..."
                        
                        # STEP 1: Click and fill username
                        print("[DEBUG] Clicking username field...")
                        print(f"[DEBUG] Username element tag: {username_element.tag_name}")
                        print(f"[DEBUG] Username element displayed: {username_element.is_displayed()}")
                        print(f"[DEBUG] Username element enabled: {username_element.is_enabled()}")
                        
                        # AGGRESSIVE APPROACH: Use execute_script with forced click
                        print("[DEBUG] Using AGGRESSIVE click approach...")
                        driver.execute_script("""
                            var elem = arguments[0];
                            
                            // Force visibility and enable the element
                            elem.style.display = 'block';
                            elem.style.visibility = 'visible';
                            elem.style.opacity = '1';
                            elem.disabled = false;
                            elem.readOnly = false;
                            
                            // Remove any overlays
                            var overlays = document.querySelectorAll('*');
                            overlays.forEach(function(el) {
                                if (el !== elem && el.contains(elem) === false) {
                                    var rect1 = elem.getBoundingClientRect();
                                    var rect2 = el.getBoundingClientRect();
                                    var overlap = !(rect1.right < rect2.left || 
                                                   rect1.left > rect2.right || 
                                                   rect1.bottom < rect2.top || 
                                                   rect1.top > rect2.bottom);
                                    if (overlap && window.getComputedStyle(el).zIndex > window.getComputedStyle(elem).zIndex) {
                                        el.style.pointerEvents = 'none';
                                    }
                                }
                            });
                            
                            // Force focus and click
                            elem.focus();
                            elem.click();
                            
                            // Simulate human typing behavior
                            elem.value = '';
                            var username = 'I017346';
                            for (var i = 0; i < username.length; i++) {
                                elem.value += username[i];
                                elem.dispatchEvent(new Event('input', { bubbles: true }));
                                elem.dispatchEvent(new KeyboardEvent('keydown', { key: username[i], bubbles: true }));
                                elem.dispatchEvent(new KeyboardEvent('keypress', { key: username[i], bubbles: true }));
                                elem.dispatchEvent(new KeyboardEvent('keyup', { key: username[i], bubbles: true }));
                            }
                            elem.dispatchEvent(new Event('change', { bubbles: true }));
                            return elem.value;
                        """, username_element)
                        current_status = "Username entered, moving to password..."
                        
                        # Get element position and size for debugging
                        rect = username_element.rect
                        print(f"[DEBUG] Username field position - x: {rect['x']}, y: {rect['y']}, width: {rect['width']}, height: {rect['height']}")
                        
                        # First try JavaScript click at exact coordinates
                        print("[DEBUG] Attempting JavaScript click at exact coordinates...")
                        js_click_result = driver.execute_script("""
                            var element = arguments[0];
                            var rect = element.getBoundingClientRect();
                            var x = rect.left + rect.width / 2;
                            var y = rect.top + rect.height / 2;
                            
                            console.log('Clicking at coordinates:', x, y);
                            
                            // Create and dispatch mouse events
                            var clickEvent = new MouseEvent('click', {
                                view: window,
                                bubbles: true,
                                cancelable: true,
                                clientX: x,
                                clientY: y,
                                buttons: 1
                            });
                            
                            var mouseDownEvent = new MouseEvent('mousedown', {
                                view: window,
                                bubbles: true,
                                cancelable: true,
                                clientX: x,
                                clientY: y,
                                buttons: 1
                            });
                            
                            var mouseUpEvent = new MouseEvent('mouseup', {
                                view: window,
                                bubbles: true,
                                cancelable: true,
                                clientX: x,
                                clientY: y,
                                buttons: 0
                            });
                            
                            element.dispatchEvent(mouseDownEvent);
                            element.dispatchEvent(mouseUpEvent);
                            element.dispatchEvent(clickEvent);
                            element.focus();
                            
                            // Also try typing directly
                            element.value = 'I017346';
                            element.dispatchEvent(new Event('input', { bubbles: true }));
                            element.dispatchEvent(new Event('change', { bubbles: true }));
                            
                            return {clicked: true, value: element.value};
                        """, username_element)
                        
                        print(f"[DEBUG] JavaScript click result: {js_click_result}")
                        time.sleep(0.5)
                        
                        # Scroll to element
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", username_element)
                        time.sleep(0.5)
                        
                        try:
                            # Try ActionChains first - most reliable method
                            print("[DEBUG] Attempting ActionChains interaction...")
                            
                            # First, ensure the element is in the viewport
                            driver.execute_script("""
                                var elem = arguments[0];
                                elem.scrollIntoView({behavior: 'smooth', block: 'center'});
                                // Remove any overlays that might be blocking
                                var overlays = document.querySelectorAll('div[style*="z-index"]');
                                overlays.forEach(function(overlay) {
                                    if (overlay.style.position === 'fixed' || overlay.style.position === 'absolute') {
                                        overlay.style.pointerEvents = 'none';
                                    }
                                });
                            """, username_element)
                            time.sleep(0.5)
                            
                            # Use ActionChains to move to element and click
                            actions = ActionChains(driver)
                            actions.move_to_element(username_element).pause(0.5).click().perform()
                            print("[DEBUG] ActionChains click executed")
                            time.sleep(0.3)
                            
                            # Clear the field multiple ways
                            print("[DEBUG] Clearing field...")
                            try:
                                username_element.clear()
                            except:
                                # If clear() fails, use keyboard shortcuts
                                actions.double_click(username_element).perform()
                                username_element.send_keys(Keys.CONTROL + "a")
                                username_element.send_keys(Keys.DELETE)
                            
                            time.sleep(0.3)
                            
                            # Type username character by character
                            print("[DEBUG] Typing username character by character...")
                            for char in "I017346":
                                username_element.send_keys(char)
                                time.sleep(0.05)  # Small delay between characters
                            
                            print("[DEBUG] Username entered successfully via ActionChains")
                        except Exception as e:
                            print(f"[DEBUG] ActionChains interaction failed: {e}")
                            try:
                                # Fallback to direct click
                                print("[DEBUG] Trying direct Selenium click...")
                                username_element.click()
                                time.sleep(0.3)
                                username_element.clear()
                                time.sleep(0.3)
                                username_element.send_keys("I017346")
                                print("[DEBUG] Username entered successfully via direct Selenium")
                            except Exception as e2:
                                print(f"[DEBUG] Direct Selenium also failed: {e2}")
                            # Try JavaScript as backup
                            print("[DEBUG] Trying JavaScript interaction...")
                            result = driver.execute_script("""
                                var el = arguments[0];
                                console.log('Element:', el);
                                el.scrollIntoView({block: 'center'});
                                el.click();
                                el.focus();
                                el.value = 'I017346';
                                el.dispatchEvent(new Event('input', { bubbles: true }));
                                el.dispatchEvent(new Event('change', { bubbles: true }));
                                return 'JavaScript execution completed';
                            """, username_element)
                            print(f"[DEBUG] JavaScript result: {result}")
                        
                        time.sleep(0.5)
                        
                        # STEP 2: Click and fill password
                        print("[DEBUG] Clicking password field...")
                        current_status = "Clicking password field..."
                        print(f"[DEBUG] Password element tag: {password_element.tag_name}")
                        print(f"[DEBUG] Password element displayed: {password_element.is_displayed()}")
                        print(f"[DEBUG] Password element enabled: {password_element.is_enabled()}")
                        
                        # AGGRESSIVE APPROACH for password too
                        print("[DEBUG] Using AGGRESSIVE click approach for password...")
                        driver.execute_script("""
                            var elem = arguments[0];
                            
                            // Force visibility and enable the element
                            elem.style.display = 'block';
                            elem.style.visibility = 'visible';
                            elem.style.opacity = '1';
                            elem.disabled = false;
                            elem.readOnly = false;
                            
                            // Force focus and click
                            elem.focus();
                            elem.click();
                            
                            // Clear and type password
                            elem.value = '';
                            var password = '25Nickc124';
                            for (var i = 0; i < password.length; i++) {
                                elem.value += password[i];
                                elem.dispatchEvent(new Event('input', { bubbles: true }));
                                elem.dispatchEvent(new KeyboardEvent('keydown', { key: password[i], bubbles: true }));
                                elem.dispatchEvent(new KeyboardEvent('keypress', { key: password[i], bubbles: true }));
                                elem.dispatchEvent(new KeyboardEvent('keyup', { key: password[i], bubbles: true }));
                            }
                            elem.dispatchEvent(new Event('change', { bubbles: true }));
                            return elem.value;
                        """, password_element)
                        current_status = "Password entered, looking for sign-in button..."
                        
                        # Scroll to element first
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", password_element)
                        time.sleep(0.5)
                        
                        try:
                            # Try ActionChains first for password
                            print("[DEBUG] Attempting ActionChains for password...")
                            actions = ActionChains(driver)
                            actions.move_to_element(password_element).click().perform()
                            time.sleep(0.3)
                            print("[DEBUG] ActionChains click successful, clearing password field...")
                            actions.double_click(password_element).perform()
                            password_element.send_keys(Keys.CONTROL + "a")
                            password_element.send_keys(Keys.DELETE)
                            time.sleep(0.3)
                            print("[DEBUG] Field cleared, typing password...")
                            password_element.send_keys("25Nickc124")
                            print("[DEBUG] Password entered successfully via ActionChains")
                        except Exception as e:
                            print(f"[DEBUG] ActionChains password failed: {e}")
                            try:
                                # Fallback to direct click
                                print("[DEBUG] Trying direct Selenium click on password...")
                                password_element.click()
                                time.sleep(0.3)
                                password_element.clear()
                                time.sleep(0.3)
                                password_element.send_keys("25Nickc124")
                                print("[DEBUG] Password entered successfully via direct Selenium")
                            except Exception as e2:
                                print(f"[DEBUG] Direct Selenium password also failed: {e2}")
                            # Try JavaScript as backup
                            print("[DEBUG] Trying JavaScript for password...")
                            result = driver.execute_script("""
                                var el = arguments[0];
                                console.log('Password element:', el);
                                el.scrollIntoView({block: 'center'});
                                el.click();
                                el.focus();
                                el.value = '25Nickc124';
                                el.dispatchEvent(new Event('input', { bubbles: true }));
                                el.dispatchEvent(new Event('change', { bubbles: true }));
                                return 'Password JavaScript execution completed';
                            """, password_element)
                            print(f"[DEBUG] JavaScript password result: {result}")
                        
                        time.sleep(0.5)
                        
                        # STEP 3: Find and click sign-in button
                        print("[DEBUG] Looking for sign-in button...")
                        current_status = "Clicking sign-in button..."
                        button_clicked = False
                        
                        # Try to find the button next to the password field
                        try:
                            # Look for buttons near the password field
                            buttons = driver.find_elements(By.XPATH, "//button | //input[@type='submit']")
                            for button in buttons:
                                if button.is_displayed() and button.is_enabled():
                                    button_text = button.text.lower() if button.text else ""
                                    button_value = button.get_attribute('value')
                                    button_value = button_value.lower() if button_value else ""
                                    
                                    if 'sign' in button_text or 'log' in button_text or \
                                       'sign' in button_value or 'log' in button_value or \
                                       button.get_attribute('type') == 'submit':
                                        print(f"[DEBUG] Found button: {button_text or button_value}")
                                        button.click()
                                        button_clicked = True
                                        print("[DEBUG] Button clicked!")
                                        break
                        except Exception as e:
                            print(f"[DEBUG] Error finding button: {e}")
                        
                        # If button not clicked, try form submission
                        if not button_clicked:
                            print("[DEBUG] Trying form submission...")
                            try:
                                driver.execute_script("""
                                    var forms = document.querySelectorAll('form');
                                    for (var i = 0; i < forms.length; i++) {
                                        var form = forms[i];
                                        if (form.querySelector('input[type="password"]')) {
                                            form.submit();
                                            return true;
                                        }
                                    }
                                    return false;
                                """)
                                print("[DEBUG] Form submitted")
                            except Exception as e:
                                print(f"[DEBUG] Form submission error: {e}")
                        
                        print("[DEBUG] Login automation completed")
                        current_status = "Login submitted - waiting for page load..."
                        
                    except Exception as e:
                        print(f"[DEBUG] Error during auto-login: {e}")
                        current_status = f"Login error: {str(e)}"
                        import traceback
                        traceback.print_exc()
                
                # Now continue with element detection for visual feedback
                # This will show the red boxes around detected elements
                
                # Find username field for visual display
                try:
                    username_fields = driver.find_elements(By.XPATH, "//input[@type='text' or @type='email' or @name='username' or @name='j_username' or @id='username' or contains(@placeholder, 'username') or contains(@placeholder, 'Username') or contains(@aria-label, 'username') or contains(@aria-label, 'Username')]")
                    for field in username_fields:
                        if field.is_displayed():
                            rect = field.rect
                            # Only add if element has valid position and size
                            if rect['width'] > 0 and rect['height'] > 0:
                                elements_found.append({
                                    'label': 'Username',
                                    'x': rect['x'],
                                    'y': rect['y'],
                                    'width': rect['width'],
                                    'height': rect['height']
                                })
                                break
                except:
                    pass
                
                # Find password field
                try:
                    password_fields = driver.find_elements(By.XPATH, "//input[@type='password' or @name='password' or @name='j_password' or @id='password']")
                    for field in password_fields:
                        if field.is_displayed():
                            rect = field.rect
                            if rect['width'] > 0 and rect['height'] > 0:
                                elements_found.append({
                                    'label': 'Password',
                                    'x': rect['x'],
                                    'y': rect['y'],
                                    'width': rect['width'],
                                    'height': rect['height']
                                })
                                break
                except:
                    pass
                
                # Find Sign In button - avoid duplicates
                try:
                    signin_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Sign') or contains(text(), 'sign') or contains(text(), 'Log') or contains(text(), 'log')]")
                    seen_positions = set()
                    for button in signin_buttons:
                        if button.is_displayed():
                            rect = button.rect
                            # Create a position key to check for duplicates
                            pos_key = f"{rect['x']},{rect['y']},{rect['width']},{rect['height']}"
                            if pos_key not in seen_positions and rect['width'] > 0 and rect['height'] > 0:
                                seen_positions.add(pos_key)
                                elements_found.append({
                                    'label': 'Sign In',
                                    'x': rect['x'],
                                    'y': rect['y'],
                                    'width': rect['width'],
                                    'height': rect['height']
                                })
                                break  # Only add the first visible sign in button
                except:
                    pass
                
                # Find Forgot Password link
                try:
                    forgot_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Forgot') or contains(text(), 'forgot')]")
                    for link in forgot_links:
                        if link.is_displayed():
                            rect = link.rect
                            if rect['width'] > 0 and rect['height'] > 0:
                                elements_found.append({
                                    'label': 'Forgot Password',
                                    'x': rect['x'],
                                    'y': rect['y'],
                                    'width': rect['width'],
                                    'height': rect['height']
                                })
                                break
                except:
                    pass
                
                # Also detect other page elements (ZIP code, quote buttons, etc.)
                # Find ZIP code input
                try:
                    zip_inputs = driver.find_elements(By.XPATH, "//input[contains(@placeholder, 'ZIP') or contains(@placeholder, 'zip') or contains(@name, 'zip')]")
                    for inp in zip_inputs:
                        if inp.is_displayed():
                            rect = inp.rect
                            if rect['width'] > 0 and rect['height'] > 0:
                                elements_found.append({
                                    'label': 'ZIP Code',
                                    'x': rect['x'],
                                    'y': rect['y'],
                                    'width': rect['width'],
                                    'height': rect['height']
                                })
                                break
                except:
                    pass
                
                # Find Get Quote button
                try:
                    quote_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Quote') or contains(text(), 'quote')]")
                    for btn in quote_buttons:
                        if btn.is_displayed():
                            rect = btn.rect
                            if rect['width'] > 0 and rect['height'] > 0:
                                elements_found.append({
                                    'label': 'Get Quote',
                                    'x': rect['x'],
                                    'y': rect['y'],
                                    'width': rect['width'],
                                    'height': rect['height']
                                })
                                break
                except:
                    pass
                
                # Update global detected_elements
                detected_elements = elements_found
                
                # Update status if we're not in a special state
                if not current_status.startswith("Login") and not current_status.startswith("Clicking"):
                    current_status = f"Scanning... Found {len(elements_found)} elements"
                
                # Update FPS counter
                frame_count += 1
                current_time = time.time()
                if current_time - last_time >= 1.0:
                    fps_counter = frame_count
                    frame_count = 0
                    last_time = current_time
                
                # Small delay to achieve ~10 FPS
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error in scan loop: {e}")
                time.sleep(0.5)
    
    except Exception as e:
        print(f"[ERROR] Error initializing scanner: {e}")
        import traceback
        traceback.print_exc()
        # Write error to debug log
        with open('scanner_debug_thread.log', 'a') as f:
            f.write(f"[ERROR] {time.strftime('%Y-%m-%d %H:%M:%S')} Error: {str(e)}\n")
            f.flush()
        # Ensure we reset the scanning state even on error
        current_screenshot = None
        detected_elements = []
    
    finally:
        print("[DEBUG] Cleaning up scanner")
        if driver:
            try:
                driver.quit()
            except:
                pass
            driver = None
        is_scanning = False
        # Clean up temporary directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"[DEBUG] Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                print(f"[DEBUG] Could not clean up temp directory: {e}")
        # Reset state
        current_screenshot = None
        detected_elements = []
        current_status = "Scanner stopped"

if __name__ == '__main__':
    print("\n=== Geico Auto Quota Scanner ===")
    print("Open your browser and go to: http://localhost:5558")
    print("Or from another device: http://192.168.40.232:5558")
    print("Press Ctrl+C to stop the server\n")
    
    app.run(host='0.0.0.0', port=5558, debug=False)