#!/usr/bin/env python3
"""
Click Commercial Auto/Trucking from GEICO Dashboard
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
    
    print("\n" + "="*60)
    print("CLICKING COMMERCIAL AUTO/TRUCKING ON DASHBOARD")
    print("="*60)
    
    # Verify we're on dashboard
    body_text = driver.find_element(By.TAG_NAME, "body").text
    if "dashboard" in body_text.lower() and "Commercial Auto/Trucking" in body_text:
        print("✓ On GEICO Dashboard")
        print("✓ Commercial Auto/Trucking option found")
        
        # Find and click Commercial Auto/Trucking
        # Method 1: Direct text search
        try:
            element = driver.find_element(By.XPATH, "//*[text()='Commercial Auto/Trucking']")
            print(f"\nFound element: {element.tag_name}")
            
            # Scroll into view
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            
            # Highlight it
            driver.execute_script("""
                arguments[0].style.border = '5px solid lime';
                arguments[0].style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
            """, element)
            
            print("✓ Element highlighted in GREEN")
            time.sleep(1)
            
            # Click it
            print("Clicking Commercial Auto/Trucking...")
            element.click()
            print("✓ CLICKED!")
            
            # Wait for navigation
            time.sleep(3)
            new_url = driver.current_url
            print(f"\nNew URL: {new_url[:80]}...")
            
            # Check if we navigated
            new_text = driver.find_element(By.TAG_NAME, "body").text
            if "quote" in new_url.lower() or "commercial" in new_url.lower():
                print("✓ Successfully navigated to Commercial Auto quote!")
            else:
                print("⚠️  Click registered but may need additional action")
                
        except Exception as e:
            print(f"Method 1 failed: {e}")
            
            # Method 2: Click parent element
            try:
                print("\nTrying to click parent element...")
                element = driver.find_element(By.XPATH, "//*[contains(text(), 'Commercial Auto/Trucking')]")
                parent = element.find_element(By.XPATH, "..")
                
                print(f"Parent element: {parent.tag_name}")
                parent.click()
                print("✓ Parent clicked!")
                
            except Exception as e2:
                print(f"Method 2 failed: {e2}")
                
                # Method 3: JavaScript click all possibilities
                print("\nTrying JavaScript click...")
                result = driver.execute_script("""
                    var elements = document.querySelectorAll('*');
                    for (var i = 0; i < elements.length; i++) {
                        if (elements[i].textContent === 'Commercial Auto/Trucking') {
                            elements[i].style.border = '5px solid red';
                            elements[i].click();
                            
                            // Also try parent
                            if (elements[i].parentElement) {
                                elements[i].parentElement.click();
                            }
                            
                            return 'clicked';
                        }
                    }
                    return 'not found';
                """)
                print(f"JavaScript result: {result}")
    else:
        print("❌ Not on GEICO dashboard or Commercial Auto option not visible")
        print(f"Current URL: {driver.current_url}")
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\nDone!")