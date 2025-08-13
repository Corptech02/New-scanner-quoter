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
    
    # Kill any existing Chrome processes first
    import subprocess
    subprocess.run(['pkill', '-f', 'chrome|chromium'], capture_output=True)
    
    print("[DEBUG] Starting scan_geico_site function")
    temp_profile = None
    try:
        # Set up Chrome options
        print("[DEBUG] Setting up Chrome options")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        # Run in normal mode to allow proper interaction
        # chrome_options.add_argument('--headless=new')
        print("[DEBUG] Running in normal mode for better interaction")
        # Add unique user data directory to avoid conflicts
        import tempfile
        temp_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f'--user-data-dir={temp_dir}')
        # Add more options to prevent conflicts
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize driver
        print("[DEBUG] Initializing Chrome driver")
        try:
            driver = webdriver.Chrome(options=chrome_options)
            print("[DEBUG] Chrome driver initialized successfully")
            driver.set_window_size(1920, 1080)
        except Exception as chrome_error:
            print(f"[ERROR] Failed to initialize Chrome driver: {chrome_error}")
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
        driver.get('https://gateway.geico.com/')
        print("[DEBUG] Successfully loaded Geico gateway page")
        
        # Wait for page to load
        time.sleep(2)
        
        # Check if we need to go to the login page directly
        try:
            manage_policy_links = driver.find_elements(By.XPATH, "//a[contains(text(), 'Manage') and contains(text(), 'Policy')]")
            if manage_policy_links:
                print("[DEBUG] Found 'Manage My Policy' link, clicking it")
                manage_policy_links[0].click()
                time.sleep(3)  # Wait for redirect
        except Exception as e:
            print(f"[DEBUG] No manage policy link found or error clicking: {e}")
        
        frame_count = 0
        last_time = time.time()
        
        while is_scanning:
            try:
                # Take screenshot
                screenshot = driver.get_screenshot_as_png()
                img = Image.open(io.BytesIO(screenshot))
                
                # Convert to base64
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                current_screenshot = base64.b64encode(buffered.getvalue()).decode()
                
                # Detect elements
                elements_found = []
                
                # Check for login fields on ANY page (not just login pages)
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
                    
                    # SIMPLIFIED LOGIN AUTOMATION - Just use JavaScript with visual feedback
                    try:
                        # Fill username with visual feedback
                        print("[DEBUG] Filling username field...")
                        current_status = "Typing username..."
                        driver.execute_script("""
                            var usernameField = arguments[0];
                            var passwordField = arguments[1];
                            
                            // Visual feedback - highlight field
                            usernameField.style.border = '3px solid green';
                            usernameField.style.backgroundColor = '#ffffcc';
                            usernameField.scrollIntoView({block: 'center'});
                            
                            // Focus and clear
                            usernameField.focus();
                            usernameField.click();
                            usernameField.value = '';
                            
                            // Type username slowly so user can see it
                            var username = 'I017346';
                            var index = 0;
                            
                            function typeNextChar() {
                                if (index < username.length) {
                                    usernameField.value += username[index];
                                    usernameField.dispatchEvent(new Event('input', { bubbles: true }));
                                    index++;
                                    setTimeout(typeNextChar, 150); // 150ms between characters
                                } else {
                                    // Username done, move to password
                                    usernameField.style.border = '3px solid blue';
                                    usernameField.dispatchEvent(new Event('change', { bubbles: true }));
                                    
                                    // Start password after a pause
                                    setTimeout(function() {
                                        // Highlight password field
                                        passwordField.style.border = '3px solid green';
                                        passwordField.style.backgroundColor = '#ffffcc';
                                        passwordField.scrollIntoView({block: 'center'});
                                        
                                        // Focus and clear
                                        passwordField.focus();
                                        passwordField.click();
                                        passwordField.value = '';
                                        
                                        // Type password
                                        var password = '25Nickc124';
                                        var pwIndex = 0;
                                        
                                        function typeNextPwChar() {
                                            if (pwIndex < password.length) {
                                                passwordField.value += password[pwIndex];
                                                passwordField.dispatchEvent(new Event('input', { bubbles: true }));
                                                pwIndex++;
                                                setTimeout(typeNextPwChar, 150); // 150ms between characters
                                            } else {
                                                // Password done
                                                passwordField.style.border = '3px solid blue';
                                                passwordField.dispatchEvent(new Event('change', { bubbles: true }));
                                                
                                                // Look for and click submit button after a pause
                                                setTimeout(function() {
                                                    var buttons = document.querySelectorAll('button, input[type="submit"]');
                                                    for (var i = 0; i < buttons.length; i++) {
                                                        var btn = buttons[i];
                                                        if (!btn.offsetParent) continue;
                                                        
                                                        var text = (btn.textContent || btn.value || '').toLowerCase();
                                                        if (text.includes('sign') || text.includes('log') || btn.type === 'submit') {
                                                            btn.style.border = '3px solid red';
                                                            btn.scrollIntoView({block: 'center'});
                                                            
                                                            setTimeout(function() {
                                                                btn.click();
                                                            }, 500);
                                                            break;
                                                        }
                                                    }
                                                }, 1000);
                                            }
                                        }
                                        typeNextPwChar();
                                    }, 1000);
                                }
                            }
                            typeNextChar();
                            
                            return 'Started login automation';
                        """, username_element, password_element)
                        
                        # Update status while typing happens
                        for i in range(5):  # About 5 seconds total
                            if i < 2:
                                current_status = f"Typing username... {'I017346'[:i*4]}"
                            elif i < 4:
                                current_status = f"Typing password... {'*' * ((i-2)*5)}"
                            else:
                                current_status = "Clicking sign-in button..."
                            time.sleep(1)
                        
                        current_status = "Login submitted - waiting for page load..."
                        print("[DEBUG] Login automation completed")
                        
                    except Exception as e:
                        print(f"[DEBUG] Error during auto-login: {e}")
                        current_status = f"Login error: {str(e)}"
                        import traceback
                        traceback.print_exc()
                
                # Now continue with element detection for visual feedback
                # Find username field for visual display
                try:
                    username_fields = driver.find_elements(By.XPATH, "//input[@type='text' or @type='email' or @name='username' or @name='j_username' or @id='username' or contains(@placeholder, 'username') or contains(@placeholder, 'Username') or contains(@aria-label, 'username') or contains(@aria-label, 'Username')]")
                    for field in username_fields:
                        if field.is_displayed():
                            rect = field.rect
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
                
                # Find Sign In button
                try:
                    signin_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Sign') or contains(text(), 'sign') or contains(text(), 'Log') or contains(text(), 'log')]")
                    seen_positions = set()
                    for button in signin_buttons:
                        if button.is_displayed():
                            rect = button.rect
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
                                break
                except:
                    pass
                
                # Find other elements (ZIP code, quote buttons, etc.)
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
                
                # Update global detected_elements
                detected_elements = elements_found
                
                # Update status if we're not in a special state
                if not current_status.startswith("Login") and not current_status.startswith("Typing"):
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
        current_screenshot = None
        detected_elements = []

if __name__ == '__main__':
    print("\n=== Geico Auto Quota Scanner ===")
    print("Open your browser and go to: http://localhost:5559")
    print("Or from another device: http://192.168.40.232:5559")
    print("Press Ctrl+C to stop the server\n")
    
    app.run(host='0.0.0.0', port=5559, debug=False)