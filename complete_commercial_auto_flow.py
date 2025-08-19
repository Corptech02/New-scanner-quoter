#!/usr/bin/env python3
"""
Complete flow to select Commercial Auto and proceed
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

def complete_commercial_auto_selection():
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        print("\nCOMPLETE COMMERCIAL AUTO SELECTION FLOW")
        print("="*60)
        
        initial_url = driver.current_url
        print(f"Starting URL: {initial_url[:80]}...")
        
        # Step 1: Check/Select Commercial Auto checkbox
        print("\nStep 1: Checking Commercial Auto checkbox...")
        
        checkbox_result = driver.execute_script("""
            // Find and check Commercial Auto checkbox
            var checkboxes = document.querySelectorAll('input[type="checkbox"]');
            var found = false;
            
            for (var i = 0; i < checkboxes.length; i++) {
                var cb = checkboxes[i];
                var label = cb.parentElement;
                var text = label ? label.textContent : '';
                
                if (cb.value === 'CommercialAuto' || text.includes('Commercial Auto')) {
                    // Make visible
                    cb.style.display = 'block';
                    cb.style.opacity = '1';
                    
                    if (!cb.checked) {
                        cb.checked = true;
                        cb.dispatchEvent(new Event('change', {bubbles: true}));
                        cb.dispatchEvent(new Event('click', {bubbles: true}));
                        
                        // Also click the label
                        if (label && label.tagName === 'LABEL') {
                            label.style.border = '3px solid green';
                            label.click();
                        }
                        
                        return 'Checkbox was unchecked - now CHECKED';
                    } else {
                        return 'Checkbox was already CHECKED';
                    }
                }
            }
            
            return 'Commercial Auto checkbox not found';
        """)
        
        print(f"  Result: {checkbox_result}")
        time.sleep(1)
        
        # Step 2: Click Start/Continue/Next
        print("\nStep 2: Looking for proceed button/link...")
        
        proceed_result = driver.execute_script("""
            // Find any proceed element
            var elements = document.querySelectorAll('a, button, input[type="submit"]');
            var candidates = [];
            
            for (var i = 0; i < elements.length; i++) {
                var elem = elements[i];
                if (elem.offsetWidth > 0 && elem.offsetHeight > 0) {
                    var text = (elem.textContent || elem.value || '').trim().toLowerCase();
                    
                    if (text === 'start' || 
                        text.includes('continue') || 
                        text.includes('next') || 
                        text.includes('proceed') ||
                        text.includes('begin') ||
                        text.includes('get quote') ||
                        text.includes('start quote')) {
                        
                        candidates.push({
                            text: elem.textContent || elem.value,
                            tag: elem.tagName,
                            elem: elem
                        });
                    }
                }
            }
            
            // Click the first good candidate
            if (candidates.length > 0) {
                var target = candidates[0].elem;
                target.style.border = '5px solid red';
                target.style.backgroundColor = 'yellow';
                target.scrollIntoView({block: 'center'});
                
                // Try to click
                target.click();
                
                // If it's a link, also try navigation
                if (target.href) {
                    setTimeout(function() {
                        window.location.href = target.href;
                    }, 500);
                }
                
                return 'Clicked: ' + candidates[0].text + ' (' + candidates[0].tag + ')';
            }
            
            return 'No proceed button found - ' + candidates.length + ' candidates';
        """)
        
        print(f"  Result: {proceed_result}")
        
        # Wait for any navigation
        time.sleep(3)
        
        # Check final state
        final_url = driver.current_url
        print(f"\nFinal URL: {final_url[:80]}...")
        
        if initial_url != final_url:
            print("\n✅ SUCCESS! Navigation occurred!")
            print("You should now be on the Commercial Auto quote page.")
        else:
            print("\n⚠️  URL did not change")
            print("\nTroubleshooting:")
            print("1. Check if Commercial Auto checkbox is visibly checked")
            print("2. Look for any error messages on the page")
            print("3. Try manually clicking any visible 'Start' or 'Continue' button")
            
            # Show current page state
            body_text = driver.find_element(By.TAG_NAME, "body").text
            lines = body_text.split('\n')[:20]
            print("\nFirst 20 lines of current page:")
            for i, line in enumerate(lines):
                if line.strip():
                    print(f"  {i+1}. {line.strip()}")
        
        return final_url != initial_url
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = complete_commercial_auto_selection()
    
    if not success:
        print("\n" + "="*60)
        print("MANUAL STEPS:")
        print("1. Make sure Commercial Auto/Trucking checkbox is checked")
        print("2. Click the 'Start' button (usually at top of page)")
        print("3. If no Start button, look for Continue/Next/Begin Quote")
        print("="*60)