#!/usr/bin/env python3
"""
Final Commercial Auto click solution - simulates exact user behavior
"""

import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

def ensure_commercial_auto_clicked(driver):
    """
    Click Commercial Auto checkbox by simulating exact user behavior
    """
    print("\n[Commercial Auto] FINAL SOLUTION - Simulating user click...")
    
    try:
        # Find the label element (this is what users actually see and click)
        label = None
        try:
            # Method 1: Find by exact text
            labels = driver.find_elements(By.XPATH, "//label[contains(text(), 'Commercial Auto/Trucking')]")
            if labels and labels[0].is_displayed():
                label = labels[0]
                print("[Commercial Auto] Found label by text")
        except:
            pass
        
        # Method 2: Find label containing the checkbox
        if not label:
            try:
                checkbox = driver.find_element(By.CSS_SELECTOR, "input[value='CommercialAuto']")
                label = driver.find_element(By.CSS_SELECTOR, f"label[for='{checkbox.get_attribute('id')}']")
                if label.is_displayed():
                    print("[Commercial Auto] Found label by 'for' attribute")
            except:
                pass
        
        if label:
            print(f"[Commercial Auto] Label found: {label.text}")
            print(f"[Commercial Auto] Label location: {label.location}")
            print(f"[Commercial Auto] Label size: {label.size}")
            
            # Highlight the label
            driver.execute_script("""
                arguments[0].style.border = '3px solid red';
                arguments[0].style.backgroundColor = 'rgba(255, 255, 0, 0.3)';
            """, label)
            
            # Scroll to label
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
            time.sleep(0.5)
            
            # Get the exact click coordinates (left side of label where checkbox would be)
            label_rect = label.rect
            click_x = label_rect['x'] + 20  # 20 pixels from left edge
            click_y = label_rect['y'] + label_rect['height'] / 2  # Middle height
            
            print(f"[Commercial Auto] Click coordinates: ({click_x}, {click_y})")
            
            # Method 1: Use ActionChains to click at specific coordinates
            success = False
            try:
                print("[Commercial Auto] Attempting coordinate click with ActionChains...")
                actions = ActionChains(driver)
                
                # Move to the label first
                actions.move_to_element(label)
                actions.pause(0.3)
                
                # Then move to specific offset (checkbox location)
                actions.move_to_element_with_offset(label, -label.size['width']/2 + 20, 0)
                actions.pause(0.3)
                
                # Click
                actions.click()
                actions.perform()
                
                print("[Commercial Auto] ✓ Coordinate click executed")
                success = True
            except Exception as e:
                print(f"[Commercial Auto] Coordinate click failed: {e}")
            
            # Method 2: JavaScript click at coordinates
            if not success:
                try:
                    print("[Commercial Auto] Attempting JavaScript coordinate click...")
                    result = driver.execute_script("""
                        var label = arguments[0];
                        var rect = label.getBoundingClientRect();
                        
                        // Create and dispatch mouse events at checkbox location
                        var x = rect.left + 20;
                        var y = rect.top + rect.height / 2;
                        
                        console.log('Clicking at:', x, y);
                        
                        // Create mouse events
                        var mousedown = new MouseEvent('mousedown', {
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            clientX: x,
                            clientY: y
                        });
                        
                        var mouseup = new MouseEvent('mouseup', {
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            clientX: x,
                            clientY: y
                        });
                        
                        var click = new MouseEvent('click', {
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            clientX: x,
                            clientY: y
                        });
                        
                        // Find element at coordinates
                        var elem = document.elementFromPoint(x, y);
                        console.log('Element at point:', elem);
                        
                        if (elem) {
                            elem.dispatchEvent(mousedown);
                            elem.dispatchEvent(mouseup);
                            elem.dispatchEvent(click);
                            
                            // Also click the label itself
                            label.click();
                            
                            return 'Clicked at coordinates';
                        }
                        
                        return 'No element at coordinates';
                    """, label)
                    
                    print(f"[Commercial Auto] JavaScript result: {result}")
                    success = True
                except Exception as e:
                    print(f"[Commercial Auto] JavaScript click failed: {e}")
            
            # Method 3: Direct label click as fallback
            if not success:
                try:
                    print("[Commercial Auto] Attempting direct label click...")
                    label.click()
                    success = True
                    print("[Commercial Auto] ✓ Direct label click executed")
                except Exception as e:
                    print(f"[Commercial Auto] Direct click failed: {e}")
            
            if success:
                # Wait for state change
                time.sleep(1)
                
                # Verify checkbox is checked
                try:
                    checkbox = driver.find_element(By.CSS_SELECTOR, "input[value='CommercialAuto']")
                    is_checked = checkbox.is_selected()
                    print(f"[Commercial Auto] Checkbox is now: {'CHECKED' if is_checked else 'NOT CHECKED'}")
                    
                    # If not checked, force check it
                    if not is_checked:
                        print("[Commercial Auto] Force checking checkbox...")
                        driver.execute_script("""
                            var cb = document.querySelector('input[value="CommercialAuto"]');
                            if (cb) {
                                cb.checked = true;
                                cb.dispatchEvent(new Event('change', {bubbles: true}));
                            }
                        """)
                        time.sleep(0.5)
                        is_checked = checkbox.is_selected()
                        print(f"[Commercial Auto] After force: {'CHECKED' if is_checked else 'NOT CHECKED'}")
                except:
                    pass
                
                # Submit form
                print("[Commercial Auto] Submitting form...")
                submit_result = driver.execute_script("""
                    // Ensure checkbox is checked
                    var cb = document.querySelector('input[value="CommercialAuto"]');
                    if (cb && !cb.checked) {
                        cb.checked = true;
                        cb.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                    
                    // Submit form
                    var form = document.querySelector('form');
                    if (form) {
                        form.submit();
                        return 'Form submitted';
                    }
                    
                    // Click Start button
                    var links = document.querySelectorAll('a');
                    for (var i = 0; i < links.length; i++) {
                        if (links[i].textContent.trim() === 'Start') {
                            links[i].click();
                            return 'Start clicked';
                        }
                    }
                    
                    return 'No submit method found';
                """)
                
                print(f"[Commercial Auto] Submit result: {submit_result}")
                
                # Set the flag so scanner knows we clicked
                try:
                    driver.execute_script("window.commercialAutoClicked = true;")
                    print("[Commercial Auto] Set commercialAutoClicked flag to true")
                except:
                    pass
                
                return True
        else:
            print("[Commercial Auto] ✗ Could not find Commercial Auto label!")
            
            # Debug output
            print("\n[Commercial Auto] Debug: All labels on page...")
            all_labels = driver.find_elements(By.TAG_NAME, "label")
            for i, lbl in enumerate(all_labels[:5]):
                print(f"  Label {i}: '{lbl.text[:30]}...'")
            
            return False
            
    except Exception as e:
        print(f"[Commercial Auto] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False