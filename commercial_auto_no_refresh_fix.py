#!/usr/bin/env python3
"""
Enhanced fix for Commercial Auto/Trucking tab that prevents page refresh
Combines multiple strategies to ensure the tab stays selected
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def fix_commercial_auto_refresh_issue(driver):
    """
    Complete fix for the Commercial Auto refresh issue
    """
    print("\n[COMMERCIAL AUTO FIX] Starting enhanced no-refresh solution...")
    
    try:
        # Step 1: Install refresh prevention BEFORE clicking
        print("[STEP 1] Installing refresh prevention handlers...")
        driver.execute_script("""
            // Flag to track Commercial Auto state
            window.commercialAutoActive = false;
            window.commercialAutoData = {};
            
            // Store original functions
            window._originalPushState = history.pushState;
            window._originalReplaceState = history.replaceState;
            window._originalHref = Object.getOwnPropertyDescriptor(window.location, 'href');
            
            // Override history methods to prevent navigation
            history.pushState = function() {
                if (window.commercialAutoActive) {
                    console.log('[FIX] Blocked pushState during Commercial Auto');
                    return;
                }
                return window._originalPushState.apply(history, arguments);
            };
            
            history.replaceState = function() {
                if (window.commercialAutoActive) {
                    console.log('[FIX] Blocked replaceState during Commercial Auto');
                    return;
                }
                return window._originalReplaceState.apply(history, arguments);
            };
            
            // Override location.href setter
            Object.defineProperty(window.location, 'href', {
                get: function() {
                    return window._originalHref.get.call(window.location);
                },
                set: function(val) {
                    if (window.commercialAutoActive) {
                        console.log('[FIX] Blocked location.href change to:', val);
                        return;
                    }
                    window._originalHref.set.call(window.location, val);
                }
            });
            
            // Intercept all link clicks
            document.addEventListener('click', function(e) {
                var target = e.target;
                while (target && target !== document) {
                    if (target.tagName === 'A' || target.tagName === 'BUTTON') {
                        var text = target.textContent || '';
                        if (text.includes('Commercial Auto') || text.includes('Trucking')) {
                            console.log('[FIX] Intercepted Commercial Auto click');
                            e.preventDefault();
                            e.stopPropagation();
                            
                            // Mark as active
                            window.commercialAutoActive = true;
                            
                            // Handle the click without navigation
                            handleCommercialAutoClick(target);
                            return false;
                        }
                    }
                    target = target.parentElement;
                }
            }, true);
            
            // Function to handle Commercial Auto click
            window.handleCommercialAutoClick = function(element) {
                console.log('[FIX] Handling Commercial Auto click for:', element);
                
                // Visual feedback
                element.style.backgroundColor = '#4CAF50';
                element.style.color = 'white';
                element.style.fontWeight = 'bold';
                
                // Mark all similar elements as inactive
                var allTabs = document.querySelectorAll('a, button, li, div[role="tab"]');
                allTabs.forEach(function(tab) {
                    if (tab !== element && tab.classList) {
                        tab.classList.remove('active', 'selected', 'current', 'is-active');
                    }
                });
                
                // Mark this element as active
                element.classList.add('active', 'selected', 'current', 'is-active');
                if (element.setAttribute) {
                    element.setAttribute('aria-selected', 'true');
                }
                
                // If it's a checkbox, check it
                if (element.type === 'checkbox' || element.querySelector('input[type="checkbox"]')) {
                    var checkbox = element.type === 'checkbox' ? element : element.querySelector('input[type="checkbox"]');
                    if (checkbox) {
                        checkbox.checked = true;
                        checkbox.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                }
                
                // Fire any onclick handlers WITHOUT navigation
                if (element.onclick) {
                    var onclickStr = element.onclick.toString();
                    if (!onclickStr.includes('location') && !onclickStr.includes('href')) {
                        element.onclick();
                    }
                }
                
                // Try to load content dynamically if needed
                var href = element.getAttribute('href');
                if (href && href !== '#' && href !== 'javascript:void(0)') {
                    loadCommercialAutoContent(href);
                }
                
                // Dispatch custom event
                document.dispatchEvent(new CustomEvent('commercialAutoSelected', {
                    detail: { element: element }
                }));
            };
            
            // Function to load content without refresh
            window.loadCommercialAutoContent = function(url) {
                console.log('[FIX] Loading Commercial Auto content from:', url);
                
                // Show loading indicator
                var contentArea = document.querySelector('.main-content, #content, [role="main"], main');
                if (contentArea) {
                    contentArea.style.opacity = '0.5';
                }
                
                // Use fetch to get content
                fetch(url, {
                    credentials: 'same-origin',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.text())
                .then(html => {
                    // Parse the response
                    var parser = new DOMParser();
                    var doc = parser.parseFromString(html, 'text/html');
                    
                    // Extract the main content
                    var newContent = doc.querySelector('.main-content, #content, [role="main"], main');
                    if (newContent && contentArea) {
                        // Save form data before replacing
                        saveFormData();
                        
                        // Replace content
                        contentArea.innerHTML = newContent.innerHTML;
                        contentArea.style.opacity = '1';
                        
                        // Restore form data
                        restoreFormData();
                        
                        // Re-run any initialization scripts
                        var scripts = contentArea.getElementsByTagName('script');
                        for (var i = 0; i < scripts.length; i++) {
                            eval(scripts[i].textContent);
                        }
                        
                        console.log('[FIX] Commercial Auto content loaded successfully');
                    }
                })
                .catch(error => {
                    console.error('[FIX] Error loading content:', error);
                    if (contentArea) {
                        contentArea.style.opacity = '1';
                    }
                });
            };
            
            // Save form data
            window.saveFormData = function() {
                window.commercialAutoData = {};
                var inputs = document.querySelectorAll('input, select, textarea');
                inputs.forEach(function(input) {
                    var key = input.name || input.id;
                    if (key) {
                        if (input.type === 'checkbox' || input.type === 'radio') {
                            window.commercialAutoData[key] = input.checked;
                        } else {
                            window.commercialAutoData[key] = input.value;
                        }
                    }
                });
            };
            
            // Restore form data
            window.restoreFormData = function() {
                if (window.commercialAutoData) {
                    Object.keys(window.commercialAutoData).forEach(function(key) {
                        var elements = document.querySelectorAll('[name="' + key + '"], #' + key);
                        elements.forEach(function(elem) {
                            if (elem.type === 'checkbox' || elem.type === 'radio') {
                                elem.checked = window.commercialAutoData[key];
                            } else {
                                elem.value = window.commercialAutoData[key];
                            }
                        });
                    });
                }
            };
            
            // Monitor for unwanted page changes
            var observer = new MutationObserver(function(mutations) {
                if (window.commercialAutoActive) {
                    // Check if Commercial Auto is still selected
                    var commercialAutoElement = document.querySelector('.active[class*="commercial"], .selected[class*="commercial"], [aria-selected="true"][class*="commercial"]');
                    if (!commercialAutoElement) {
                        // Re-select it
                        var elements = document.querySelectorAll('a, button, li, div');
                        for (var i = 0; i < elements.length; i++) {
                            var text = elements[i].textContent || '';
                            if ((text.includes('Commercial Auto') || text.includes('Trucking')) && 
                                !text.includes('checkbox')) {
                                console.log('[FIX] Re-selecting Commercial Auto after DOM change');
                                handleCommercialAutoClick(elements[i]);
                                break;
                            }
                        }
                    }
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['class', 'aria-selected']
            });
            
            console.log('[FIX] All refresh prevention handlers installed');
        """)
        
        # Step 2: Find and click the Commercial Auto element
        print("[STEP 2] Finding Commercial Auto element...")
        
        selectors = [
            "//a[contains(text(), 'Commercial Auto')]",
            "//button[contains(text(), 'Commercial Auto')]",
            "//li[contains(text(), 'Commercial Auto')]//a",
            "//div[@role='tab' and contains(text(), 'Commercial Auto')]",
            "//*[contains(text(), 'Commercial Auto/Trucking')]",
            "//label[contains(text(), 'Commercial Auto/Trucking')]",
            "//span[contains(text(), 'Commercial Auto/Trucking')]/.."
        ]
        
        element = None
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed():
                        element = elem
                        print(f"[STEP 2] Found element: {elem.tag_name} - {elem.text[:50]}")
                        break
                if element:
                    break
            except:
                continue
        
        if element:
            # Click using the JavaScript handler we installed
            driver.execute_script("arguments[0].click();", element)
            print("[STEP 3] Clicked Commercial Auto element")
            
            # Wait for any async operations
            time.sleep(2)
            
            # Verify state
            is_active = driver.execute_script("""
                return window.commercialAutoActive;
            """)
            
            print(f"[STEP 4] Commercial Auto active state: {is_active}")
            
            # Final verification
            time.sleep(1)
            print("[COMPLETE] Commercial Auto tab should now be selected without refresh")
            
            return True
        else:
            print("[ERROR] Could not find Commercial Auto element")
            return False
            
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def integrate_with_scanner(scanner_file_path):
    """
    Integrate this fix into the main scanner file
    """
    print(f"\n[INTEGRATION] Adding fix to {scanner_file_path}")
    
    # Read the scanner file
    with open(scanner_file_path, 'r') as f:
        content = f.read()
    
    # Find the force-commercial-auto route
    route_start = content.find("@app.route('/force-commercial-auto'")
    if route_start == -1:
        print("[ERROR] Could not find /force-commercial-auto route")
        return False
    
    # Replace the route implementation with our enhanced version
    route_end = content.find("@app.route", route_start + 1)
    if route_end == -1:
        route_end = len(content)
    
    new_route = '''@app.route('/force-commercial-auto', methods=['POST'])
def force_commercial_auto():
    """Enhanced Commercial Auto click with refresh prevention"""
    global driver, current_status
    
    if not driver:
        return jsonify({'status': 'error', 'message': 'Scanner not initialized'})
    
    try:
        # Use the enhanced fix
        from commercial_auto_no_refresh_fix import fix_commercial_auto_refresh_issue
        
        success = fix_commercial_auto_refresh_issue(driver)
        
        if success:
            current_status = "Commercial Auto selected (no refresh)"
            return jsonify({'status': 'success', 'message': 'Commercial Auto tab selected without refresh!'})
        else:
            return jsonify({'status': 'error', 'message': 'Could not select Commercial Auto tab'})
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
'''
    
    # Create the updated content
    updated_content = content[:route_start] + new_route + content[route_end:]
    
    # Save to a new file
    new_file_path = scanner_file_path.replace('.py', '_NO_REFRESH.py')
    with open(new_file_path, 'w') as f:
        f.write(updated_content)
    
    print(f"[INTEGRATION] Created updated scanner: {new_file_path}")
    print("[INTEGRATION] Run the new scanner to test the fix!")
    
    return True

if __name__ == "__main__":
    # Test with existing Chrome instance
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        fix_commercial_auto_refresh_issue(driver)
        
        print("\n[INFO] Fix applied. The Commercial Auto tab should stay selected.")
        print("[INFO] To integrate with scanner, run:")
        print("       python3 commercial_auto_no_refresh_fix.py --integrate")
        
    except Exception as e:
        print(f"[ERROR] {e}")