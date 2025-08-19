#!/usr/bin/env python3
"""
Force check the Commercial Auto checkbox and submit
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

try:
    driver = webdriver.Chrome(options=chrome_options)
    
    print("\nFORCING COMMERCIAL AUTO CHECKBOX")
    print("="*60)
    
    # Force check the checkbox with JavaScript
    result = driver.execute_script("""
        // Find the Commercial Auto checkbox
        var checkbox = document.getElementById('checkbox-Id_ExtendsGiveAgencyBundlingOptions_37522-CommercialAuto');
        
        if (!checkbox) {
            // Try to find by other means
            var inputs = document.querySelectorAll('input[type="checkbox"]');
            for (var i = 0; i < inputs.length; i++) {
                if (inputs[i].value === 'CommercialAuto' || 
                    inputs[i].name.includes('CommercialAuto')) {
                    checkbox = inputs[i];
                    break;
                }
            }
        }
        
        if (checkbox) {
            console.log('Found checkbox:', checkbox);
            
            // Make it visible and interactable
            checkbox.style.display = 'block';
            checkbox.style.visibility = 'visible';
            checkbox.style.opacity = '1';
            checkbox.style.width = '20px';
            checkbox.style.height = '20px';
            checkbox.style.position = 'relative';
            checkbox.style.zIndex = '9999';
            
            // Check it
            checkbox.checked = true;
            
            // Trigger change events
            checkbox.dispatchEvent(new Event('change', {bubbles: true}));
            checkbox.dispatchEvent(new Event('click', {bubbles: true}));
            
            // Also click the label
            var label = checkbox.parentElement;
            if (label && label.tagName === 'LABEL') {
                label.style.border = '3px solid green';
                label.click();
            }
            
            return 'Checkbox checked: ' + checkbox.checked;
        } else {
            return 'Checkbox not found';
        }
    """)
    
    print(f"Result: {result}")
    
    # Wait a moment
    time.sleep(1)
    
    # Now look for and click submit/continue button
    print("\nLooking for submit button...")
    
    submit_result = driver.execute_script("""
        // Find submit/continue button
        var buttons = document.querySelectorAll('button, input[type="submit"], a');
        var foundButton = null;
        
        for (var i = 0; i < buttons.length; i++) {
            var btn = buttons[i];
            var text = (btn.textContent || btn.value || '').toLowerCase();
            
            if (text.includes('continue') || 
                text.includes('next') || 
                text.includes('submit') || 
                text.includes('start quote') ||
                text.includes('get quote')) {
                
                if (btn.offsetWidth > 0 && btn.offsetHeight > 0) {
                    foundButton = btn;
                    console.log('Found button:', text);
                    break;
                }
            }
        }
        
        if (foundButton) {
            foundButton.style.border = '5px solid red';
            foundButton.style.backgroundColor = 'yellow';
            
            // Scroll to it
            foundButton.scrollIntoView({block: 'center'});
            
            // Click it
            foundButton.click();
            
            // If it's a link, navigate
            if (foundButton.href) {
                window.location.href = foundButton.href;
            }
            
            return 'Button clicked: ' + (foundButton.textContent || foundButton.value);
        } else {
            return 'No submit button found';
        }
    """)
    
    print(f"Submit result: {submit_result}")
    
    # Wait for navigation
    time.sleep(3)
    
    # Check final state
    print(f"\nFinal URL: {driver.current_url[:80]}...")
    
    # Verify Commercial Auto is selected
    verify = driver.execute_script("""
        var checkbox = document.querySelector('input[value="CommercialAuto"]');
        if (checkbox) {
            return 'Commercial Auto checkbox is ' + (checkbox.checked ? 'CHECKED' : 'NOT CHECKED');
        }
        return 'Checkbox not found';
    """)
    
    print(f"Verification: {verify}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()