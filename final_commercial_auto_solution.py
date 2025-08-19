#!/usr/bin/env python3
"""
Final solution to check Commercial Auto/Trucking and proceed
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.webdriver.common.action_chains import ActionChains
import time

def check_commercial_auto_and_proceed():
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        
        print("\nFINAL COMMERCIAL AUTO SOLUTION")
        print("="*60)
        
        # Take initial screenshot
        driver.save_screenshot("/tmp/before_fix.png")
        
        # Step 1: Find and check the Commercial Auto checkbox using multiple methods
        print("\nStep 1: Checking Commercial Auto/Trucking checkbox...")
        
        # Method 1: Find by partial ID
        checkbox_found = False
        try:
            checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
            print(f"Found {len(checkboxes)} checkboxes on page")
            
            for cb in checkboxes:
                cb_id = cb.get_attribute("id") or ""
                cb_name = cb.get_attribute("name") or ""
                cb_value = cb.get_attribute("value") or ""
                
                if "CommercialAuto" in cb_value or "CommercialAuto" in cb_id or "CommercialAuto" in cb_name:
                    print(f"\n✓ Found Commercial Auto checkbox!")
                    print(f"  ID: {cb_id}")
                    print(f"  Name: {cb_name}")
                    print(f"  Value: {cb_value}")
                    print(f"  Currently checked: {cb.is_selected()}")
                    
                    if not cb.is_selected():
                        # Make it visible first
                        driver.execute_script("""
                            arguments[0].style.display = 'block';
                            arguments[0].style.visibility = 'visible';
                            arguments[0].style.opacity = '1';
                            arguments[0].style.width = '20px';
                            arguments[0].style.height = '20px';
                        """, cb)
                        
                        # Try clicking it
                        try:
                            cb.click()
                            print("  ✓ Clicked checkbox directly")
                        except:
                            # Click using JavaScript
                            driver.execute_script("arguments[0].click();", cb)
                            print("  ✓ Clicked checkbox via JavaScript")
                        
                        # Also set checked property
                        driver.execute_script("arguments[0].checked = true;", cb)
                        
                        # Trigger change event
                        driver.execute_script("""
                            arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                            arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                        """, cb)
                        
                        checkbox_found = True
                        break
                    else:
                        print("  ✓ Checkbox already checked!")
                        checkbox_found = True
                        break
        except Exception as e:
            print(f"Method 1 error: {e}")
        
        # Method 2: Click the label containing Commercial Auto/Trucking
        if not checkbox_found:
            print("\nMethod 2: Clicking the label...")
            try:
                # Find the span with text
                span = driver.find_element(By.XPATH, "//span[text()='Commercial Auto/Trucking']")
                print("Found Commercial Auto/Trucking span")
                
                # Get parent label
                label = span.find_element(By.XPATH, "..")
                print(f"Parent element: {label.tag_name}")
                
                # Click the label
                label.click()
                print("✓ Clicked the label")
                checkbox_found = True
            except Exception as e:
                print(f"Method 2 error: {e}")
        
        # Method 3: Use coordinates
        if not checkbox_found:
            print("\nMethod 3: Clicking by coordinates...")
            try:
                # Based on the screenshot, the checkbox is around x=1310, y=560
                actions = ActionChains(driver)
                
                # Click slightly to the left of the text where checkbox should be
                actions.move_to_element_with_offset(driver.find_element(By.TAG_NAME, "body"), 1290, 560)
                actions.click()
                actions.perform()
                print("✓ Clicked at checkbox coordinates")
            except Exception as e:
                print(f"Method 3 error: {e}")
        
        # Wait a moment
        time.sleep(2)
        
        # Verify checkbox is now checked
        print("\nVerifying checkbox state...")
        is_checked = driver.execute_script("""
            var checkboxes = document.querySelectorAll('input[type="checkbox"]');
            for (var i = 0; i < checkboxes.length; i++) {
                if (checkboxes[i].value === 'CommercialAuto' || 
                    checkboxes[i].id.includes('CommercialAuto')) {
                    return checkboxes[i].checked;
                }
            }
            return false;
        """)
        
        print(f"Commercial Auto checkbox is now: {'CHECKED' if is_checked else 'NOT CHECKED'}")
        
        # Take screenshot after checkbox
        driver.save_screenshot("/tmp/after_checkbox.png")
        
        # Step 2: Click Start button
        print("\nStep 2: Clicking Start button...")
        try:
            start_button = driver.find_element(By.LINK_TEXT, "Start")
            start_button.click()
            print("✓ Start button clicked!")
            
            time.sleep(3)
            
            new_url = driver.current_url
            print(f"\nFinal URL: {new_url[:100]}...")
            
            # Take final screenshot
            driver.save_screenshot("/tmp/final_page.png")
            
            print("\n✅ COMPLETE! Check screenshots:")
            print("  - /tmp/before_fix.png (initial state)")
            print("  - /tmp/after_checkbox.png (after checkbox click)")
            print("  - /tmp/final_page.png (final result)")
            
        except Exception as e:
            print(f"Error clicking Start: {e}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_commercial_auto_and_proceed()