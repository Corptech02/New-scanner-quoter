#!/usr/bin/env python3
"""
Geico Auto Quota Scanner - Commercial Auto Fix
Enhanced version with reliable commercial auto/trucking tab clicking
"""

from flask import Flask, render_template_string, jsonify, Response, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
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
current_status = "Ready to scan"
commercial_auto_clicked = False
commercial_click_attempts = 0
last_commercial_check = 0

# Enhanced HTML template with force commercial auto button
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
            --danger-bg: #dc3545;
            --danger-bg-hover: #c82333;
            --success-bg: #28a745;
            --success-bg-hover: #218838;
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
            --danger-bg: #ff4444;
            --danger-bg-hover: #cc0000;
            --success-bg: #44ff44;
            --success-bg-hover: #00cc00;
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
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            gap: 20px;
        }
        
        .button {
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            border-radius: 5px;
            cursor: pointer;
            transition: background-color 0.3s;
            color: white;
        }
        
        .start-button {
            background-color: var(--button-bg);
        }
        
        .start-button:hover {
            background-color: var(--button-bg-hover);
        }
        
        .start-button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        
        .force-commercial-button {
            background-color: var(--danger-bg);
        }
        
        .force-commercial-button:hover {
            background-color: var(--danger-bg-hover);
        }
        
        .force-commercial-button:disabled {
            background-color: #999;
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
        
        .status {
            text-align: center;
            margin-bottom: 20px;
            font-size: 16px;
            color: var(--text-secondary);
            transition: color 0.3s ease;
        }
        
        .screenshot-container {
            background: var(--container-bg);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            transition: background-color 0.3s ease;
            position: relative;
        }
        
        #screenshot {
            max-width: 100%;
            height: auto;
            border-radius: 5px;
            box-shadow: 0 2px 10px var(--shadow-color);
            display: block;
            margin: 0 auto;
            cursor: pointer;
            position: relative;
        }
        
        #overlay {
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            pointer-events: none;
            z-index: 10;
        }
        
        .detected-elements {
            margin-top: 20px;
            padding: 20px;
            background: var(--container-bg);
            border-radius: 8px;
            transition: background-color 0.3s ease;
        }
        
        .detected-elements h3 {
            margin-top: 0;
            color: var(--text-primary);
            transition: color 0.3s ease;
        }
        
        .element-list {
            list-style: none;
            padding: 0;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .element-list li {
            padding: 8px 12px;
            margin: 4px 0;
            background: var(--bg-secondary);
            border-radius: 4px;
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
            cursor: pointer;
            color: var(--text-primary);
        }
        
        .element-list li:hover {
            background: var(--bg-primary);
            transform: translateX(5px);
        }
        
        .fps-counter {
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 14px;
            z-index: 1000;
        }
        
        .commercial-status {
            text-align: center;
            margin: 10px 0;
            font-size: 14px;
            padding: 10px;
            border-radius: 5px;
            background-color: var(--container-bg);
            color: var(--text-secondary);
        }
        
        .commercial-status.success {
            background-color: var(--success-bg);
            color: white;
        }
        
        .commercial-status.pending {
            background-color: var(--danger-bg);
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Geico Auto Quota Scanner</h1>
        <div class="controls">
            <button class="button start-button" id="startBtn" onclick="toggleScanning()">Start Quote</button>
            <button class="button force-commercial-button" id="forceCommercialBtn" onclick="forceCommercialClick()" disabled>Force Commercial Auto Click</button>
            <div class="theme-toggle" onclick="toggleTheme()">
                <div class="theme-toggle-slider"></div>
            </div>
        </div>
        <div class="status" id="status">Ready to scan</div>
        <div class="commercial-status" id="commercialStatus">Commercial Auto: Not Clicked</div>
        
        <div class="screenshot-container">
            <canvas id="overlay"></canvas>
            <img id="screenshot" src="/api/screenshot" alt="Screenshot" onclick="handleImageClick(event)">
        </div>
        
        <div class="detected-elements">
            <h3>Detected Elements</h3>
            <ul class="element-list" id="elementList"></ul>
        </div>
    </div>
    
    <div class="fps-counter" id="fpsCounter">FPS: 0</div>
    
    <script>
        let isScanning = false;
        let updateInterval;
        let lastFrameTime = 0;
        let frameCount = 0;
        let fps = 0;
        let detectedElements = [];
        
        function toggleScanning() {
            const btn = document.getElementById('startBtn');
            const forceBtn = document.getElementById('forceCommercialBtn');
            
            if (!isScanning) {
                btn.textContent = 'Stop Scanning';
                btn.style.backgroundColor = '#dc3545';
                forceBtn.disabled = false;
                isScanning = true;
                
                fetch('/start-scan', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        console.log('Scan started:', data);
                        startUpdating();
                    });
            } else {
                btn.textContent = 'Start Quote';
                btn.style.backgroundColor = '';
                forceBtn.disabled = true;
                isScanning = false;
                
                fetch('/stop-scan', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        console.log('Scan stopped:', data);
                        stopUpdating();
                    });
            }
        }
        
        function forceCommercialClick() {
            const forceBtn = document.getElementById('forceCommercialBtn');
            forceBtn.disabled = true;
            forceBtn.textContent = 'Clicking...';
            
            fetch('/force-commercial-click', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    console.log('Force commercial click result:', data);
                    forceBtn.textContent = 'Force Commercial Auto Click';
                    forceBtn.disabled = false;
                    
                    if (data.status === 'success') {
                        updateCommercialStatus('Commercial Auto: Clicked Successfully', 'success');
                    } else {
                        updateCommercialStatus('Commercial Auto: Click Failed - ' + data.message, 'pending');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    forceBtn.textContent = 'Force Commercial Auto Click';
                    forceBtn.disabled = false;
                });
        }
        
        function updateCommercialStatus(text, className) {
            const statusDiv = document.getElementById('commercialStatus');
            statusDiv.textContent = text;
            statusDiv.className = 'commercial-status ' + (className || '');
        }
        
        function startUpdating() {
            updateInterval = setInterval(() => {
                updateScreenshot();
                updateElements();
                updateStatus();
                updateCommercialClickStatus();
            }, 100);
        }
        
        function stopUpdating() {
            if (updateInterval) {
                clearInterval(updateInterval);
            }
        }
        
        function updateScreenshot() {
            const img = document.getElementById('screenshot');
            const currentTime = Date.now();
            
            img.src = '/api/screenshot?t=' + currentTime;
            
            img.onload = function() {
                updateFPS();
                drawOverlay();
            };
        }
        
        function updateElements() {
            fetch('/api/elements')
                .then(response => response.json())
                .then(data => {
                    detectedElements = data.elements;
                    updateElementList(data.elements);
                });
        }
        
        function updateStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('status').textContent = data.status;
                });
        }
        
        function updateCommercialClickStatus() {
            fetch('/api/commercial-status')
                .then(response => response.json())
                .then(data => {
                    if (data.clicked) {
                        updateCommercialStatus('Commercial Auto: Clicked (Attempts: ' + data.attempts + ')', 'success');
                    } else {
                        updateCommercialStatus('Commercial Auto: Not Clicked (Attempts: ' + data.attempts + ')', 'pending');
                    }
                });
        }
        
        function updateElementList(elements) {
            const list = document.getElementById('elementList');
            list.innerHTML = '';
            
            elements.forEach((element, index) => {
                const li = document.createElement('li');
                li.textContent = element.label;
                li.onclick = () => clickElement(element);
                list.appendChild(li);
            });
        }
        
        function drawOverlay() {
            const canvas = document.getElementById('overlay');
            const ctx = canvas.getContext('2d');
            const img = document.getElementById('screenshot');
            
            canvas.width = img.width;
            canvas.height = img.height;
            
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            detectedElements.forEach(element => {
                ctx.strokeStyle = 'red';
                ctx.lineWidth = 3;
                ctx.strokeRect(element.x, element.y, element.width, element.height);
                
                ctx.fillStyle = 'rgba(255, 0, 0, 0.1)';
                ctx.fillRect(element.x, element.y, element.width, element.height);
                
                ctx.fillStyle = 'red';
                ctx.font = 'bold 14px Arial';
                ctx.fillText(element.label, element.x, element.y - 5);
            });
        }
        
        function handleImageClick(event) {
            const img = event.target;
            const rect = img.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;
            
            const scaleX = img.naturalWidth / img.width;
            const scaleY = img.naturalHeight / img.height;
            
            const realX = x * scaleX;
            const realY = y * scaleY;
            
            for (let element of detectedElements) {
                if (realX >= element.x && realX <= element.x + element.width &&
                    realY >= element.y && realY <= element.y + element.height) {
                    clickElement(element);
                    return;
                }
            }
        }
        
        function clickElement(element) {
            console.log('Clicking element:', element);
            
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
            });
        }
        
        function updateFPS() {
            frameCount++;
            const currentTime = Date.now();
            
            if (currentTime - lastFrameTime >= 1000) {
                fps = frameCount;
                frameCount = 0;
                lastFrameTime = currentTime;
                
                document.getElementById('fpsCounter').textContent = 'FPS: ' + fps;
            }
        }
        
        function toggleTheme() {
            document.body.classList.toggle('dark-theme');
            localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
        }
        
        if (localStorage.getItem('theme') === 'dark') {
            document.body.classList.add('dark-theme');
        }
        
        window.addEventListener('beforeunload', () => {
            if (isScanning) {
                fetch('/stop-scan', { method: 'POST' });
            }
        });
    </script>
</body>
</html>
'''

def kill_existing_chrome():
    """Kill any existing Chrome processes to avoid conflicts"""
    try:
        subprocess.run(['pkill', '-f', 'chrome'], capture_output=True)
        subprocess.run(['pkill', '-f', 'chromium'], capture_output=True)
        time.sleep(2)
    except:
        pass

def setup_driver():
    """Setup Chrome driver with appropriate options"""
    global driver
    
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    # Initialize tracking variables
    driver.execute_script("""
        window.commercialAutoClicked = false;
        window.commercialAutoTabActive = false;
        window.lastCommercialClickTime = 0;
        window.commercialClickAttempts = 0;
    """)

def check_and_click_commercial_auto():
    """Enhanced function to check and click Commercial Auto/Trucking tab"""
    global driver, current_status, commercial_auto_clicked, commercial_click_attempts
    
    if not driver:
        return False
    
    try:
        # Check if we've already successfully clicked
        if driver.execute_script("return window.commercialAutoTabActive || false"):
            return True
        
        # Wait for page stability
        time.sleep(1)
        
        print(f"[DEBUG] Checking for Commercial Auto/Trucking tab...")
        current_url = driver.current_url
        
        # Multiple strategies to find the element
        strategies = [
            # Strategy 1: Exact text match
            {
                'xpath': "//a[normalize-space(.)='Commercial Auto/Trucking'] | //button[normalize-space(.)='Commercial Auto/Trucking'] | //div[@role='button' and normalize-space(.)='Commercial Auto/Trucking']",
                'name': 'exact_text'
            },
            # Strategy 2: Contains text
            {
                'xpath': "//a[contains(., 'Commercial Auto/Trucking')] | //button[contains(., 'Commercial Auto/Trucking')] | //div[contains(@class, 'tab') and contains(., 'Commercial Auto/Trucking')]",
                'name': 'contains_text'
            },
            # Strategy 3: Partial matches
            {
                'xpath': "//*[contains(text(), 'Commercial Auto') and contains(text(), 'Trucking')]",
                'name': 'partial_match'
            },
            # Strategy 4: Class-based search
            {
                'xpath': "//*[contains(@class, 'product') and contains(., 'Commercial')]",
                'name': 'class_based'
            }
        ]
        
        for strategy in strategies:
            try:
                elements = driver.find_elements(By.XPATH, strategy['xpath'])
                print(f"[DEBUG] Strategy '{strategy['name']}' found {len(elements)} elements")
                
                if elements:
                    # Find the best element to click
                    best_element = None
                    for elem in elements:
                        try:
                            if elem.is_displayed() and elem.is_enabled():
                                elem_text = elem.text.strip()
                                if 'Commercial Auto' in elem_text or 'Trucking' in elem_text:
                                    best_element = elem
                                    break
                        except:
                            continue
                    
                    if best_element:
                        print(f"[DEBUG] Found clickable element: '{best_element.text.strip()}'")
                        current_status = "Clicking Commercial Auto/Trucking..."
                        
                        # Try multiple click methods
                        click_success = False
                        
                        # Method 1: JavaScript click with checks
                        try:
                            driver.execute_script("""
                                var elem = arguments[0];
                                var rect = elem.getBoundingClientRect();
                                console.log('Element position:', rect);
                                
                                // Scroll into view
                                elem.scrollIntoView({block: 'center', behavior: 'smooth'});
                                
                                // Wait for scroll
                                return new Promise(resolve => {
                                    setTimeout(() => {
                                        // Click the element
                                        elem.click();
                                        
                                        // Mark as clicked
                                        window.commercialAutoClicked = true;
                                        window.commercialAutoTabActive = true;
                                        window.lastCommercialClickTime = Date.now();
                                        window.commercialClickAttempts++;
                                        
                                        console.log('Commercial Auto clicked successfully');
                                        resolve(true);
                                    }, 500);
                                });
                            """, best_element)
                            click_success = True
                            print("[DEBUG] JavaScript click successful")
                        except Exception as e:
                            print(f"[DEBUG] JavaScript click failed: {e}")
                        
                        # Method 2: Action chains click
                        if not click_success:
                            try:
                                actions = ActionChains(driver)
                                actions.move_to_element(best_element).click().perform()
                                driver.execute_script("""
                                    window.commercialAutoClicked = true;
                                    window.commercialAutoTabActive = true;
                                    window.lastCommercialClickTime = Date.now();
                                    window.commercialClickAttempts++;
                                """)
                                click_success = True
                                print("[DEBUG] Action chains click successful")
                            except Exception as e:
                                print(f"[DEBUG] Action chains click failed: {e}")
                        
                        # Method 3: Direct click
                        if not click_success:
                            try:
                                best_element.click()
                                driver.execute_script("""
                                    window.commercialAutoClicked = true;
                                    window.commercialAutoTabActive = true;
                                    window.lastCommercialClickTime = Date.now();
                                    window.commercialClickAttempts++;
                                """)
                                click_success = True
                                print("[DEBUG] Direct click successful")
                            except Exception as e:
                                print(f"[DEBUG] Direct click failed: {e}")
                        
                        if click_success:
                            commercial_auto_clicked = True
                            commercial_click_attempts += 1
                            current_status = "Commercial Auto/Trucking clicked - verifying..."
                            
                            # Wait for page changes
                            time.sleep(2)
                            
                            # Verify the click worked
                            new_url = driver.current_url
                            page_changed = new_url != current_url
                            
                            # Check for commercial content
                            page_source = driver.page_source.lower()
                            has_commercial_content = 'commercial' in page_source or 'trucking' in page_source
                            
                            # Additional verification - check if tab is active
                            tab_active = driver.execute_script("""
                                // Look for active tab indicators
                                var activeTab = document.querySelector('.active[class*="commercial"], .selected[class*="commercial"], [aria-selected="true"][class*="commercial"]');
                                if (activeTab) return true;
                                
                                // Check if URL contains commercial
                                if (window.location.href.toLowerCase().includes('commercial')) return true;
                                
                                // Check page title
                                if (document.title.toLowerCase().includes('commercial')) return true;
                                
                                return false;
                            """)
                            
                            if page_changed or has_commercial_content or tab_active:
                                print("[DEBUG] Commercial Auto tab successfully activated")
                                current_status = "On Commercial Auto/Trucking page"
                                
                                # Set persistent flag
                                driver.execute_script("window.commercialAutoTabActive = true;")
                                return True
                            else:
                                print("[DEBUG] Click may not have activated the tab properly")
                                current_status = "Commercial Auto click needs retry"
                                # Reset the flag for retry
                                driver.execute_script("window.commercialAutoTabActive = false;")
                        
                        return click_success
                        
            except Exception as e:
                print(f"[DEBUG] Error with strategy '{strategy['name']}': {e}")
                continue
        
        print("[DEBUG] No Commercial Auto/Trucking element found with any strategy")
        return False
        
    except Exception as e:
        print(f"[DEBUG] Error in check_and_click_commercial_auto: {e}")
        import traceback
        traceback.print_exc()
        return False

def force_commercial_auto_click():
    """Force click Commercial Auto/Trucking with enhanced methods"""
    global driver, current_status
    
    if not driver:
        return {'status': 'error', 'message': 'No active browser session'}
    
    try:
        print("[DEBUG] Force commercial auto click initiated")
        current_status = "Force clicking Commercial Auto/Trucking..."
        
        # Reset the active flag to force re-click
        driver.execute_script("window.commercialAutoTabActive = false;")
        
        # Try the enhanced click function
        success = check_and_click_commercial_auto()
        
        if success:
            return {'status': 'success', 'message': 'Commercial Auto/Trucking clicked successfully'}
        else:
            # If standard method fails, try more aggressive approaches
            print("[DEBUG] Standard click failed, trying aggressive methods...")
            
            # Aggressive method 1: Click all possible commercial elements
            aggressive_success = driver.execute_script("""
                var clicked = false;
                var selectors = [
                    'a:contains("Commercial Auto")',
                    'button:contains("Commercial Auto")',
                    'div:contains("Commercial Auto")',
                    '[class*="commercial"]',
                    '[id*="commercial"]',
                    '[href*="commercial"]'
                ];
                
                // jQuery-like contains selector
                function contains(selector, text) {
                    var elements = document.querySelectorAll(selector.split(':')[0]);
                    var matches = [];
                    for (var i = 0; i < elements.length; i++) {
                        if (elements[i].textContent.includes(text)) {
                            matches.push(elements[i]);
                        }
                    }
                    return matches;
                }
                
                for (var i = 0; i < selectors.length; i++) {
                    var elements;
                    if (selectors[i].includes(':contains')) {
                        elements = contains(selectors[i], "Commercial Auto");
                    } else {
                        elements = document.querySelectorAll(selectors[i]);
                    }
                    
                    for (var j = 0; j < elements.length; j++) {
                        var elem = elements[j];
                        if (elem && elem.offsetParent !== null) {  // Is visible
                            console.log('Attempting to click:', elem);
                            try {
                                elem.scrollIntoView({block: 'center'});
                                elem.click();
                                clicked = true;
                                window.commercialAutoClicked = true;
                                window.commercialAutoTabActive = true;
                                console.log('Successfully clicked:', elem);
                                break;
                            } catch (e) {
                                console.log('Click failed:', e);
                            }
                        }
                    }
                    if (clicked) break;
                }
                
                return clicked;
            """)
            
            if aggressive_success:
                current_status = "Commercial Auto/Trucking force clicked"
                return {'status': 'success', 'message': 'Force clicked using aggressive method'}
            else:
                current_status = "Commercial Auto/Trucking not found"
                return {'status': 'error', 'message': 'Could not find Commercial Auto/Trucking element'}
            
    except Exception as e:
        print(f"[DEBUG] Error in force_commercial_auto_click: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e)}

def scan_loop():
    """Main scanning loop with enhanced commercial auto detection"""
    global driver, is_scanning, current_screenshot, detected_elements, fps_counter, current_status
    global commercial_auto_clicked, last_commercial_check
    
    kill_existing_chrome()
    setup_driver()
    
    try:
        driver.get('https://gateway.geico.com/')
        print(f"[DEBUG] Navigated to: {driver.current_url}")
        current_status = "Loading Geico gateway..."
        
        while is_scanning:
            try:
                # Take screenshot
                screenshot = driver.get_screenshot_as_png()
                current_screenshot = screenshot
                fps_counter += 1
                
                # Clear previous detected elements
                detected_elements = []
                
                # Check current URL for context
                current_url = driver.current_url
                
                # Check if we need to click Commercial Auto (every 5 seconds)
                current_time = time.time()
                if current_time - last_commercial_check > 5:
                    last_commercial_check = current_time
                    
                    # Check if we're past login and Commercial Auto hasn't been clicked
                    if not driver.execute_script("return window.commercialAutoTabActive || false"):
                        # Check if we're on a page where Commercial Auto tab might appear
                        if 'login' not in current_url.lower() and 'gateway' not in current_url.lower():
                            print("[DEBUG] Checking for Commercial Auto tab...")
                            check_and_click_commercial_auto()
                
                # Detect elements based on page context
                if 'gateway.geico.com' in current_url:
                    # Login page elements
                    detect_login_elements()
                else:
                    # Other page elements
                    detect_general_elements()
                
                time.sleep(0.1)  # Small delay to prevent overwhelming the system
                
            except Exception as e:
                print(f"Error in scan loop: {e}")
                time.sleep(1)
                
    except Exception as e:
        print(f"Fatal error in scan_loop: {e}")
    finally:
        if driver:
            driver.quit()

def detect_login_elements():
    """Detect login page elements"""
    global detected_elements, current_status
    
    try:
        # Username field
        username_fields = driver.find_elements(By.XPATH, "//input[@type='text' or @type='email' or @name='username' or @id='username' or contains(@placeholder, 'Username')]")
        for field in username_fields:
            if field.is_displayed():
                rect = field.rect
                detected_elements.append({
                    'label': 'Username Field',
                    'x': rect['x'],
                    'y': rect['y'],
                    'width': rect['width'],
                    'height': rect['height'],
                    'element': field
                })
        
        # Password field
        password_fields = driver.find_elements(By.XPATH, "//input[@type='password']")
        for field in password_fields:
            if field.is_displayed():
                rect = field.rect
                detected_elements.append({
                    'label': 'Password Field',
                    'x': rect['x'],
                    'y': rect['y'],
                    'width': rect['width'],
                    'height': rect['height'],
                    'element': field
                })
        
        # Login button
        login_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Log') or contains(text(), 'Sign')]")
        for button in login_buttons:
            if button.is_displayed():
                rect = button.rect
                detected_elements.append({
                    'label': 'Login Button',
                    'x': rect['x'],
                    'y': rect['y'],
                    'width': rect['width'],
                    'height': rect['height'],
                    'element': button
                })
                
    except Exception as e:
        print(f"Error detecting login elements: {e}")

def detect_general_elements():
    """Detect general page elements including Commercial Auto"""
    global detected_elements, current_status
    
    try:
        # Commercial Auto/Trucking elements - HIGH PRIORITY
        commercial_selectors = [
            "//a[contains(., 'Commercial Auto/Trucking')]",
            "//button[contains(., 'Commercial Auto/Trucking')]",
            "//div[contains(., 'Commercial Auto/Trucking') and (@role='button' or @onclick or contains(@class, 'tab'))]",
            "//*[contains(@class, 'product') and contains(., 'Commercial')]"
        ]
        
        for selector in commercial_selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                if elem.is_displayed():
                    rect = elem.rect
                    detected_elements.append({
                        'label': 'Commercial Auto/Trucking',
                        'x': rect['x'],
                        'y': rect['y'],
                        'width': rect['width'],
                        'height': rect['height'],
                        'element': elem,
                        'priority': 'high'
                    })
        
        # Other important elements
        # Quote buttons
        quote_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Quote') or contains(text(), 'Start')]")
        for button in quote_buttons:
            if button.is_displayed():
                rect = button.rect
                detected_elements.append({
                    'label': 'Quote Button',
                    'x': rect['x'],
                    'y': rect['y'],
                    'width': rect['width'],
                    'height': rect['height'],
                    'element': button
                })
                
    except Exception as e:
        print(f"Error detecting general elements: {e}")

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/start-scan', methods=['POST'])
def start_scan():
    global is_scanning, scan_thread, commercial_auto_clicked, commercial_click_attempts
    
    if not is_scanning:
        is_scanning = True
        commercial_auto_clicked = False
        commercial_click_attempts = 0
        scan_thread = threading.Thread(target=scan_loop)
        scan_thread.daemon = True
        scan_thread.start()
        return jsonify({'status': 'success', 'message': 'Scan started'})
    
    return jsonify({'status': 'error', 'message': 'Scan already running'})

@app.route('/stop-scan', methods=['POST'])
def stop_scan():
    global is_scanning, driver
    
    is_scanning = False
    if driver:
        driver.quit()
        driver = None
    
    return jsonify({'status': 'success', 'message': 'Scan stopped'})

@app.route('/api/screenshot')
def get_screenshot():
    global current_screenshot
    
    if current_screenshot:
        return Response(current_screenshot, mimetype='image/png')
    else:
        # Return a placeholder image
        img = Image.new('RGB', (800, 600), color='gray')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return Response(buf.getvalue(), mimetype='image/png')

@app.route('/api/elements')
def get_elements():
    global detected_elements
    
    # Return elements without the selenium element object
    safe_elements = []
    for elem in detected_elements:
        safe_elem = {
            'label': elem['label'],
            'x': elem['x'],
            'y': elem['y'],
            'width': elem['width'],
            'height': elem['height']
        }
        if 'priority' in elem:
            safe_elem['priority'] = elem['priority']
        safe_elements.append(safe_elem)
    
    return jsonify({'elements': safe_elements})

@app.route('/api/status')
def get_status():
    global current_status
    return jsonify({'status': current_status})

@app.route('/api/commercial-status')
def get_commercial_status():
    global commercial_auto_clicked, commercial_click_attempts
    return jsonify({
        'clicked': commercial_auto_clicked,
        'attempts': commercial_click_attempts
    })

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
        driver.execute_script(f"""
            var x = {x};
            var y = {y};
            var element = document.elementFromPoint(x, y);
            if (element) {{
                element.click();
                console.log('Clicked element at', x, y);
            }}
        """)
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        print(f"Error clicking element: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/force-commercial-click', methods=['POST'])
def force_commercial_click_route():
    """API endpoint for force clicking Commercial Auto"""
    result = force_commercial_auto_click()
    return jsonify(result)

if __name__ == '__main__':
    print("Starting Geico Auto Quota Scanner...")
    print("Access the scanner at: https://localhost:5558")
    app.run(host='0.0.0.0', port=5558, debug=False, ssl_context='adhoc')