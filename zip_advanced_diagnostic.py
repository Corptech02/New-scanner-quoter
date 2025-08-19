#!/usr/bin/env python3
"""
Advanced diagnostic tool to capture EVERYTHING about manual ZIP entry
This will help us understand what GEICO's form validation is checking
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json

def install_advanced_monitor(driver):
    """
    Installs the most comprehensive monitoring possible
    """
    monitor_script = """
    (function() {
        console.log('[ADVANCED MONITOR] Installing comprehensive tracking...');
        
        window.captureData = {
            events: [],
            mouseMovements: [],
            timings: [],
            requests: [],
            formData: {},
            browserState: {}
        };
        
        // Capture browser state
        window.captureData.browserState = {
            userAgent: navigator.userAgent,
            webdriver: navigator.webdriver,
            plugins: navigator.plugins.length,
            languages: navigator.languages,
            platform: navigator.platform,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine,
            deviceMemory: navigator.deviceMemory,
            hardwareConcurrency: navigator.hardwareConcurrency
        };
        
        // Find ZIP field
        var zipField = null;
        var inputs = document.querySelectorAll('input');
        for (var i = 0; i < inputs.length; i++) {
            var input = inputs[i];
            var text = (input.name + input.id + input.placeholder + (input.getAttribute('aria-label') || '')).toLowerCase();
            if (text.includes('zip') || text.includes('garage') || text.includes('postal')) {
                if (input.type !== 'hidden') {
                    zipField = input;
                    console.log('[ADVANCED MONITOR] Found ZIP field:', {
                        name: input.name,
                        id: input.id,
                        type: input.type,
                        className: input.className
                    });
                    break;
                }
            }
        }
        
        if (!zipField) {
            console.error('[ADVANCED MONITOR] No ZIP field found!');
            return;
        }
        
        // Store reference
        window.monitoredZipField = zipField;
        
        // Track ALL events with isTrusted property
        var allEventTypes = [
            'mousedown', 'mouseup', 'click', 'dblclick', 'contextmenu',
            'mouseover', 'mouseout', 'mouseenter', 'mouseleave', 'mousemove',
            'focus', 'blur', 'focusin', 'focusout',
            'keydown', 'keypress', 'keyup', 'input', 'change',
            'compositionstart', 'compositionupdate', 'compositionend',
            'beforeinput', 'textInput', 'paste', 'cut', 'copy',
            'select', 'selectstart', 'selectionchange'
        ];
        
        allEventTypes.forEach(function(eventType) {
            zipField.addEventListener(eventType, function(e) {
                var eventData = {
                    type: e.type,
                    timestamp: Date.now(),
                    isTrusted: e.isTrusted,
                    value: e.target.value,
                    selectionStart: e.target.selectionStart,
                    selectionEnd: e.target.selectionEnd
                };
                
                // Add type-specific data
                if (e.type.includes('key')) {
                    eventData.key = e.key;
                    eventData.code = e.code;
                    eventData.keyCode = e.keyCode;
                    eventData.charCode = e.charCode;
                    eventData.which = e.which;
                    eventData.shiftKey = e.shiftKey;
                    eventData.ctrlKey = e.ctrlKey;
                    eventData.altKey = e.altKey;
                    eventData.metaKey = e.metaKey;
                }
                
                if (e.type.includes('mouse')) {
                    eventData.clientX = e.clientX;
                    eventData.clientY = e.clientY;
                    eventData.screenX = e.screenX;
                    eventData.screenY = e.screenY;
                    eventData.movementX = e.movementX;
                    eventData.movementY = e.movementY;
                    eventData.button = e.button;
                    eventData.buttons = e.buttons;
                }
                
                if (e.type === 'input' || e.type === 'beforeinput') {
                    eventData.inputType = e.inputType;
                    eventData.data = e.data;
                }
                
                window.captureData.events.push(eventData);
                
                if (e.isTrusted) {
                    console.log('[TRUSTED EVENT]', e.type, 'Value:', e.target.value);
                } else {
                    console.log('[SYNTHETIC EVENT]', e.type, 'Value:', e.target.value);
                }
            }, true);
        });
        
        // Track mouse movements globally
        document.addEventListener('mousemove', function(e) {
            window.captureData.mouseMovements.push({
                x: e.clientX,
                y: e.clientY,
                timestamp: Date.now()
            });
        });
        
        // Override XMLHttpRequest to catch validation calls
        var originalXHR = window.XMLHttpRequest.prototype.open;
        window.XMLHttpRequest.prototype.open = function(method, url) {
            console.log('[XHR]', method, url);
            window.captureData.requests.push({
                type: 'xhr',
                method: method,
                url: url,
                timestamp: Date.now()
            });
            
            // Track response
            this.addEventListener('load', function() {
                console.log('[XHR Response]', this.responseText.substring(0, 200));
            });
            
            return originalXHR.apply(this, arguments);
        };
        
        // Override fetch
        var originalFetch = window.fetch;
        window.fetch = function(url, options) {
            console.log('[FETCH]', url, options);
            window.captureData.requests.push({
                type: 'fetch',
                url: url,
                options: options,
                timestamp: Date.now()
            });
            return originalFetch.apply(this, arguments);
        };
        
        // Monitor form data changes
        var formObserver = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes') {
                    console.log('[FORM MUTATION]', mutation.attributeName, 'on', mutation.target.tagName);
                }
            });
        });
        
        // Observe the entire form
        var form = zipField.closest('form');
        if (form) {
            formObserver.observe(form, {
                attributes: true,
                childList: true,
                subtree: true,
                attributeOldValue: true
            });
        }
        
        // Function to analyze captured data
        window.analyzeCapture = function() {
            var data = window.captureData;
            
            console.log('=== CAPTURE ANALYSIS ===');
            console.log('Total events:', data.events.length);
            console.log('Trusted events:', data.events.filter(e => e.isTrusted).length);
            console.log('Synthetic events:', data.events.filter(e => !e.isTrusted).length);
            console.log('Mouse movements:', data.mouseMovements.length);
            console.log('XHR/Fetch requests:', data.requests.length);
            
            // Event sequence
            console.log('\n=== EVENT SEQUENCE ===');
            data.events.forEach(function(e, i) {
                var prev = i > 0 ? data.events[i-1] : null;
                var timeDiff = prev ? e.timestamp - prev.timestamp : 0;
                console.log(`${i}: ${e.type} (${e.isTrusted ? 'TRUSTED' : 'synthetic'}) +${timeDiff}ms Value: "${e.value}"`);
            });
            
            // Timing analysis
            console.log('\n=== TYPING TIMING ===');
            var inputEvents = data.events.filter(e => e.type === 'input');
            inputEvents.forEach(function(e, i) {
                if (i > 0) {
                    var timeDiff = e.timestamp - inputEvents[i-1].timestamp;
                    console.log(`Char ${i}: ${timeDiff}ms`);
                }
            });
            
            // Request analysis
            if (data.requests.length > 0) {
                console.log('\n=== VALIDATION REQUESTS ===');
                data.requests.forEach(function(req) {
                    console.log(`${req.type}: ${req.method || 'GET'} ${req.url}`);
                });
            }
            
            return data;
        };
        
        // Function to replay captured events
        window.replayCapture = function() {
            console.log('[REPLAY] Starting replay of captured events...');
            
            var field = window.monitoredZipField;
            var events = window.captureData.events;
            
            field.focus();
            field.value = '';
            
            var index = 0;
            function replayNext() {
                if (index >= events.length) {
                    console.log('[REPLAY] Complete!');
                    return;
                }
                
                var event = events[index];
                var prevTime = index > 0 ? events[index-1].timestamp : event.timestamp;
                var delay = event.timestamp - prevTime;
                
                setTimeout(function() {
                    console.log('[REPLAY]', event.type, 'Value:', event.value);
                    
                    // Recreate the event as closely as possible
                    if (event.type.includes('key')) {
                        field.dispatchEvent(new KeyboardEvent(event.type, {
                            key: event.key,
                            code: event.code,
                            keyCode: event.keyCode,
                            which: event.which,
                            bubbles: true
                        }));
                    } else if (event.type === 'input') {
                        field.value = event.value;
                        field.dispatchEvent(new InputEvent('input', {
                            data: event.data,
                            inputType: event.inputType,
                            bubbles: true
                        }));
                    } else {
                        field.dispatchEvent(new Event(event.type, {bubbles: true}));
                    }
                    
                    index++;
                    replayNext();
                }, Math.min(delay, 500)); // Cap delay at 500ms
            }
            
            replayNext();
        };
        
        console.log('[ADVANCED MONITOR] Ready! Type in ZIP field manually.');
        console.log('Then run: window.analyzeCapture() to see results');
        console.log('Or run: window.replayCapture() to replay the sequence');
        
        return zipField;
    })();
    """
    
    return driver.execute_script(monitor_script)

def create_perfect_zip_entry():
    """
    Creates a function that uses all discovered techniques
    """
    return """
    window.ultimateZipEntry = function(zipCode) {
        console.log('[ULTIMATE ZIP] Starting with all discovered techniques...');
        
        var field = window.monitoredZipField;
        if (!field) {
            console.error('[ULTIMATE ZIP] No field found!');
            return;
        }
        
        // Check if webdriver is detected
        if (navigator.webdriver) {
            console.warn('[ULTIMATE ZIP] Warning: navigator.webdriver is true (bot detected)');
        }
        
        // Simulate natural mouse movement to field
        var rect = field.getBoundingClientRect();
        var startX = Math.random() * window.innerWidth;
        var startY = Math.random() * window.innerHeight;
        var steps = 20;
        
        for (var i = 0; i <= steps; i++) {
            (function(step) {
                setTimeout(function() {
                    var progress = step / steps;
                    var x = startX + (rect.left + rect.width/2 - startX) * progress;
                    var y = startY + (rect.top + rect.height/2 - startY) * progress;
                    
                    document.dispatchEvent(new MouseEvent('mousemove', {
                        clientX: x,
                        clientY: y,
                        bubbles: true
                    }));
                }, step * 10);
            })(i);
        }
        
        // Click after mouse movement
        setTimeout(function() {
            // Natural click sequence
            field.dispatchEvent(new MouseEvent('mousedown', {
                clientX: rect.left + rect.width/2,
                clientY: rect.top + rect.height/2,
                bubbles: true,
                cancelable: true,
                view: window
            }));
            
            setTimeout(function() {
                field.dispatchEvent(new MouseEvent('mouseup', {
                    clientX: rect.left + rect.width/2,
                    clientY: rect.top + rect.height/2,
                    bubbles: true,
                    cancelable: true,
                    view: window
                }));
                
                field.click();
                field.focus();
                
                // Clear field naturally
                setTimeout(function() {
                    field.select();
                    
                    // Type each character with human-like timing
                    var chars = zipCode.split('');
                    var currentValue = '';
                    
                    function typeChar(index) {
                        if (index >= chars.length) {
                            // Done typing - validate
                            setTimeout(function() {
                                // Tab out
                                field.dispatchEvent(new KeyboardEvent('keydown', {
                                    key: 'Tab',
                                    code: 'Tab',
                                    keyCode: 9,
                                    bubbles: true
                                }));
                                
                                field.blur();
                                
                                console.log('[ULTIMATE ZIP] Complete!');
                            }, 200);
                            return;
                        }
                        
                        var char = chars[index];
                        
                        // Variable timing (80-200ms)
                        var delay = 80 + Math.random() * 120;
                        
                        setTimeout(function() {
                            // Use execCommand for most natural input
                            document.execCommand('insertText', false, char);
                            
                            console.log('[ULTIMATE ZIP] Typed:', char);
                            
                            typeChar(index + 1);
                        }, delay);
                    }
                    
                    // Start typing
                    typeChar(0);
                }, 300);
            }, 50);
        }, 250);
    };
    """

if __name__ == "__main__":
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        print("[DIAGNOSTIC] Installing advanced monitor...")
        result = install_zip_monitor(driver)
        
        if result:
            print("[DIAGNOSTIC] Monitor installed successfully!")
            print("\n[INSTRUCTIONS]")
            print("1. Manually type the ZIP code in the field")
            print("2. Watch for state population")
            print("3. In browser console, run: window.analyzeCapture()")
            print("4. Share the results to understand what's different")
            
            # Also install ultimate entry function
            driver.execute_script(create_perfect_zip_entry())
            print("\n[TESTING]")
            print("To test ultimate entry, run in console: window.ultimateZipEntry('44256')")
        else:
            print("[DIAGNOSTIC] Failed to install monitor")
            
    except Exception as e:
        print(f"[ERROR] {e}")