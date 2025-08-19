#!/usr/bin/env python3
"""
Enhanced fix for Commercial Auto/Trucking refresh issue
This fix prevents page refresh and maintains the checkbox state
"""

def apply_commercial_auto_fix(driver):
    """
    Apply comprehensive fix to prevent page refresh when clicking Commercial Auto
    """
    print("[FIX] Applying Commercial Auto refresh prevention fix...")
    
    # Install the comprehensive fix
    fix_script = """
    (function() {
        console.log('[COMMERCIAL AUTO FIX] Installing refresh prevention...');
        
        // Flag to track if we're in Commercial Auto mode
        window.commercialAutoMode = false;
        window.commercialAutoClicked = false;
        
        // Store original navigation functions
        if (!window._navigationBackup) {
            window._navigationBackup = {
                pushState: history.pushState,
                replaceState: history.replaceState,
                assign: window.location.assign,
                replace: window.location.replace,
                reload: window.location.reload,
                href: Object.getOwnPropertyDescriptor(window.location, 'href')
            };
        }
        
        // Override history.pushState
        history.pushState = function() {
            if (window.commercialAutoMode) {
                console.log('[FIX] Blocked pushState during Commercial Auto mode');
                return;
            }
            return window._navigationBackup.pushState.apply(history, arguments);
        };
        
        // Override history.replaceState
        history.replaceState = function() {
            if (window.commercialAutoMode) {
                console.log('[FIX] Blocked replaceState during Commercial Auto mode');
                return;
            }
            return window._navigationBackup.replaceState.apply(history, arguments);
        };
        
        // Override location methods
        window.location.assign = function(url) {
            if (window.commercialAutoMode) {
                console.log('[FIX] Blocked location.assign to:', url);
                return;
            }
            return window._navigationBackup.assign.call(window.location, url);
        };
        
        window.location.replace = function(url) {
            if (window.commercialAutoMode) {
                console.log('[FIX] Blocked location.replace to:', url);
                return;
            }
            return window._navigationBackup.replace.call(window.location, url);
        };
        
        window.location.reload = function() {
            if (window.commercialAutoMode) {
                console.log('[FIX] Blocked location.reload');
                return;
            }
            return window._navigationBackup.reload.call(window.location);
        };
        
        // Override location.href setter
        Object.defineProperty(window.location, 'href', {
            get: function() {
                return window._navigationBackup.href.get.call(window.location);
            },
            set: function(val) {
                if (window.commercialAutoMode) {
                    console.log('[FIX] Blocked location.href change to:', val);
                    return;
                }
                window._navigationBackup.href.set.call(window.location, val);
            }
        });
        
        // Intercept beforeunload event
        window.addEventListener('beforeunload', function(e) {
            if (window.commercialAutoMode) {
                console.log('[FIX] Preventing page unload during Commercial Auto mode');
                e.preventDefault();
                e.returnValue = '';
                return '';
            }
        }, true);
        
        // Monitor and intercept all clicks
        document.addEventListener('click', function(e) {
            var target = e.target;
            var text = '';
            
            // Get text from element and its children
            while (target && target !== document.body) {
                text += (target.textContent || target.innerText || '');
                
                // Check if this is a Commercial Auto/Trucking element
                if (text.includes('Commercial Auto') || text.includes('Trucking')) {
                    console.log('[FIX] Intercepted Commercial Auto click on:', target);
                    
                    // Prevent default behavior
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    
                    // Enable Commercial Auto mode
                    window.commercialAutoMode = true;
                    window.commercialAutoClicked = true;
                    
                    // Handle the click visually
                    handleCommercialAutoClick(target);
                    
                    // Disable Commercial Auto mode after 5 seconds
                    setTimeout(function() {
                        window.commercialAutoMode = false;
                        console.log('[FIX] Commercial Auto mode disabled after timeout');
                    }, 5000);
                    
                    return false;
                }
                
                target = target.parentElement;
            }
        }, true);
        
        // Function to handle Commercial Auto click
        window.handleCommercialAutoClick = function(element) {
            console.log('[FIX] Handling Commercial Auto click...');
            
            // Find the actual clickable element if needed
            var clickTarget = element;
            if (element.tagName === 'SPAN' || element.tagName === 'DIV') {
                var parent = element.parentElement;
                if (parent && (parent.tagName === 'A' || parent.tagName === 'BUTTON')) {
                    clickTarget = parent;
                }
            }
            
            // Visual feedback
            clickTarget.style.backgroundColor = '#28a745';
            clickTarget.style.color = 'white';
            clickTarget.style.fontWeight = 'bold';
            
            // Add active classes
            clickTarget.classList.add('active', 'selected', 'current');
            
            // If it's a link, try to handle it without navigation
            if (clickTarget.tagName === 'A' && clickTarget.href) {
                var href = clickTarget.href;
                console.log('[FIX] Handling link click without navigation:', href);
                
                // Try to load content via AJAX if possible
                if (href.includes('commercial') || href.includes('trucking')) {
                    loadCommercialContent(href);
                }
            }
            
            // Fire any onclick handlers safely
            if (clickTarget.onclick) {
                try {
                    var onclickStr = clickTarget.onclick.toString();
                    if (!onclickStr.includes('location') && !onclickStr.includes('href')) {
                        clickTarget.onclick();
                    }
                } catch (e) {
                    console.log('[FIX] Error executing onclick:', e);
                }
            }
            
            // Mark other tabs as inactive
            var allTabs = document.querySelectorAll('a, button, li, div[role="tab"]');
            allTabs.forEach(function(tab) {
                if (tab !== clickTarget && !tab.contains(clickTarget)) {
                    tab.classList.remove('active', 'selected', 'current');
                }
            });
        };
        
        // Function to load content without refresh
        window.loadCommercialContent = function(url) {
            console.log('[FIX] Loading commercial content via AJAX from:', url);
            
            // Find content area
            var contentArea = document.querySelector('.main-content, #content, [role="main"], main, .content-wrapper');
            if (!contentArea) {
                console.log('[FIX] Could not find content area');
                return;
            }
            
            // Show loading state
            contentArea.style.opacity = '0.5';
            
            // Attempt to fetch content
            fetch(url, {
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'text/html'
                }
            })
            .then(response => response.text())
            .then(html => {
                // Parse the response
                var parser = new DOMParser();
                var doc = parser.parseFromString(html, 'text/html');
                
                // Find the main content in the response
                var newContent = doc.querySelector('.main-content, #content, [role="main"], main, .content-wrapper');
                if (newContent) {
                    contentArea.innerHTML = newContent.innerHTML;
                    console.log('[FIX] Content loaded successfully');
                    
                    // Re-run any scripts
                    var scripts = contentArea.getElementsByTagName('script');
                    for (var i = 0; i < scripts.length; i++) {
                        try {
                            eval(scripts[i].textContent);
                        } catch (e) {
                            console.log('[FIX] Error executing script:', e);
                        }
                    }
                }
                
                contentArea.style.opacity = '1';
            })
            .catch(error => {
                console.log('[FIX] Could not load content via AJAX:', error);
                contentArea.style.opacity = '1';
            });
        };
        
        // Monitor for any form submissions that might cause refresh
        document.addEventListener('submit', function(e) {
            if (window.commercialAutoMode) {
                console.log('[FIX] Preventing form submission during Commercial Auto mode');
                e.preventDefault();
                return false;
            }
        }, true);
        
        // Override window.open to prevent popups during Commercial Auto mode
        var originalOpen = window.open;
        window.open = function() {
            if (window.commercialAutoMode) {
                console.log('[FIX] Blocked window.open during Commercial Auto mode');
                return null;
            }
            return originalOpen.apply(window, arguments);
        };
        
        console.log('[COMMERCIAL AUTO FIX] All preventions installed successfully');
    })();
    """
    
    driver.execute_script(fix_script)
    print("[FIX] Commercial Auto refresh prevention installed successfully")

def integrate_fix_into_scanner(scanner_path):
    """
    Integrate this fix into the main scanner file
    """
    import os
    
    print(f"\n[INTEGRATION] Reading scanner file: {scanner_path}")
    
    with open(scanner_path, 'r') as f:
        content = f.read()
    
    # Find where Commercial Auto is clicked
    commercial_auto_section = content.find("# CHECK IF WE'RE ON DASHBOARD AND NEED TO CLICK COMMERCIAL AUTO/TRUCKING")
    
    if commercial_auto_section == -1:
        print("[ERROR] Could not find Commercial Auto section in scanner")
        return False
    
    # Find the line before the commercial auto check
    insert_position = commercial_auto_section
    
    # Create the fix insertion
    fix_insertion = """
                # APPLY COMMERCIAL AUTO REFRESH FIX BEFORE ANY CLICKS
                from commercial_auto_refresh_fix_enhanced import apply_commercial_auto_fix
                apply_commercial_auto_fix(driver)
                print("[DEBUG] Commercial Auto refresh prevention applied")
                
"""
    
    # Insert the fix
    new_content = content[:insert_position] + fix_insertion + content[insert_position:]
    
    # Save to new file
    new_path = scanner_path.replace('.py', '_NO_REFRESH.py')
    with open(new_path, 'w') as f:
        f.write(new_content)
    
    print(f"[INTEGRATION] Created enhanced scanner: {new_path}")
    print("[INTEGRATION] The fix will:")
    print("  1. Prevent page refresh when clicking Commercial Auto")
    print("  2. Block all navigation attempts during Commercial Auto mode")
    print("  3. Maintain checkbox/button state")
    print("  4. Handle content loading without refresh")
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--integrate":
        # Integrate into the main scanner
        scanner_path = "/home/corp06/software_projects/New-scanner-quoter/geico_scanner_https.py"
        integrate_fix_into_scanner(scanner_path)
    else:
        # Test standalone
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            apply_commercial_auto_fix(driver)
            print("\n[SUCCESS] Fix applied! Commercial Auto clicks will no longer cause page refresh.")
        except Exception as e:
            print(f"[ERROR] {e}")