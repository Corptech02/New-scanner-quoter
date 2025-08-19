#!/usr/bin/env python3
"""
Ultimate fix for GEICO scanner Commercial Auto clicking issue
This version aggressively searches for and clicks the Commercial Auto tab
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def fix_geico_scanner():
    """
    Direct fix that bypasses all the scanner complexity
    """
    print("\n" + "="*60)
    print("GEICO SCANNER COMMERCIAL AUTO FIX")
    print("="*60)
    
    # Connect to existing Chrome instance
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✓ Connected to browser")
        print(f"Current URL: {driver.current_url}")
        
        # Continuous loop to find and click Commercial Auto
        print("\nSearching for Commercial Auto tab...")
        attempts = 0
        
        while attempts < 300:  # Try for 5 minutes
            attempts += 1
            
            try:
                # Method 1: Direct JavaScript search and click
                result = driver.execute_script("""
                    // Clear any previous highlights
                    var highlighted = document.querySelectorAll('[style*="border: 5px solid"]');
                    for (var i = 0; i < highlighted.length; i++) {
                        highlighted[i].style.border = '';
                    }
                    
                    // Search for Commercial Auto
                    var found = false;
                    var searchTerms = ['Commercial Auto/Trucking', 'Commercial Auto / Trucking', 'Commercial Auto', 'Trucking'];
                    
                    for (var t = 0; t < searchTerms.length; t++) {
                        var elements = document.querySelectorAll('a, button, [role="tab"], [role="button"], li, span, div');
                        
                        for (var i = 0; i < elements.length; i++) {
                            var elem = elements[i];
                            var text = elem.textContent || '';
                            
                            if (text.includes(searchTerms[t]) && text.length < 100) {
                                console.log('Found element with text:', text);
                                
                                // Find clickable element
                                var clickable = elem;
                                if (elem.tagName === 'SPAN' || elem.tagName === 'DIV') {
                                    var parent = elem.parentElement;
                                    while (parent) {
                                        if (parent.tagName === 'A' || parent.tagName === 'BUTTON' || 
                                            parent.getAttribute('role') === 'tab' || 
                                            parent.getAttribute('onclick') ||
                                            parent.style.cursor === 'pointer') {
                                            clickable = parent;
                                            break;
                                        }
                                        parent = parent.parentElement;
                                    }
                                }
                                
                                // Highlight in GREEN
                                clickable.style.border = '5px solid #00FF00';
                                clickable.style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
                                clickable.style.boxShadow = '0 0 30px #00FF00';
                                clickable.scrollIntoView({block: 'center'});
                                
                                // Click it
                                clickable.click();
                                found = true;
                                
                                return {
                                    found: true,
                                    text: text,
                                    tag: clickable.tagName
                                };
                            }
                        }
                    }
                    
                    return {found: false};
                """)
                
                if result['found']:
                    print(f"\n✓ FOUND AND CLICKED: {result['text']} ({result['tag']})")
                    print("✓ Look for GREEN highlight!")
                    time.sleep(3)
                    print(f"New URL: {driver.current_url}")
                    break
                
            except Exception as e:
                pass
            
            # Check every 0.5 seconds
            if attempts % 10 == 0:
                print(f"Still searching... (attempt {attempts})")
            
            time.sleep(0.5)
        
        if attempts >= 300:
            print("\n✗ Could not find Commercial Auto tab after 5 minutes")
            
            # Show what's on the page
            try:
                visible_elements = driver.execute_script("""
                    var texts = [];
                    var clickables = document.querySelectorAll('a, button, [role="tab"], li');
                    for (var i = 0; i < Math.min(clickables.length, 20); i++) {
                        if (clickables[i].offsetWidth > 0) {
                            texts.push(clickables[i].textContent.trim().substring(0, 50));
                        }
                    }
                    return texts;
                """)
                print("\nVisible clickable elements on page:")
                for text in visible_elements:
                    print(f"  - {text}")
            except:
                pass
                
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure:")
        print("1. Chrome is running with --remote-debugging-port=9222")
        print("2. You're logged into GEICO")

if __name__ == "__main__":
    fix_geico_scanner()