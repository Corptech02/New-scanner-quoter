#!/usr/bin/env python3
"""
Geico Auto Quota Scanner - Web Interface
A web-based scanner that captures screenshots and detects elements on Geico's website
"""

from flask import Flask, render_template_string, jsonify, Response, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
import base64
import io
import time
import threading
import json
import subprocess
from PIL import Image
import sys

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
        :root {
            --bg-primary: #f5f5f5;
            --bg-secondary: white;
            --text-primary: #333;
            --text-secondary: #666;
            --text-muted: #999;
            --border-color: #ddd;
            --shadow-color: rgba(0,0,0,0.1);
            --button-bg: #0066cc;
            --button-bg-hover: #0052a3;
            --container-bg: #f0f0f0;
        }
        
        body.dark-theme {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2a2a2a;
            --text-primary: #e0e0e0;
            --text-secondary: #b0b0b0;
            --text-muted: #707070;
            --border-color: #444;
            --shadow-color: rgba(0,0,0,0.5);
            --button-bg: #0080ff;
            --button-bg-hover: #0066cc;
            --container-bg: #333333;
        }
        
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            transition: background-color 0.3s ease, color 0.3s ease;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: var(--bg-secondary);
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px var(--shadow-color);
            transition: background-color 0.3s ease, box-shadow 0.3s ease;
        }
        
        h1 {
            text-align: center;
            color: var(--text-primary);
            margin-bottom: 30px;
            transition: color 0.3s ease;
        }
        
        .controls {
            text-align: center;
            margin-bottom: 30px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
        }
        
        .start-button {
            background-color: var(--button-bg);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        
        .start-button:hover {
            background-color: var(--button-bg-hover);
        }
        
        .start-button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        
        .theme-toggle {
            position: relative;
            width: 60px;
            height: 30px;
            background-color: var(--border-color);
            border-radius: 15px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        
        .theme-toggle-slider {
            position: absolute;
            top: 3px;
            left: 3px;
            width: 24px;
            height: 24px;
            background-color: white;
            border-radius: 50%;
            transition: transform 0.3s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        body.dark-theme .theme-toggle-slider {
            transform: translateX(30px);
        }
        
        .theme-toggle-label {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            color: var(--text-secondary);
        }
        
        .screenshot-container {
            position: relative;
            background: var(--container-bg);
            border: 2px solid var(--border-color);
            border-radius: 5px;
            min-height: 600px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: visible;
            transition: background-color 0.3s ease, border-color 0.3s ease;
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
        
        .overlay-container .element-overlay {
            pointer-events: auto !important;
        }
        
        .element-overlay {
            position: absolute;
            border: 3px solid red;
            background-color: rgba(255, 0, 0, 0.1);
            pointer-events: auto;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 0 10px rgba(255, 0, 0, 0.3);
        }
        
        .element-overlay:hover {
            background-color: rgba(255, 0, 0, 0.4);
            border-color: #ff3333;
            z-index: 1000;
        }
        
        .element-label {
            position: absolute;
            background-color: rgba(220, 0, 0, 0.95);
            color: white;
            padding: 4px 8px;
            font-size: 12px;
            font-weight: bold;
            top: 2px;
            left: 2px;
            white-space: nowrap;
            border-radius: 3px;
            z-index: 1001;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            opacity: 1;
            pointer-events: none;
            visibility: visible;
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
            color: var(--text-secondary);
            transition: color 0.3s ease;
        }
        
        .placeholder-message {
            color: var(--text-muted);
            font-size: 18px;
            transition: color 0.3s ease;
        }
        
        .scroll-controls {
            position: fixed;
            bottom: 30px;
            right: 30px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            z-index: 1000;
        }
        
        .scroll-button {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background-color: var(--button-bg);
            color: white;
            border: none;
            font-size: 20px;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            transition: background-color 0.3s, transform 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .scroll-button:hover {
            background-color: var(--button-bg-hover);
            transform: scale(1.1);
        }
        
        .scroll-button:active {
            transform: scale(0.95);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Geico Auto Quota Scanner</h1>
        
        <div class="controls">
            <button class="start-button" onclick="startScanning()">Start Quote</button>
            <label class="theme-toggle-label">
                <span>Dark Theme</span>
                <div class="theme-toggle" onclick="toggleTheme()">
                    <div class="theme-toggle-slider"></div>
                </div>
            </label>
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
    
    <div class="scroll-controls" id="scrollControls" style="display: none;">
        <button class="scroll-button" onclick="scrollPage('up')" title="Scroll Up">↑</button>
        <button class="scroll-button" onclick="scrollPage('down')" title="Scroll Down">↓</button>
    </div>

    <script>
        let isScanning = false;
        let updateInterval = null;
        
        // Initialize theme from localStorage
        if (localStorage.getItem('darkTheme') === 'true') {
            document.body.classList.add('dark-theme');
        }
        
        function toggleTheme() {
            document.body.classList.toggle('dark-theme');
            const isDark = document.body.classList.contains('dark-theme');
            localStorage.setItem('darkTheme', isDark.toString());
        }
        
        function scrollPage(direction) {
            fetch('/scroll-page', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ direction: direction })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Scroll result:', data);
            })
            .catch(error => {
                console.error('Error scrolling:', error);
            });
        }
        
        function startScanning() {
            console.log('Start scanning clicked');
            if (isScanning) {
                console.log('Already scanning, returning');
                return;
            }
            
            isScanning = true;
            const button = document.querySelector('.start-button');
            button.disabled = true;
            button.textContent = 'Scanning...';
            
            document.getElementById('fpsCounter').style.display = 'block';
            document.getElementById('scrollControls').style.display = 'flex';
            document.getElementById('statusMessage').textContent = 'Initializing scanner...';
            
            console.log('Sending POST to /start-scan');
            fetch('/start-scan', { method: 'POST' })
                .then(response => {
                    console.log('Response received:', response);
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        return response.json();
                    } else {
                        return response.text().then(text => {
                            throw new Error(`Server returned non-JSON response: ${text.substring(0, 100)}...`);
                        });
                    }
                })
                .then(data => {
                    console.log('Data received:', data);
                    if (data.status === 'started') {
                        document.getElementById('statusMessage').textContent = 'Scanner started. Loading Geico website...';
                        console.log('Starting screenshot updates');
                        startUpdating();
                    } else {
                        console.log('Unexpected status:', data.status);
                    }
                })
                .catch(error => {
                    console.error('Error starting scan:', error);
                    document.getElementById('statusMessage').textContent = 'Error starting scanner: ' + error.message;
                    resetButton();
                });
        }
        
        function startUpdating() {
            console.log('startUpdating called - setting up interval');
            updateInterval = setInterval(() => {
                fetch('/get-screenshot')
                    .then(response => response.json())
                    .then(data => {
                        console.log('Screenshot data received:', data.screenshot ? 'has screenshot' : 'no screenshot', 'elements:', data.elements ? data.elements.length : 0);
                        if (data.screenshot) {
                            updateScreenshot(data.screenshot, data.elements);
                            document.getElementById('fpsCounter').textContent = `FPS: ${data.fps || 0}`;
                        } else {
                            console.log('No screenshot in response');
                        }
                    })
                    .catch(error => {
                        console.error('Error getting screenshot:', error);
                    });
            }, 50); // Update every 50ms for much higher FPS
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
                        label.textContent = element.label || 'Element';
                        overlay.appendChild(label);
                        
                        // Add click handler
                        overlay.addEventListener('click', function(e) {
                            e.preventDefault();
                            e.stopPropagation();
                            
                            console.log('Overlay clicked:', element.label, 'at', element.x + element.width/2, element.y + element.height/2);
                            
                            // Show visual feedback
                            overlay.style.backgroundColor = 'rgba(0, 255, 0, 0.5)';
                            overlay.style.borderColor = '#00ff00';
                            
                            // Send click request to backend
                            console.log('Sending click request for:', element.label);
                            fetch('/click-element', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({
                                    x: element.x + element.width / 2,
                                    y: element.y + element.height / 2,
                                    label: element.label
                                })
                            })
                            .then(response => response.json())
                            .then(data => {
                                console.log('Click result:', data);
                                // Reset visual feedback after a moment
                                setTimeout(() => {
                                    overlay.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
                                    overlay.style.borderColor = 'red';
                                }, 300);
                            })
                            .catch(error => {
                                console.error('Error clicking element:', error);
                                overlay.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
                                overlay.style.borderColor = 'red';
                            });
                        });
                        
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
    try:
        global driver, is_scanning, scan_thread
        
        print("[API] Start scan requested", flush=True)
        print(f"[API] Request method: {request.method}", flush=True)
        print(f"[API] Request headers: {dict(request.headers)}", flush=True)
        print(f"[API] Request data: {request.get_data()}", flush=True)
        sys.stdout.flush()
        
        # Clean up any existing browser instance first
        if driver:
            print("[API] Cleaning up existing driver")
            try:
                driver.quit()
            except:
                pass
            driver = None
        
        # Wait a bit for any existing scan to fully stop
        if is_scanning:
            print("[API] Stopping existing scan")
            is_scanning = False
            time.sleep(0.5)
        
        print("[API] Starting new scan thread")
        is_scanning = True
        scan_thread = threading.Thread(target=scan_geico_site)
        scan_thread.start()
        
        print("[API] Scan thread started, returning JSON response")
        response = jsonify({'status': 'started'})
        print(f"[API] Response: {response.get_data()}", flush=True)
        return response
    except Exception as e:
        print(f"[ERROR] Exception in start_scan: {e}", flush=True)
        import traceback
        traceback.print_exc()
        error_response = jsonify({'status': 'error', 'message': str(e)})
        return error_response, 500

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

@app.route('/click-element', methods=['POST'])
def click_element():
    global driver, current_status
    
    if not driver:
        return jsonify({'status': 'error', 'message': 'No active browser session'})
    
    try:
        data = request.get_json()
        x = data.get('x')
        y = data.get('y')
        label = data.get('label', 'Unknown')
        
        print(f"[DEBUG] Clicking element: {label} at ({x}, {y})")
        current_status = f"Clicking: {label}"
        
        # Use JavaScript to click at exact coordinates
        click_script = """
        var x = arguments[0];
        var y = arguments[1];
        
        // Find element at coordinates
        var element = document.elementFromPoint(x - window.scrollX, y - window.scrollY);
        
        if (element) {
            // Visual feedback
            var originalBg = element.style.backgroundColor;
            var originalBorder = element.style.border;
            element.style.backgroundColor = 'rgba(0, 255, 0, 0.5)';
            element.style.border = '3px solid #00ff00';
            
            // Click the element
            element.click();
            
            // Also dispatch mouse events for better compatibility
            var clickEvent = new MouseEvent('click', {
                view: window,
                bubbles: true,
                cancelable: true,
                clientX: x - window.scrollX,
                clientY: y - window.scrollY
            });
            element.dispatchEvent(clickEvent);
            
            // Reset style after a moment
            setTimeout(function() {
                element.style.backgroundColor = originalBg;
                element.style.border = originalBorder;
            }, 500);
            
            return {success: true, element: element.tagName, text: element.textContent.substring(0, 50)};
        } else {
            return {success: false, message: 'No element found at coordinates'};
        }
        """
        
        result = driver.execute_script(click_script, x, y)
        print(f"[DEBUG] Click result: {result}")
        
        # Wait a moment for any page changes
        time.sleep(0.5)
        
        return jsonify({
            'status': 'success',
            'result': result,
            'clicked': label
        })
        
    except Exception as e:
        print(f"[ERROR] Click failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/scroll-page', methods=['POST'])
def scroll_page():
    global driver, current_status
    
    if not driver:
        return jsonify({'status': 'error', 'message': 'No active browser session'})
    
    try:
        data = request.get_json()
        direction = data.get('direction', 'down')
        
        print(f"[DEBUG] Scrolling page: {direction}")
        current_status = f"Scrolling {direction}..."
        
        # Scroll the page
        if direction == 'down':
            driver.execute_script("window.scrollBy(0, 300);")
        elif direction == 'up':
            driver.execute_script("window.scrollBy(0, -300);")
        
        # Wait a moment for elements to update
        time.sleep(0.3)
        
        # Get current scroll position
        scroll_pos = driver.execute_script("return {top: window.pageYOffset, height: document.documentElement.scrollHeight, viewport: window.innerHeight};")
        
        return jsonify({
            'status': 'success',
            'direction': direction,
            'scroll_position': scroll_pos
        })
        
    except Exception as e:
        print(f"[ERROR] Scroll failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

def scan_geico_site():
    global driver, is_scanning, current_screenshot, detected_elements, fps_counter, last_fps_time, current_status
    
    print("\n[DEBUG] scan_geico_site() function called!", flush=True)
    sys.stdout.flush()
    
    # Kill any existing Chrome processes first - more aggressive
    import subprocess
    import os
    import tempfile
    import shutil
    
    print("[DEBUG] Killing existing Chrome processes...", flush=True)
    sys.stdout.flush()
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
        # Add more arguments to fix Chrome startup issues
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--disable-extensions')
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
                
                print(f"\n[DEBUG LOGIN SCAN] Starting login field detection on URL: {driver.current_url}", flush=True)
                sys.stdout.flush()
                
                # Check for username field
                try:
                    username_fields = driver.find_elements(By.XPATH, "//input[@type='text' or @type='email' or @name='username' or @name='j_username' or @id='username' or contains(@placeholder, 'username') or contains(@placeholder, 'Username') or contains(@aria-label, 'username') or contains(@aria-label, 'Username')]")
                    print(f"[DEBUG LOGIN SCAN] Found {len(username_fields)} potential username fields")
                    for field in username_fields:
                        if field.is_displayed():
                            has_username_field = True
                            username_element = field
                            print(f"[DEBUG LOGIN SCAN] Username field found! Type: {field.get_attribute('type')}, Name: {field.get_attribute('name')}, ID: {field.get_attribute('id')}")
                            break
                    if not has_username_field:
                        print("[DEBUG LOGIN SCAN] No visible username field found")
                except Exception as e:
                    print(f"[DEBUG LOGIN SCAN] Error finding username field: {e}")
                
                # Check for password field
                try:
                    password_fields = driver.find_elements(By.XPATH, "//input[@type='password' or @name='password' or @name='j_password' or @id='password']")
                    print(f"[DEBUG LOGIN SCAN] Found {len(password_fields)} potential password fields")
                    for field in password_fields:
                        if field.is_displayed():
                            has_password_field = True
                            password_element = field
                            print(f"[DEBUG LOGIN SCAN] Password field found! Type: {field.get_attribute('type')}, Name: {field.get_attribute('name')}, ID: {field.get_attribute('id')}")
                            break
                    if not has_password_field:
                        print("[DEBUG LOGIN SCAN] No visible password field found")
                except Exception as e:
                    print(f"[DEBUG LOGIN SCAN] Error finding password field: {e}")
                
                print(f"[DEBUG LOGIN SCAN] Detection complete. Has username: {has_username_field}, Has password: {has_password_field}")
                
                # If we found both username and password fields, try to auto-fill them
                if has_username_field and has_password_field and not driver.execute_script("return window.geicoLoginAttempted || false"):
                    # Mark that we've attempted login to avoid repeated attempts
                    driver.execute_script("window.geicoLoginAttempted = true;")
                    
                    print(f"[DEBUG] Found login fields on page: {driver.current_url}")
                    print("[DEBUG] Waiting 5 seconds before auto-fill so you can see the highlighted fields...")
                    
                    # Wait 5 seconds with countdown so user can see the highlighted login fields
                    for i in range(5, 0, -1):
                        current_status = f"Login detected - Auto-fill in {i} seconds..."
                        print(f"[DEBUG] Countdown: {i} seconds remaining...")
                        time.sleep(1)
                    
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
                
                # CHECK IF WE'RE ON DASHBOARD AND NEED TO CLICK COMMERCIAL AUTO/TRUCKING
                # This runs after login is complete
                if not has_username_field and not has_password_field:
                    # We're not on login page anymore, check if we need to click Commercial Auto/Trucking
                    try:
                        # APPLY COMMERCIAL AUTO REFRESH PREVENTION FIX
                        if not driver.execute_script("return window.commercialAutoFixApplied || false"):
                            print("[DEBUG] Applying Commercial Auto refresh prevention fix...")
                            driver.execute_script("""
                            (function() {
                                console.log('[COMMERCIAL AUTO FIX] Installing refresh prevention...');
                                
                                // Flag to track if fix is applied
                                window.commercialAutoFixApplied = true;
                                window.commercialAutoMode = false;
                                
                                // Store original navigation functions
                                if (!window._navigationBackup) {
                                    window._navigationBackup = {
                                        pushState: history.pushState,
                                        replaceState: history.replaceState,
                                        assign: window.location.assign,
                                        replace: window.location.replace,
                                        reload: window.location.reload,
                                        href: Object.getOwnPropertyDescriptor(window.location, 'href')
                                    };
                                }
                                
                                // Override navigation methods to prevent refresh during Commercial Auto mode
                                history.pushState = function() {
                                    if (window.commercialAutoMode) {
                                        console.log('[FIX] Blocked pushState during Commercial Auto mode');
                                        return;
                                    }
                                    return window._navigationBackup.pushState.apply(history, arguments);
                                };
                                
                                history.replaceState = function() {
                                    if (window.commercialAutoMode) {
                                        console.log('[FIX] Blocked replaceState during Commercial Auto mode');
                                        return;
                                    }
                                    return window._navigationBackup.replaceState.apply(history, arguments);
                                };
                                
                                window.location.assign = function(url) {
                                    if (window.commercialAutoMode) {
                                        console.log('[FIX] Blocked location.assign to:', url);
                                        return;
                                    }
                                    return window._navigationBackup.assign.call(window.location, url);
                                };
                                
                                window.location.replace = function(url) {
                                    if (window.commercialAutoMode) {
                                        console.log('[FIX] Blocked location.replace to:', url);
                                        return;
                                    }
                                    return window._navigationBackup.replace.call(window.location, url);
                                };
                                
                                window.location.reload = function() {
                                    if (window.commercialAutoMode) {
                                        console.log('[FIX] Blocked location.reload');
                                        return;
                                    }
                                    return window._navigationBackup.reload.call(window.location);
                                };
                                
                                // Override location.href setter
                                Object.defineProperty(window.location, 'href', {
                                    get: function() {
                                        return window._navigationBackup.href.get.call(window.location);
                                    },
                                    set: function(val) {
                                        if (window.commercialAutoMode) {
                                            console.log('[FIX] Blocked location.href change to:', val);
                                            return;
                                        }
                                        window._navigationBackup.href.set.call(window.location, val);
                                    }
                                });
                                
                                // Intercept form submissions
                                document.addEventListener('submit', function(e) {
                                    if (window.commercialAutoMode) {
                                        console.log('[FIX] Preventing form submission during Commercial Auto mode');
                                        e.preventDefault();
                                        return false;
                                    }
                                }, true);
                                
                                // Monitor all clicks for Commercial Auto
                                document.addEventListener('click', function(e) {
                                    var target = e.target;
                                    var text = '';
                                    
                                    // Check element and parents for Commercial Auto text
                                    var checkElement = target;
                                    while (checkElement && checkElement !== document.body) {
                                        text = (checkElement.textContent || checkElement.innerText || '');
                                        
                                        if (text.includes('Commercial Auto') || text.includes('Trucking')) {
                                            console.log('[FIX] Detected Commercial Auto click, enabling protection mode');
                                            
                                            // Enable protection mode
                                            window.commercialAutoMode = true;
                                            window.commercialAutoClicked = true;
                                            
                                            // Disable protection after 3 seconds
                                            setTimeout(function() {
                                                window.commercialAutoMode = false;
                                                console.log('[FIX] Commercial Auto protection mode disabled');
                                            }, 3000);
                                            
                                            break;
                                        }
                                        checkElement = checkElement.parentElement;
                                    }
                                }, true);
                                
                                console.log('[COMMERCIAL AUTO FIX] Refresh prevention installed successfully');
                            })();
                            """)
                            print("[DEBUG] Commercial Auto refresh prevention fix applied")
                        
                        # Check if we've already clicked commercial auto (avoid repeated clicks)
                        if not driver.execute_script("return window.commercialAutoClicked || false"):
                            print(f"[DEBUG] Checking for Commercial Auto/Trucking tab on URL: {driver.current_url}")
                            
                            # Wait a bit for page to fully load after login
                            time.sleep(2)
                            
                            # Look for Commercial Auto/Trucking element - be more specific
                            # First try exact text match
                            commercial_elements = driver.find_elements(By.XPATH, 
                                "//a[normalize-space(text())='Commercial Auto/Trucking'] | " +
                                "//button[normalize-space(text())='Commercial Auto/Trucking'] | " +
                                "//div[normalize-space(text())='Commercial Auto/Trucking'] | " +
                                "//span[normalize-space(text())='Commercial Auto/Trucking']"
                            )
                            
                            # If not found, try contains approach but be more selective
                            if not commercial_elements:
                                commercial_elements = driver.find_elements(By.XPATH, 
                                    "//a[contains(text(), 'Commercial Auto/Trucking')] | " +
                                    "//button[contains(text(), 'Commercial Auto/Trucking')] | " +
                                    "//div[@role='button' and contains(text(), 'Commercial Auto/Trucking')] | " +
                                    "//div[@onclick and contains(text(), 'Commercial Auto/Trucking')]"
                                )
                            
                            print(f"[DEBUG] Found {len(commercial_elements)} potential Commercial Auto/Trucking elements")
                            
                            # Look for the most specific, smallest element that contains the text
                            best_element = None
                            smallest_area = float('inf')
                            
                            for elem in commercial_elements:
                                if elem.is_displayed():
                                    elem_text = elem.text.strip()
                                    rect = elem.rect
                                    area = rect['width'] * rect['height']
                                    
                                    # Skip very large elements (likely containers)
                                    if area > 50000:
                                        print(f"[DEBUG] Skipping large element (area={area}): '{elem_text[:50]}...'")
                                        continue
                                    
                                    # Look for exact match or close match
                                    if elem_text == "Commercial Auto/Trucking" or \
                                       (elem_text.startswith("Commercial Auto/Trucking") and len(elem_text) < 50):
                                        print(f"[DEBUG] Found good Commercial Auto element: '{elem_text}' (area={area})")
                                        if area < smallest_area:
                                            smallest_area = area
                                            best_element = elem
                            
                            if best_element:
                                elem = best_element
                                elem_text = elem.text.strip()
                                print(f"[DEBUG] Selected best Commercial Auto element to click: '{elem_text}'")
                                current_status = "Found Commercial Auto/Trucking - clicking..."
                                
                                # Highlight the element briefly before clicking
                                driver.execute_script("""
                                    var elem = arguments[0];
                                    elem.style.border = '3px solid green';
                                    elem.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
                                """, elem)
                                
                                time.sleep(1)  # Brief pause to show highlight
                                
                                try:
                                    # Store initial URL before clicking
                                    initial_url = driver.current_url
                                    print(f"[DEBUG] URL before click: {initial_url}")
                                    
                                    # Try JavaScript click first for reliability
                                    driver.execute_script("""
                                        var elem = arguments[0];
                                        elem.scrollIntoView({block: 'center'});
                                        elem.click();
                                        window.commercialAutoClicked = true;
                                        console.log('Commercial Auto/Trucking clicked via JavaScript');
                                    """, elem)
                                    print("[DEBUG] Successfully clicked Commercial Auto/Trucking tab via JavaScript")
                                    current_status = "Commercial Auto/Trucking clicked - loading..."
                                    
                                    # Wait for page to fully load and verify navigation
                                    try:
                                        # Wait for document ready state
                                        WebDriverWait(driver, 10).until(
                                            lambda d: d.execute_script("return document.readyState") == "complete"
                                        )
                                        
                                        # Check if URL changed (indicating navigation)
                                        time.sleep(1)  # Small delay to allow URL to update
                                        new_url = driver.current_url
                                        print(f"[DEBUG] URL after click: {new_url}")
                                        
                                        if new_url != initial_url:
                                            print("[DEBUG] Navigation detected - waiting for new page to load")
                                            # Wait for new page elements to appear
                                            time.sleep(3)
                                            
                                            # Verify we're on commercial auto page
                                            page_source = driver.page_source.lower()
                                            if "commercial" in page_source or "trucking" in page_source:
                                                print("[DEBUG] Successfully navigated to Commercial Auto page")
                                                current_status = "On Commercial Auto/Trucking page"
                                            else:
                                                print("[DEBUG] Page loaded but may not be Commercial Auto page")
                                        else:
                                            print("[DEBUG] No URL change detected - checking for dynamic content")
                                            # Page might load content dynamically without URL change
                                            time.sleep(3)
                                            
                                    except TimeoutException:
                                        print("[DEBUG] Timeout waiting for page load - continuing anyway")
                                        time.sleep(2)
                                        
                                except Exception as js_error:
                                    print(f"[DEBUG] JavaScript click failed: {js_error}, trying Selenium click")
                                    try:
                                        # Store initial URL before clicking
                                        initial_url = driver.current_url
                                        
                                        elem.click()
                                        driver.execute_script("window.commercialAutoClicked = true;")
                                        print("[DEBUG] Successfully clicked Commercial Auto/Trucking tab via Selenium")
                                        current_status = "Commercial Auto/Trucking clicked - loading..."
                                        
                                        # Same wait logic as above
                                        try:
                                            WebDriverWait(driver, 10).until(
                                                lambda d: d.execute_script("return document.readyState") == "complete"
                                            )
                                            time.sleep(1)
                                            new_url = driver.current_url
                                            print(f"[DEBUG] URL after Selenium click: {new_url}")
                                            
                                            if new_url != initial_url:
                                                print("[DEBUG] Navigation detected after Selenium click")
                                                time.sleep(3)
                                            else:
                                                time.sleep(3)
                                                
                                        except TimeoutException:
                                            print("[DEBUG] Timeout after Selenium click - continuing")
                                            time.sleep(2)
                                            
                                    except Exception as selenium_error:
                                        print(f"[DEBUG] Selenium click also failed: {selenium_error}")
                            
                            else:
                                print("[DEBUG] No clickable Commercial Auto/Trucking element found on this page")
                            
                            if not driver.execute_script("return window.commercialAutoClicked || false"):
                                print("[DEBUG] Commercial Auto/Trucking element not clicked yet")
                                
                    except Exception as e:
                        print(f"[DEBUG] Error checking for Commercial Auto/Trucking: {e}")
                        import traceback
                        traceback.print_exc()
                
                # CHECK IF WE'RE ON COMMERCIAL AUTO PAGE AND NEED TO FILL ZIP CODE
                # This runs after Commercial Auto/Trucking is clicked
                if driver.execute_script("return window.commercialAutoClicked || false") and \
                   not driver.execute_script("return window.zipCodeFilled || false"):
                    try:
                        print(f"[DEBUG] On Commercial Auto page, checking for zip code field...")
                        print(f"[DEBUG] Current URL: {driver.current_url}")
                        # Wait longer for form to load
                        time.sleep(5)
                        
                        # Look for ALL input fields first to debug
                        all_inputs = driver.find_elements(By.TAG_NAME, "input")
                        print(f"[DEBUG] Total input fields on page: {len(all_inputs)}")
                        
                        # Look for garage/zip code field - try multiple selectors including case variations
                        zip_elements = driver.find_elements(By.XPATH, 
                            "//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'zip')] | " +
                            "//input[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'zip')] | " +
                            "//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'zip')] | " +
                            "//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'garage')] | " +
                            "//input[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'garage')] | " +
                            "//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'garage')] | " +
                            "//input[@type='text' or @type='number'][position() > 1]"  # Get text/number inputs that aren't the first one
                        )
                        
                        print(f"[DEBUG] Found {len(zip_elements)} potential zip code fields")
                        
                        # Debug: print info about visible inputs
                        if len(zip_elements) == 0:
                            print("[DEBUG] No zip fields found. Checking all visible inputs:")
                            for idx, inp in enumerate(all_inputs[:10]):  # Check first 10 inputs
                                if inp.is_displayed():
                                    inp_type = inp.get_attribute('type') or 'text'
                                    inp_name = inp.get_attribute('name') or ''
                                    inp_id = inp.get_attribute('id') or ''
                                    inp_placeholder = inp.get_attribute('placeholder') or ''
                                    print(f"[DEBUG] Input {idx}: type={inp_type}, name={inp_name}, id={inp_id}, placeholder={inp_placeholder}")
                        
                        zip_filled = False
                        for zip_elem in zip_elements:
                            if zip_elem.is_displayed() and zip_elem.is_enabled():
                                try:
                                    elem_name = zip_elem.get_attribute('name') or ''
                                    elem_id = zip_elem.get_attribute('id') or ''
                                    elem_placeholder = zip_elem.get_attribute('placeholder') or ''
                                    print(f"[DEBUG] Found zip field - name: '{elem_name}', id: '{elem_id}', placeholder: '{elem_placeholder}'")
                                    
                                    # Highlight the field
                                    driver.execute_script("""
                                        var elem = arguments[0];
                                        elem.style.border = '3px solid blue';
                                        elem.style.backgroundColor = 'rgba(0, 0, 255, 0.1)';
                                    """, zip_elem)
                                    
                                    current_status = "Filling garage zip code..."
                                    time.sleep(1)
                                    
                                    # Use Chrome DevTools Protocol for undetected ZIP entry
                                    print("[DEBUG] Using Chrome DevTools Protocol (CDP) for undetected ZIP entry...")
                                    
                                    # First, hide webdriver detection
                                    try:
                                        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                                            'source': '''
                                                Object.defineProperty(navigator, 'webdriver', {
                                                    get: () => undefined
                                                });
                                            '''
                                        })
                                    except:
                                        pass
                                    
                                    # Check if webdriver is being detected
                                    bot_detected = driver.execute_script("return navigator.webdriver;")
                                    if bot_detected:
                                        print("[DEBUG] WARNING: Browser detecting automated control (navigator.webdriver = true)")
                                    
                                    try:
                                        # Method 1: Try CDP input events (most undetectable)
                                        print("[DEBUG] Method 1: Using Chrome DevTools Protocol...")
                                        
                                        # Get element position
                                        element_info = driver.execute_script("""
                                            var elem = arguments[0];
                                            var rect = elem.getBoundingClientRect();
                                            elem.scrollIntoView({block: 'center'});
                                            return {
                                                x: Math.round(rect.left + rect.width/2),
                                                y: Math.round(rect.top + rect.height/2),
                                                width: rect.width,
                                                height: rect.height
                                            };
                                        """, zip_elem)
                                        
                                        # Click using CDP
                                        driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
                                            'type': 'mousePressed',
                                            'x': element_info['x'],
                                            'y': element_info['y'],
                                            'button': 'left',
                                            'clickCount': 1
                                        })
                                        
                                        driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
                                            'type': 'mouseReleased',
                                            'x': element_info['x'],
                                            'y': element_info['y'],
                                            'button': 'left',
                                            'clickCount': 1
                                        })
                                        
                                        time.sleep(0.3)
                                        
                                        # Clear field with Ctrl+A and Delete via CDP
                                        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
                                            'type': 'keyDown',
                                            'modifiers': 2,  # Ctrl
                                            'key': 'a',
                                            'code': 'KeyA',
                                            'windowsVirtualKeyCode': 65
                                        })
                                        
                                        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
                                            'type': 'keyUp',
                                            'modifiers': 2,
                                            'key': 'a',
                                            'code': 'KeyA',
                                            'windowsVirtualKeyCode': 65
                                        })
                                        
                                        time.sleep(0.1)
                                        
                                        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
                                            'type': 'keyDown',
                                            'key': 'Delete',
                                            'code': 'Delete',
                                            'windowsVirtualKeyCode': 46
                                        })
                                        
                                        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
                                            'type': 'keyUp',
                                            'key': 'Delete',
                                            'code': 'Delete',
                                            'windowsVirtualKeyCode': 46
                                        })
                                        
                                        time.sleep(0.2)
                                        
                                        # Type each character via CDP
                                        zip_code = '44256'
                                        for i, char in enumerate(zip_code):
                                            # Key down
                                            driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
                                                'type': 'keyDown',
                                                'key': char,
                                                'code': f'Digit{char}',
                                                'text': char,
                                                'windowsVirtualKeyCode': 48 + int(char)
                                            })
                                            
                                            # Character event
                                            driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
                                                'type': 'char',
                                                'text': char,
                                                'key': char,
                                                'windowsVirtualKeyCode': 48 + int(char)
                                            })
                                            
                                            # Key up
                                            driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
                                                'type': 'keyUp',
                                                'key': char,
                                                'code': f'Digit{char}',
                                                'windowsVirtualKeyCode': 48 + int(char)
                                            })
                                            
                                            # Natural typing delay
                                            time.sleep(0.08 + (0.04 * (i % 2)))
                                            print(f"[DEBUG] CDP typed: {char}")
                                        
                                        # Tab to trigger validation
                                        time.sleep(0.3)
                                        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
                                            'type': 'keyDown',
                                            'key': 'Tab',
                                            'code': 'Tab',
                                            'windowsVirtualKeyCode': 9
                                        })
                                        
                                        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
                                            'type': 'keyUp',
                                            'key': 'Tab',
                                            'code': 'Tab',
                                            'windowsVirtualKeyCode': 9
                                        })
                                        
                                        print("[DEBUG] CDP method completed")
                                        
                                    except Exception as cdp_error:
                                        print(f"[DEBUG] CDP method failed: {cdp_error}")
                                        
                                        # Fallback: Try execCommand
                                        print("[DEBUG] Fallback: Using execCommand...")
                                        success = driver.execute_script("""
                                            var elem = arguments[0];
                                            elem.focus();
                                            elem.select();
                                            document.execCommand('delete');
                                            
                                            var success = true;
                                            '44256'.split('').forEach(function(char) {
                                                if (!document.execCommand('insertText', false, char)) {
                                                    success = false;
                                                }
                                            });
                                            
                                            elem.blur();
                                            return success;
                                        """, zip_elem)
                                        
                                        if not success:
                                            # Final fallback: ActionChains
                                            print("[DEBUG] Final fallback: ActionChains...")
                                            actions = ActionChains(driver)
                                            actions.move_to_element(zip_elem).click().perform()
                                            time.sleep(0.2)
                                            actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
                                            actions.send_keys(Keys.DELETE).perform()
                                            time.sleep(0.1)
                                            for char in '44256':
                                                actions.send_keys(char).perform()
                                                time.sleep(0.1)
                                            actions.send_keys(Keys.TAB).perform()
                                        
                                        # Wait for validation
                                        time.sleep(1.5)
                                        
                                        # Method 3: If still no state, try clicking elsewhere to trigger validation
                                        state_check = driver.execute_script("""
                                            var states = document.querySelectorAll('select[name*="state"], input[name*="state"], #state');
                                            for (var i = 0; i < states.length; i++) {
                                                if (states[i].value && states[i].value !== '') {
                                                    return states[i].value;
                                                }
                                            }
                                            return null;
                                        """)
                                        
                                        if not state_check:
                                            print("[DEBUG] State not populated yet, trying to trigger validation...")
                                            
                                            # Click on body to ensure field loses focus
                                            driver.execute_script("document.body.click();")
                                            time.sleep(0.5)
                                            
                                            # Try clicking next visible input field
                                            driver.execute_script("""
                                                var inputs = document.querySelectorAll('input:not([type="hidden"]), select');
                                                var zipField = arguments[0];
                                                var foundZip = false;
                                                
                                                for (var i = 0; i < inputs.length; i++) {
                                                    if (inputs[i] === zipField) {
                                                        foundZip = true;
                                                    } else if (foundZip && inputs[i].offsetParent !== null) {
                                                        inputs[i].click();
                                                        inputs[i].focus();
                                                        break;
                                                    }
                                                }
                                            """, zip_elem)
                                            
                                            time.sleep(1)
                                            
                                            # Final state check
                                            state_check = driver.execute_script("""
                                                var states = document.querySelectorAll('select[name*="state"], input[name*="state"], #state');
                                                for (var i = 0; i < states.length; i++) {
                                                    if (states[i].value && states[i].value !== '') {
                                                        return states[i].value;
                                                    }
                                                }
                                                return null;
                                            """)
                                        
                                        if state_check:
                                            print(f"[DEBUG] SUCCESS! State populated: {state_check}")
                                            driver.execute_script("arguments[0].style.backgroundColor = 'lightgreen';", zip_elem)
                                        else:
                                            print("[DEBUG] WARNING: State still not populated")
                                            print("[DEBUG] ZIP code is in field but validation may not have triggered")
                                            
                                            # Log any validation messages
                                            validation_msg = driver.execute_script("""
                                                var elem = arguments[0];
                                                return {
                                                    validity: elem.validity,
                                                    validationMessage: elem.validationMessage,
                                                    value: elem.value
                                                };
                                            """, zip_elem)
                                            print(f"[DEBUG] Field state: {validation_msg}")
                                            
                                    except Exception as e:
                                        print(f"[DEBUG] Error during ZIP entry: {e}")
                                        import traceback
                                        traceback.print_exc()
                                    
                                    zip_filled = True
                                    # Wait for validation to complete
                                    time.sleep(1)
                                    
                                    # Now look for USDOT field to click
                                    print("[DEBUG] Looking for USDOT field...")
                                    usdot_elements = driver.find_elements(By.XPATH,
                                        "//input[contains(@name, 'usdot') or contains(@id, 'usdot') or contains(@name, 'USDOT') or contains(@id, 'USDOT')] | " +
                                        "//input[contains(@placeholder, 'USDOT') or contains(@aria-label, 'USDOT')] | " +
                                        "//input[contains(@placeholder, 'DOT') or contains(@aria-label, 'DOT')] | " +
                                        "//input[@type='text'][contains(preceding-sibling::label/text(), 'USDOT') or contains(following-sibling::label/text(), 'USDOT')]"
                                    )
                                    
                                    print(f"[DEBUG] Found {len(usdot_elements)} potential USDOT fields")
                                    
                                    for usdot_elem in usdot_elements:
                                        if usdot_elem.is_displayed() and usdot_elem.is_enabled():
                                            try:
                                                # Highlight and click USDOT field
                                                driver.execute_script("""
                                                    var elem = arguments[0];
                                                    elem.style.border = '3px solid green';
                                                    elem.style.backgroundColor = 'rgba(0, 255, 0, 0.1)';
                                                    elem.scrollIntoView({block: 'center'});
                                                    elem.click();
                                                    elem.focus();
                                                    console.log('USDOT field clicked');
                                                """, usdot_elem)
                                                
                                                print("[DEBUG] Successfully clicked USDOT field")
                                                current_status = "USDOT field selected - ready for input"
                                                break
                                            except Exception as usdot_error:
                                                print(f"[DEBUG] Error clicking USDOT field: {usdot_error}")
                                    
                                    break  # Exit after successfully filling zip
                                    
                                except Exception as zip_error:
                                    print(f"[DEBUG] Error filling zip code in this field: {zip_error}")
                        
                        if not zip_filled:
                            print("[DEBUG] Could not find or fill zip code field")
                            
                    except Exception as e:
                        print(f"[DEBUG] Error in zip code filling process: {e}")
                        import traceback
                        traceback.print_exc()
                
                # Now continue with element detection for visual feedback
                # This will show the red boxes around detected elements
                
                # ENHANCED ELEMENT SCANNING - Smart filtering to prevent duplicates
                # Keep track of already found elements
                elements_found = []
                
                # SPECIAL HANDLING FOR LOGIN PAGE - Add username and password fields
                if has_username_field and has_password_field:
                    print(f"[DEBUG LOGIN SCAN] Login page detected! Username field: {username_element is not None}, Password field: {password_element is not None}")
                    
                    # Add username field
                    if username_element and username_element.is_displayed():
                        rect = username_element.rect
                        print(f"[DEBUG LOGIN SCAN] Username field rect: x={rect['x']}, y={rect['y']}, width={rect['width']}, height={rect['height']}")
                        if rect['width'] > 20 and rect['height'] > 10:
                            elements_found.append({
                                'label': 'Username',
                                'x': rect['x'],
                                'y': rect['y'],
                                'width': rect['width'],
                                'height': rect['height']
                            })
                            print("[DEBUG LOGIN SCAN] Username field added to elements_found")
                        else:
                            print(f"[DEBUG LOGIN SCAN] Username field too small: {rect['width']}x{rect['height']}")
                    else:
                        print(f"[DEBUG LOGIN SCAN] Username element not displayed or None: {username_element}")
                    
                    # Add password field
                    if password_element and password_element.is_displayed():
                        rect = password_element.rect
                        print(f"[DEBUG LOGIN SCAN] Password field rect: x={rect['x']}, y={rect['y']}, width={rect['width']}, height={rect['height']}")
                        if rect['width'] > 20 and rect['height'] > 10:
                            elements_found.append({
                                'label': 'Password',
                                'x': rect['x'],
                                'y': rect['y'],
                                'width': rect['width'],
                                'height': rect['height']
                            })
                            print("[DEBUG LOGIN SCAN] Password field added to elements_found")
                        else:
                            print(f"[DEBUG LOGIN SCAN] Password field too small: {rect['width']}x{rect['height']}")
                    else:
                        print(f"[DEBUG LOGIN SCAN] Password element not displayed or None: {password_element}")
                    
                    # Also find and add the Sign In button on login page
                    try:
                        sign_in_buttons = driver.find_elements(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'sign') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log')] | //input[@type='submit']")
                        for btn in sign_in_buttons:
                            if btn.is_displayed():
                                rect = btn.rect
                                if rect['width'] > 30 and rect['height'] > 20:
                                    btn_text = btn.text.strip() or btn.get_attribute('value') or 'Sign In'
                                    elements_found.append({
                                        'label': btn_text[:20],
                                        'x': rect['x'],
                                        'y': rect['y'],
                                        'width': rect['width'],
                                        'height': rect['height']
                                    })
                                    break  # Only add the first sign-in button found
                    except:
                        pass
                
                def is_element_overlapping(new_elem, existing_elem):
                    """Check if two elements overlap significantly"""
                    # Calculate the overlap area
                    x_overlap = max(0, min(new_elem['x'] + new_elem['width'], existing_elem['x'] + existing_elem['width']) - 
                                   max(new_elem['x'], existing_elem['x']))
                    y_overlap = max(0, min(new_elem['y'] + new_elem['height'], existing_elem['y'] + existing_elem['height']) - 
                                   max(new_elem['y'], existing_elem['y']))
                    
                    overlap_area = x_overlap * y_overlap
                    new_area = new_elem['width'] * new_elem['height']
                    
                    # If more than 70% overlap, consider it duplicate
                    return overlap_area > (new_area * 0.7)
                
                def is_element_contained(child, parent):
                    """Check if child element is fully contained within parent"""
                    return (child['x'] >= parent['x'] and 
                            child['y'] >= parent['y'] and 
                            child['x'] + child['width'] <= parent['x'] + parent['width'] and 
                            child['y'] + child['height'] <= parent['y'] + parent['height'])
                
                def add_unique_element(elem_data):
                    """Add element only if it's not duplicate/overlapping/contained"""
                    # Skip elements that are too large (likely containers/backgrounds)
                    if elem_data['width'] > 800 or elem_data['height'] > 400:
                        return False
                    
                    # Skip elements that are too small
                    if elem_data['width'] < 15 or elem_data['height'] < 8:
                        return False
                    
                    # Check against existing elements
                    for existing in elements_found:
                        # Skip if this element significantly overlaps with existing
                        if is_element_overlapping(elem_data, existing):
                            return False
                        
                        # Skip if this element is contained within existing
                        if is_element_contained(elem_data, existing):
                            return False
                        
                        # Skip if existing element is contained within this one
                        # (keep the smaller, more specific element)
                        if is_element_contained(existing, elem_data):
                            return False
                    
                    elements_found.append(elem_data)
                    return True
                
                # Find only important input elements (excluding login fields on login page)
                try:
                    # Always scan inputs
                    if True:
                        all_inputs = driver.find_elements(By.TAG_NAME, "input")
                        for idx, inp in enumerate(all_inputs):
                            if inp.is_displayed():
                                rect = inp.rect
                                if rect['width'] > 20 and rect['height'] > 10:
                                    # Skip only hidden inputs
                                    input_type = inp.get_attribute('type') or 'text'
                                    if input_type in ['hidden']:
                                        continue
                                    
                                    # Skip if this is the username or password field we already added
                                    if has_username_field and inp == username_element:
                                        continue
                                    if has_password_field and inp == password_element:
                                        continue
                                    
                                    placeholder = inp.get_attribute('placeholder') or ''
                                    name = inp.get_attribute('name') or ''
                                    id_attr = inp.get_attribute('id') or ''
                                    
                                    # Create descriptive label
                                    label = f"Input [{input_type}]"
                                    if placeholder:
                                        label = placeholder
                                    elif name:
                                        label = f"Input: {name}"
                                    elif id_attr:
                                        label = f"Input: {id_attr}"
                                    
                                    add_unique_element({
                                        'label': label,
                                        'x': rect['x'],
                                        'y': rect['y'],
                                        'width': rect['width'],
                                        'height': rect['height']
                                    })
                except Exception as e:
                    print(f"Error scanning inputs: {e}")
                
                # Find buttons
                try:
                    all_buttons = driver.find_elements(By.TAG_NAME, "button")
                    for btn in all_buttons:
                        if btn.is_displayed():
                            rect = btn.rect
                            if rect['width'] > 30 and rect['height'] > 20:
                                # Get button text or aria-label
                                btn_text = btn.text.strip()
                                if not btn_text:
                                    btn_text = btn.get_attribute('aria-label') or ''
                                
                                # Skip empty buttons
                                if btn_text:
                                    add_unique_element({
                                        'label': f"Button: {btn_text[:20]}",
                                        'x': rect['x'],
                                        'y': rect['y'],
                                        'width': rect['width'],
                                        'height': rect['height']
                                    })
                except Exception as e:
                    print(f"Error scanning buttons: {e}")
                
                # Find important links
                try:
                    all_links = driver.find_elements(By.TAG_NAME, "a")
                    for link in all_links:
                        if link.is_displayed():
                            rect = link.rect
                            # More lenient size limits to capture more links
                            if rect['width'] > 15 and rect['height'] > 8 and rect['width'] < 500 and rect['height'] < 120:
                                link_text = link.text.strip()
                                aria_label = link.get_attribute('aria-label') or ''
                                
                                # Skip links without meaningful text
                                if link_text or aria_label:
                                    label = link_text[:30] if link_text else aria_label[:30]
                                    
                                    # Accept even short labels
                                    if len(label) > 0:
                                        add_unique_element({
                                            'label': f"{label}",
                                            'x': rect['x'],
                                            'y': rect['y'],
                                            'width': rect['width'],
                                            'height': rect['height']
                                        })
                except Exception as e:
                    print(f"Error scanning links: {e}")
                
                # Find select dropdowns
                try:
                    all_selects = driver.find_elements(By.TAG_NAME, "select")
                    for sel in all_selects:
                        if sel.is_displayed():
                            rect = sel.rect
                            if rect['width'] > 30 and rect['height'] > 20:
                                name = sel.get_attribute('name') or sel.get_attribute('id') or 'Dropdown'
                                add_unique_element({
                                    'label': f"Select: {name}",
                                    'x': rect['x'],
                                    'y': rect['y'],
                                    'width': rect['width'],
                                    'height': rect['height']
                                })
                except Exception as e:
                    print(f"Error scanning selects: {e}")
                
                # Find textareas
                try:
                    all_textareas = driver.find_elements(By.TAG_NAME, "textarea")
                    for ta in all_textareas:
                        if ta.is_displayed():
                            rect = ta.rect
                            if rect['width'] > 50 and rect['height'] > 30:
                                placeholder = ta.get_attribute('placeholder') or 'Textarea'
                                add_unique_element({
                                    'label': placeholder,
                                    'x': rect['x'],
                                    'y': rect['y'],
                                    'width': rect['width'],
                                    'height': rect['height']
                                })
                except Exception as e:
                    print(f"Error scanning textareas: {e}")
                
                # Find clickable elements with specific text patterns (dashboard elements)
                try:
                    # Important text to look for (case insensitive) - ENHANCED LIST
                    important_texts = [
                        ("start", "quote"),
                        ("search", "policy"),
                        ("look", "prior", "quote"),
                        ("private", "passenger", "auto"),
                        ("motorcycle", "atv"),
                        ("commercial", "auto"),
                        ("commercial", "truck"),
                        ("get", "quote"),
                        ("continue", "quote"),
                        ("view", "policy"),
                        ("make", "payment"),
                        ("starter", "quote"),
                        ("manage", "policy"),
                        ("claim", "center"),
                        ("pay", "bill"),
                        ("get", "id", "card"),
                        # New patterns for the missing buttons
                        ("private", "passenger"),
                        ("motorcycle",),
                        ("atv",),
                        ("off-road",),
                        ("off", "road"),
                        ("commercial",),
                        ("trucking",),
                        ("auto",)
                    ]
                    
                    # Search for specific clickable elements containing these text patterns
                    # Only look for buttons, links, and specific clickable elements
                    for text_parts in important_texts:
                        # Build XPath that looks for all parts of the text
                        xpath_conditions = []
                        for part in text_parts:
                            xpath_conditions.append(f"contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{part}')")
                        
                        # IMPORTANT: Only search in clickable elements, not ALL elements
                        xpath = f"//button[{' and '.join(xpath_conditions)}] | //a[{' and '.join(xpath_conditions)}] | //span[@role='button' and {' and '.join(xpath_conditions)}] | //div[@role='button' and {' and '.join(xpath_conditions)}] | //div[@tabindex and {' and '.join(xpath_conditions)}]"
                        try:
                            pattern_elements = driver.find_elements(By.XPATH, xpath)
                            for elem in pattern_elements:
                                if elem.is_displayed():
                                    rect = elem.rect
                                    # More strict size filtering
                                    if rect['width'] > 25 and rect['height'] > 12 and rect['width'] < 600 and rect['height'] < 150:
                                        elem_text = elem.text.strip()[:40]
                                        if elem_text:
                                            add_unique_element({
                                                'label': f"{elem_text}",
                                                'x': rect['x'],
                                                'y': rect['y'],
                                                'width': rect['width'],
                                                'height': rect['height']
                                            })
                        except:
                            pass
                except Exception as e:
                    print(f"Error scanning clickable text patterns: {e}")
                
                # Also search for single important keywords (more flexible)
                try:
                    single_keywords = [
                        "start", "quote", "policy", "search", "private", "passenger",
                        "motorcycle", "commercial", "auto", "truck", "manage", "claim",
                        "atv", "off-road", "trucking"  # Added missing keywords
                    ]
                    
                    for keyword in single_keywords:
                        # ENHANCED: Also search in parent divs and spans
                        xpath = f"//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')] | //a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')] | //div[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')] | //span[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]"
                        try:
                            keyword_elements = driver.find_elements(By.XPATH, xpath)
                            for elem in keyword_elements:
                                if elem.is_displayed():
                                    rect = elem.rect
                                    if rect['width'] > 25 and rect['height'] > 12 and rect['width'] < 600 and rect['height'] < 150:
                                        elem_text = elem.text.strip()[:40]
                                        if elem_text and len(elem_text) > 3:
                                            add_unique_element({
                                                'label': f"{elem_text}",
                                                'x': rect['x'],
                                                'y': rect['y'],
                                                'width': rect['width'],
                                                'height': rect['height']
                                            })
                        except:
                            pass
                except Exception as e:
                    print(f"Error scanning single keywords: {e}")
                
                # Find elements with role attributes only (skip onclick to reduce duplicates)
                try:
                    # More aggressive search for role elements and clickable divs/spans
                    role_elements = driver.find_elements(By.XPATH, "//span[@role='button' or @role='link'] | //div[@role='button' or @role='link'] | //*[@onclick] | //*[@ng-click] | //*[contains(@class, 'button')] | //*[contains(@class, 'btn')] | //*[@tabindex]")
                    for elem in role_elements:
                        if elem.is_displayed():
                            rect = elem.rect
                            # More lenient size limits
                            if rect['width'] > 15 and rect['height'] > 8 and rect['width'] < 600 and rect['height'] < 150:
                                elem_text = elem.text.strip()[:30] or elem.get_attribute('aria-label') or ''
                                if elem_text and len(elem_text) > 2:
                                    add_unique_element({
                                        'label': f"{elem_text}",
                                        'x': rect['x'],
                                        'y': rect['y'],
                                        'width': rect['width'],
                                        'height': rect['height']
                                    })
                except Exception as e:
                    print(f"Error scanning role elements: {e}")
                
                # SPECIFIC SEARCH for "products to quote" section and its buttons
                try:
                    # First, find the "products to quote" section
                    products_section_xpath = "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'products to quote')]"
                    products_sections = driver.find_elements(By.XPATH, products_section_xpath)
                    
                    for section in products_sections:
                        if section.is_displayed():
                            print(f"[DEBUG] Found 'products to quote' section: {section.text}")
                            # Find all elements below this section
                            parent = section
                            for _ in range(5):  # Go up to 5 levels to find container
                                parent = parent.find_element(By.XPATH, "..")
                                # Find all clickable children
                                children = parent.find_elements(By.XPATH, ".//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'private passenger') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'motorcycle') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'atv') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'off-road') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'commercial') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'trucking')]")
                                for child in children:
                                    if child.is_displayed():
                                        rect = child.rect
                                        if rect['width'] > 20 and rect['height'] > 10:
                                            elem_text = child.text.strip()
                                            if elem_text:
                                                print(f"[DEBUG] Found product button: {elem_text}")
                                                add_unique_element({
                                                    'label': elem_text[:40],
                                                    'x': rect['x'],
                                                    'y': rect['y'],
                                                    'width': rect['width'],
                                                    'height': rect['height']
                                                })
                except Exception as e:
                    print(f"[DEBUG] Error in products to quote section search: {e}")
                
                # EXTREMELY AGGRESSIVE SEARCH for all clickable text elements
                try:
                    # Search for ALL elements containing these specific product texts
                    product_keywords = ['private passenger', 'motorcycle', 'atv', 'off-road', 'off road', 'commercial', 'trucking']
                    
                    for keyword in product_keywords:
                        # Search in ALL element types, not just buttons
                        xpath = f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]"
                        elements = driver.find_elements(By.XPATH, xpath)
                        
                        for elem in elements:
                            if elem.is_displayed():
                                rect = elem.rect
                                if rect['width'] > 20 and rect['height'] > 10 and rect['width'] < 800 and rect['height'] < 200:
                                    elem_text = elem.text.strip()
                                    if elem_text:
                                        # Check if element or parent is clickable
                                        is_clickable = False
                                        current = elem
                                        
                                        for _ in range(3):  # Check element and up to 2 parents
                                            try:
                                                # Check various clickability indicators
                                                onclick = current.get_attribute('onclick')
                                                role = current.get_attribute('role')
                                                tabindex = current.get_attribute('tabindex')
                                                cursor = driver.execute_script("return window.getComputedStyle(arguments[0]).cursor;", current)
                                                tag = current.tag_name.lower()
                                                
                                                if onclick or role in ['button', 'link'] or tabindex or cursor == 'pointer' or tag in ['a', 'button']:
                                                    is_clickable = True
                                                    break
                                                
                                                # Go to parent
                                                current = current.find_element(By.XPATH, "..")
                                            except:
                                                break
                                        
                                        if is_clickable:
                                            print(f"[DEBUG] Found clickable product element: {elem_text}")
                                            add_unique_element({
                                                'label': elem_text[:40],
                                                'x': rect['x'],
                                                'y': rect['y'],
                                                'width': rect['width'],
                                                'height': rect['height']
                                            })
                                        elif 'auto' in elem_text.lower() or 'motorcycle' in elem_text.lower() or 'commercial' in elem_text.lower():
                                            # Add these even if not explicitly clickable since they're important
                                            print(f"[DEBUG] Adding important product text: {elem_text}")
                                            add_unique_element({
                                                'label': elem_text[:40],
                                                'x': rect['x'],
                                                'y': rect['y'],
                                                'width': rect['width'],
                                                'height': rect['height']
                                            })
                    
                    # Additional specific search for the exact phrases
                    exact_phrases = [
                        "Private Passenger Auto",
                        "Motorcycle/ATV/Off-road",
                        "Commercial Auto/Trucking"
                    ]
                    
                    for phrase in exact_phrases:
                        # Case-insensitive but exact phrase search
                        xpath = f"//*[normalize-space(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')) = '{phrase.lower()}']"
                        elements = driver.find_elements(By.XPATH, xpath)
                        
                        for elem in elements:
                            if elem.is_displayed():
                                rect = elem.rect
                                if rect['width'] > 20 and rect['height'] > 10:
                                    print(f"[DEBUG] Found exact product phrase: {phrase}")
                                    add_unique_element({
                                        'label': phrase,
                                        'x': rect['x'],
                                        'y': rect['y'],
                                        'width': rect['width'],
                                        'height': rect['height']
                                    })
                except Exception as e:
                    print(f"[DEBUG] Error in aggressive product search: {e}")
                
                # Continue with the extremely aggressive general search
                try:
                    # First, try to find ALL elements that might be clickable
                    all_elements_xpath = "//*[text() and not(self::script) and not(self::style)]"
                    all_elements = driver.find_elements(By.XPATH, all_elements_xpath)[:200]  # Increased limit00 for performance
                    
                    # Keywords to search for
                    target_keywords = [
                        "private passenger", "motorcycle", "atv", "off-road", "off road",
                        "commercial auto", "commercial trucking", "trucking"
                    ]
                    
                    for elem in all_elements:
                        try:
                            if elem.is_displayed():
                                elem_text = elem.text.strip().lower()
                                # Check if element contains any of our target keywords
                                for keyword in target_keywords:
                                    if keyword in elem_text and len(elem_text) < 100:  # Avoid huge text blocks
                                        rect = elem.rect
                                        if rect['width'] > 15 and rect['height'] > 8 and rect['width'] < 800:
                                            # Check if this element or its parent is clickable
                                            clickable = False
                                            current = elem
                                            
                                            # Check element and up to 3 parent levels for clickability
                                            for _ in range(4):
                                                tag_name = current.tag_name.lower()
                                                if tag_name in ['a', 'button', 'input']:
                                                    clickable = True
                                                    break
                                                
                                                # Check for clickable attributes
                                                onclick = current.get_attribute('onclick')
                                                role = current.get_attribute('role')
                                                tabindex = current.get_attribute('tabindex')
                                                cursor = current.value_of_css_property('cursor')
                                                
                                                if onclick or role in ['button', 'link'] or tabindex or cursor == 'pointer':
                                                    clickable = True
                                                    break
                                                
                                                # Move to parent
                                                try:
                                                    current = current.find_element(By.XPATH, '..')
                                                except:
                                                    break
                                            
                                            if clickable:
                                                add_unique_element({
                                                    'label': elem.text.strip()[:50],
                                                    'x': rect['x'],
                                                    'y': rect['y'],
                                                    'width': rect['width'],
                                                    'height': rect['height']
                                                })
                                                break  # Found this keyword, move to next element
                        except:
                            continue
                            
                except Exception as e:
                    print(f"Error in aggressive element search: {e}")
                
                # Skip cursor:pointer scanning as it creates too many duplicates
                # The above methods should catch all important clickable elements
                
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
                
                # Maximum FPS - minimal delay for ~50+ FPS
                time.sleep(0.01)
                
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
    import ssl
    import os
    
    # Check for SSL certificates
    cert_path = '/home/corp06/software_projects/ClaudeVoiceBot/EXPERIMENT_MULTIVOICE_V1/cert.pem'
    key_path = '/home/corp06/software_projects/ClaudeVoiceBot/EXPERIMENT_MULTIVOICE_V1/key.pem'
    
    print("\n=== Geico Auto Quota Scanner (HTTPS) ===")
    
    # Enable Flask logging and error handling
    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Add CORS headers for debugging
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    if os.path.exists(cert_path) and os.path.exists(key_path):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        print("Open your browser and go to: https://localhost:8405")
        print("Or from another device: https://192.168.40.232:8405")
        print("Running with HTTPS on port 8405")
        app.run(host='0.0.0.0', port=8405, ssl_context=context, debug=True, use_reloader=False)
    else:
        print("SSL certificates not found, running HTTP on port 5558")
        print("Open your browser and go to: http://localhost:5558")
        print("Or from another device: http://192.168.40.232:5558")
        app.run(host='0.0.0.0', port=5558, debug=True, use_reloader=False)