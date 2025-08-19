#!/usr/bin/env python3
"""
Fix for Commercial Auto/Trucking tab page refresh issue
Prevents page reset and maintains data/click state
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def handle_commercial_auto_tab(driver):
    """
    Enhanced Commercial Auto tab handler that prevents page refresh
    """
    print("\n[Commercial Auto Fix] Starting enhanced click handler...")
    
    try:
        # First, check if we're already on Commercial Auto page
        current_url = driver.current_url
        page_source = driver.page_source.lower()
        
        if "commercial" in current_url.lower() or ("commercial" in page_source and "trucking" in page_source):
            print("[Commercial Auto Fix] Already on Commercial Auto page")
            return True
        
        # Look for the Commercial Auto/Trucking element
        selectors = [
            # Try link elements first
            "//a[normalize-space(text())='Commercial Auto/Trucking']",
            "//a[contains(text(), 'Commercial Auto/Trucking')]",
            # Then buttons
            "//button[normalize-space(text())='Commercial Auto/Trucking']",
            "//button[contains(text(), 'Commercial Auto/Trucking')]",
            # Divs with role button
            "//div[@role='button' and contains(text(), 'Commercial Auto/Trucking')]",
            # Any clickable element
            "//*[@onclick and contains(text(), 'Commercial Auto/Trucking')]",
            # Tab elements
            "//li[contains(@class, 'tab') and contains(text(), 'Commercial Auto/Trucking')]//a",
            "//div[contains(@class, 'tab') and contains(text(), 'Commercial Auto/Trucking')]"
        ]
        
        element = None
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    # Find the most specific visible element
                    for elem in elements:
                        if elem.is_displayed():
                            element = elem
                            print(f"[Commercial Auto Fix] Found element with selector: {selector}")
                            break
                    if element:
                        break
            except:
                continue
        
        if not element:
            print("[Commercial Auto Fix] No Commercial Auto/Trucking element found")
            return False
        
        # Store current page state before clicking
        print("[Commercial Auto Fix] Preserving page state...")
        
        # Save all form data before click
        form_data = driver.execute_script("""
            var formData = {};
            var inputs = document.querySelectorAll('input, select, textarea');
            for (var i = 0; i < inputs.length; i++) {
                var input = inputs[i];
                if (input.name || input.id) {
                    var key = input.name || input.id;
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        formData[key] = input.checked;
                    } else {
                        formData[key] = input.value;
                    }
                }
            }
            window.savedFormData = formData;
            return formData;
        """)
        print(f"[Commercial Auto Fix] Saved {len(form_data)} form fields")
        
        # Check if it's a link that might cause navigation
        tag_name = element.tag_name.lower()
        href = element.get_attribute('href') if tag_name == 'a' else None
        
        if href and href != '#' and href != 'javascript:void(0)':
            print(f"[Commercial Auto Fix] Element is a link with href: {href}")
            # This is likely causing the page refresh
            
            # Method 1: Prevent default and handle click via JavaScript
            print("[Commercial Auto Fix] Using JavaScript to prevent page refresh...")
            click_result = driver.execute_script("""
                var elem = arguments[0];
                var href = elem.href;
                
                // Add event listener to prevent default
                elem.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    console.log('Commercial Auto click intercepted');
                    
                    // If there's an onclick handler, execute it
                    if (elem.onclick) {
                        elem.onclick(e);
                    }
                    
                    // Mark as clicked
                    window.commercialAutoClicked = true;
                    elem.classList.add('active');
                    elem.classList.add('selected');
                    
                    // Try to load content via AJAX if possible
                    if (href && href !== '#') {
                        // Check if page uses AJAX navigation
                        if (window.jQuery && window.jQuery.ajax) {
                            window.jQuery.ajax({
                                url: href,
                                success: function(data) {
                                    // Update page content without refresh
                                    var container = document.querySelector('.main-content, #content, main');
                                    if (container && data) {
                                        container.innerHTML = data;
                                    }
                                }
                            });
                        } else if (window.fetch) {
                            fetch(href)
                                .then(response => response.text())
                                .then(data => {
                                    var container = document.querySelector('.main-content, #content, main');
                                    if (container && data) {
                                        container.innerHTML = data;
                                    }
                                });
                        }
                    }
                }, true);
                
                // Trigger click
                elem.click();
                
                return 'Click handled without refresh';
            """, element)
            print(f"[Commercial Auto Fix] Click result: {click_result}")
            
        else:
            # Not a navigation link, should be safe to click
            print("[Commercial Auto Fix] Element is not a navigation link, clicking normally...")
            
            # Highlight before clicking
            driver.execute_script("""
                arguments[0].style.border = '3px solid green';
                arguments[0].style.backgroundColor = 'rgba(0, 255, 0, 0.3)';
            """, element)
            
            # Click using JavaScript to ensure event handlers fire
            driver.execute_script("""
                var elem = arguments[0];
                elem.scrollIntoView({block: 'center'});
                elem.click();
                window.commercialAutoClicked = true;
            """, element)
        
        # Wait a moment to see if page will refresh
        time.sleep(2)
        
        # Check if page refreshed by comparing URLs
        new_url = driver.current_url
        if new_url != current_url:
            print(f"[Commercial Auto Fix] Page navigated from {current_url} to {new_url}")
            
            # Wait for new page to load
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except:
                pass
            
            # Restore form data if needed
            print("[Commercial Auto Fix] Attempting to restore form data...")
            driver.execute_script("""
                if (window.savedFormData) {
                    var formData = window.savedFormData;
                    for (var key in formData) {
                        var elements = document.querySelectorAll('[name="' + key + '"], #' + key);
                        for (var i = 0; i < elements.length; i++) {
                            var elem = elements[i];
                            if (elem.type === 'checkbox' || elem.type === 'radio') {
                                elem.checked = formData[key];
                            } else {
                                elem.value = formData[key];
                            }
                        }
                    }
                    console.log('Form data restored');
                }
            """)
            
            # Re-mark Commercial Auto as clicked
            driver.execute_script("window.commercialAutoClicked = true;")
            
        else:
            print("[Commercial Auto Fix] No page refresh detected - good!")
        
        # Verify we're on Commercial Auto page
        time.sleep(1)
        page_source = driver.page_source.lower()
        if "commercial" in page_source or "trucking" in page_source:
            print("[Commercial Auto Fix] Successfully on Commercial Auto page!")
            
            # Ensure the tab stays selected
            driver.execute_script("""
                // Find and mark Commercial Auto tab as active
                var tabs = document.querySelectorAll('a, button, div[role="button"]');
                for (var i = 0; i < tabs.length; i++) {
                    var tab = tabs[i];
                    if (tab.textContent.includes('Commercial Auto/Trucking')) {
                        tab.classList.add('active', 'selected', 'current');
                        // Remove active class from other tabs
                        var siblings = tab.parentElement.children;
                        for (var j = 0; j < siblings.length; j++) {
                            if (siblings[j] !== tab) {
                                siblings[j].classList.remove('active', 'selected', 'current');
                            }
                        }
                        break;
                    }
                }
            """)
            
            return True
        else:
            print("[Commercial Auto Fix] Not on Commercial Auto page yet")
            return False
            
    except Exception as e:
        print(f"[Commercial Auto Fix] Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def prevent_refresh_after_click(driver):
    """
    Monitor and prevent page refreshes after Commercial Auto is clicked
    """
    print("\n[Refresh Prevention] Installing refresh prevention handler...")
    
    try:
        # Install JavaScript to intercept and prevent unwanted refreshes
        driver.execute_script("""
            // Prevent page unload if Commercial Auto was clicked
            window.addEventListener('beforeunload', function(e) {
                if (window.commercialAutoClicked && !window.allowRefresh) {
                    console.log('Preventing page refresh - Commercial Auto was clicked');
                    e.preventDefault();
                    e.returnValue = '';
                    return '';
                }
            });
            
            // Override location changes
            var originalLocation = window.location.href;
            Object.defineProperty(window, 'location', {
                get: function() { return window._location || document.location; },
                set: function(val) {
                    if (window.commercialAutoClicked && !window.allowRefresh) {
                        console.log('Preventing location change to:', val);
                        return;
                    }
                    window._location = val;
                    document.location = val;
                }
            });
            
            // Intercept form submissions that might cause refresh
            document.addEventListener('submit', function(e) {
                var form = e.target;
                if (window.commercialAutoClicked && !form.classList.contains('commercial-auto-form')) {
                    console.log('Preventing form submission that might cause refresh');
                    e.preventDefault();
                    
                    // Submit via AJAX instead
                    if (window.jQuery && window.jQuery.ajax) {
                        var formData = window.jQuery(form).serialize();
                        window.jQuery.ajax({
                            url: form.action || window.location.href,
                            method: form.method || 'POST',
                            data: formData,
                            success: function(response) {
                                console.log('Form submitted via AJAX');
                            }
                        });
                    }
                }
            }, true);
            
            console.log('Refresh prevention installed');
        """)
        
        print("[Refresh Prevention] Handler installed successfully")
        return True
        
    except Exception as e:
        print(f"[Refresh Prevention] Error installing handler: {e}")
        return False