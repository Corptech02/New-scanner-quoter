#!/usr/bin/env python3
"""
Deep investigation tool for GEICO ZIP code validation
This will help us understand what's really happening when manual entry works
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json

def investigate_zip_validation(driver):
    """
    Investigates what happens during ZIP code entry
    """
    print("\n[INVESTIGATION] Starting deep ZIP validation analysis...")
    
    # First, let's install comprehensive monitoring
    investigation_script = """
    (function() {
        console.log('[ZIP INVESTIGATION] Installing comprehensive monitoring...');
        
        // Monitor ALL events on the page
        window.capturedEvents = [];
        window.capturedRequests = [];
        
        // Override XMLHttpRequest to capture AJAX calls
        var originalXHR = window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            var xhr = new originalXHR();
            var originalOpen = xhr.open;
            var originalSend = xhr.send;
            
            xhr.open = function(method, url) {
                this._method = method;
                this._url = url;
                return originalOpen.apply(this, arguments);
            };
            
            xhr.send = function(data) {
                window.capturedRequests.push({
                    method: this._method,
                    url: this._url,
                    data: data,
                    timestamp: new Date().toISOString()
                });
                console.log('[ZIP INVESTIGATION] XHR Request:', this._method, this._url);
                return originalSend.apply(this, arguments);
            };
            
            return xhr;
        };
        
        // Override fetch to capture fetch API calls
        var originalFetch = window.fetch;
        window.fetch = function(url, options) {
            window.capturedRequests.push({
                method: (options && options.method) || 'GET',
                url: url,
                data: options && options.body,
                timestamp: new Date().toISOString(),
                type: 'fetch'
            });
            console.log('[ZIP INVESTIGATION] Fetch Request:', url);
            return originalFetch.apply(this, arguments);
        };
        
        // Find all ZIP input fields
        var zipInputs = document.querySelectorAll('input[type="text"], input[type="number"], input[type="tel"]');
        var zipField = null;
        
        zipInputs.forEach(function(input) {
            var name = (input.name || '').toLowerCase();
            var id = (input.id || '').toLowerCase();
            var placeholder = (input.placeholder || '').toLowerCase();
            
            if (name.includes('zip') || id.includes('zip') || placeholder.includes('zip') ||
                name.includes('garage') || id.includes('garage') || placeholder.includes('garage')) {
                zipField = input;
                console.log('[ZIP INVESTIGATION] Found ZIP field:', {
                    name: input.name,
                    id: input.id,
                    placeholder: input.placeholder,
                    type: input.type
                });
            }
        });
        
        if (zipField) {
            // Monitor all events on the ZIP field
            var eventTypes = [
                'focus', 'blur', 'input', 'change', 'keydown', 'keypress', 'keyup',
                'paste', 'cut', 'compositionstart', 'compositionend', 'compositionupdate',
                'beforeinput', 'textInput', 'propertychange'
            ];
            
            eventTypes.forEach(function(eventType) {
                zipField.addEventListener(eventType, function(e) {
                    var eventData = {
                        type: e.type,
                        value: e.target.value,
                        timestamp: new Date().toISOString(),
                        key: e.key,
                        keyCode: e.keyCode,
                        which: e.which,
                        data: e.data
                    };
                    window.capturedEvents.push(eventData);
                    console.log('[ZIP INVESTIGATION] Event:', eventType, 'Value:', e.target.value);
                }, true);
            });
            
            // Monitor value changes using MutationObserver
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'value') {
                        console.log('[ZIP INVESTIGATION] Value changed via attribute:', zipField.value);
                    }
                });
            });
            
            observer.observe(zipField, {
                attributes: true,
                attributeFilter: ['value']
            });
            
            // Monitor property changes
            var originalValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value');
            Object.defineProperty(zipField, 'value', {
                get: function() {
                    return originalValue.get.call(this);
                },
                set: function(val) {
                    console.log('[ZIP INVESTIGATION] Value set programmatically:', val);
                    window.capturedEvents.push({
                        type: 'value_set',
                        value: val,
                        timestamp: new Date().toISOString()
                    });
                    return originalValue.set.call(this, val);
                }
            });
            
            // Store reference for later use
            window.monitoredZipField = zipField;
        }
        
        // Monitor state field changes
        var stateFields = document.querySelectorAll('select[name*="state"], input[name*="state"], #state');
        stateFields.forEach(function(field) {
            field.addEventListener('change', function(e) {
                console.log('[ZIP INVESTIGATION] State changed:', e.target.value);
            });
        });
        
        console.log('[ZIP INVESTIGATION] Monitoring installed. Please manually type a ZIP code...');
        
        // Function to get validation functions attached to ZIP field
        window.getZipValidation = function() {
            if (!window.monitoredZipField) return null;
            
            var field = window.monitoredZipField;
            var validation = {
                events: {},
                properties: {}
            };
            
            // Get event listeners (this might not work in all browsers)
            try {
                var listeners = getEventListeners(field);
                for (var event in listeners) {
                    validation.events[event] = listeners[event].length;
                }
            } catch (e) {
                console.log('[ZIP INVESTIGATION] Could not get event listeners');
            }
            
            // Check for validation attributes
            validation.properties = {
                pattern: field.pattern,
                required: field.required,
                maxLength: field.maxLength,
                minLength: field.minLength,
                'data-validate': field.getAttribute('data-validate'),
                'data-validation': field.getAttribute('data-validation')
            };
            
            // Check for Angular/React/Vue
            validation.framework = {
                angular: !!(window.angular || field.__ngContext__),
                react: !!(field._reactProps || field._reactRootContainer),
                vue: !!(field.__vue__ || field._isVue)
            };
            
            return validation;
        };
        
        // Function to simulate exact manual typing
        window.simulateManualTyping = function(value) {
            if (!window.monitoredZipField) {
                console.error('[ZIP INVESTIGATION] No ZIP field found');
                return;
            }
            
            var field = window.monitoredZipField;
            field.focus();
            field.select();
            
            // Clear events for clean comparison
            window.capturedEvents = [];
            window.capturedRequests = [];
            
            console.log('[ZIP INVESTIGATION] Starting simulated manual typing...');
            
            // Type each character
            value.split('').forEach(function(char, index) {
                setTimeout(function() {
                    // Focus if needed
                    if (document.activeElement !== field) {
                        field.focus();
                    }
                    
                    // Create and dispatch events in exact order
                    var keydownEvent = new KeyboardEvent('keydown', {
                        key: char,
                        code: 'Digit' + char,
                        keyCode: 48 + parseInt(char),
                        charCode: 48 + parseInt(char),
                        which: 48 + parseInt(char),
                        bubbles: true,
                        cancelable: true,
                        composed: true
                    });
                    field.dispatchEvent(keydownEvent);
                    
                    // Set selection range before typing
                    var start = field.value.length;
                    field.setSelectionRange(start, start);
                    
                    // Actually modify the value
                    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(field, field.value + char);
                    
                    // Trigger input event
                    var inputEvent = new InputEvent('input', {
                        data: char,
                        inputType: 'insertText',
                        dataTransfer: null,
                        isComposing: false,
                        bubbles: true,
                        cancelable: true,
                        composed: true
                    });
                    field.dispatchEvent(inputEvent);
                    
                    // Keypress (deprecated but might still be used)
                    var keypressEvent = new KeyboardEvent('keypress', {
                        key: char,
                        keyCode: 48 + parseInt(char),
                        charCode: 48 + parseInt(char),
                        which: 48 + parseInt(char),
                        bubbles: true,
                        cancelable: true
                    });
                    field.dispatchEvent(keypressEvent);
                    
                    // Keyup
                    var keyupEvent = new KeyboardEvent('keyup', {
                        key: char,
                        code: 'Digit' + char,
                        keyCode: 48 + parseInt(char),
                        charCode: 48 + parseInt(char),
                        which: 48 + parseInt(char),
                        bubbles: true,
                        cancelable: true,
                        composed: true
                    });
                    field.dispatchEvent(keyupEvent);
                    
                    console.log('[ZIP INVESTIGATION] Typed:', char, 'Value now:', field.value);
                    
                    // After last character
                    if (index === value.length - 1) {
                        setTimeout(function() {
                            // Blur the field
                            field.blur();
                            field.dispatchEvent(new FocusEvent('blur', {
                                bubbles: true,
                                cancelable: true,
                                relatedTarget: document.body
                            }));
                            
                            field.dispatchEvent(new Event('change', {
                                bubbles: true,
                                cancelable: true
                            }));
                            
                            console.log('[ZIP INVESTIGATION] Typing complete. Checking results...');
                            
                            setTimeout(function() {
                                // Check state field
                                var stateFields = document.querySelectorAll('select[name*="state"], input[name*="state"], #state');
                                stateFields.forEach(function(sf) {
                                    if (sf.value) {
                                        console.log('[ZIP INVESTIGATION] State populated:', sf.value);
                                    }
                                });
                                
                                // Check for enabled buttons
                                var buttons = document.querySelectorAll('button, input[type="submit"]');
                                buttons.forEach(function(btn) {
                                    var text = (btn.textContent || btn.value || '').toLowerCase();
                                    if (text.includes('quote') || text.includes('continue')) {
                                        console.log('[ZIP INVESTIGATION] Button:', text, 'Disabled:', btn.disabled);
                                    }
                                });
                                
                                // Log captured events and requests
                                console.log('[ZIP INVESTIGATION] Total events captured:', window.capturedEvents.length);
                                console.log('[ZIP INVESTIGATION] Total requests captured:', window.capturedRequests.length);
                                
                                if (window.capturedRequests.length > 0) {
                                    console.log('[ZIP INVESTIGATION] Requests made:');
                                    window.capturedRequests.forEach(function(req) {
                                        console.log('  -', req.method, req.url);
                                    });
                                }
                            }, 1000);
                        }, 500);
                    }
                }, index * 150);
            });
        };
        
        return {
            zipField: zipField,
            message: 'Investigation ready. Call window.simulateManualTyping("44256") to test.'
        };
    })();
    """
    
    result = driver.execute_script(investigation_script)
    print(f"[INVESTIGATION] Setup complete: {result}")
    
    return result

def create_enhanced_zip_filler():
    """
    Creates an enhanced ZIP filler based on investigation results
    """
    return """
    function fillZipWithMaxCompatibility(zipElement, zipCode) {
        console.log('[ENHANCED ZIP] Starting maximum compatibility ZIP entry...');
        
        // Ensure element is ready
        zipElement.scrollIntoView({block: 'center'});
        
        // Click to focus
        zipElement.click();
        zipElement.focus();
        
        // Clear any existing value properly
        zipElement.select();
        document.execCommand('delete');
        
        // Small delay
        setTimeout(function() {
            // Type each character
            zipCode.split('').forEach(function(char, index) {
                setTimeout(function() {
                    // Ensure focus
                    if (document.activeElement !== zipElement) {
                        zipElement.focus();
                    }
                    
                    // Use the most compatible way to set value
                    var currentValue = zipElement.value;
                    var newValue = currentValue + char;
                    
                    // Try multiple methods to set the value
                    try {
                        // Method 1: Native setter
                        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value'
                        ).set;
                        nativeInputValueSetter.call(zipElement, newValue);
                    } catch (e) {
                        // Fallback: Direct assignment
                        zipElement.value = newValue;
                    }
                    
                    // Dispatch all possible events
                    var events = [
                        new KeyboardEvent('keydown', {
                            key: char, keyCode: 48 + parseInt(char), 
                            which: 48 + parseInt(char), bubbles: true
                        }),
                        new InputEvent('input', {
                            data: char, inputType: 'insertText', 
                            bubbles: true, composed: true
                        }),
                        new Event('input', {bubbles: true}),
                        new KeyboardEvent('keypress', {
                            key: char, keyCode: 48 + parseInt(char),
                            which: 48 + parseInt(char), bubbles: true
                        }),
                        new KeyboardEvent('keyup', {
                            key: char, keyCode: 48 + parseInt(char),
                            which: 48 + parseInt(char), bubbles: true
                        })
                    ];
                    
                    events.forEach(function(evt) {
                        try {
                            zipElement.dispatchEvent(evt);
                        } catch (e) {
                            console.log('[ENHANCED ZIP] Event dispatch failed:', e);
                        }
                    });
                    
                    // Also try React/Angular specific triggers
                    try {
                        // React
                        if (zipElement._valueTracker) {
                            zipElement._valueTracker.setValue(currentValue);
                        }
                        
                        // Angular
                        if (window.angular && angular.element) {
                            angular.element(zipElement).triggerHandler('input');
                        }
                    } catch (e) {}
                    
                    console.log('[ENHANCED ZIP] Typed:', char, 'Value:', zipElement.value);
                    
                    // After last character
                    if (index === zipCode.length - 1) {
                        setTimeout(function() {
                            // Multiple blur/change triggers
                            zipElement.blur();
                            zipElement.dispatchEvent(new FocusEvent('blur', {bubbles: true}));
                            zipElement.dispatchEvent(new Event('change', {bubbles: true}));
                            zipElement.dispatchEvent(new Event('focusout', {bubbles: true}));
                            
                            // Force validation by focusing elsewhere
                            if (document.body) {
                                document.body.click();
                            }
                            
                            console.log('[ENHANCED ZIP] Entry complete');
                        }, 200);
                    }
                }, index * 200); // Slower typing for better compatibility
            });
        }, 100);
    }
    """

if __name__ == "__main__":
    # Connect to existing Chrome instance
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        result = investigate_zip_validation(driver)
        
        print("\n[INVESTIGATION] Setup complete!")
        print("[INVESTIGATION] Now you can:")
        print("1. Manually type a ZIP code and watch the console")
        print("2. Run: window.simulateManualTyping('44256') in console")
        print("3. Compare the events between manual and simulated")
        
    except Exception as e:
        print(f"[ERROR] {e}")