#!/usr/bin/env python3
"""
Click the Commercial Auto/Trucking checkbox on GEICO dashboard
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

try:
    driver = webdriver.Chrome(options=chrome_options)
    
    print("\nCLICKING COMMERCIAL AUTO/TRUCKING CHECKBOX")
    print("="*60)
    
    # Find the Commercial Auto/Trucking checkbox by the label text
    try:
        # Method 1: Find the label and then find the checkbox
        label = driver.find_element(By.XPATH, "//label[contains(., 'Commercial Auto/Trucking')]")
        print("✓ Found Commercial Auto/Trucking label")
        
        # Find the checkbox within or associated with this label
        checkbox = label.find_element(By.XPATH, ".//input[@type='checkbox']")
        print(f"✓ Found checkbox - Currently checked: {checkbox.is_selected()}")
        
        # Click the checkbox if not selected
        if not checkbox.is_selected():
            print("  Checkbox is NOT selected. Clicking...")
            
            # Try multiple click methods
            try:
                # Method 1: Click the checkbox directly
                checkbox.click()
                print("  ✓ Clicked checkbox directly")
            except:
                # Method 2: Click the label
                print("  Direct click failed, clicking the label...")
                label.click()
                print("  ✓ Clicked the label")
        else:
            print("  ✓ Checkbox is already selected!")
            
        # Verify it's now checked
        time.sleep(1)
        is_checked = checkbox.is_selected()
        print(f"\n✓ Checkbox is now: {'CHECKED' if is_checked else 'NOT CHECKED'}")
        
        if is_checked:
            print("\n✅ SUCCESS! Commercial Auto/Trucking is selected!")
            print("\nNext step: Click the 'Start' button in the top-left corner")
        
    except Exception as e:
        print(f"Method 1 failed: {e}")
        
        # Method 2: Use JavaScript
        print("\nTrying JavaScript method...")
        result = driver.execute_script("""
            // Find the Commercial Auto checkbox
            var labels = document.querySelectorAll('label');
            for (var i = 0; i < labels.length; i++) {
                if (labels[i].textContent.includes('Commercial Auto/Trucking')) {
                    var checkbox = labels[i].querySelector('input[type="checkbox"]');
                    if (!checkbox) {
                        // Check if checkbox is a sibling
                        checkbox = labels[i].previousElementSibling;
                        if (!checkbox || checkbox.type !== 'checkbox') {
                            checkbox = labels[i].nextElementSibling;
                        }
                    }
                    
                    if (checkbox && checkbox.type === 'checkbox') {
                        console.log('Found checkbox:', checkbox);
                        
                        // Check it
                        if (!checkbox.checked) {
                            checkbox.checked = true;
                            checkbox.dispatchEvent(new Event('change', {bubbles: true}));
                            labels[i].click(); // Also click the label
                            return 'Checkbox checked via JavaScript';
                        } else {
                            return 'Checkbox was already checked';
                        }
                    }
                }
            }
            return 'Checkbox not found';
        """)
        
        print(f"JavaScript result: {result}")
    
    # Now highlight the Start button
    print("\nHighlighting the Start button...")
    try:
        start_button = driver.find_element(By.LINK_TEXT, "Start")
        driver.execute_script("""
            arguments[0].style.border = '5px solid lime';
            arguments[0].style.backgroundColor = 'yellow';
            arguments[0].style.fontSize = '20px';
        """, start_button)
        print("✓ Start button highlighted in GREEN/YELLOW - Click it to proceed!")
    except:
        print("Could not find Start button")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()