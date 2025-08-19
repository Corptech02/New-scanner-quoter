#!/usr/bin/env python3
"""
Fix for ZIP code entry to properly trigger validation and state lookup
Simulates human typing behavior to ensure all events are fired
"""

def create_enhanced_zip_code_filler():
    """
    Returns JavaScript code that properly fills ZIP code with all necessary events
    """
    return """
    function fillZipCodeProperly(element, zipCode) {
        console.log('[ZIP FIX] Starting enhanced ZIP code entry for:', zipCode);
        
        // First, ensure element is ready
        element.scrollIntoView({block: 'center'});
        
        // Trigger focus event
        element.focus();
        element.dispatchEvent(new FocusEvent('focus', {bubbles: true}));
        element.dispatchEvent(new Event('focusin', {bubbles: true}));
        
        // Clear existing value properly
        element.select();
        element.value = '';
        
        // Small delay after clearing
        setTimeout(function() {
            // Type each character individually
            var chars = zipCode.split('');
            var currentValue = '';
            
            chars.forEach(function(char, index) {
                setTimeout(function() {
                    currentValue += char;
                    
                    // Simulate keydown
                    var keydownEvent = new KeyboardEvent('keydown', {
                        key: char,
                        code: 'Digit' + char,
                        keyCode: char.charCodeAt(0),
                        which: char.charCodeAt(0),
                        bubbles: true,
                        cancelable: true
                    });
                    element.dispatchEvent(keydownEvent);
                    
                    // Update value
                    element.value = currentValue;
                    
                    // Simulate input event
                    var inputEvent = new InputEvent('input', {
                        data: char,
                        inputType: 'insertText',
                        bubbles: true,
                        cancelable: true
                    });
                    element.dispatchEvent(inputEvent);
                    
                    // Simulate keypress
                    var keypressEvent = new KeyboardEvent('keypress', {
                        key: char,
                        code: 'Digit' + char,
                        keyCode: char.charCodeAt(0),
                        which: char.charCodeAt(0),
                        bubbles: true,
                        cancelable: true
                    });
                    element.dispatchEvent(keypressEvent);
                    
                    // Simulate keyup
                    var keyupEvent = new KeyboardEvent('keyup', {
                        key: char,
                        code: 'Digit' + char,
                        keyCode: char.charCodeAt(0),
                        which: char.charCodeAt(0),
                        bubbles: true,
                        cancelable: true
                    });
                    element.dispatchEvent(keyupEvent);
                    
                    console.log('[ZIP FIX] Typed character:', char, 'Current value:', element.value);
                    
                    // After typing all characters, trigger validation
                    if (index === chars.length - 1) {
                        setTimeout(function() {
                            // Trigger change event
                            element.dispatchEvent(new Event('change', {bubbles: true}));
                            
                            // Trigger blur to ensure validation
                            element.blur();
                            element.dispatchEvent(new FocusEvent('blur', {bubbles: true}));
                            element.dispatchEvent(new Event('focusout', {bubbles: true}));
                            
                            console.log('[ZIP FIX] Completed ZIP code entry, triggering validation');
                            
                            // Re-focus after a moment to check if state was populated
                            setTimeout(function() {
                                element.focus();
                                element.blur();
                                
                                // Mark as filled
                                window.zipCodeFilled = true;
                                
                                // Check if state was populated
                                setTimeout(function() {
                                    var stateElements = document.querySelectorAll('select[name*="state"], input[name*="state"], #state');
                                    var stateFound = false;
                                    
                                    stateElements.forEach(function(stateElem) {
                                        if (stateElem.value && stateElem.value !== '') {
                                            console.log('[ZIP FIX] State was populated:', stateElem.value);
                                            stateFound = true;
                                        }
                                    });
                                    
                                    if (!stateFound) {
                                        console.log('[ZIP FIX] State not auto-populated, may need manual selection');
                                    }
                                    
                                    // Look for enabled submit/continue buttons
                                    var buttons = document.querySelectorAll('button, input[type="submit"]');
                                    buttons.forEach(function(btn) {
                                        var text = btn.textContent || btn.value || '';
                                        if (text.toLowerCase().includes('quote') || text.toLowerCase().includes('continue')) {
                                            if (!btn.disabled) {
                                                console.log('[ZIP FIX] Quote button is enabled:', text);
                                            }
                                        }
                                    });
                                }, 500);
                            }, 100);
                        }, 200);
                    }
                }, index * 150); // 150ms delay between each character
            });
        }, 100);
    }
    """

def apply_zip_code_fix_to_scanner():
    """
    Creates the modified scanner code with enhanced ZIP code entry
    """
    
    # Read the current scanner
    with open('/home/corp06/software_projects/New-scanner-quoter/geico_scanner_https.py', 'r') as f:
        content = f.read()
    
    # Find the ZIP code filling section
    zip_section_start = content.find("# Click and fill the zip code")
    if zip_section_start == -1:
        print("[ERROR] Could not find ZIP code section")
        return False
    
    # Find the end of the JavaScript execution for ZIP code
    zip_section_end = content.find('print("[DEBUG] Successfully filled zip code 44256")', zip_section_start)
    if zip_section_end == -1:
        print("[ERROR] Could not find end of ZIP code section")
        return False
    
    # Extract the section to replace
    old_section = content[zip_section_start:zip_section_end]
    
    # Create the new section with enhanced ZIP code entry
    new_section = """# Click and fill the zip code with enhanced event simulation
                                    print("[DEBUG] Using enhanced ZIP code entry method...")
                                    
                                    # First, inject the enhanced fill function
                                    driver.execute_script('''
                                    function fillZipCodeProperly(element, zipCode) {
                                        console.log('[ZIP FIX] Starting enhanced ZIP code entry for:', zipCode);
                                        
                                        // First, ensure element is ready
                                        element.scrollIntoView({block: 'center'});
                                        
                                        // Trigger focus event
                                        element.focus();
                                        element.dispatchEvent(new FocusEvent('focus', {bubbles: true}));
                                        element.dispatchEvent(new Event('focusin', {bubbles: true}));
                                        
                                        // Clear existing value properly
                                        element.select();
                                        element.value = '';
                                        
                                        // Small delay after clearing
                                        setTimeout(function() {
                                            // Type each character individually
                                            var chars = zipCode.split('');
                                            var currentValue = '';
                                            
                                            chars.forEach(function(char, index) {
                                                setTimeout(function() {
                                                    currentValue += char;
                                                    
                                                    // Simulate keydown
                                                    var keydownEvent = new KeyboardEvent('keydown', {
                                                        key: char,
                                                        code: 'Digit' + char,
                                                        keyCode: char.charCodeAt(0),
                                                        which: char.charCodeAt(0),
                                                        bubbles: true,
                                                        cancelable: true
                                                    });
                                                    element.dispatchEvent(keydownEvent);
                                                    
                                                    // Update value
                                                    element.value = currentValue;
                                                    
                                                    // Simulate input event
                                                    var inputEvent;
                                                    if (typeof InputEvent !== 'undefined') {
                                                        try {
                                                            inputEvent = new InputEvent('input', {
                                                                data: char,
                                                                inputType: 'insertText',
                                                                bubbles: true,
                                                                cancelable: true
                                                            });
                                                        } catch (e) {
                                                            // Fallback for browsers that don't support InputEvent constructor
                                                            inputEvent = new Event('input', {bubbles: true});
                                                        }
                                                    } else {
                                                        inputEvent = new Event('input', {bubbles: true});
                                                    }
                                                    element.dispatchEvent(inputEvent);
                                                    
                                                    // Simulate keypress
                                                    var keypressEvent = new KeyboardEvent('keypress', {
                                                        key: char,
                                                        code: 'Digit' + char,
                                                        keyCode: char.charCodeAt(0),
                                                        which: char.charCodeAt(0),
                                                        bubbles: true,
                                                        cancelable: true
                                                    });
                                                    element.dispatchEvent(keypressEvent);
                                                    
                                                    // Simulate keyup
                                                    var keyupEvent = new KeyboardEvent('keyup', {
                                                        key: char,
                                                        code: 'Digit' + char,
                                                        keyCode: char.charCodeAt(0),
                                                        which: char.charCodeAt(0),
                                                        bubbles: true,
                                                        cancelable: true
                                                    });
                                                    element.dispatchEvent(keyupEvent);
                                                    
                                                    console.log('[ZIP FIX] Typed character:', char, 'Current value:', element.value);
                                                    
                                                    // After typing all characters, trigger validation
                                                    if (index === chars.length - 1) {
                                                        setTimeout(function() {
                                                            // Trigger change event
                                                            element.dispatchEvent(new Event('change', {bubbles: true}));
                                                            
                                                            // Trigger blur to ensure validation
                                                            element.blur();
                                                            element.dispatchEvent(new FocusEvent('blur', {bubbles: true}));
                                                            element.dispatchEvent(new Event('focusout', {bubbles: true}));
                                                            
                                                            console.log('[ZIP FIX] Completed ZIP code entry, triggering validation');
                                                            
                                                            // Re-focus after a moment to check if state was populated
                                                            setTimeout(function() {
                                                                element.focus();
                                                                element.blur();
                                                                
                                                                // Mark as filled
                                                                window.zipCodeFilled = true;
                                                                
                                                                console.log('[ZIP FIX] ZIP code entry completed');
                                                            }, 100);
                                                        }, 200);
                                                    }
                                                }, index * 150); // 150ms delay between each character
                                            });
                                        }, 100);
                                    }
                                    ''')
                                    
                                    # Now use the function to fill the ZIP code
                                    driver.execute_script("""
                                        var elem = arguments[0];
                                        fillZipCodeProperly(elem, '44256');
                                    """, zip_elem)
                                    
                                    # Wait for the typing to complete (5 digits * 150ms + buffer)
                                    time.sleep(2)
                                    
                                    """
    
    # Replace the old section with the new one
    new_content = content.replace(old_section, new_section)
    
    # Save to a new file
    output_path = '/home/corp06/software_projects/New-scanner-quoter/geico_scanner_https_ZIP_FIX.py'
    with open(output_path, 'w') as f:
        f.write(new_content)
    
    print(f"[SUCCESS] Created enhanced scanner with ZIP code fix: {output_path}")
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Test mode - just show the JavaScript
        print("Enhanced ZIP code entry JavaScript:")
        print(create_enhanced_zip_code_filler())
    else:
        # Apply the fix to the scanner
        apply_zip_code_fix_to_scanner()