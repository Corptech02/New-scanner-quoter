#!/usr/bin/env python3
"""
Ultimate ZIP code fix that monitors manual entry and replicates it exactly
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time

def install_zip_monitor(driver):
    """
    Installs comprehensive monitoring to understand what GEICO expects
    """
    monitor_script = """
    (function() {
        console.log('[ZIP MONITOR] Installing comprehensive monitoring system...');
        
        // Find the ZIP input field
        var zipInputs = document.querySelectorAll('input');
        var zipField = null;
        
        for (var i = 0; i < zipInputs.length; i++) {
            var input = zipInputs[i];
            var attrs = ['name', 'id', 'placeholder', 'aria-label'];
            var isZipField = false;
            
            attrs.forEach(function(attr) {
                var value = (input.getAttribute(attr) || '').toLowerCase();
                if (value.includes('zip') || value.includes('garage') || value.includes('postal')) {
                    isZipField = true;
                }
            });
            
            if (isZipField && input.type !== 'hidden') {
                zipField = input;
                console.log('[ZIP MONITOR] Found ZIP field:', {
                    name: input.name,
                    id: input.id,
                    type: input.type,
                    placeholder: input.placeholder
                });
                break;
            }
        }
        
        if (!zipField) {
            console.error('[ZIP MONITOR] No ZIP field found!');
            return null;
        }
        
        // Store original validation function
        window.zipFieldInfo = {
            field: zipField,
            originalValidation: null,
            validationCalls: [],
            ajaxCalls: []
        };
        
        // Check for validation functions
        var possibleHandlers = ['onchange', 'oninput', 'onblur', 'onfocus', 'onkeyup'];
        possibleHandlers.forEach(function(handler) {
            if (zipField[handler]) {
                console.log('[ZIP MONITOR] Found handler:', handler, zipField[handler].toString().substring(0, 100));
            }
        });
        
        // Check for jQuery validation
        if (window.jQuery && jQuery(zipField).data()) {
            var data = jQuery(zipField).data();
            console.log('[ZIP MONITOR] jQuery data:', Object.keys(data));
        }
        
        // Monitor XHR/Fetch for validation calls
        var originalXHR = window.XMLHttpRequest.prototype.open;
        window.XMLHttpRequest.prototype.open = function(method, url) {
            if (url.includes('zip') || url.includes('postal') || url.includes('location') || url.includes('validate')) {
                console.log('[ZIP MONITOR] XHR Call:', method, url);
                window.zipFieldInfo.ajaxCalls.push({method: method, url: url, timestamp: Date.now()});
            }
            return originalXHR.apply(this, arguments);
        };
        
        // Monitor all property access on the ZIP field
        var properties = ['value', 'validity', 'validationMessage'];
        properties.forEach(function(prop) {
            var originalDescriptor = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, prop);
            if (originalDescriptor) {
                Object.defineProperty(zipField, prop, {
                    get: function() {
                        var result = originalDescriptor.get.call(this);
                        if (prop === 'validity') {
                            console.log('[ZIP MONITOR] Validity check:', result);
                        }
                        return result;
                    },
                    set: function(val) {
                        console.log('[ZIP MONITOR] Setting', prop, 'to:', val);
                        return originalDescriptor.set.call(this, val);
                    }
                });
            }
        });
        
        // Function to get all event listeners (Chrome DevTools API)
        window.getZipEventListeners = function() {
            if (typeof getEventListeners !== 'undefined') {
                try {
                    var listeners = getEventListeners(zipField);
                    console.log('[ZIP MONITOR] Event listeners:', listeners);
                    return listeners;
                } catch (e) {}
            }
            return null;
        };
        
        // Create the perfect ZIP entry function
        window.perfectZipEntry = function(zipCode) {
            console.log('[ZIP PERFECT] Starting perfect ZIP entry for:', zipCode);
            
            var field = window.zipFieldInfo.field;
            
            // Step 1: Ensure field is ready
            field.scrollIntoView({behavior: 'smooth', block: 'center'});
            
            // Step 2: Mouse over (some forms track this)
            var rect = field.getBoundingClientRect();
            var mouseOverEvent = new MouseEvent('mouseover', {
                clientX: rect.left + rect.width / 2,
                clientY: rect.top + rect.height / 2,
                bubbles: true
            });
            field.dispatchEvent(mouseOverEvent);
            
            // Step 3: Click with full mouse sequence
            setTimeout(function() {
                // Mouse down
                field.dispatchEvent(new MouseEvent('mousedown', {
                    clientX: rect.left + rect.width / 2,
                    clientY: rect.top + rect.height / 2,
                    bubbles: true,
                    button: 0
                }));
                
                // Focus
                field.focus();
                
                // Mouse up
                field.dispatchEvent(new MouseEvent('mouseup', {
                    clientX: rect.left + rect.width / 2,
                    clientY: rect.top + rect.height / 2,
                    bubbles: true,
                    button: 0
                }));
                
                // Click
                field.click();
                
                // Clear any existing value properly
                setTimeout(function() {
                    // Select all
                    field.select();
                    
                    // Delete using key events
                    field.dispatchEvent(new KeyboardEvent('keydown', {
                        key: 'Delete',
                        keyCode: 46,
                        bubbles: true
                    }));
                    
                    field.value = '';
                    
                    field.dispatchEvent(new KeyboardEvent('keyup', {
                        key: 'Delete',
                        keyCode: 46,
                        bubbles: true
                    }));
                    
                    // Start typing after a pause
                    setTimeout(function() {
                        var chars = zipCode.split('');
                        var currentIndex = 0;
                        
                        function typeNextChar() {
                            if (currentIndex >= chars.length) {
                                // Finished typing - trigger validation
                                setTimeout(function() {
                                    console.log('[ZIP PERFECT] Triggering final validation...');
                                    
                                    // Tab out (often triggers validation)
                                    field.dispatchEvent(new KeyboardEvent('keydown', {
                                        key: 'Tab',
                                        keyCode: 9,
                                        bubbles: true
                                    }));
                                    
                                    field.blur();
                                    
                                    // Find next focusable element
                                    var allFocusable = document.querySelectorAll('input, select, textarea, button');
                                    var currentIndex = Array.from(allFocusable).indexOf(field);
                                    if (currentIndex >= 0 && currentIndex < allFocusable.length - 1) {
                                        allFocusable[currentIndex + 1].focus();
                                    }
                                    
                                    // Final change event
                                    field.dispatchEvent(new Event('change', {bubbles: true}));
                                    
                                    console.log('[ZIP PERFECT] Entry complete! Checking state...');
                                    
                                    setTimeout(function() {
                                        // Check if state was populated
                                        var stateSelects = document.querySelectorAll('select');
                                        stateSelects.forEach(function(select) {
                                            if (select.options.length > 1 && select.value) {
                                                console.log('[ZIP PERFECT] State populated:', select.value);
                                            }
                                        });
                                        
                                        // Check button states
                                        var buttons = document.querySelectorAll('button, input[type="submit"]');
                                        buttons.forEach(function(btn) {
                                            var text = (btn.textContent || btn.value || '').toLowerCase();
                                            if (text.includes('quote') || text.includes('start') || text.includes('continue')) {
                                                console.log('[ZIP PERFECT] Button:', text, 'Enabled:', !btn.disabled);
                                            }
                                        });
                                    }, 1000);
                                }, 300);
                                return;
                            }
                            
                            var char = chars[currentIndex];
                            var charCode = char.charCodeAt(0);
                            
                            // Keydown
                            field.dispatchEvent(new KeyboardEvent('keydown', {
                                key: char,
                                keyCode: charCode,
                                which: charCode,
                                charCode: 0,
                                bubbles: true,
                                cancelable: true
                            }));
                            
                            // Update value character by character
                            var oldValue = field.value;
                            field.value = oldValue + char;
                            
                            // Trigger value change for React/Angular
                            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                                window.HTMLInputElement.prototype, 'value'
                            ).set;
                            nativeInputValueSetter.call(field, field.value);
                            
                            // Input event
                            var inputEvent = new InputEvent('input', {
                                data: char,
                                inputType: 'insertText',
                                bubbles: true
                            });
                            field.dispatchEvent(inputEvent);
                            
                            // Keypress
                            field.dispatchEvent(new KeyboardEvent('keypress', {
                                key: char,
                                keyCode: charCode,
                                which: charCode,
                                charCode: charCode,
                                bubbles: true
                            }));
                            
                            // Keyup
                            field.dispatchEvent(new KeyboardEvent('keyup', {
                                key: char,
                                keyCode: charCode,
                                which: charCode,
                                charCode: 0,
                                bubbles: true
                            }));
                            
                            console.log('[ZIP PERFECT] Typed:', char, 'Value:', field.value);
                            
                            currentIndex++;
                            
                            // Random typing delay between 80-150ms
                            var delay = 80 + Math.random() * 70;
                            setTimeout(typeNextChar, delay);
                        }
                        
                        // Start typing
                        typeNextChar();
                    }, 300);
                }, 200);
            }, 100);
        };
        
        console.log('[ZIP MONITOR] Ready! Use window.perfectZipEntry("44256") to test');
        return zipField;
    })();
    """
    
    return driver.execute_script(monitor_script)

def apply_ultimate_zip_fix(driver, zip_code="44256"):
    """
    Applies the ultimate ZIP code fix using Selenium's native methods
    """
    print("[ZIP FIX] Applying ultimate ZIP code fix...")
    
    try:
        # Find the ZIP field using multiple strategies
        zip_field = None
        strategies = [
            ("//input[contains(@name, 'zip')]", "name contains 'zip'"),
            ("//input[contains(@id, 'zip')]", "id contains 'zip'"),
            ("//input[contains(@placeholder, 'ZIP')]", "placeholder contains 'ZIP'"),
            ("//input[contains(@name, 'garage')]", "name contains 'garage'"),
            ("//input[@type='text'][contains(@aria-label, 'zip')]", "aria-label contains 'zip'"),
            ("//input[@type='number'][contains(@aria-label, 'zip')]", "number input with zip label")
        ]
        
        for xpath, description in strategies:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        zip_field = elem
                        print(f"[ZIP FIX] Found ZIP field using: {description}")
                        break
                if zip_field:
                    break
            except:
                continue
        
        if not zip_field:
            print("[ZIP FIX] ERROR: Could not find ZIP field!")
            return False
        
        # Use ActionChains for more realistic interaction
        actions = ActionChains(driver)
        
        # Move to element and click
        print("[ZIP FIX] Moving to ZIP field and clicking...")
        actions.move_to_element(zip_field).click().perform()
        time.sleep(0.5)
        
        # Clear the field
        print("[ZIP FIX] Clearing field...")
        actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
        time.sleep(0.1)
        actions.send_keys(Keys.DELETE).perform()
        time.sleep(0.3)
        
        # Type each character with realistic delays
        print(f"[ZIP FIX] Typing ZIP code: {zip_code}")
        for char in zip_code:
            actions.send_keys(char).perform()
            time.sleep(0.1 + (0.05 * (1 if char == '4' else 0)))  # Vary timing slightly
        
        # Tab out to trigger validation
        print("[ZIP FIX] Tabbing out to trigger validation...")
        time.sleep(0.5)
        actions.send_keys(Keys.TAB).perform()
        
        # Wait for validation
        time.sleep(1)
        
        # Check if state was populated
        print("[ZIP FIX] Checking if state was populated...")
        state_selects = driver.find_elements(By.TAG_NAME, "select")
        for select in state_selects:
            if select.get_attribute("value"):
                print(f"[ZIP FIX] State populated: {select.get_attribute('value')}")
        
        return True
        
    except Exception as e:
        print(f"[ZIP FIX] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def integrate_ultimate_fix():
    """
    Creates the integration for the scanner
    """
    integration_code = '''
# Enhanced ZIP code entry with ultimate fix
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

print("[DEBUG] Using ULTIMATE ZIP entry method with ActionChains...")

# First clear any existing value
actions = ActionChains(driver)
actions.move_to_element(zip_elem).click().perform()
time.sleep(0.3)

# Select all and delete
actions.key_down(Keys.CONTROL).send_keys('a').key_up(Keys.CONTROL).perform()
time.sleep(0.1)
actions.send_keys(Keys.DELETE).perform()
time.sleep(0.3)

# Type each character naturally
for char in '44256':
    actions.send_keys(char).perform()
    time.sleep(0.12)  # Natural typing speed

# Tab to next field (triggers validation)
time.sleep(0.5)
actions.send_keys(Keys.TAB).perform()

print("[DEBUG] ZIP code entered using natural typing method")
'''
    
    return integration_code

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            # Install monitor
            result = install_zip_monitor(driver)
            print(f"[TEST] Monitor installed: {result is not None}")
            
            # Apply fix
            if apply_ultimate_zip_fix(driver):
                print("[TEST] Ultimate fix applied successfully!")
            else:
                print("[TEST] Fix failed!")
                
        except Exception as e:
            print(f"[ERROR] {e}")
    else:
        print("Ultimate ZIP Code Fix")
        print("====================")
        print("This fix uses Selenium's ActionChains to perfectly mimic human typing")
        print("\nTo test: python3 zip_code_ultimate_fix.py --test")
        print("\nIntegration code:")
        print(integrate_ultimate_fix())