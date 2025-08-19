#!/usr/bin/env python3
"""
Deep analysis tool for GEICO's ZIP code validation
This performs comprehensive research on why automated entry fails
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import json

def analyze_bot_detection(driver):
    """
    Comprehensive bot detection analysis
    """
    print("\n[DEEP ANALYSIS] Starting comprehensive bot detection research...")
    
    analysis_script = """
    (function() {
        var results = {
            botDetection: {},
            formAnalysis: {},
            eventListeners: {},
            validationMechanism: {},
            networkInterception: {},
            recommendations: []
        };
        
        // 1. CHECK BOT DETECTION SIGNALS
        console.log('=== BOT DETECTION ANALYSIS ===');
        
        // Navigator properties that reveal automation
        results.botDetection.navigatorWebdriver = navigator.webdriver;
        results.botDetection.navigatorPlugins = navigator.plugins.length;
        results.botDetection.navigatorLanguages = navigator.languages.join(',');
        
        // Check for automation properties
        var automationProps = [
            'webdriver', '_Selenium_IDE_Recorder', '_selenium', 'callSelenium',
            '__webdriver_script_fn', '__driver_evaluate', '__webdriver_evaluate',
            '__selenium_evaluate', '__fxdriver_evaluate', '__driver_unwrapped',
            '__webdriver_unwrapped', '__selenium_unwrapped', '__fxdriver_unwrapped',
            '_phantom', '__nightmare', 'domAutomation', 'domAutomationController'
        ];
        
        automationProps.forEach(function(prop) {
            if (window[prop] || document[prop]) {
                results.botDetection['found_' + prop] = true;
            }
        });
        
        // Check Chrome specific automation
        results.botDetection.chromeAutomation = window.chrome && window.chrome.runtime;
        results.botDetection.permissionAPI = navigator.permissions ? 'present' : 'missing';
        
        // WebGL fingerprinting
        try {
            var canvas = document.createElement('canvas');
            var gl = canvas.getContext('webgl');
            results.botDetection.webglVendor = gl.getParameter(gl.VENDOR);
            results.botDetection.webglRenderer = gl.getParameter(gl.RENDERER);
        } catch (e) {
            results.botDetection.webglError = e.message;
        }
        
        // 2. ANALYZE THE ZIP FIELD
        console.log('\\n=== FORM FIELD ANALYSIS ===');
        
        var zipField = null;
        var inputs = document.querySelectorAll('input');
        
        for (var i = 0; i < inputs.length; i++) {
            var input = inputs[i];
            var text = (input.name + input.id + input.placeholder + (input.getAttribute('aria-label') || '')).toLowerCase();
            if ((text.includes('zip') || text.includes('garage')) && input.type !== 'hidden') {
                zipField = input;
                break;
            }
        }
        
        if (zipField) {
            results.formAnalysis.found = true;
            results.formAnalysis.fieldDetails = {
                name: zipField.name,
                id: zipField.id,
                className: zipField.className,
                type: zipField.type,
                pattern: zipField.pattern,
                maxLength: zipField.maxLength,
                required: zipField.required,
                autocomplete: zipField.autocomplete
            };
            
            // Check for data attributes
            var dataAttrs = {};
            for (var attr of zipField.attributes) {
                if (attr.name.startsWith('data-')) {
                    dataAttrs[attr.name] = attr.value;
                }
            }
            results.formAnalysis.dataAttributes = dataAttrs;
            
            // 3. ANALYZE EVENT LISTENERS
            console.log('\\n=== EVENT LISTENER ANALYSIS ===');
            
            // Check for event listeners using Chrome DevTools API
            if (typeof getEventListeners !== 'undefined') {
                try {
                    var listeners = getEventListeners(zipField);
                    for (var eventType in listeners) {
                        results.eventListeners[eventType] = listeners[eventType].length + ' listeners';
                    }
                } catch (e) {}
            }
            
            // Check inline handlers
            var inlineHandlers = ['onchange', 'oninput', 'onblur', 'onfocus', 'onkeyup', 'onkeydown'];
            inlineHandlers.forEach(function(handler) {
                if (zipField[handler]) {
                    results.eventListeners[handler] = 'present (inline)';
                }
            });
            
            // 4. CHECK VALIDATION MECHANISM
            console.log('\\n=== VALIDATION MECHANISM ===');
            
            // Look for validation library signatures
            results.validationMechanism.jQuery = typeof jQuery !== 'undefined';
            results.validationMechanism.jQueryValidation = results.validationMechanism.jQuery && jQuery.fn && jQuery.fn.validate;
            
            // Check for React
            results.validationMechanism.react = !!(
                zipField._reactRootContainer || 
                zipField.__reactInternalInstance || 
                zipField.__reactEventHandlers ||
                zipField._reactProps
            );
            
            // Check for Angular
            results.validationMechanism.angular = !!(
                window.angular || 
                zipField.getAttribute('ng-model') ||
                zipField.__ngContext__
            );
            
            // Check for Vue
            results.validationMechanism.vue = !!(
                window.Vue ||
                zipField.__vue__ ||
                zipField._isVue
            );
            
            // Check form element
            var form = zipField.closest('form');
            if (form) {
                results.validationMechanism.formMethod = form.method;
                results.validationMechanism.formAction = form.action;
                results.validationMechanism.formNoValidate = form.noValidate;
            }
            
            // 5. NETWORK INTERCEPTION CHECK
            console.log('\\n=== NETWORK ANALYSIS ===');
            
            // Check if fetch/XHR are modified
            results.networkInterception.fetchModified = window.fetch.toString().includes('[native code]') ? false : true;
            results.networkInterception.xhrModified = window.XMLHttpRequest.prototype.open.toString().includes('[native code]') ? false : true;
            
            // 6. GENERATE RECOMMENDATIONS
            console.log('\\n=== GENERATING RECOMMENDATIONS ===');
            
            if (results.botDetection.navigatorWebdriver) {
                results.recommendations.push('Navigator.webdriver is true - use undetected-chromedriver or CDP');
            }
            
            if (results.validationMechanism.react) {
                results.recommendations.push('React detected - may need to trigger React events specifically');
            }
            
            if (results.validationMechanism.angular) {
                results.recommendations.push('Angular detected - may need to trigger Angular digest cycle');
            }
            
            if (Object.keys(results.eventListeners).length > 0) {
                results.recommendations.push('Multiple event listeners found - ensure all events are triggered in correct order');
            }
            
            // 7. TEST ACTUAL VALIDATION
            window.testZipValidation = function(zipCode) {
                console.log('[VALIDATION TEST] Testing with ZIP:', zipCode);
                
                zipField.focus();
                zipField.value = zipCode;
                
                // Trigger all possible events
                var events = ['input', 'change', 'blur', 'keyup'];
                events.forEach(function(eventType) {
                    var event = new Event(eventType, { bubbles: true });
                    zipField.dispatchEvent(event);
                });
                
                // Check for AJAX calls
                var originalFetch = window.fetch;
                var originalXHR = window.XMLHttpRequest.prototype.open;
                
                window.fetch = function() {
                    console.log('[VALIDATION TEST] Fetch called:', arguments[0]);
                    return originalFetch.apply(this, arguments);
                };
                
                window.XMLHttpRequest.prototype.open = function() {
                    console.log('[VALIDATION TEST] XHR called:', arguments[1]);
                    return originalXHR.apply(this, arguments);
                };
                
                // Wait and check state
                setTimeout(function() {
                    var states = document.querySelectorAll('select[name*="state"], input[name*="state"]');
                    var stateFound = false;
                    states.forEach(function(s) {
                        if (s.value) {
                            console.log('[VALIDATION TEST] State populated:', s.value);
                            stateFound = true;
                        }
                    });
                    
                    if (!stateFound) {
                        console.log('[VALIDATION TEST] No state populated after validation');
                    }
                    
                    // Restore originals
                    window.fetch = originalFetch;
                    window.XMLHttpRequest.prototype.open = originalXHR;
                }, 1000);
            };
            
            // Store field reference
            window.analyzedZipField = zipField;
        } else {
            results.formAnalysis.found = false;
            results.recommendations.push('Could not find ZIP field - check selector');
        }
        
        return results;
    })();
    """
    
    results = driver.execute_script(analysis_script)
    
    # Print analysis results
    print("\n[ANALYSIS RESULTS]")
    print("==================")
    
    print("\n1. BOT DETECTION:")
    for key, value in results['botDetection'].items():
        print(f"   - {key}: {value}")
    
    print("\n2. FORM FIELD:")
    if results['formAnalysis'].get('found'):
        print("   - Field found: YES")
        for key, value in results['formAnalysis']['fieldDetails'].items():
            if value:
                print(f"   - {key}: {value}")
        if results['formAnalysis'].get('dataAttributes'):
            print("   - Data attributes:")
            for key, value in results['formAnalysis']['dataAttributes'].items():
                print(f"     * {key}: {value}")
    else:
        print("   - Field found: NO")
    
    print("\n3. EVENT LISTENERS:")
    for event, count in results['eventListeners'].items():
        print(f"   - {event}: {count}")
    
    print("\n4. VALIDATION MECHANISM:")
    for key, value in results['validationMechanism'].items():
        print(f"   - {key}: {value}")
    
    print("\n5. NETWORK INTERCEPTION:")
    for key, value in results['networkInterception'].items():
        print(f"   - {key}: {value}")
    
    print("\n6. RECOMMENDATIONS:")
    for rec in results['recommendations']:
        print(f"   * {rec}")
    
    return results

def create_undetected_solution():
    """
    Creates solution based on analysis
    """
    return """
    // Solution for GEICO ZIP validation
    window.geicoZipSolution = function(zipCode) {
        console.log('[SOLUTION] Applying comprehensive fix for ZIP:', zipCode);
        
        var field = window.analyzedZipField;
        if (!field) {
            console.error('[SOLUTION] No ZIP field found');
            return;
        }
        
        // Step 1: Remove automation indicators
        delete window.navigator.webdriver;
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false
        });
        
        // Step 2: Focus naturally with mouse events
        var rect = field.getBoundingClientRect();
        field.dispatchEvent(new MouseEvent('mouseover', {
            clientX: rect.left + rect.width/2,
            clientY: rect.top + rect.height/2,
            bubbles: true
        }));
        
        field.dispatchEvent(new MouseEvent('mousedown', {
            clientX: rect.left + rect.width/2,
            clientY: rect.top + rect.height/2,
            bubbles: true
        }));
        
        field.focus();
        
        // Step 3: Clear field naturally
        field.select();
        
        // Step 4: Type with perfect timing
        var chars = zipCode.split('');
        var index = 0;
        
        function typeNext() {
            if (index >= chars.length) {
                // Done typing - validate
                setTimeout(function() {
                    field.blur();
                    
                    // Tab to next field
                    var next = field.nextElementSibling;
                    if (next && next.focus) {
                        next.focus();
                    }
                    
                    console.log('[SOLUTION] ZIP entry complete');
                }, 200);
                return;
            }
            
            var char = chars[index];
            
            // Use the most natural typing method
            if (document.execCommand) {
                document.execCommand('insertText', false, char);
            } else {
                field.value += char;
                field.dispatchEvent(new InputEvent('input', {
                    data: char,
                    inputType: 'insertText',
                    bubbles: true
                }));
            }
            
            index++;
            
            // Human-like delay
            setTimeout(typeNext, 50 + Math.random() * 100);
        }
        
        typeNext();
    };
    """

def apply_stealth_mode(driver):
    """
    Apply stealth techniques to avoid detection
    """
    # Execute CDP commands to hide automation
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            // Hide webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Hide automation indicators
            window.navigator.chrome = {
                runtime: {}
            };
            
            // Fix permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        '''
    })
    
    print("[STEALTH] Applied stealth mode to hide automation")

if __name__ == "__main__":
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    # Try to hide automation
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        # Apply stealth mode
        try:
            apply_stealth_mode(driver)
        except Exception as e:
            print(f"[WARNING] Could not apply stealth mode: {e}")
        
        # Run analysis
        results = analyze_bot_detection(driver)
        
        # Install solution
        driver.execute_script(create_undetected_solution())
        
        print("\n[TESTING]")
        print("=========")
        print("1. To test validation: window.testZipValidation('44256')")
        print("2. To apply solution: window.geicoZipSolution('44256')")
        print("\nCheck browser console for detailed output")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()