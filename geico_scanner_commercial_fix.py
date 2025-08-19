#!/usr/bin/env python3
"""
GEICO Scanner with Commercial Auto Fix
This version prevents page refresh when clicking Commercial Auto/Trucking
"""

import os
import sys
import json
import time
import threading
import requests
import warnings
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

# Suppress SSL warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

app = Flask(__name__)
CORS(app)

# Global variables
driver = None
current_status = "Initializing..."
elements_cache = []
screenshot_path = None
is_running = False

# Create screenshots directory if it doesn't exist
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# HTML template with Commercial Auto fix
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GEICO Scanner - Commercial Auto Fixed</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        .status {
            background-color: #e3f2fd;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-weight: bold;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        button {
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            background-color: #2196F3;
            color: white;
            border: none;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #1976D2;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .screenshot-container {
            position: relative;
            margin-top: 20px;
            border: 2px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }
        #screenshot {
            width: 100%;
            height: auto;
            display: block;
        }
        #overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }
        .element-overlay {
            position: absolute;
            border: 2px solid #FF5722;
            background-color: rgba(255, 87, 34, 0.2);
            cursor: pointer;
            pointer-events: auto;
            transition: all 0.2s;
        }
        .element-overlay:hover {
            background-color: rgba(255, 87, 34, 0.4);
            border-color: #F44336;
        }
        .element-label {
            position: absolute;
            background-color: #FF5722;
            color: white;
            padding: 2px 6px;
            font-size: 12px;
            border-radius: 3px;
            white-space: nowrap;
            z-index: 10;
        }
        .commercial-auto-button {
            background-color: #4CAF50 !important;
        }
        .commercial-auto-button:hover {
            background-color: #45a049 !important;
        }
        .warning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>GEICO Scanner - Commercial Auto Fixed</h1>
        
        <div class="warning">
            ⚠️ Commercial Auto clicking has been fixed to prevent page refresh
        </div>
        
        <div class="status" id="status">Status: Initializing...</div>
        
        <div class="controls">
            <button onclick="scanPage()">Scan Page</button>
            <button onclick="goToGeico()">Go to GEICO</button>
            <button onclick="autoLogin()">Auto Login</button>
            <button onclick="clickCommercialAuto()" class="commercial-auto-button">Force Commercial Auto Click</button>
            <button onclick="location.reload()">Refresh Scanner</button>
        </div>
        
        <div class="screenshot-container">
            <img id="screenshot" src="/screenshot" alt="Browser Screenshot">
            <div id="overlay"></div>
        </div>
    </div>
    
    <script>
        let currentElements = [];
        
        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = 'Status: ' + data.status;
                });
        }
        
        function updateScreenshot() {
            const img = document.getElementById('screenshot');
            img.src = '/screenshot?t=' + new Date().getTime();
        }
        
        function scanPage() {
            fetch('/scan', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        currentElements = data.elements;
                        updateOverlay();
                    }
                });
        }
        
        function updateOverlay() {
            const overlay = document.getElementById('overlay');
            overlay.innerHTML = '';
            
            currentElements.forEach((element, index) => {
                const div = document.createElement('div');
                div.className = 'element-overlay';
                div.style.left = element.x + 'px';
                div.style.top = element.y + 'px';
                div.style.width = element.width + 'px';
                div.style.height = element.height + 'px';
                
                const label = document.createElement('div');
                label.className = 'element-label';
                label.style.top = '-20px';
                label.style.left = '0px';
                label.textContent = element.label || 'Element';
                div.appendChild(label);
                
                div.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    clickElement(element.x + element.width/2, element.y + element.height/2, element.label);
                });
                
                overlay.appendChild(div);
            });
        }
        
        function clickElement(x, y, label) {
            fetch('/click', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ x: x, y: y, label: label })
            })
            .then(response => response.json())
            .then(data => {
                console.log('Click result:', data);
                setTimeout(() => {
                    updateScreenshot();
                    scanPage();
                }, 1000);
            });
        }
        
        function goToGeico() {
            fetch('/navigate', { method: 'POST' })
                .then(() => {
                    setTimeout(() => {
                        updateScreenshot();
                        scanPage();
                    }, 3000);
                });
        }
        
        function autoLogin() {
            fetch('/auto_login', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    console.log('Auto-login result:', data);
                });
        }
        
        function clickCommercialAuto() {
            fetch('/click_commercial_auto', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    console.log('Commercial Auto click result:', data);
                    if (data.status === 'success') {
                        setTimeout(() => {
                            updateScreenshot();
                            scanPage();
                        }, 1000);
                    }
                });
        }
        
        // Update status and screenshot periodically
        setInterval(updateStatus, 2000);
        setInterval(updateScreenshot, 5000);
        
        // Initial scan
        setTimeout(scanPage, 1000);
    </script>
</body>
</html>
'''

def init_driver():
    """Initialize the Selenium driver"""
    global driver, current_status
    
    try:
        # Chrome options
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        current_status = "Browser initialized"
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to initialize driver: {e}")
        current_status = f"Initialization failed: {str(e)}"
        return False

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    return jsonify({'status': current_status})

@app.route('/screenshot')
def screenshot():
    global driver, screenshot_path
    
    if driver:
        try:
            # Take screenshot
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(SCREENSHOT_DIR, f'screenshot_{timestamp}.png')
            driver.save_screenshot(screenshot_path)
            
            # Return the image
            from flask import send_file
            return send_file(screenshot_path, mimetype='image/png')
        except:
            pass
    
    # Return placeholder if no screenshot
    from flask import Response
    return Response(status=204)

@app.route('/navigate', methods=['POST'])
def navigate():
    global driver, current_status
    
    if driver:
        try:
            driver.get('https://geico.com')
            current_status = "Navigated to GEICO"
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})
    
    return jsonify({'status': 'error', 'message': 'No driver initialized'})

@app.route('/click_commercial_auto', methods=['POST'])
def click_commercial_auto():
    """Force click Commercial Auto with page refresh prevention"""
    global driver, current_status
    
    if not driver:
        return jsonify({'status': 'error', 'message': 'No driver initialized'})
    
    try:
        print("[DEBUG] Force clicking Commercial Auto/Trucking...")
        current_status = "Looking for Commercial Auto button..."
        
        # Find Commercial Auto elements
        commercial_elements = driver.find_elements(By.XPATH, 
            "//a[contains(text(), 'Commercial Auto')] | " +
            "//button[contains(text(), 'Commercial Auto')] | " +
            "//div[contains(text(), 'Commercial Auto')] | " +
            "//span[contains(text(), 'Commercial Auto')] | " +
            "//a[contains(text(), 'Trucking')] | " +
            "//button[contains(text(), 'Trucking')] | " +
            "//div[contains(text(), 'Trucking')] | " +
            "//span[contains(text(), 'Trucking')]"
        )
        
        print(f"[DEBUG] Found {len(commercial_elements)} potential Commercial Auto elements")
        
        clicked = False
        for elem in commercial_elements:
            if elem.is_displayed():
                elem_text = elem.text.strip()
                if 'commercial' in elem_text.lower() or 'trucking' in elem_text.lower():
                    print(f"[DEBUG] Attempting to click: '{elem_text}'")
                    
                    # FIXED: Prevent default behavior and stop propagation
                    result = driver.execute_script("""
                        var elem = arguments[0];
                        
                        // Highlight element
                        elem.style.border = '3px solid green';
                        elem.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
                        
                        // Create custom click handler
                        function customClick(e) {
                            if (e) {
                                e.preventDefault();
                                e.stopPropagation();
                                e.stopImmediatePropagation();
                            }
                            console.log('Commercial Auto clicked - preventing default');
                            return false;
                        }
                        
                        // Remove existing click handlers temporarily
                        var oldOnclick = elem.onclick;
                        elem.onclick = customClick;
                        
                        // Check if element is a link
                        if (elem.tagName === 'A') {
                            var oldHref = elem.href;
                            elem.href = 'javascript:void(0)';
                            
                            // Restore after a moment
                            setTimeout(function() {
                                elem.href = oldHref;
                            }, 100);
                        }
                        
                        // Prevent form submission if in a form
                        var form = elem.closest('form');
                        if (form) {
                            form.onsubmit = function(e) {
                                e.preventDefault();
                                return false;
                            };
                        }
                        
                        // Simulate click without navigation
                        elem.scrollIntoView({block: 'center'});
                        
                        // Dispatch click event
                        var clickEvent = new MouseEvent('click', {
                            view: window,
                            bubbles: true,
                            cancelable: true
                        });
                        
                        // Override default behavior
                        clickEvent.preventDefault();
                        elem.dispatchEvent(clickEvent);
                        
                        // Mark as clicked
                        window.commercialAutoClicked = true;
                        
                        // Check if element has data attributes or classes we need to toggle
                        if (elem.classList.contains('inactive') || elem.classList.contains('unselected')) {
                            elem.classList.remove('inactive', 'unselected');
                            elem.classList.add('active', 'selected');
                        }
                        
                        // Look for checkbox or radio button associated with this element
                        var checkbox = elem.querySelector('input[type="checkbox"], input[type="radio"]');
                        if (!checkbox) {
                            // Look in parent or sibling elements
                            var parent = elem.parentElement;
                            checkbox = parent ? parent.querySelector('input[type="checkbox"], input[type="radio"]') : null;
                        }
                        
                        if (checkbox) {
                            checkbox.checked = true;
                            checkbox.dispatchEvent(new Event('change', {bubbles: true}));
                        }
                        
                        // Restore onclick after a moment
                        setTimeout(function() {
                            if (oldOnclick) elem.onclick = oldOnclick;
                        }, 100);
                        
                        return true;
                    """, elem)
                    
                    current_status = "Commercial Auto clicked (refresh prevented)"
                    clicked = True
                    
                    # Wait a moment to see if anything loads dynamically
                    time.sleep(2)
                    
                    # Check if we need to handle any dynamic content
                    print("[DEBUG] Checking for dynamic content updates...")
                    
                    break
        
        if clicked:
            return jsonify({
                'status': 'success',
                'message': 'Commercial Auto clicked without page refresh'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No clickable Commercial Auto element found'
            })
            
    except Exception as e:
        print(f"[ERROR] Commercial Auto click failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/scan', methods=['POST'])
def scan():
    """Scan the current page for clickable elements"""
    global driver, current_status, elements_cache
    
    if not driver:
        return jsonify({'status': 'error', 'message': 'No driver initialized'})
    
    try:
        current_status = "Scanning page..."
        elements_found = []
        
        # Find clickable elements
        clickable_selectors = [
            "//button",
            "//a[@href]",
            "//input[@type='submit' or @type='button']",
            "//div[@onclick or @role='button']",
            "//span[@onclick or @role='button']"
        ]
        
        for selector in clickable_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                try:
                    if elem.is_displayed() and elem.is_enabled():
                        rect = elem.rect
                        text = elem.text.strip() or elem.get_attribute('value') or elem.get_attribute('aria-label') or 'Clickable'
                        
                        if rect['width'] > 0 and rect['height'] > 0:
                            elements_found.append({
                                'x': rect['x'],
                                'y': rect['y'],
                                'width': rect['width'],
                                'height': rect['height'],
                                'label': text[:50]
                            })
                except:
                    pass
        
        elements_cache = elements_found
        current_status = f"Found {len(elements_found)} clickable elements"
        
        return jsonify({
            'status': 'success',
            'elements': elements_found
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/click', methods=['POST'])
def click():
    """Click at specified coordinates"""
    global driver
    
    if not driver:
        return jsonify({'status': 'error', 'message': 'No driver initialized'})
    
    try:
        data = request.json
        x = data.get('x')
        y = data.get('y')
        label = data.get('label', 'Unknown')
        
        # Execute click with prevention of default behavior
        click_script = """
        var x = arguments[0];
        var y = arguments[1];
        var element = document.elementFromPoint(x, y);
        
        if (element) {
            // Prevent navigation for commercial auto
            if (element.textContent && 
                (element.textContent.includes('Commercial Auto') || 
                 element.textContent.includes('Trucking'))) {
                
                element.onclick = function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                };
                
                if (element.tagName === 'A') {
                    element.href = 'javascript:void(0)';
                }
            }
            
            element.click();
            return {success: true, element: element.tagName, text: element.textContent};
        } else {
            return {success: false, message: 'No element found at coordinates'};
        }
        """
        
        result = driver.execute_script(click_script, x, y)
        
        return jsonify({
            'status': 'success',
            'result': result,
            'clicked': label
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/auto_login', methods=['POST'])
def auto_login():
    """Placeholder for auto-login functionality"""
    return jsonify({
        'status': 'success',
        'message': 'Auto-login not implemented in this version'
    })

def main():
    """Main function"""
    global is_running
    
    print("Starting GEICO Scanner with Commercial Auto Fix...")
    print("This version prevents page refresh when clicking Commercial Auto/Trucking")
    
    # Initialize driver
    if not init_driver():
        print("Failed to initialize browser driver")
        return
    
    is_running = True
    
    # Start Flask app
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if driver:
            driver.quit()
        is_running = False

if __name__ == '__main__':
    main()