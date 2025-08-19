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
            <button class="commercial-auto-button" onclick="forceCommercialAuto()" style="display: none; background-color: #ff6b00; margin-left: 10px;">Force Commercial Auto Click</button>
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
        
        function forceCommercialAuto() {
            console.log('Force Commercial Auto clicked');
            const button = document.querySelector('.commercial-auto-button');
            button.disabled = true;
            button.textContent = 'Clicking...';
            
            fetch('/force-commercial-auto', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Commercial Auto result:', data);
                if (data.status === 'success') {
                    button.textContent = 'Clicked!';
                    button.style.backgroundColor = '#00ff00';
                    setTimeout(() => {
                        button.textContent = 'Force Commercial Auto Click';
                        button.style.backgroundColor = '#ff6b00';
                        button.disabled = false;
                    }, 3000);
                } else {
                    alert('Failed to click Commercial Auto tab: ' + data.message);
                    button.textContent = 'Force Commercial Auto Click';
                    button.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error clicking Commercial Auto:', error);
                alert('Error: ' + error);
                button.textContent = 'Force Commercial Auto Click';
                button.disabled = false;
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
            
            // Show Commercial Auto button
            document.querySelector('.commercial-auto-button').style.display = 'inline-block';
            
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

@app.route('/force-commercial-auto', methods=['POST'])
def force_commercial_auto():
    """Force click on Commercial Auto/Trucking tab"""
    global driver, current_status
    
    if not driver:
        return jsonify({'status': 'error', 'message': 'Scanner not running'})
    
    try:
        print("\n[MANUAL FORCE] User requested Commercial Auto click!")
        
        # Execute the click
        result = driver.execute_script("""
            console.log('[MANUAL] Searching for Commercial Auto tab...');
            var found = false;
            var allElements = document.querySelectorAll('*');
            
            // First, highlight ALL potential matches
            var matches = [];
            for (var i = 0; i < allElements.length; i++) {
                var elem = allElements[i];
                if (elem.textContent && 
                    (elem.textContent.includes('Commercial Auto') || 
                     elem.textContent.includes('Trucking'))) {
                    elem.style.outline = '2px dashed orange';
                    matches.push(elem);
                }
            }
            console.log('Found ' + matches.length + ' potential matches');
            
            // Now find the exact one
            for (var i = 0; i < allElements.length; i++) {
                var elem = allElements[i];
                if (elem.textContent && 
                    (elem.textContent.includes('Commercial Auto/Trucking') || 
                     elem.textContent.includes('Commercial Auto / Trucking') ||
                     elem.textContent === 'Commercial Auto')) {
                    
                    if (elem.offsetWidth * elem.offsetHeight > 100000) continue;
                    
                    var clickable = elem;
                    if (elem.tagName !== 'A' && elem.tagName !== 'BUTTON') {
                        var parent = elem.parentElement;
                        while (parent && parent.tagName !== 'BODY') {
                            if (parent.tagName === 'A' || parent.tagName === 'BUTTON' ||
                                parent.getAttribute('role') === 'tab' ||
                                parent.getAttribute('role') === 'button' ||
                                parent.onclick ||
                                parent.style.cursor === 'pointer') {
                                clickable = parent;
                                break;
                            }
                            parent = parent.parentElement;
                        }
                    }
                    
                    // BRIGHT GREEN HIGHLIGHT
                    clickable.style.border = '5px solid #00FF00';
                    clickable.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
                    clickable.style.boxShadow = '0 0 30px #00FF00';
                    clickable.scrollIntoView({block: 'center'});
                    
                    // Multiple click methods
                    console.log('Clicking element:', clickable);
                    clickable.click();
                    clickable.focus();
                    clickable.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                    
                    // Try Enter key
                    var enterEvent = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        keyCode: 13,
                        bubbles: true
                    });
                    clickable.dispatchEvent(enterEvent);
                    
                    window.commercialAutoClicked = true;
                    found = true;
                    
                    return {
                        found: true,
                        element: {
                            tag: clickable.tagName,
                            text: clickable.textContent.trim(),
                            href: clickable.href || null
                        }
                    };
                }
            }
            
            return {found: false, matchCount: matches.length};
        """)
        
        if result['found']:
            current_status = "Commercial Auto tab clicked!"
            return jsonify({
                'status': 'success',
                'message': 'Commercial Auto tab clicked!',
                'element': result['element']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Commercial Auto tab not found. Found {result.get("matchCount", 0)} partial matches.'
            })
            
    except Exception as e:
        print(f"[ERROR] Force Commercial Auto failed: {e}")
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
        
        # Initialize check timers
        last_commercial_check_time = 0
        last_fps_calculation_time = time.time()
        commercial_check_counter = 0  # Separate counter for Commercial Auto checks
        
        while is_scanning:
            try:
                # CRITICAL DEBUG: Verify loop is running
                if commercial_check_counter == 0:
                    print("\n[SCANNER STARTED] Main detection loop is running!", flush=True)
                
                # DEBUG: Print loop status MORE FREQUENTLY
                if commercial_check_counter % 5 == 0:
                    print(f"\n[MAIN LOOP ACTIVE] Counter: {commercial_check_counter}, Status: {current_status}")
                    print(f"[MAIN LOOP ACTIVE] URL: {driver.current_url}")
                    
                    # If stuck on login status for too long, force reset
                    if "Login submitted" in current_status and commercial_check_counter > 50:
                        print("[MAIN LOOP] Forcing status reset due to stuck login!")
                        current_status = "Searching for Commercial Auto..."
                
                # EMERGENCY FORCE CHECK: If we have a scheduled force check time, do it NOW
                if hasattr(driver, 'force_commercial_check_time') and time.time() >= driver.force_commercial_check_time:
                    print("\n[EMERGENCY] FORCING COMMERCIAL AUTO CHECK NOW!")
                    driver.force_commercial_check_time = float('inf')  # Prevent repeated checks
                    
                    # Reset status to allow normal operation
                    current_status = "Forcing Commercial Auto detection..."
                    
                    # Force the Commercial Auto check RIGHT NOW
                    try:
                        click_result = driver.execute_script("""
                            console.log('[FORCE] Emergency Commercial Auto search started!');
                            var found = false;
                            var allElements = document.querySelectorAll('*');
                            
                            for (var i = 0; i < allElements.length; i++) {
                                var elem = allElements[i];
                                if (elem.textContent && 
                                    (elem.textContent.includes('Commercial Auto/Trucking') || 
                                     elem.textContent.includes('Commercial Auto / Trucking') ||
                                     elem.textContent.includes('Commercial Auto'))) {
                                    
                                    if (elem.offsetWidth * elem.offsetHeight > 100000) continue;
                                    
                                    var clickable = elem;
                                    if (elem.tagName !== 'A' && elem.tagName !== 'BUTTON') {
                                        var parent = elem.parentElement;
                                        while (parent && parent.tagName !== 'BODY') {
                                            if (parent.tagName === 'A' || parent.tagName === 'BUTTON' ||
                                                parent.getAttribute('role') === 'tab' ||
                                                parent.getAttribute('role') === 'button') {
                                                clickable = parent;
                                                break;
                                            }
                                            parent = parent.parentElement;
                                        }
                                    }
                                    
                                    // BRIGHT GREEN HIGHLIGHT
                                    clickable.style.border = '5px solid #00FF00';
                                    clickable.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
                                    clickable.style.boxShadow = '0 0 30px #00FF00';
                                    
                                    // Multiple click attempts
                                    clickable.click();
                                    clickable.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                                    
                                    console.log('[FORCE] Clicked Commercial Auto:', clickable);
                                    window.commercialAutoClicked = true;
                                    found = true;
                                    break;
                                }
                            }
                            
                            return found;
                        """)
                        
                        if click_result:
                            print("[EMERGENCY] COMMERCIAL AUTO TAB CLICKED!")
                            current_status = "Commercial Auto tab clicked!"
                        else:
                            print("[EMERGENCY] Commercial Auto tab not found")
                            current_status = "On dashboard - Commercial Auto not found"
                    except Exception as e:
                        print(f"[EMERGENCY] Error during forced click: {e}")
                        current_status = "Dashboard ready"
                
                # IMMEDIATE COMMERCIAL AUTO CHECK - Run this EVERY loop iteration
                # Check if we need to click Commercial Auto tab
                # Run immediately on first iteration, then every 5 iterations
                if commercial_check_counter % 5 == 0:  # Check every 5 iterations (about 0.5 seconds)
                    try:
                        # Check if already clicked
                        commercial_clicked = False  # PATCHED: Always try to click Commercial Auto
                        
                        if not commercial_clicked:
                            print(f"\n[COMMERCIAL AUTO CHECK] Frame {frame_count} - Checking for Commercial Auto tab...")
                            print(f"[COMMERCIAL AUTO CHECK] Current URL: {driver.current_url}")
                            print(f"[COMMERCIAL AUTO CHECK] Current status: {current_status}")
                            
                            # Direct JavaScript search and click
                            click_result = driver.execute_script("""
                                var found = false;
                                var clickCount = 0;
                                
                                // Search for Commercial Auto elements
                                var allElements = document.querySelectorAll('*');
                                for (var i = 0; i < allElements.length; i++) {
                                    var elem = allElements[i];
                                    if (elem.textContent && 
                                        (elem.textContent.includes('Commercial Auto/Trucking') || 
                                         elem.textContent.includes('Commercial Auto / Trucking') ||
                                         elem.textContent.includes('Commercial Auto'))) {
                                        
                                        // Skip large containers
                                        if (elem.offsetWidth * elem.offsetHeight > 100000) continue;
                                        
                                        // Find clickable element
                                        var clickable = elem;
                                        if (elem.tagName !== 'A' && elem.tagName !== 'BUTTON') {
                                            var parent = elem.parentElement;
                                            while (parent && parent.tagName !== 'BODY') {
                                                if (parent.tagName === 'A' || parent.tagName === 'BUTTON' ||
                                                    parent.getAttribute('role') === 'tab' ||
                                                    parent.getAttribute('role') === 'button' ||
                                                    parent.onclick) {
                                                    clickable = parent;
                                                    break;
                                                }
                                                parent = parent.parentElement;
                                            }
                                        }
                                        
                                        // Highlight in GREEN
                                        clickable.style.border = '5px solid #00FF00';
                                        clickable.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
                                        clickable.style.boxShadow = '0 0 20px #00FF00';
                                        
                                        // Click it
                                        try {
                                            clickable.click();
                                            clickCount++;
                                            console.log('Clicked Commercial Auto element:', clickable);
                                        } catch(e) {
                                            console.log('Click failed:', e);
                                        }
                                        
                                        // Also try JavaScript click
                                        var event = new MouseEvent('click', {
                                            view: window,
                                            bubbles: true,
                                            cancelable: true
                                        });
                                        clickable.dispatchEvent(event);
                                        
                                        found = true;
                                        window.commercialAutoClicked = true;
                                        break;
                                    }
                                }
                                
                                return {found: found, clickCount: clickCount};
                            """)
                            
                            if click_result['found']:
                                print(f"[COMMERCIAL AUTO CLICKED!] Found and clicked Commercial Auto tab!")
                                current_status = "Commercial Auto tab clicked!"
                            else:
                                print(f"[COMMERCIAL AUTO CHECK] Not found yet")
                    except Exception as e:
                        print(f"[COMMERCIAL AUTO CHECK] Error: {e}")
                
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
                
                # BYPASS: If we've been running for more than 30 seconds, stop checking for login
                if not hasattr(driver, 'scanner_start_time'):
                    driver.scanner_start_time = time.time()
                
                if time.time() - driver.scanner_start_time > 30:
                    if frame_count % 100 == 0:  # Only print every 10 seconds
                        print("[BYPASS] Skipping login detection after 30 seconds - focusing on Commercial Auto")
                    has_username_field = False
                    has_password_field = False
                
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
                    print("[DEBUG] Waiting 2 seconds before auto-fill...")
                    
                    # Wait 2 seconds with countdown
                    for i in range(2, 0, -1):
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
                                        
                                        # Start Commercial Auto monitor immediately after login
                                        try:
                                            from commercial_auto_immediate_fix import start_commercial_auto_monitor
                                            start_commercial_auto_monitor(driver)
                                            print("[INFO] Commercial Auto monitor started - will detect and click tab automatically")
                                        except Exception as e:
                                            print(f"[WARNING] Could not start Commercial Auto monitor: {e}")
                                        
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
                                
                                # Start Commercial Auto monitor after form submission too
                                try:
                                    from commercial_auto_immediate_fix import start_commercial_auto_monitor
                                    start_commercial_auto_monitor(driver)
                                    print("[INFO] Commercial Auto monitor started after form submission")
                                except Exception as e:
                                    print(f"[WARNING] Could not start Commercial Auto monitor: {e}")
                            except Exception as e:
                                print(f"[DEBUG] Form submission error: {e}")
                        
                        print("[DEBUG] Login automation completed")
                        current_status = "Login submitted - waiting for page load..."
                        # Mark login time for timeout
                        if not hasattr(driver, 'login_submit_time'):
                            driver.login_submit_time = time.time()
                        
                        # FORCE: Set a flag to trigger Commercial Auto check in 3 seconds
                        driver.force_commercial_check_time = time.time() + 3
                        print("[FORCE] Commercial Auto check scheduled for 3 seconds after login")
                        
                    except Exception as e:
                        print(f"[DEBUG] Error during auto-login: {e}")
                        current_status = f"Login error: {str(e)}"
                        import traceback
                        traceback.print_exc()
                
                # IMMEDIATE FIX: If we detect login was attempted but we're still seeing login fields, reset
                if has_username_field and has_password_field and driver.execute_script("return window.geicoLoginAttempted || false"):
                    # Check if URL changed (indicates successful login)
                    current_url = driver.current_url
                    if "login" not in current_url.lower():
                        print("[FIX] Login successful but still detecting login fields - clearing status")
                        has_username_field = False
                        has_password_field = False
                        current_status = "On dashboard - searching for Commercial Auto"
                        # Reset login flag
                        driver.execute_script("window.geicoLoginAttempted = false;")
                
                # FORCE FIX: Check if we're stuck on "Login submitted - waiting for page load..."
                if "Login submitted" in current_status and "waiting" in current_status:
                    if hasattr(driver, 'login_submit_time'):
                        # After 5 seconds, force check for Commercial Auto
                        if time.time() - driver.login_submit_time > 5:
                            print("\n[TIMEOUT] Login wait timeout after 5 seconds - forcing Commercial Auto check!")
                            current_status = "Forcing Commercial Auto detection..."
                            
                            # Force the commercial auto check
                            try:
                                from commercial_auto_force_click import ensure_commercial_auto_clicked
                                print("\n[FORCE] Running Commercial Auto detection regardless of page state!")
                                print(f"[FORCE] Current URL: {driver.current_url}")
                                success = ensure_commercial_auto_clicked(driver)
                                if success:
                                    current_status = "Commercial Auto tab clicked!"
                                    driver.login_submit_time = time.time() + 1000  # Prevent repeated attempts
                                else:
                                    current_status = "Dashboard loaded - Commercial Auto not found"
                                    driver.login_submit_time = time.time() + 1000  # Prevent repeated attempts
                            except Exception as e:
                                print(f"[ERROR] Force detection failed: {e}")
                                current_status = "On dashboard"
                                driver.login_submit_time = time.time() + 1000  # Prevent repeated attempts
                
                # ALWAYS CHECK FOR COMMERCIAL AUTO/TRUCKING - NO CONDITIONS
                # Force check every 3 seconds
                if time.time() - last_commercial_check_time > 3:
                    # Update the commercial check timer
                    last_commercial_check_time = time.time()
                    # We're not on login page anymore, check if we need to click Commercial Auto/Trucking
                    print(f"[DEBUG] Commercial Auto check - Login fields: username={has_username_field}, password={has_password_field}")
                    try:
                        # Import the AGGRESSIVE Commercial Auto detection
                        try:
                            from commercial_auto_force_click import ensure_commercial_auto_clicked
                            force_method_available = True
                        except ImportError:
                            force_method_available = False
                            try:
                                from commercial_auto_click_fix import click_commercial_auto_tab
                                enhanced_method_available = True
                            except ImportError:
                                enhanced_method_available = False
                                print("[WARNING] Enhanced Commercial Auto detection not available, using original method")
                        
                        # Check if we've already clicked commercial auto (avoid repeated clicks)
                        commercial_clicked = False  # PATCHED: Always try to click Commercial Auto
                        print(f"[DEBUG] Commercial Auto already clicked: {commercial_clicked}")
                        
                        success = False
                        
                        # Try FORCE method first (most aggressive)
                        if not commercial_clicked and force_method_available:
                            print("\n[ALERT] Using AGGRESSIVE force click method for Commercial Auto/Trucking tab!")
                            success = ensure_commercial_auto_clicked(driver)
                            
                            if success:
                                print("[SUCCESS] Commercial Auto/Trucking tab FORCE CLICKED!")
                                current_status = "Navigated to Commercial Auto/Trucking"
                                continue  # Skip everything else
                            else:
                                print("[WARNING] Force method failed, trying enhanced method...")
                        
                        # Try enhanced method if force method not available or failed
                        if not commercial_clicked and not success and enhanced_method_available:
                            # Use enhanced clicking method
                            print("[DEBUG] Using enhanced Commercial Auto/Trucking tab detection")
                            success = click_commercial_auto_tab(driver, max_attempts=5, debug=True)
                            
                            if success:
                                print("[SUCCESS] Commercial Auto/Trucking tab clicked successfully")
                                current_status = "Navigated to Commercial Auto/Trucking"
                                continue  # Skip the old implementation
                            else:
                                print("[WARNING] Enhanced method failed, falling back to original implementation")
                        
                        if not commercial_clicked and not success:
                            print(f"[DEBUG] Checking for Commercial Auto/Trucking tab on URL: {driver.current_url}")
                            
                            # First, let's try a simple Tab navigation approach
                            print("[DEBUG] Trying Tab navigation to find Commercial Auto...")
                            try:
                                # Send Tab keys to navigate through page elements
                                body = driver.find_element(By.TAG_NAME, "body")
                                for i in range(20):  # Try up to 20 tabs
                                    body.send_keys(Keys.TAB)
                                    time.sleep(0.2)
                                    
                                    # Check if we've focused on Commercial Auto element
                                    focused_text = driver.execute_script("""
                                        var focused = document.activeElement;
                                        if (focused) {
                                            return focused.textContent || focused.value || '';
                                        }
                                        return '';
                                    """)
                                    
                                    if "Commercial Auto" in focused_text:
                                        print(f"[DEBUG] Found Commercial Auto via Tab navigation at position {i}")
                                        body.send_keys(Keys.ENTER)
                                        print("[DEBUG] Pressed Enter on focused element")
                                        time.sleep(3)
                                        break
                            except Exception as e:
                                print(f"[DEBUG] Tab navigation failed: {e}")
                            
                            # Wait longer for page to fully load after login
                            print("[DEBUG] Waiting for page to fully load...")
                            time.sleep(5)
                            
                            # Wait for any dynamic content and JavaScript to finish
                            try:
                                driver.execute_script("""
                                    return new Promise((resolve) => {
                                        if (document.readyState === 'complete') {
                                            // Wait a bit more for any async JavaScript
                                            setTimeout(() => resolve(true), 2000);
                                        } else {
                                            window.addEventListener('load', () => {
                                                setTimeout(() => resolve(true), 2000);
                                            });
                                        }
                                    });
                                """)
                                print("[DEBUG] Page fully loaded with JavaScript")
                            except:
                                print("[DEBUG] Page load wait completed")
                            
                            # First, let's diagnose what's on the page
                            print("[DEBUG] Running page diagnostics...")
                            page_info = driver.execute_script("""
                                var results = {
                                    allLinks: [],
                                    allButtons: [],
                                    commercialElements: [],
                                    clickableElements: []
                                };
                                
                                // Find all links
                                var links = document.querySelectorAll('a');
                                for (var i = 0; i < links.length; i++) {
                                    if (links[i].textContent.trim()) {
                                        results.allLinks.push({
                                            text: links[i].textContent.trim().substring(0, 50),
                                            href: links[i].href || 'no href',
                                            onclick: links[i].onclick ? 'has onclick' : 'no onclick'
                                        });
                                    }
                                }
                                
                                // Find all buttons
                                var buttons = document.querySelectorAll('button');
                                for (var i = 0; i < buttons.length; i++) {
                                    if (buttons[i].textContent.trim()) {
                                        results.allButtons.push({
                                            text: buttons[i].textContent.trim().substring(0, 50),
                                            onclick: buttons[i].onclick ? 'has onclick' : 'no onclick'
                                        });
                                    }
                                }
                                
                                // Find elements with Commercial Auto text
                                var allElems = document.querySelectorAll('*');
                                for (var i = 0; i < allElems.length; i++) {
                                    if (allElems[i].textContent && allElems[i].textContent.includes('Commercial Auto')) {
                                        results.commercialElements.push({
                                            tag: allElems[i].tagName,
                                            text: allElems[i].textContent.trim().substring(0, 100),
                                            class: allElems[i].className,
                                            id: allElems[i].id,
                                            parent: allElems[i].parentElement ? allElems[i].parentElement.tagName : 'no parent'
                                        });
                                    }
                                }
                                
                                // Find clickable divs and spans
                                var divs = document.querySelectorAll('div[onclick], div[role="button"], div[role="tab"], span[onclick]');
                                for (var i = 0; i < divs.length; i++) {
                                    if (divs[i].textContent.trim()) {
                                        results.clickableElements.push({
                                            tag: divs[i].tagName,
                                            text: divs[i].textContent.trim().substring(0, 50),
                                            role: divs[i].getAttribute('role') || 'none',
                                            onclick: divs[i].onclick ? 'has onclick' : 'no onclick'
                                        });
                                    }
                                }
                                
                                return results;
                            """)
                            
                            print("[DEBUG] Page diagnostic results:")
                            print(f"[DEBUG] Links found: {len(page_info['allLinks'])}")
                            for link in page_info['allLinks'][:5]:  # Show first 5
                                print(f"[DEBUG]   Link: {link}")
                            
                            print(f"[DEBUG] Buttons found: {len(page_info['allButtons'])}")
                            for button in page_info['allButtons'][:5]:  # Show first 5
                                print(f"[DEBUG]   Button: {button}")
                            
                            print(f"[DEBUG] Commercial Auto elements found: {len(page_info['commercialElements'])}")
                            for elem in page_info['commercialElements']:
                                print(f"[DEBUG]   Commercial elem: {elem}")
                            
                            print(f"[DEBUG] Clickable elements found: {len(page_info['clickableElements'])}")
                            for elem in page_info['clickableElements'][:5]:  # Show first 5
                                print(f"[DEBUG]   Clickable: {elem}")
                            
                            # First try to find navigation tabs/links specifically
                            print("[DEBUG] Looking for Commercial Auto in navigation elements...")
                            nav_click = driver.execute_script("""
                                // Look for navigation elements specifically
                                var navElements = document.querySelectorAll('nav a, nav button, .nav a, .nav button, .tabs a, .tabs button, .tab-list a, .tab-list button, ul.tabs li, ul.nav li');
                                
                                for (var i = 0; i < navElements.length; i++) {
                                    if (navElements[i].textContent.includes('Commercial Auto')) {
                                        console.log('Found Commercial Auto in navigation:', navElements[i]);
                                        navElements[i].style.border = '5px solid purple';
                                        navElements[i].click();
                                        return 'clicked nav';
                                    }
                                }
                                
                                // Also check for elements with specific navigation classes
                                var possibleNavs = document.querySelectorAll('[class*="nav"], [class*="tab"], [role="navigation"] a');
                                for (var i = 0; i < possibleNavs.length; i++) {
                                    if (possibleNavs[i].textContent.includes('Commercial Auto')) {
                                        console.log('Found Commercial Auto in possible nav:', possibleNavs[i]);
                                        possibleNavs[i].style.border = '5px solid blue';
                                        possibleNavs[i].click();
                                        return 'clicked possible nav';
                                    }
                                }
                                
                                return 'no nav found';
                            """)
                            
                            print(f"[DEBUG] Navigation click result: {nav_click}")
                            
                            if nav_click.startswith('clicked'):
                                time.sleep(3)
                                print("[DEBUG] Clicked navigation element")
                            else:
                                # Brute force approach - try clicking ALL Commercial Auto elements
                                print("[DEBUG] Trying brute force approach - clicking all Commercial Auto elements...")
                                brute_force_result = driver.execute_script("""
                                    var clicked = [];
                                    var allElements = document.querySelectorAll('*');
                                    
                                    for (var i = 0; i < allElements.length; i++) {
                                        var elem = allElements[i];
                                        if (elem.textContent && elem.textContent.includes('Commercial Auto') && 
                                            elem.textContent.length < 100) {  // Avoid large containers
                                            
                                            // Skip if already processed
                                            if (elem.dataset.processedCommercial) continue;
                                            elem.dataset.processedCommercial = 'true';
                                            
                                            // Get element info
                                            var info = {
                                                tag: elem.tagName,
                                                text: elem.textContent.trim().substring(0, 50),
                                                clickable: elem.onclick || elem.href || elem.tagName === 'A' || elem.tagName === 'BUTTON'
                                            };
                                            
                                            // Try to click it
                                            try {
                                                elem.click();
                                                info.clicked = true;
                                                clicked.push(info);
                                                
                                                // Also try clicking parent
                                                if (elem.parentElement && !elem.parentElement.dataset.processedCommercial) {
                                                    elem.parentElement.click();
                                                    elem.parentElement.dataset.processedCommercial = 'true';
                                                }
                                                
                                                // Wait a bit between clicks
                                                return clicked;  // Return after first successful click
                                                
                                            } catch(e) {
                                                info.error = e.toString();
                                                clicked.push(info);
                                            }
                                        }
                                    }
                                    
                                    return clicked;
                                """)
                                
                                print(f"[DEBUG] Brute force clicks: {brute_force_result}")
                                
                                if brute_force_result and len(brute_force_result) > 0:
                                    time.sleep(3)
                                    print("[DEBUG] Performed brute force clicks")
                            
                            # Try the most specific approach - click by known IDs
                            print("[DEBUG] Trying to click by specific element IDs...")
                            specific_click = driver.execute_script("""
                                // Try known IDs from logs
                                var clicked = false;
                                
                                // Try label for commercial auto
                                var label = document.getElementById('labelForCommercialAuto');
                                if (label) {
                                    console.log('Found labelForCommercialAuto');
                                    label.style.border = '5px solid orange';
                                    label.click();
                                    
                                    // Also try to click associated checkbox/radio
                                    var forAttr = label.getAttribute('for');
                                    if (forAttr) {
                                        var input = document.getElementById(forAttr);
                                        if (input) {
                                            input.click();
                                            clicked = true;
                                        }
                                    }
                                }
                                
                                // Try to find and click any radio/checkbox for commercial auto
                                var inputs = document.querySelectorAll('input[type="radio"], input[type="checkbox"]');
                                for (var i = 0; i < inputs.length; i++) {
                                    var parentText = inputs[i].parentElement ? inputs[i].parentElement.textContent : '';
                                    if (parentText.includes('Commercial Auto')) {
                                        console.log('Found Commercial Auto input:', inputs[i]);
                                        inputs[i].checked = true;
                                        inputs[i].click();
                                        clicked = true;
                                        break;
                                    }
                                }
                                
                                return clicked ? 'clicked' : 'not found';
                            """)
                            
                            print(f"[DEBUG] Specific click result: {specific_click}")
                            
                            if specific_click == 'clicked':
                                time.sleep(3)
                                print("[DEBUG] Clicked using specific ID approach")
                            
                            # Now try the general JavaScript approach to find and click
                            print("[DEBUG] Attempting general JavaScript click on Commercial Auto/Trucking...")
                            js_click_result = driver.execute_script("""
                                // Find all elements that contain 'Commercial Auto/Trucking' text
                                var allElements = document.querySelectorAll('*');
                                var foundElement = null;
                                
                                for (var i = 0; i < allElements.length; i++) {
                                    var elem = allElements[i];
                                    // Check if element directly contains the text (not in children)
                                    if (elem.textContent && elem.textContent.trim() === 'Commercial Auto/Trucking') {
                                        // Skip if it's inside a form or is a checkbox/radio label
                                        var isFormElement = false;
                                        var checkParent = elem.parentElement;
                                        while (checkParent && checkParent.tagName !== 'BODY') {
                                            if (checkParent.tagName === 'FORM' || 
                                                (checkParent.tagName === 'LABEL' && (checkParent.className.includes('checkbox') || checkParent.className.includes('radio')))) {
                                                isFormElement = true;
                                                break;
                                            }
                                            checkParent = checkParent.parentElement;
                                        }
                                        
                                        if (isFormElement) {
                                            console.log('Skipping form/checkbox element:', elem.tagName);
                                            continue;
                                        }
                                        
                                        var hasChildText = false;
                                        for (var j = 0; j < elem.children.length; j++) {
                                            if (elem.children[j].textContent.includes('Commercial Auto/Trucking')) {
                                                hasChildText = true;
                                                break;
                                            }
                                        }
                                        
                                        if (!hasChildText) {
                                            console.log('Found element with Commercial Auto text:', elem.tagName, elem.className);
                                            
                                            // Look for the actual clickable element (might be parent)
                                            var clickableElem = elem;
                                            var parent = elem.parentElement;
                                            
                                            // Check up to 3 levels of parents for clickable elements
                                            for (var level = 0; level < 3 && parent; level++) {
                                                if (parent.tagName === 'A' || parent.tagName === 'BUTTON' || 
                                                    parent.getAttribute('role') === 'button' || 
                                                    parent.getAttribute('role') === 'tab' ||
                                                    parent.onclick || parent.getAttribute('href') ||
                                                    parent.classList.contains('tab') ||
                                                    parent.classList.contains('link') ||
                                                    parent.classList.contains('clickable')) {
                                                    clickableElem = parent;
                                                    console.log('Found clickable parent:', parent.tagName, parent.className);
                                                    break;
                                                }
                                                parent = parent.parentElement;
                                            }
                                            
                                            foundElement = clickableElem;
                                            break;
                                        }
                                    }
                                }
                                
                                if (foundElement) {
                                    console.log('Clicking element:', foundElement.tagName, foundElement.textContent);
                                    
                                    // Highlight the element
                                    foundElement.style.border = '3px solid red';
                                    foundElement.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
                                    
                                    // Try multiple click methods
                                    try {
                                        foundElement.click();
                                        console.log('Standard click executed');
                                    } catch(e) {
                                        console.log('Standard click failed:', e);
                                    }
                                    
                                    // Force navigation if it's a link
                                    if (foundElement.href) {
                                        console.log('Element has href, navigating to:', foundElement.href);
                                        window.location.href = foundElement.href;
                                        return 'navigated';
                                    }
                                    
                                    // Dispatch mouse events
                                    var event = new MouseEvent('click', {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true
                                    });
                                    foundElement.dispatchEvent(event);
                                    
                                    return 'clicked';
                                }
                                
                                console.log('No Commercial Auto/Trucking element found');
                                return 'not found';
                            """)
                            
                            print(f"[DEBUG] JavaScript click result: {js_click_result}")
                            
                            if js_click_result == 'clicked' or js_click_result == 'navigated':
                                time.sleep(3)  # Wait for navigation
                                print(f"[DEBUG] Current URL after JS click: {driver.current_url}")
                                # Continue with the rest of the detection logic below
                            else:
                                print("[DEBUG] JavaScript click failed, trying alternative approach...")
                                
                                # Alternative approach: Try clicking based on what we found in diagnostics
                                if len(page_info['commercialElements']) > 0:
                                    print("[DEBUG] Trying to click based on diagnostic info...")
                                    
                                    # Find the most specific Commercial Auto element
                                    for comm_elem in page_info['commercialElements']:
                                        if 'Commercial Auto/Trucking' in comm_elem['text'] and len(comm_elem['text']) < 50:
                                            print(f"[DEBUG] Found specific element: {comm_elem}")
                                            
                                            # Try to click using tag and text
                                            click_attempt = driver.execute_script("""
                                                var tag = arguments[0];
                                                var text = arguments[1];
                                                var elements = document.getElementsByTagName(tag);
                                                
                                                for (var i = 0; i < elements.length; i++) {
                                                    if (elements[i].textContent.trim() === text) {
                                                        console.log('Found exact match element:', elements[i]);
                                                        
                                                        // Highlight it
                                                        elements[i].style.border = '5px solid yellow';
                                                        
                                                        // Try to click it
                                                        elements[i].click();
                                                        
                                                        // If it has a parent that might be clickable, try that too
                                                        if (elements[i].parentElement) {
                                                            elements[i].parentElement.click();
                                                        }
                                                        
                                                        return 'clicked';
                                                    }
                                                }
                                                return 'not found';
                                            """, comm_elem['tag'], 'Commercial Auto/Trucking')
                                            
                                            print(f"[DEBUG] Click attempt result: {click_attempt}")
                                            
                                            if click_attempt == 'clicked':
                                                time.sleep(3)
                                                break
                                
                                # Last resort: Try coordinate-based click from visual detection
                                print("[DEBUG] Trying coordinate-based click from visual detection...")
                                if 'detected_elements' in globals() and detected_elements:
                                    for elem in detected_elements:
                                        if elem.get('text', '').strip() == 'Commercial Auto/Trucking':
                                            print(f"[DEBUG] Found Commercial Auto at coordinates: x={elem['x']}, y={elem['y']}")
                                            
                                            # Use ActionChains for precise clicking
                                            try:
                                                from selenium.webdriver.common.action_chains import ActionChains
                                                actions = ActionChains(driver)
                                                # Move to the center of the element
                                                x = elem['x'] + elem['width'] // 2
                                                y = elem['y'] + elem['height'] // 2
                                                
                                                # Move to element and click
                                                actions.move_by_offset(x, y).click().perform()
                                                print(f"[DEBUG] Performed coordinate click at ({x}, {y})")
                                                time.sleep(3)
                                                break
                                            except Exception as e:
                                                print(f"[DEBUG] Coordinate click failed: {e}")
                                                
                                                # Try JavaScript coordinate click
                                                driver.execute_script(f"""
                                                    // Simulate click at coordinates
                                                    var evt = new MouseEvent('click', {{
                                                        view: window,
                                                        bubbles: true,
                                                        cancelable: true,
                                                        clientX: {x},
                                                        clientY: {y}
                                                    }});
                                                    
                                                    var element = document.elementFromPoint({x}, {y});
                                                    if (element) {{
                                                        element.dispatchEvent(evt);
                                                        console.log('Dispatched click event at coordinates');
                                                    }}
                                                """)
                            
                            # Look for Commercial Auto/Trucking element - be more specific
                            # Exclude checkbox labels and form elements
                            commercial_elements = driver.find_elements(By.XPATH, 
                                "//a[contains(text(), 'Commercial Auto/Trucking')] | " +
                                "//button[contains(text(), 'Commercial Auto/Trucking')] | " +
                                "//div[@role='button' and contains(text(), 'Commercial Auto/Trucking')] | " +
                                "//div[@role='tab' and contains(text(), 'Commercial Auto/Trucking')] | " +
                                "//li[@role='tab' and contains(text(), 'Commercial Auto/Trucking')] | " +
                                "//span[contains(text(), 'Commercial Auto/Trucking')]/ancestor::a | " +
                                "//span[contains(text(), 'Commercial Auto/Trucking')]/ancestor::button | " +
                                "//span[contains(text(), 'Commercial Auto/Trucking')]/ancestor::div[@role='tab'] | " +
                                "//span[contains(text(), 'Commercial Auto/Trucking')]/ancestor::li[@role='tab'] | " +
                                "//div[contains(@class, 'tab') and contains(text(), 'Commercial Auto/Trucking')] | " +
                                "//li[contains(@class, 'tab') and contains(text(), 'Commercial Auto/Trucking')]"
                            )
                            
                            # Filter out checkbox labels
                            filtered_elements = []
                            for elem in commercial_elements:
                                try:
                                    # Skip if it's inside a label with class 'checkbox' or 'radio'
                                    parent_classes = driver.execute_script("""
                                        var elem = arguments[0];
                                        var parent = elem.parentElement;
                                        if (parent && parent.tagName === 'LABEL') {
                                            return parent.className;
                                        }
                                        return '';
                                    """, elem)
                                    
                                    if 'checkbox' not in parent_classes.lower() and 'radio' not in parent_classes.lower():
                                        filtered_elements.append(elem)
                                        print(f"[DEBUG] Found potential Commercial Auto element: {elem.tag_name}")
                                except:
                                    filtered_elements.append(elem)
                            
                            commercial_elements = filtered_elements
                            
                            print(f"[DEBUG] Found {len(commercial_elements)} potential Commercial Auto/Trucking elements via XPath")
                            
                            # If XPath doesn't work, try JavaScript to find elements
                            if not commercial_elements:
                                print("[DEBUG] XPath failed, trying JavaScript search...")
                                js_elements = driver.execute_script("""
                                    var elements = [];
                                    var allElements = document.querySelectorAll('*');
                                    for (var i = 0; i < allElements.length; i++) {
                                        var elem = allElements[i];
                                        if (elem.textContent.includes('Commercial Auto/Trucking') && 
                                            elem.textContent.trim() === 'Commercial Auto/Trucking') {
                                            // Check if this element is clickable
                                            if (elem.tagName === 'A' || elem.tagName === 'BUTTON' || 
                                                elem.getAttribute('role') === 'button' || 
                                                elem.getAttribute('role') === 'tab' ||
                                                elem.classList.contains('tab') ||
                                                elem.onclick || elem.getAttribute('href')) {
                                                elements.push(elem);
                                            } else {
                                                // Look for clickable parent
                                                var parent = elem.parentElement;
                                                while (parent && parent.tagName !== 'BODY') {
                                                    if (parent.tagName === 'A' || parent.tagName === 'BUTTON' || 
                                                        parent.getAttribute('role') === 'button' || 
                                                        parent.getAttribute('role') === 'tab' ||
                                                        parent.classList.contains('tab') ||
                                                        parent.onclick || parent.getAttribute('href')) {
                                                        elements.push(parent);
                                                        break;
                                                    }
                                                    parent = parent.parentElement;
                                                }
                                                // If no clickable parent found, add the original element
                                                if (!parent || parent.tagName === 'BODY') {
                                                    elements.push(elem);
                                                }
                                            }
                                        }
                                    }
                                    return elements;
                                """)
                                commercial_elements = js_elements if js_elements else []
                                print(f"[DEBUG] Found {len(commercial_elements)} elements via JavaScript")
                            
                            print(f"[DEBUG] Total found: {len(commercial_elements)} potential Commercial Auto/Trucking elements")
                            
                            # Look for the most specific, smallest element that contains the text
                            best_element = None
                            smallest_area = float('inf')
                            
                            for elem in commercial_elements:
                                if elem.is_displayed():
                                    elem_text = elem.text.strip()
                                    elem_tag = elem.tag_name
                                    elem_href = elem.get_attribute('href') or 'No href'
                                    elem_onclick = elem.get_attribute('onclick') or 'No onclick'
                                    elem_role = elem.get_attribute('role') or 'No role'
                                    rect = elem.rect
                                    area = rect['width'] * rect['height']
                                    
                                    print(f"[DEBUG] Checking element: tag={elem_tag}, href={elem_href[:50] if len(elem_href) > 50 else elem_href}, role={elem_role}, area={area}")
                                    
                                    # Skip very large elements (likely containers)
                                    if area > 50000:
                                        print(f"[DEBUG] Skipping large element (area={area}): '{elem_text[:50]}...'")
                                        continue
                                    
                                    # Look for exact match or close match
                                    if elem_text == "Commercial Auto/Trucking" or \
                                       (elem_text.startswith("Commercial Auto/Trucking") and len(elem_text) < 50):
                                        print(f"[DEBUG] Found good Commercial Auto element: '{elem_text}' (tag={elem_tag}, area={area})")
                                        # Prefer clickable elements (a, button) over generic elements
                                        if elem_tag.lower() in ['a', 'button'] or elem_role == 'button':
                                            print(f"[DEBUG] This is a clickable element! Setting as best element.")
                                            best_element = elem
                                            break  # Found a clickable element, use it
                                        elif area < smallest_area:
                                            smallest_area = area
                                            best_element = elem
                            
                            if best_element:
                                elem = best_element
                                elem_text = elem.text.strip()
                                print(f"[DEBUG] Selected best Commercial Auto element to click: '{elem_text}'")
                                current_status = "Found Commercial Auto/Trucking - clicking..."
                                
                                # Highlight the element and get detailed diagnostics
                                elem_diagnostics = driver.execute_script("""
                                    var elem = arguments[0];
                                    elem.style.border = '3px solid green';
                                    elem.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
                                    
                                    // Get comprehensive element information
                                    var rect = elem.getBoundingClientRect();
                                    var computedStyle = window.getComputedStyle(elem);
                                    
                                    var diagnostics = {
                                        tagName: elem.tagName,
                                        className: elem.className,
                                        id: elem.id,
                                        href: elem.href || 'none',
                                        onclick: elem.onclick ? 'has onclick' : 'none',
                                        cursor: computedStyle.cursor,
                                        pointerEvents: computedStyle.pointerEvents,
                                        display: computedStyle.display,
                                        visibility: computedStyle.visibility,
                                        position: computedStyle.position,
                                        zIndex: computedStyle.zIndex,
                                        isClickable: elem.tagName === 'A' || elem.tagName === 'BUTTON' || elem.onclick || elem.getAttribute('role') === 'button',
                                        rect: {x: rect.x, y: rect.y, width: rect.width, height: rect.height},
                                        parentTag: elem.parentElement ? elem.parentElement.tagName : 'none',
                                        parentClass: elem.parentElement ? elem.parentElement.className : 'none',
                                        hasOverlay: false
                                    };
                                    
                                    // Check for overlapping elements
                                    var centerX = rect.left + rect.width / 2;
                                    var centerY = rect.top + rect.height / 2;
                                    var topElement = document.elementFromPoint(centerX, centerY);
                                    
                                    if (topElement !== elem) {
                                        diagnostics.hasOverlay = true;
                                        diagnostics.overlayElement = {
                                            tag: topElement.tagName,
                                            class: topElement.className
                                        };
                                    }
                                    
                                    console.log('Element diagnostics:', diagnostics);
                                    return diagnostics;
                                """, elem)
                                
                                print(f"[DEBUG] Green element diagnostics: {elem_diagnostics}")
                                
                                # Capture the HTML structure around this element
                                elem_html = driver.execute_script("""
                                    var elem = arguments[0];
                                    var html = {
                                        outer: elem.outerHTML.substring(0, 200),
                                        parent: elem.parentElement ? elem.parentElement.outerHTML.substring(0, 200) : 'no parent',
                                        grandparent: elem.parentElement && elem.parentElement.parentElement ? 
                                                     elem.parentElement.parentElement.outerHTML.substring(0, 200) : 'no grandparent'
                                    };
                                    return html;
                                """, elem)
                                
                                print(f"[DEBUG] Element HTML structure:")
                                print(f"[DEBUG]   Element: {elem_html['outer']}")
                                print(f"[DEBUG]   Parent: {elem_html['parent']}")
                                print(f"[DEBUG]   Grandparent: {elem_html['grandparent']}")
                                
                                time.sleep(1)  # Brief pause to show highlight
                                
                                # Decide on click strategy based on diagnostics
                                if elem_diagnostics.get('hasOverlay'):
                                    print(f"[DEBUG] Element has overlay! Overlay element: {elem_diagnostics.get('overlayElement')}")
                                
                                if not elem_diagnostics.get('isClickable'):
                                    print(f"[DEBUG] Element is not directly clickable. Parent: {elem_diagnostics.get('parentTag')}")
                                
                                try:
                                    # Smart click based on element properties
                                    click_success = driver.execute_script("""
                                        var elem = arguments[0];
                                        var diagnostics = arguments[1];
                                        
                                        elem.scrollIntoView({block: 'center'});
                                        
                                        console.log('Attempting smart click based on diagnostics:', diagnostics);
                                        
                                        // If element has overlay, try to click at its position
                                        if (diagnostics.hasOverlay) {
                                            console.log('Element has overlay, trying coordinate click');
                                            var rect = elem.getBoundingClientRect();
                                            var x = rect.left + rect.width / 2;
                                            var y = rect.top + rect.height / 2;
                                            
                                            // Click at the element's position
                                            var clickEvent = new MouseEvent('click', {
                                                view: window,
                                                bubbles: true,
                                                cancelable: true,
                                                clientX: x,
                                                clientY: y
                                            });
                                            
                                            // Dispatch to whatever is at that position
                                            var targetElement = document.elementFromPoint(x, y);
                                            if (targetElement) {
                                                console.log('Clicking overlay element:', targetElement);
                                                targetElement.click();
                                                targetElement.dispatchEvent(clickEvent);
                                            }
                                        }
                                        
                                        // If element is not clickable, try parent
                                        if (!diagnostics.isClickable && elem.parentElement) {
                                            console.log('Element not clickable, trying parent');
                                            elem.parentElement.click();
                                            
                                            // Also try grandparent
                                            if (elem.parentElement.parentElement) {
                                                elem.parentElement.parentElement.click();
                                            }
                                        }
                                        
                                        console.log('Element to click:', elem.tagName, elem.textContent, elem.href || 'no href');
                                        
                                        // Method 1: Direct click
                                        try {
                                            elem.click();
                                            console.log('Method 1: Direct click executed');
                                        } catch(e) {
                                            console.log('Method 1 failed:', e);
                                        }
                                        
                                        // Method 2: Dispatch full mouse event sequence
                                        try {
                                            var rect = elem.getBoundingClientRect();
                                            var x = rect.left + rect.width / 2;
                                            var y = rect.top + rect.height / 2;
                                            
                                            // Mousedown
                                            var mouseDownEvent = new MouseEvent('mousedown', {
                                                view: window,
                                                bubbles: true,
                                                cancelable: true,
                                                clientX: x,
                                                clientY: y,
                                                buttons: 1
                                            });
                                            elem.dispatchEvent(mouseDownEvent);
                                            
                                            // Mouseup
                                            var mouseUpEvent = new MouseEvent('mouseup', {
                                                view: window,
                                                bubbles: true,
                                                cancelable: true,
                                                clientX: x,
                                                clientY: y,
                                                buttons: 0
                                            });
                                            elem.dispatchEvent(mouseUpEvent);
                                            
                                            // Click
                                            var clickEvent = new MouseEvent('click', {
                                                view: window,
                                                bubbles: true,
                                                cancelable: true,
                                                clientX: x,
                                                clientY: y,
                                                buttons: 0
                                            });
                                            elem.dispatchEvent(clickEvent);
                                            console.log('Method 2: Full mouse event sequence dispatched');
                                        } catch(e) {
                                            console.log('Method 2 failed:', e);
                                        }
                                        
                                        // Method 3: If it's a link, navigate directly
                                        try {
                                            if (elem.tagName === 'A' && elem.href) {
                                                console.log('Method 3: Found link, navigating to:', elem.href);
                                                window.location.href = elem.href;
                                                return true;
                                            }
                                        } catch(e) {
                                            console.log('Method 3 failed:', e);
                                        }
                                        
                                        // Method 4: Focus and simulate Enter/Space
                                        try {
                                            elem.focus();
                                            
                                            // Try Enter
                                            var enterEvent = new KeyboardEvent('keydown', {
                                                key: 'Enter',
                                                code: 'Enter',
                                                keyCode: 13,
                                                which: 13,
                                                bubbles: true
                                            });
                                            elem.dispatchEvent(enterEvent);
                                            
                                            // Try Space
                                            var spaceEvent = new KeyboardEvent('keydown', {
                                                key: ' ',
                                                code: 'Space',
                                                keyCode: 32,
                                                which: 32,
                                                bubbles: true
                                            });
                                            elem.dispatchEvent(spaceEvent);
                                            console.log('Method 4: Enter and Space key dispatched');
                                        } catch(e) {
                                            console.log('Method 4 failed:', e);
                                        }
                                        
                                        // Method 5: jQuery click if available
                                        try {
                                            if (typeof jQuery !== 'undefined') {
                                                jQuery(elem).click();
                                                console.log('Method 5: jQuery click executed');
                                            }
                                        } catch(e) {
                                            console.log('Method 5 failed:', e);
                                        }
                                        
                                        // Don't set commercialAutoClicked here - verify navigation first
                                        console.log('Commercial Auto/Trucking click attempted with all methods');
                                        return false;  // Return false unless we navigated directly
                                    """, elem, elem_diagnostics)
                                    print("[DEBUG] Attempted Commercial Auto/Trucking click with multiple methods")
                                    current_status = "Commercial Auto/Trucking clicked - loading..."
                                    time.sleep(3)  # Wait for page to load
                                except Exception as js_error:
                                    print(f"[DEBUG] JavaScript methods failed: {js_error}, trying other approaches")
                                    
                                # Try focused approach based on element type
                                if elem_diagnostics.get('tagName') == 'SPAN':
                                    print("[DEBUG] Green element is a SPAN - looking for clickable parent")
                                    try:
                                        # For SPAN elements, the parent is usually the clickable element
                                        parent_elem = driver.execute_script("return arguments[0].parentElement;", elem)
                                        if parent_elem:
                                            print("[DEBUG] Clicking parent of SPAN element")
                                            parent_elem.click()
                                            time.sleep(2)
                                    except Exception as e:
                                        print(f"[DEBUG] Parent click failed: {e}")
                                
                                # Try simulating a real user click with all events
                                print("[DEBUG] Trying real user simulation click...")
                                try:
                                    user_click_result = driver.execute_script("""
                                        var elem = arguments[0];
                                        
                                        // Simulate hovering first
                                        var hoverEvent = new MouseEvent('mouseover', {
                                            view: window,
                                            bubbles: true,
                                            cancelable: true
                                        });
                                        elem.dispatchEvent(hoverEvent);
                                        
                                        // Then mousedown
                                        var mouseDownEvent = new MouseEvent('mousedown', {
                                            view: window,
                                            bubbles: true,
                                            cancelable: true,
                                            button: 0,
                                            buttons: 1
                                        });
                                        elem.dispatchEvent(mouseDownEvent);
                                        
                                        // Then mouseup
                                        var mouseUpEvent = new MouseEvent('mouseup', {
                                            view: window,
                                            bubbles: true,
                                            cancelable: true,
                                            button: 0,
                                            buttons: 0
                                        });
                                        elem.dispatchEvent(mouseUpEvent);
                                        
                                        // Finally click
                                        var clickEvent = new MouseEvent('click', {
                                            view: window,
                                            bubbles: true,
                                            cancelable: true,
                                            button: 0
                                        });
                                        elem.dispatchEvent(clickEvent);
                                        
                                        // Try native click too
                                        elem.click();
                                        
                                        return 'user simulation complete';
                                    """, elem)
                                    
                                    print(f"[DEBUG] User simulation result: {user_click_result}")
                                    time.sleep(2)
                                except Exception as e:
                                    print(f"[DEBUG] User simulation failed: {e}")
                                
                                # Try Selenium click
                                try:
                                    elem.click()
                                    # Don't set commercialAutoClicked here - will verify after
                                    print("[DEBUG] Attempted Commercial Auto/Trucking click via Selenium")
                                    current_status = "Commercial Auto/Trucking clicked - loading..."
                                    time.sleep(2)  # Wait for page to load
                                except Exception as selenium_error:
                                    print(f"[DEBUG] Selenium click failed: {selenium_error}, trying ActionChains")
                                    
                                    # Try ActionChains
                                    try:
                                        from selenium.webdriver.common.action_chains import ActionChains
                                        actions = ActionChains(driver)
                                        actions.move_to_element(elem).click().perform()
                                        # Don't set commercialAutoClicked here - will verify after
                                        print("[DEBUG] Attempted Commercial Auto/Trucking click via ActionChains")
                                        current_status = "Commercial Auto/Trucking clicked - loading..."
                                        time.sleep(2)
                                    except Exception as action_error:
                                        print(f"[DEBUG] ActionChains also failed: {action_error}")
                                        
                                        # Try keyboard navigation as last resort
                                        print("[DEBUG] Trying keyboard navigation approach...")
                                        try:
                                            # Focus on the element first
                                            driver.execute_script("arguments[0].focus();", elem)
                                            time.sleep(0.5)
                                            
                                            # Try pressing Enter
                                            elem.send_keys(Keys.ENTER)
                                            print("[DEBUG] Sent Enter key to element")
                                            time.sleep(2)
                                            
                                            # Check if page changed
                                            new_url = driver.current_url
                                            if new_url != current_url:
                                                print(f"[DEBUG] URL changed after Enter key: {new_url}")
                                            else:
                                                # Try Space key
                                                elem.send_keys(Keys.SPACE)
                                                print("[DEBUG] Sent Space key to element")
                                                time.sleep(2)
                                        except Exception as kbd_error:
                                            print(f"[DEBUG] Keyboard navigation failed: {kbd_error}")
                            
                            else:
                                print("[DEBUG] No clickable Commercial Auto/Trucking element found via DOM search")
                                
                                # Try clicking using coordinates from visual detection
                                print("[DEBUG] Attempting to click Commercial Auto using visual detection...")
                                try:
                                    # Look for Commercial Auto in detected elements
                                    for elem_data in detected_elements:
                                        if elem_data.get('text', '').strip() == 'Commercial Auto/Trucking':
                                            x = elem_data['x'] + elem_data['width'] // 2
                                            y = elem_data['y'] + elem_data['height'] // 2
                                            print(f"[DEBUG] Found Commercial Auto in visual detection at ({x}, {y})")
                                            
                                            # Click using JavaScript at coordinates
                                            driver.execute_script(f"""
                                                var element = document.elementFromPoint({x}, {y});
                                                if (element) {{
                                                    console.log('Found element at coordinates:', element.tagName, element.textContent);
                                                    
                                                    // Look for clickable parent if current element isn't clickable
                                                    var clickableElement = element;
                                                    var parent = element.parentElement;
                                                    while (parent && parent.tagName !== 'BODY') {{
                                                        if (parent.tagName === 'A' || parent.tagName === 'BUTTON' || 
                                                            parent.getAttribute('role') === 'button' || 
                                                            parent.onclick || parent.getAttribute('href')) {{
                                                            clickableElement = parent;
                                                            console.log('Found clickable parent:', parent.tagName);
                                                            break;
                                                        }}
                                                        parent = parent.parentElement;
                                                    }}
                                                    
                                                    // Try to click the element
                                                    clickableElement.click();
                                                    
                                                    // If it's a link, navigate directly
                                                    if (clickableElement.tagName === 'A' && clickableElement.href) {{
                                                        window.location.href = clickableElement.href;
                                                    }}
                                                    
                                                    // Don't set commercialAutoClicked here - verify navigation first
                                                    return true;
                                                }}
                                                return false;
                                            """)
                                            print("[DEBUG] Clicked Commercial Auto via visual detection coordinates")
                                            current_status = "Commercial Auto clicked via visual detection"
                                            time.sleep(3)
                                            break
                                except Exception as e:
                                    print(f"[DEBUG] Visual detection click failed: {e}")
                            
                            # After all click attempts, verify if we actually navigated
                            time.sleep(3)  # Give page time to load
                            current_url = driver.current_url
                            print(f"[DEBUG] Current URL after click attempt: {current_url}")
                            
                            # More comprehensive check for successful navigation
                            page_changed = False
                            
                            # Check 1: URL changed
                            if "commercial" in current_url.lower() or "trucking" in current_url.lower() or "product" not in current_url.lower():
                                page_changed = True
                                print("[DEBUG] URL indicates we're on Commercial Auto page")
                            
                            # Check 2: Look for form elements that appear after clicking Commercial Auto
                            if not page_changed:
                                form_indicators = driver.find_elements(By.XPATH, 
                                    "//input[contains(@placeholder, 'ZIP') or contains(@placeholder, 'zip') or contains(@name, 'zip')] | " +
                                    "//input[contains(@placeholder, 'DOT') or contains(@name, 'dot')] | " +
                                    "//label[contains(text(), 'ZIP')] | " +
                                    "//label[contains(text(), 'Garage')] | " +
                                    "//h1[contains(text(), 'Commercial')] | " +
                                    "//h2[contains(text(), 'Commercial')]"
                                )
                                if len(form_indicators) > 0:
                                    page_changed = True
                                    print(f"[DEBUG] Found {len(form_indicators)} Commercial Auto form elements")
                            
                            # Check 3: Page title changed
                            if not page_changed:
                                try:
                                    page_title = driver.title
                                    if "commercial" in page_title.lower() or "trucking" in page_title.lower():
                                        page_changed = True
                                        print(f"[DEBUG] Page title indicates Commercial Auto: {page_title}")
                                except:
                                    pass
                            
                            if page_changed:
                                driver.execute_script("window.commercialAutoClicked = true;")
                                print("[DEBUG] Successfully navigated to Commercial Auto page!")
                            else:
                                print("[DEBUG] Commercial Auto click failed - still on product selection page")
                                driver.execute_script("window.commercialAutoClicked = false;")
                                # Force another attempt on next scan
                                commercial_clicked = False
                                
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
                                    
                                    # Click and fill the zip code with proper event sequence
                                    driver.execute_script("""
                                        var elem = arguments[0];
                                        elem.scrollIntoView({block: 'center'});
                                        elem.click();
                                        elem.focus();
                                        
                                        // Clear field first
                                        elem.value = '';
                                        elem.dispatchEvent(new Event('input', { bubbles: true }));
                                        
                                        // Type each character to simulate real typing
                                        var zipCode = '44256';
                                        for (var i = 0; i < zipCode.length; i++) {
                                            elem.value += zipCode[i];
                                            elem.dispatchEvent(new Event('input', { bubbles: true }));
                                        }
                                        
                                        // Trigger change and blur events
                                        elem.dispatchEvent(new Event('change', { bubbles: true }));
                                        elem.dispatchEvent(new Event('blur', { bubbles: true }));
                                        
                                        // Wait a moment then double-click the field
                                        setTimeout(function() {
                                            console.log('Double-clicking zip field to activate...');
                                            
                                            // Double click to activate the field
                                            var dblClickEvent = new MouseEvent('dblclick', {
                                                view: window,
                                                bubbles: true,
                                                cancelable: true
                                            });
                                            elem.dispatchEvent(dblClickEvent);
                                            
                                            // Also try regular clicks
                                            elem.click();
                                            elem.click();
                                            
                                            // Then press Enter
                                            setTimeout(function() {
                                                console.log('Pressing Enter after double-click...');
                                                var enterEvent = new KeyboardEvent('keydown', {
                                                    key: 'Enter',
                                                    code: 'Enter',
                                                    keyCode: 13,
                                                    which: 13,
                                                    bubbles: true
                                                });
                                                elem.dispatchEvent(enterEvent);
                                                
                                                var enterEventUp = new KeyboardEvent('keyup', {
                                                    key: 'Enter',
                                                    code: 'Enter',
                                                    keyCode: 13,
                                                    which: 13,
                                                    bubbles: true
                                                });
                                                elem.dispatchEvent(enterEventUp);
                                                
                                                console.log('Zip code 44256 filled, double-clicked, and Enter pressed');
                                            }, 500);
                                        }, 1000);
                                        
                                        window.zipCodeFilled = true;
                                    """, zip_elem)
                                    
                                    print("[DEBUG] Successfully filled zip code 44256")
                                    
                                    # Wait for JavaScript to complete
                                    time.sleep(2)
                                    
                                    # Now use Selenium to ensure the field is focused and press Enter
                                    print("[DEBUG] Using Selenium to focus and press Enter on zip field")
                                    try:
                                        zip_elem.click()  # Click to focus
                                        time.sleep(0.5)
                                        
                                        # Send Enter key using Selenium
                                        from selenium.webdriver.common.keys import Keys
                                        zip_elem.send_keys(Keys.ENTER)
                                        print("[DEBUG] Sent Enter key using Selenium")
                                        
                                        # Also try with JavaScript one more time
                                        driver.execute_script("""
                                            var elem = arguments[0];
                                            elem.focus();
                                            
                                            // Simulate pressing Enter key
                                            var event = new KeyboardEvent('keypress', {
                                                key: 'Enter',
                                                code: 'Enter',
                                                keyCode: 13,
                                                which: 13,
                                                bubbles: true,
                                                cancelable: true
                                            });
                                            elem.dispatchEvent(event);
                                            
                                            // Also try form submit if element is in a form
                                            if (elem.form) {
                                                console.log('Submitting form...');
                                                elem.form.submit();
                                            }
                                        """, zip_elem)
                                        
                                    except Exception as e:
                                        print(f"[DEBUG] Error with Selenium Enter: {e}")
                                    
                                    zip_filled = True
                                    saved_zip_elem = zip_elem  # Save reference to zip field
                                    
                                    # Set up a JavaScript observer to monitor the zip field
                                    print("[DEBUG] Setting up zip field monitor...")
                                    try:
                                        driver.execute_script("""
                                            var zipElem = arguments[0];
                                            
                                            // Store the zip element globally
                                            window.geicoZipElement = zipElem;
                                            window.geicoZipValue = '44256';
                                            
                                            // Function to refill zip if it gets cleared
                                            window.checkAndRefillZip = function() {
                                                if (window.geicoZipElement && window.geicoZipElement.value !== window.geicoZipValue) {
                                                    console.log('Zip field cleared! Refilling...');
                                                    window.geicoZipElement.value = window.geicoZipValue;
                                                    window.geicoZipElement.dispatchEvent(new Event('input', { bubbles: true }));
                                                    window.geicoZipElement.dispatchEvent(new Event('change', { bubbles: true }));
                                                    
                                                    // Also press Enter to re-submit
                                                    var enterEvent = new KeyboardEvent('keydown', {
                                                        key: 'Enter',
                                                        code: 'Enter',
                                                        keyCode: 13,
                                                        which: 13,
                                                        bubbles: true
                                                    });
                                                    window.geicoZipElement.dispatchEvent(enterEvent);
                                                }
                                            };
                                            
                                            // Check every 500ms
                                            window.zipMonitorInterval = setInterval(window.checkAndRefillZip, 500);
                                            
                                            // Also set up a MutationObserver
                                            var observer = new MutationObserver(function(mutations) {
                                                mutations.forEach(function(mutation) {
                                                    if (mutation.type === 'attributes' && mutation.attributeName === 'value') {
                                                        window.checkAndRefillZip();
                                                    }
                                                });
                                            });
                                            
                                            observer.observe(zipElem, {
                                                attributes: true,
                                                attributeFilter: ['value']
                                            });
                                            
                                            window.geicoZipObserver = observer;
                                            console.log('Zip field monitor installed');
                                        """, zip_elem)
                                        print("[DEBUG] Zip field monitor installed successfully")
                                    except Exception as e:
                                        print(f"[DEBUG] Error setting up zip monitor: {e}")
                                    
                                    # Verify zip code is actually in the field
                                    time.sleep(0.5)
                                    try:
                                        current_zip_value = zip_elem.get_attribute('value')
                                        print(f"[DEBUG] Zip field value after filling: '{current_zip_value}'")
                                        
                                        # Check if there are any event listeners or validation attributes
                                        zip_events = driver.execute_script("""
                                            var elem = arguments[0];
                                            var events = [];
                                            if (elem.onblur) events.push('onblur');
                                            if (elem.onchange) events.push('onchange');
                                            if (elem.oninput) events.push('oninput');
                                            var validation = {
                                                required: elem.required,
                                                pattern: elem.pattern,
                                                minLength: elem.minLength,
                                                maxLength: elem.maxLength
                                            };
                                            return {events: events, validation: validation, form: elem.form ? elem.form.id : 'no-form'};
                                        """, zip_elem)
                                        print(f"[DEBUG] Zip field properties: {zip_events}")
                                    except Exception as e:
                                        print(f"[DEBUG] Error checking zip field: {e}")
                                    
                                    time.sleep(5)  # Give more time for double-click, Enter, and state to populate
                                    
                                    # Check if state field got populated - wait up to 10 seconds
                                    print("[DEBUG] Waiting for state field to populate with Ohio...")
                                    state_populated = False
                                    for wait_count in range(10):
                                        try:
                                            # Look for state field
                                            state_elements = driver.find_elements(By.XPATH,
                                                "//select[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'state')] | " +
                                                "//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'state')] | " +
                                                "//select[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'state')] | " +
                                                "//input[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'state')]"
                                            )
                                            
                                            for state_elem in state_elements:
                                                if state_elem.is_displayed():
                                                    state_value = state_elem.get_attribute('value') or ''
                                                    # For select elements, get selected option text
                                                    if state_elem.tag_name.lower() == 'select':
                                                        try:
                                                            selected_option = state_elem.find_element(By.CSS_SELECTOR, "option[selected]")
                                                            state_text = selected_option.text
                                                        except:
                                                            state_text = state_elem.text or ''
                                                    else:
                                                        state_text = state_elem.text or ''
                                                    
                                                    print(f"[DEBUG] Attempt {wait_count+1}: State field value: '{state_value}', text: '{state_text}'")
                                                    
                                                    # Check if Ohio/OH is selected
                                                    if 'OH' in state_value or 'Ohio' in state_value or 'OH' in state_text or 'Ohio' in state_text:
                                                        print("[DEBUG] SUCCESS! Ohio is now selected in state field")
                                                        state_populated = True
                                                        break
                                                    elif 'Please' in state_text or 'Select' in state_text or state_value == '':
                                                        print("[DEBUG] State still shows 'Please Select' - zip not submitted yet")
                                                        
                                                        # Try pressing Enter again on zip field
                                                        if wait_count < 5:  # Try a few more times
                                                            print("[DEBUG] Trying Enter on zip field again...")
                                                            try:
                                                                from selenium.webdriver.common.keys import Keys
                                                                zip_elem.click()
                                                                zip_elem.send_keys(Keys.ENTER)
                                                            except:
                                                                pass
                                                    else:
                                                        print(f"[DEBUG] State shows: {state_text} - not Ohio")
                                                    break
                                            
                                            if state_populated:
                                                break
                                                
                                            time.sleep(1)  # Wait 1 second before checking again
                                        
                                            # Re-check zip value before proceeding
                                            final_zip = zip_elem.get_attribute('value')
                                            print(f"[DEBUG] Zip value after Enter: '{final_zip}'")
                                        except Exception as e:
                                            print(f"[DEBUG] Error checking state: {e}")
                                    
                                    # Try Tab key instead of background click
                                    print("[DEBUG] Pressing Tab to move to next field...")
                                    try:
                                        driver.execute_script("""
                                            var elem = arguments[0];
                                            // Press Tab to move to next field naturally
                                            var tabEvent = new KeyboardEvent('keydown', {
                                                key: 'Tab',
                                                code: 'Tab',
                                                keyCode: 9,
                                                which: 9,
                                                bubbles: true
                                            });
                                            elem.dispatchEvent(tabEvent);
                                            
                                            var tabEventUp = new KeyboardEvent('keyup', {
                                                key: 'Tab',
                                                code: 'Tab',
                                                keyCode: 9,
                                                which: 9,
                                                bubbles: true
                                            });
                                            elem.dispatchEvent(tabEventUp);
                                            
                                            console.log('Tab key pressed after zip code');
                                            
                                            // Double-check zip value after Tab
                                            setTimeout(function() {
                                                if (window.geicoZipElement && window.geicoZipElement.value !== window.geicoZipValue) {
                                                    console.log('Zip cleared after Tab! Refilling...');
                                                    window.geicoZipElement.value = window.geicoZipValue;
                                                    window.geicoZipElement.dispatchEvent(new Event('input', { bubbles: true }));
                                                    window.geicoZipElement.dispatchEvent(new Event('change', { bubbles: true }));
                                                }
                                            }, 100);
                                        """, zip_elem)
                                        print("[DEBUG] Tab key pressed successfully")
                                        time.sleep(1)
                                    except Exception as tab_error:
                                        print(f"[DEBUG] Error pressing Tab: {tab_error}")
                                    
                                    # Now look for USDOT field to click and fill
                                    print("[DEBUG] Looking for USDOT field...")
                                    time.sleep(2)  # Wait for page to update after background click
                                    
                                    # More comprehensive USDOT search
                                    usdot_elements = driver.find_elements(By.XPATH,
                                        "//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dot')] | " +
                                        "//input[contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dot')] | " +
                                        "//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dot')] | " +
                                        "//input[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'dot')] | " +
                                        "//input[@type='text' or @type='number']"  # Get all text/number inputs as fallback
                                    )
                                    
                                    print(f"[DEBUG] Found {len(usdot_elements)} potential USDOT fields")
                                    
                                    usdot_filled = False
                                    for idx, usdot_elem in enumerate(usdot_elements):
                                        if usdot_elem.is_displayed() and usdot_elem.is_enabled():
                                            try:
                                                elem_name = usdot_elem.get_attribute('name') or ''
                                                elem_id = usdot_elem.get_attribute('id') or ''
                                                elem_placeholder = usdot_elem.get_attribute('placeholder') or ''
                                                elem_value = usdot_elem.get_attribute('value') or ''
                                                print(f"[DEBUG] USDOT field {idx}: name='{elem_name}', id='{elem_id}', placeholder='{elem_placeholder}', value='{elem_value}'")
                                                
                                                # Skip if this is the zip field we just filled
                                                if elem_value == '44256' or 'zip' in elem_name.lower() or 'zip' in elem_id.lower():
                                                    print(f"[DEBUG] Skipping field {idx} - appears to be zip field")
                                                    continue
                                                
                                                # Check if this looks like a USDOT field
                                                if ('dot' in elem_name.lower() or 'dot' in elem_id.lower() or 
                                                    'dot' in elem_placeholder.lower() or
                                                    (elem_value == '' and idx > 0)):  # Empty field after zip
                                                    
                                                    print(f"[DEBUG] Field {idx} appears to be USDOT field - clicking and filling")
                                                    
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
                                                
                                                time.sleep(0.5)
                                                
                                                # Fill USDOT number
                                                print("[DEBUG] Filling USDOT number 3431557")
                                                driver.execute_script("""
                                                    var elem = arguments[0];
                                                    elem.value = '';
                                                    elem.value = '3431557';
                                                    elem.dispatchEvent(new Event('input', { bubbles: true }));
                                                    elem.dispatchEvent(new Event('change', { bubbles: true }));
                                                    console.log('USDOT number 3431557 entered');
                                                """, usdot_elem)
                                                
                                                print("[DEBUG] Successfully filled USDOT number")
                                                current_status = "USDOT filled - pressing Enter"
                                                
                                                # Press Enter after USDOT
                                                time.sleep(0.5)
                                                print("[DEBUG] Pressing Enter key after USDOT")
                                                try:
                                                    driver.execute_script("""
                                                        var elem = arguments[0];
                                                        var enterEvent = new KeyboardEvent('keydown', {
                                                            key: 'Enter',
                                                            code: 'Enter',
                                                            keyCode: 13,
                                                            which: 13,
                                                            bubbles: true
                                                        });
                                                        elem.dispatchEvent(enterEvent);
                                                        
                                                        var enterEventUp = new KeyboardEvent('keyup', {
                                                            key: 'Enter',
                                                            code: 'Enter',
                                                            keyCode: 13,
                                                            which: 13,
                                                            bubbles: true
                                                        });
                                                        elem.dispatchEvent(enterEventUp);
                                                        
                                                        console.log('Enter key pressed after USDOT');
                                                    """, usdot_elem)
                                                    print("[DEBUG] Enter key pressed successfully after USDOT")
                                                except Exception as enter_error:
                                                    print(f"[DEBUG] Error pressing Enter after USDOT: {enter_error}")
                                                
                                                # Click background after Enter
                                                time.sleep(0.5)
                                                print("[DEBUG] Clicking background after USDOT Enter")
                                                try:
                                                    body = driver.find_element(By.TAG_NAME, "body")
                                                    driver.execute_script("""
                                                        var body = arguments[0];
                                                        var x = window.innerWidth / 2;
                                                        var y = 150; // Click middle of page
                                                        var clickEvent = new MouseEvent('click', {
                                                            view: window,
                                                            bubbles: true,
                                                            cancelable: true,
                                                            clientX: x,
                                                            clientY: y
                                                        });
                                                        body.dispatchEvent(clickEvent);
                                                        console.log('Background clicked after USDOT Enter');
                                                    """, body)
                                                    print("[DEBUG] Background clicked successfully after USDOT")
                                                    
                                                    # Check what happened to zip field
                                                    time.sleep(1)
                                                    print("[DEBUG] Checking zip field status after USDOT entry...")
                                                    try:
                                                        zip_check_elements = driver.find_elements(By.XPATH,
                                                            "//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'zip') or " +
                                                            "contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'zip')]"
                                                        )
                                                        for zip_check in zip_check_elements:
                                                            if zip_check.is_displayed():
                                                                zip_value = zip_check.get_attribute('value') or ''
                                                                zip_name = zip_check.get_attribute('name') or ''
                                                                print(f"[DEBUG] Zip field '{zip_name}' value after USDOT: '{zip_value}'")
                                                                if zip_value == '':
                                                                    print("[DEBUG] WARNING: Zip field was cleared!")
                                                                    # Store reference for periodic scanner to refill
                                                                    driver.execute_script("window.zipWasCleared = true;")
                                                    except Exception as check_error:
                                                        print(f"[DEBUG] Error checking zip field: {check_error}")
                                                        
                                                except Exception as bg_error:
                                                    print(f"[DEBUG] Error clicking background after USDOT: {bg_error}")
                                                
                                                # Wait a moment then look for Check USDOT button
                                                time.sleep(2)
                                                
                                                # Go back to zip field and double-click + Enter as final step
                                                print("[DEBUG] Going back to zip field for final double-click and Enter...")
                                                try:
                                                    # Re-find zip field
                                                    zip_recheck = driver.find_elements(By.XPATH,
                                                        "//input[contains(translate(@name, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'zip') or " +
                                                        "contains(translate(@id, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'zip')]"
                                                    )
                                                    
                                                    for zip_field in zip_recheck:
                                                        if zip_field.is_displayed() and '44256' in (zip_field.get_attribute('value') or ''):
                                                            print("[DEBUG] Found zip field with 44256 - double-clicking and pressing Enter")
                                                            driver.execute_script("""
                                                                var elem = arguments[0];
                                                                elem.scrollIntoView({block: 'center'});
                                                                
                                                                // Double-click
                                                                var dblClickEvent = new MouseEvent('dblclick', {
                                                                    view: window,
                                                                    bubbles: true,
                                                                    cancelable: true
                                                                });
                                                                elem.dispatchEvent(dblClickEvent);
                                                                elem.click();
                                                                elem.click();
                                                                
                                                                // Press Enter
                                                                setTimeout(function() {
                                                                    var enterEvent = new KeyboardEvent('keydown', {
                                                                        key: 'Enter',
                                                                        code: 'Enter',
                                                                        keyCode: 13,
                                                                        which: 13,
                                                                        bubbles: true
                                                                    });
                                                                    elem.dispatchEvent(enterEvent);
                                                                    console.log('Final zip double-click and Enter completed');
                                                                }, 500);
                                                            """, zip_field)
                                                            break
                                                except Exception as e:
                                                    print(f"[DEBUG] Error in final zip double-click: {e}")
                                                
                                                time.sleep(2)
                                                
                                                print("[DEBUG] Looking for Check USDOT button...")
                                                check_buttons = driver.find_elements(By.XPATH,
                                                    "//button[contains(text(), 'Check USDOT')] | " +
                                                    "//button[contains(text(), 'CHECK USDOT')] | " +
                                                    "//button[contains(@aria-label, 'Check USDOT')] | " +
                                                    "//input[@type='button' and contains(@value, 'Check USDOT')] | " +
                                                    "//div[@role='button' and contains(text(), 'Check USDOT')]"
                                                )
                                                
                                                print(f"[DEBUG] Found {len(check_buttons)} Check USDOT buttons")
                                                
                                                for check_btn in check_buttons:
                                                    if check_btn.is_displayed() and check_btn.is_enabled():
                                                        try:
                                                            # Check if button is blue/active
                                                            btn_style = check_btn.get_attribute('style') or ''
                                                            btn_class = check_btn.get_attribute('class') or ''
                                                            print(f"[DEBUG] Check button style: {btn_style[:50]}..., class: {btn_class}")
                                                            
                                                            # Highlight and click the button
                                                            driver.execute_script("""
                                                                var btn = arguments[0];
                                                                btn.style.border = '3px solid red';
                                                                btn.scrollIntoView({block: 'center'});
                                                                btn.click();
                                                                console.log('Check USDOT button clicked');
                                                            """, check_btn)
                                                            
                                                            print("[DEBUG] Successfully clicked Check USDOT button")
                                                            current_status = "Check USDOT button clicked"
                                                            check_usdot_clicked = True
                                                            last_zip_check_time = time.time()  # Start the timer
                                                            break
                                                        except Exception as btn_error:
                                                            print(f"[DEBUG] Error clicking Check button: {btn_error}")
                                                    
                                                    usdot_filled = True
                                                    break
                                            except Exception as usdot_error:
                                                print(f"[DEBUG] Error clicking USDOT field: {usdot_error}")
                                    
                                    if not usdot_filled:
                                        print("[DEBUG] WARNING: Could not find or fill USDOT field!")
                                        print("[DEBUG] Continuing anyway...")
                                    
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
                commercial_check_counter += 1  # Increment Commercial Auto check counter
                current_time = time.time()
                if current_time - last_fps_calculation_time >= 1.0:
                    fps_counter = frame_count
                    frame_count = 0
                    last_fps_calculation_time = current_time
                
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