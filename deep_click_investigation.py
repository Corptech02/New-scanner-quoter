#!/usr/bin/env python3
"""
Deep investigation and clicking of Commercial Auto tab
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

try:
    driver = webdriver.Chrome(options=chrome_options)
    
    print("DEEP COMMERCIAL AUTO INVESTIGATION")
    print("="*60)
    
    initial_url = driver.current_url
    print(f"Starting URL: {initial_url[:80]}...")
    
    # Save initial screenshot
    driver.save_screenshot("/tmp/geico_before.png")
    
    # Find all Commercial Auto elements
    elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Commercial Auto')]")
    print(f"\nFound {len(elements)} elements containing 'Commercial Auto'")
    
    target_found = False
    
    for i, elem in enumerate(elements):
        try:
            text = elem.text.strip()
            if text == "Commercial Auto/Trucking":
                print(f"\n🎯 TARGET FOUND - Element {i+1}:")
                print(f"  Text: '{text}'")
                print(f"  Tag: {elem.tag_name}")
                
                # Get detailed info
                rect = elem.rect
                print(f"  Position: x={rect['x']}, y={rect['y']}")
                print(f"  Size: {rect['width']}x{rect['height']}")
                
                # Make it super visible
                driver.execute_script("""
                    var elem = arguments[0];
                    elem.style.border = '5px solid red';
                    elem.style.backgroundColor = 'yellow';
                    elem.style.fontSize = '20px';
                    elem.style.padding = '10px';
                    elem.style.zIndex = '99999';
                    elem.style.position = 'relative';
                """, elem)
                
                print("  ✓ Element highlighted in RED/YELLOW")
                time.sleep(1)
                
                # Get parent hierarchy
                parent = elem.find_element(By.XPATH, "..")
                grandparent = parent.find_element(By.XPATH, "..")
                
                print(f"  Parent: {parent.tag_name} (class: {parent.get_attribute('class')})")
                print(f"  Grandparent: {grandparent.tag_name}")
                
                # Try clicking at different levels
                print("\n  Attempting clicks:")
                
                # 1. ActionChains click on exact position
                print("  1. ActionChains click...")
                try:
                    actions = ActionChains(driver)
                    actions.move_to_element(elem).click().perform()
                    print("     ✓ ActionChains executed")
                except Exception as e:
                    print(f"     ✗ Failed: {str(e)[:50]}")
                
                time.sleep(1)
                
                # 2. JavaScript click on element
                print("  2. JavaScript element click...")
                driver.execute_script("arguments[0].click();", elem)
                print("     ✓ Executed")
                
                time.sleep(1)
                
                # 3. JavaScript click on parent
                print("  3. JavaScript parent click...")
                driver.execute_script("arguments[0].click();", parent)
                print("     ✓ Executed")
                
                time.sleep(1)
                
                # 4. Simulate mouse events
                print("  4. Simulating mouse events...")
                driver.execute_script("""
                    var elem = arguments[0];
                    var evt = new MouseEvent('mousedown', {bubbles: true});
                    elem.dispatchEvent(evt);
                    evt = new MouseEvent('mouseup', {bubbles: true});
                    elem.dispatchEvent(evt);
                    evt = new MouseEvent('click', {bubbles: true});
                    elem.dispatchEvent(evt);
                """, elem)
                print("     ✓ Mouse events dispatched")
                
                time.sleep(1)
                
                # 5. Find and click the actual link/button
                print("  5. Looking for clickable ancestor...")
                clickable = driver.execute_script("""
                    var elem = arguments[0];
                    var current = elem;
                    
                    // Walk up the DOM tree
                    while (current && current.tagName !== 'BODY') {
                        if (current.tagName === 'A' || 
                            current.tagName === 'BUTTON' ||
                            current.onclick ||
                            current.getAttribute('href') ||
                            current.style.cursor === 'pointer') {
                            
                            current.style.border = '5px solid green';
                            current.click();
                            return current.tagName + ' clicked';
                        }
                        current = current.parentElement;
                    }
                    return 'No clickable ancestor found';
                """, elem)
                print(f"     Result: {clickable}")
                
                target_found = True
                break
                
        except Exception as e:
            print(f"Error with element {i+1}: {e}")
    
    # Wait and check results
    time.sleep(3)
    
    # Save after screenshot
    driver.save_screenshot("/tmp/geico_after.png")
    
    # Check if anything changed
    final_url = driver.current_url
    print(f"\n\nRESULTS:")
    print(f"Initial URL: {initial_url[:80]}...")
    print(f"Final URL:   {final_url[:80]}...")
    
    if initial_url != final_url:
        print("\n✅ SUCCESS! URL changed - navigation occurred!")
    else:
        print("\n❌ URL did not change")
        
        # Check if page content changed
        print("\nChecking for page changes...")
        new_text = driver.find_element(By.TAG_NAME, "body").text
        if "quote" in final_url.lower() or "commercial" in final_url.lower():
            print("✓ URL contains 'quote' or 'commercial'")
        
        # Try one more aggressive approach
        if not target_found:
            print("\n🔧 FINAL ATTEMPT - Brute force JavaScript:")
            result = driver.execute_script("""
                // Find any element that might navigate to Commercial Auto
                var links = document.querySelectorAll('a, button');
                for (var i = 0; i < links.length; i++) {
                    var elem = links[i];
                    if (elem.textContent && elem.textContent.includes('Commercial Auto')) {
                        console.log('Found:', elem);
                        elem.style.border = '10px solid lime';
                        
                        // Try everything
                        elem.click();
                        if (elem.href) {
                            window.location.href = elem.href;
                        }
                        return 'Attempted click on: ' + elem.textContent;
                    }
                }
                
                // Also check for any onclick handlers
                var all = document.querySelectorAll('*');
                for (var i = 0; i < all.length; i++) {
                    if (all[i].textContent === 'Commercial Auto/Trucking' && all[i].onclick) {
                        all[i].onclick();
                        return 'Called onclick handler';
                    }
                }
                
                return 'Nothing found';
            """)
            print(f"Result: {result}")
    
    print("\nScreenshots saved:")
    print("  Before: /tmp/geico_before.png")
    print("  After:  /tmp/geico_after.png")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()