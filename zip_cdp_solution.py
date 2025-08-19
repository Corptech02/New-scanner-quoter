#!/usr/bin/env python3
"""
ZIP code solution using Chrome DevTools Protocol
This bypasses most bot detection by using native browser APIs
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json

def setup_undetected_driver():
    """
    Creates a Chrome driver with maximum stealth
    """
    options = Options()
    
    # Essential anti-detection arguments
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Connect to existing instance
    options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    driver = webdriver.Chrome(options=options)
    
    # Execute stealth scripts
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Fix Chrome automation
            window.navigator.chrome = {
                app: {},
                runtime: {}
            };
            
            // Fix permissions API
            if (navigator.permissions) {
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            }
            
            // Fix plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Fix languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        '''
    })
    
    return driver

def fill_zip_with_cdp(driver, zip_code="44256"):
    """
    Fills ZIP code using Chrome DevTools Protocol
    """
    print(f"[CDP] Filling ZIP code: {zip_code}")
    
    # First, find the ZIP field normally
    zip_field = None
    try:
        # Try multiple selectors
        selectors = [
            "//input[contains(@name, 'zip')]",
            "//input[contains(@id, 'zip')]",
            "//input[contains(@placeholder, 'ZIP')]",
            "//input[contains(@name, 'garage')]"
        ]
        
        for selector in selectors:
            elements = driver.find_elements(By.XPATH, selector)
            for elem in elements:
                if elem.is_displayed() and elem.is_enabled():
                    zip_field = elem
                    print(f"[CDP] Found ZIP field with selector: {selector}")
                    break
            if zip_field:
                break
    except:
        pass
    
    if not zip_field:
        print("[CDP] Could not find ZIP field!")
        return False
    
    # Get element info for CDP
    element_info = driver.execute_script("""
        var elem = arguments[0];
        var rect = elem.getBoundingClientRect();
        return {
            x: rect.left + rect.width/2,
            y: rect.top + rect.height/2,
            id: elem.id,
            name: elem.name
        };
    """, zip_field)
    
    # Use CDP to simulate real user input
    try:
        # Move mouse to element
        driver.execute_cdp_cmd('Input.dispatchMouseEvent', {
            'type': 'mouseMoved',
            'x': element_info['x'],
            'y': element_info['y']
        })
        time.sleep(0.1)
        
        # Click on element
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
        
        time.sleep(0.2)
        
        # Clear field with Ctrl+A and Delete
        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
            'type': 'keyDown',
            'modifiers': 2,  # Ctrl
            'key': 'a',
            'code': 'KeyA'
        })
        
        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
            'type': 'keyUp',
            'modifiers': 2,
            'key': 'a',
            'code': 'KeyA'
        })
        
        time.sleep(0.1)
        
        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
            'type': 'keyDown',
            'key': 'Delete',
            'code': 'Delete'
        })
        
        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
            'type': 'keyUp',
            'key': 'Delete',
            'code': 'Delete'
        })
        
        time.sleep(0.2)
        
        # Type each character
        for char in zip_code:
            # Key down
            driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
                'type': 'keyDown',
                'key': char,
                'code': f'Digit{char}',
                'text': char
            })
            
            # Char event (for older systems)
            driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
                'type': 'char',
                'text': char
            })
            
            # Key up
            driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
                'type': 'keyUp',
                'key': char,
                'code': f'Digit{char}'
            })
            
            # Human-like delay
            time.sleep(0.1 + (0.05 * (int(char) % 3)))
            print(f"[CDP] Typed: {char}")
        
        # Tab to trigger validation
        time.sleep(0.3)
        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
            'type': 'keyDown',
            'key': 'Tab',
            'code': 'Tab'
        })
        
        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
            'type': 'keyUp',
            'key': 'Tab',
            'code': 'Tab'
        })
        
        print("[CDP] ZIP code entry completed")
        
        # Check if state was populated
        time.sleep(1)
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
            print(f"[CDP] SUCCESS! State populated: {state_check}")
            return True
        else:
            print("[CDP] Warning: State not populated yet")
            return False
            
    except Exception as e:
        print(f"[CDP] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def integrate_cdp_solution():
    """
    Returns code to integrate CDP solution into scanner
    """
    return '''
# Enhanced ZIP entry using Chrome DevTools Protocol
print("[DEBUG] Using CDP method for undetected ZIP entry...")

try:
    # Get element position for CDP
    element_info = driver.execute_script("""
        var elem = arguments[0];
        var rect = elem.getBoundingClientRect();
        return {
            x: rect.left + rect.width/2,
            y: rect.top + rect.height/2
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
    
    time.sleep(0.2)
    
    # Clear and type using CDP
    for char in '44256':
        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
            'type': 'keyDown',
            'key': char,
            'code': f'Digit{char}',
            'text': char
        })
        
        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
            'type': 'char',
            'text': char
        })
        
        driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
            'type': 'keyUp',
            'key': char,
            'code': f'Digit{char}'
        })
        
        time.sleep(0.1)
    
    # Tab to validate
    driver.execute_cdp_cmd('Input.dispatchKeyEvent', {
        'type': 'keyDown',
        'key': 'Tab',
        'code': 'Tab'
    })
    
    print("[DEBUG] CDP ZIP entry completed")
    
except Exception as e:
    print(f"[DEBUG] CDP method failed: {e}")
    # Fallback to previous method
'''

if __name__ == "__main__":
    print("GEICO ZIP Code CDP Solution")
    print("===========================")
    
    try:
        # Setup undetected driver
        driver = setup_undetected_driver()
        
        # Check if webdriver is hidden
        is_hidden = driver.execute_script("return navigator.webdriver === undefined;")
        print(f"[CHECK] Webdriver hidden: {is_hidden}")
        
        # Apply the ZIP code fix
        success = fill_zip_with_cdp(driver)
        
        if success:
            print("\n[SUCCESS] ZIP code filled and state populated!")
        else:
            print("\n[PARTIAL] ZIP code filled but state not populated yet")
            print("This might be due to:")
            print("1. Network delay in validation")
            print("2. Additional validation requirements")
            print("3. Need to fill other fields first")
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()