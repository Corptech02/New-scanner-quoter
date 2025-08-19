#!/usr/bin/env python3
"""
Direct Commercial Auto clicker - connects to running Chrome and clicks the tab
Run this while the GEICO scanner is running to force click Commercial Auto
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

def click_commercial_auto():
    print("\n" + "="*60)
    print("COMMERCIAL AUTO TAB CLICKER")
    print("="*60)
    
    # Connect to Chrome with remote debugging
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✓ Connected to Chrome browser")
        print(f"Current URL: {driver.current_url}")
        
        # Wait a moment for page to stabilize
        time.sleep(1)
        
        # Try multiple methods to find and click Commercial Auto
        methods_tried = 0
        
        # Method 1: Direct XPath search
        print("\n[Method 1] Searching with XPath...")
        try:
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Commercial Auto')]")
            print(f"Found {len(elements)} elements containing 'Commercial Auto'")
            
            for elem in elements:
                if elem.is_displayed():
                    text = elem.text.strip()
                    print(f"  - Found: '{text}' ({elem.tag_name})")
                    
                    if "Commercial Auto" in text and len(text) < 100:
                        print(f"  ✓ Clicking: {text}")
                        elem.click()
                        print("  ✓ CLICKED!")
                        time.sleep(2)
                        print(f"New URL: {driver.current_url}")
                        return True
        except Exception as e:
            print(f"  ✗ Method 1 failed: {e}")
        
        # Method 2: JavaScript search and click
        print("\n[Method 2] JavaScript search and click...")
        try:
            result = driver.execute_script("""
                var elements = document.querySelectorAll('*');
                var found = [];
                
                for (var i = 0; i < elements.length; i++) {
                    var elem = elements[i];
                    if (elem.textContent && elem.textContent.includes('Commercial Auto')) {
                        // Highlight it
                        elem.style.border = '3px solid red';
                        
                        var text = elem.textContent.trim();
                        if (text.length < 100) {
                            found.push({
                                text: text,
                                tag: elem.tagName,
                                clickable: elem.onclick || elem.href || elem.tagName === 'A' || elem.tagName === 'BUTTON'
                            });
                            
                            // If it's exactly what we want, click it
                            if (text === 'Commercial Auto/Trucking' || text === 'Commercial Auto') {
                                elem.style.border = '5px solid green';
                                elem.click();
                                return {clicked: true, element: text};
                            }
                        }
                    }
                }
                
                return {clicked: false, found: found};
            """)
            
            print(f"JavaScript result: {result}")
            
            if result.get('clicked'):
                print("✓ JavaScript click successful!")
                return True
            elif result.get('found'):
                print(f"Found {len(result['found'])} potential elements:")
                for item in result['found']:
                    print(f"  - {item['tag']}: {item['text']}")
        except Exception as e:
            print(f"  ✗ Method 2 failed: {e}")
        
        # Method 3: Find by partial link text
        print("\n[Method 3] Finding by partial link text...")
        try:
            links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Commercial")
            print(f"Found {len(links)} links with 'Commercial'")
            for link in links:
                text = link.text
                print(f"  - Link: '{text}'")
                if "Auto" in text or "Trucking" in text:
                    print(f"  ✓ Clicking: {text}")
                    link.click()
                    print("  ✓ CLICKED!")
                    return True
        except Exception as e:
            print(f"  ✗ Method 3 failed: {e}")
        
        # Method 4: CSS selector for common tab patterns
        print("\n[Method 4] CSS selector search...")
        try:
            selectors = [
                "a:contains('Commercial Auto')",
                "button:contains('Commercial Auto')",
                "[role='tab']:contains('Commercial Auto')",
                ".tab:contains('Commercial Auto')",
                "li:contains('Commercial Auto')"
            ]
            
            # Since :contains is not standard CSS, use JavaScript
            result = driver.execute_script("""
                var selectors = [
                    'a', 'button', '[role="tab"]', '.tab', 'li', 'span', 'div'
                ];
                
                for (var s = 0; s < selectors.length; s++) {
                    var elements = document.querySelectorAll(selectors[s]);
                    for (var i = 0; i < elements.length; i++) {
                        if (elements[i].textContent && elements[i].textContent.includes('Commercial Auto')) {
                            elements[i].style.backgroundColor = 'yellow';
                            elements[i].click();
                            return 'Clicked: ' + elements[i].textContent.trim();
                        }
                    }
                }
                return 'Not found';
            """)
            
            print(f"CSS selector result: {result}")
            if result != 'Not found':
                print("✓ CSS selector click successful!")
                return True
        except Exception as e:
            print(f"  ✗ Method 4 failed: {e}")
        
        print("\n✗ Could not find or click Commercial Auto tab")
        
        # Show what's on the page
        print("\nShowing visible text on page:")
        texts = driver.execute_script("""
            var texts = [];
            var elements = document.querySelectorAll('a, button, [role="tab"], li');
            for (var i = 0; i < Math.min(elements.length, 30); i++) {
                if (elements[i].offsetWidth > 0 && elements[i].offsetHeight > 0) {
                    var text = elements[i].textContent.trim();
                    if (text.length > 0 && text.length < 100) {
                        texts.push(text);
                    }
                }
            }
            return texts;
        """)
        
        for i, text in enumerate(texts):
            print(f"{i+1}. {text}")
            if "commercial" in text.lower() or "auto" in text.lower():
                print("   ^^ POTENTIAL MATCH!")
                
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure the GEICO scanner is running and Chrome is open")
    
    return False

if __name__ == "__main__":
    success = click_commercial_auto()
    if success:
        print("\n✓ Successfully clicked Commercial Auto tab!")
    else:
        print("\n✗ Failed to click Commercial Auto tab")