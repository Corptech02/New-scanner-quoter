"""
Improved Commercial Auto/Trucking Tab Clicking Module
This module provides a robust solution for clicking the Commercial Auto/Trucking tab
on the GEICO dashboard after login.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

def click_commercial_auto_tab(driver, max_attempts=5, debug=True):
    """
    Attempts to click the Commercial Auto/Trucking tab on GEICO dashboard.
    
    Args:
        driver: Selenium WebDriver instance
        max_attempts: Maximum number of attempts to click the tab
        debug: Whether to print debug messages
        
    Returns:
        bool: True if successfully clicked, False otherwise
    """
    
    # Check if we've already clicked it
    try:
        commercial_clicked = driver.execute_script("return window.commercialAutoClicked || false")
        if commercial_clicked:
            if debug:
                print("[DEBUG] Commercial Auto already clicked")
            return True
    except:
        pass
    
    for attempt in range(max_attempts):
        if debug:
            print(f"\n[DEBUG] Attempt {attempt + 1} to click Commercial Auto/Trucking tab")
        
        # Strategy 1: Wait for page to stabilize and elements to load
        try:
            WebDriverWait(driver, 10).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(2)  # Additional wait for dynamic content
        except:
            pass
        
        # Strategy 2: Direct element search with multiple selectors
        selectors = [
            # Tab-specific selectors
            "//li[@role='tab'][contains(., 'Commercial Auto/Trucking')]",
            "//div[@role='tab'][contains(., 'Commercial Auto/Trucking')]",
            "//a[@role='tab'][contains(., 'Commercial Auto/Trucking')]",
            
            # Link selectors
            "//a[normalize-space(text())='Commercial Auto/Trucking']",
            "//a[contains(@class, 'tab')][contains(., 'Commercial Auto/Trucking')]",
            
            # Button selectors
            "//button[normalize-space(text())='Commercial Auto/Trucking']",
            "//button[contains(., 'Commercial Auto/Trucking')]",
            
            # Generic clickable elements
            "//div[contains(@class, 'tab')][contains(., 'Commercial Auto/Trucking')]",
            "//span[normalize-space(text())='Commercial Auto/Trucking']/parent::*[@onclick or @href]",
            
            # Navigation specific
            "//nav//a[contains(., 'Commercial Auto/Trucking')]",
            "//nav//button[contains(., 'Commercial Auto/Trucking')]",
            "//*[contains(@class, 'navigation')]//a[contains(., 'Commercial Auto/Trucking')]",
            "//*[contains(@class, 'nav-tabs')]//a[contains(., 'Commercial Auto/Trucking')]",
            
            # ARIA labeled elements
            "//*[@aria-label='Commercial Auto/Trucking']",
            "//*[@title='Commercial Auto/Trucking']"
        ]
        
        element_found = False
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if debug and elements:
                    print(f"[DEBUG] Found {len(elements)} elements with selector: {selector}")
                
                for elem in elements:
                    try:
                        # Check if element is visible and not in a form
                        if elem.is_displayed() and elem.is_enabled():
                            # Skip if it's a form element
                            parent_form = elem.find_elements(By.XPATH, "./ancestor::form")
                            if parent_form:
                                continue
                            
                            # Get element info
                            elem_text = elem.text.strip()
                            elem_tag = elem.tag_name
                            
                            if debug:
                                print(f"[DEBUG] Trying to click: {elem_tag} - '{elem_text}'")
                            
                            # Scroll element into view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                            time.sleep(0.5)
                            
                            # Highlight element
                            driver.execute_script("""
                                arguments[0].style.border = '3px solid red';
                                arguments[0].style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
                            """, elem)
                            
                            # Try multiple click methods
                            click_success = False
                            
                            # Method 1: Standard click
                            try:
                                elem.click()
                                click_success = True
                                if debug:
                                    print("[DEBUG] Standard click successful")
                            except ElementClickInterceptedException:
                                if debug:
                                    print("[DEBUG] Standard click intercepted, trying JavaScript")
                                
                                # Method 2: JavaScript click
                                try:
                                    driver.execute_script("arguments[0].click();", elem)
                                    click_success = True
                                    if debug:
                                        print("[DEBUG] JavaScript click successful")
                                except:
                                    pass
                            
                            if not click_success:
                                # Method 3: Action chains
                                try:
                                    actions = ActionChains(driver)
                                    actions.move_to_element(elem).click().perform()
                                    click_success = True
                                    if debug:
                                        print("[DEBUG] Action chains click successful")
                                except:
                                    pass
                            
                            if click_success:
                                # Mark as clicked
                                driver.execute_script("window.commercialAutoClicked = true;")
                                
                                # Wait for potential navigation
                                time.sleep(3)
                                
                                # Verify click was successful by checking URL or page content
                                current_url = driver.current_url
                                if debug:
                                    print(f"[DEBUG] Current URL after click: {current_url}")
                                
                                # Check if we're on a commercial auto page
                                page_text = driver.find_element(By.TAG_NAME, "body").text
                                if "commercial" in page_text.lower() or "trucking" in page_text.lower():
                                    if debug:
                                        print("[DEBUG] Successfully navigated to Commercial Auto section")
                                    return True
                                
                                element_found = True
                                break
                                
                    except Exception as e:
                        if debug:
                            print(f"[DEBUG] Error clicking element: {e}")
                        continue
                
                if element_found:
                    break
                    
            except Exception as e:
                if debug:
                    print(f"[DEBUG] Error with selector {selector}: {e}")
                continue
        
        # Strategy 3: JavaScript-based comprehensive search
        if not element_found:
            if debug:
                print("[DEBUG] Trying JavaScript-based search")
            
            js_result = driver.execute_script("""
                function findAndClickCommercialAuto() {
                    // Find all text nodes containing "Commercial Auto"
                    var walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        {
                            acceptNode: function(node) {
                                if (node.nodeValue && node.nodeValue.includes('Commercial Auto')) {
                                    return NodeFilter.FILTER_ACCEPT;
                                }
                                return NodeFilter.FILTER_REJECT;
                            }
                        }
                    );
                    
                    var textNodes = [];
                    var node;
                    while (node = walker.nextNode()) {
                        textNodes.push(node);
                    }
                    
                    // For each text node, find the nearest clickable ancestor
                    for (var i = 0; i < textNodes.length; i++) {
                        var textNode = textNodes[i];
                        var parent = textNode.parentElement;
                        
                        // Walk up the DOM tree to find a clickable element
                        while (parent && parent !== document.body) {
                            var isClickable = (
                                parent.tagName === 'A' ||
                                parent.tagName === 'BUTTON' ||
                                parent.getAttribute('role') === 'button' ||
                                parent.getAttribute('role') === 'tab' ||
                                parent.getAttribute('onclick') ||
                                parent.style.cursor === 'pointer' ||
                                parent.classList.contains('clickable') ||
                                parent.classList.contains('tab') ||
                                parent.classList.contains('link')
                            );
                            
                            if (isClickable && parent.textContent.includes('Commercial Auto/Trucking')) {
                                console.log('Found clickable element:', parent);
                                
                                // Highlight
                                parent.style.border = '3px solid blue';
                                parent.style.backgroundColor = 'rgba(0, 0, 255, 0.3)';
                                
                                // Try to click
                                try {
                                    parent.click();
                                    return { success: true, element: parent.tagName };
                                } catch (e) {
                                    // Try dispatching event
                                    var event = new MouseEvent('click', {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true
                                    });
                                    parent.dispatchEvent(event);
                                    return { success: true, element: parent.tagName };
                                }
                            }
                            
                            parent = parent.parentElement;
                        }
                    }
                    
                    return { success: false, message: 'No clickable Commercial Auto element found' };
                }
                
                return findAndClickCommercialAuto();
            """)
            
            if debug:
                print(f"[DEBUG] JavaScript search result: {js_result}")
            
            if js_result and js_result.get('success'):
                driver.execute_script("window.commercialAutoClicked = true;")
                time.sleep(3)
                return True
        
        # Strategy 4: Look for navigation menu and try tab navigation
        if attempt < max_attempts - 1:
            if debug:
                print("[DEBUG] Trying keyboard navigation")
            
            try:
                # Focus on body
                body = driver.find_element(By.TAG_NAME, "body")
                body.click()
                
                # Try Tab key navigation
                from selenium.webdriver.common.keys import Keys
                for _ in range(30):  # Try up to 30 tabs
                    body.send_keys(Keys.TAB)
                    time.sleep(0.1)
                    
                    # Check focused element
                    focused_elem = driver.switch_to.active_element
                    if focused_elem and "Commercial Auto" in focused_elem.text:
                        if debug:
                            print("[DEBUG] Found Commercial Auto via Tab navigation")
                        focused_elem.send_keys(Keys.ENTER)
                        time.sleep(3)
                        return True
            except:
                pass
        
        # Wait before next attempt
        if attempt < max_attempts - 1:
            time.sleep(2)
    
    if debug:
        print("[DEBUG] Failed to click Commercial Auto/Trucking tab after all attempts")
    return False


# Integration function to be added to the main scanner
def enhance_commercial_auto_detection(driver):
    """
    Enhanced detection and clicking for Commercial Auto/Trucking tab.
    This function should be called after successful login to GEICO dashboard.
    """
    
    print("[DEBUG] Starting enhanced Commercial Auto detection")
    
    # Wait for dashboard to load
    try:
        # Wait for common dashboard elements
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Additional wait for AJAX/dynamic content
        time.sleep(3)
        
        # Try to click the Commercial Auto tab
        success = click_commercial_auto_tab(driver, max_attempts=5, debug=True)
        
        if success:
            print("[SUCCESS] Commercial Auto/Trucking tab clicked successfully")
        else:
            print("[WARNING] Could not click Commercial Auto/Trucking tab")
            
            # Log page state for debugging
            print("[DEBUG] Current URL:", driver.current_url)
            print("[DEBUG] Page title:", driver.title)
            
            # Log visible text that might help identify the issue
            try:
                visible_text = driver.execute_script("""
                    var text = [];
                    var elements = document.querySelectorAll('a, button, [role="tab"], [role="button"]');
                    for (var i = 0; i < Math.min(elements.length, 20); i++) {
                        if (elements[i].offsetWidth > 0 && elements[i].offsetHeight > 0) {
                            text.push(elements[i].textContent.trim().substring(0, 50));
                        }
                    }
                    return text;
                """)
                print("[DEBUG] Visible clickable elements:", visible_text)
            except:
                pass
                
        return success
        
    except TimeoutException:
        print("[ERROR] Dashboard did not load in time")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False