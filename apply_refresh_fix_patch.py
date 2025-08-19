#!/usr/bin/env python3
"""
Simple patch to apply the refresh fix to geico_scanner_https_enhanced.py
This modifies the existing scanner to prevent page refresh when clicking Commercial Auto
"""

import os
import shutil
from datetime import datetime

def apply_refresh_fix():
    """Apply the refresh prevention fix to the main scanner"""
    
    scanner_file = "geico_scanner_https_enhanced.py"
    
    if not os.path.exists(scanner_file):
        print(f"[ERROR] {scanner_file} not found!")
        return False
    
    # Backup original
    backup_name = f"{scanner_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(scanner_file, backup_name)
    print(f"[INFO] Created backup: {backup_name}")
    
    # Read the file
    with open(scanner_file, 'r') as f:
        lines = f.readlines()
    
    # Find the JavaScript code in the force-commercial-auto route
    in_route = False
    route_start_line = -1
    js_start_line = -1
    
    for i, line in enumerate(lines):
        if "@app.route('/force-commercial-auto'" in line:
            in_route = True
            route_start_line = i
        elif in_route and 'driver.execute_script("""' in line and 'hasCheckbox' in lines[i+1]:
            js_start_line = i
            break
    
    if js_start_line == -1:
        print("[ERROR] Could not find the JavaScript code to patch")
        return False
    
    print(f"[INFO] Found JavaScript at line {js_start_line}")
    
    # New JavaScript code with refresh prevention
    new_js_code = '''        result = driver.execute_script("""
            // REFRESH PREVENTION FIX
            // Install handlers BEFORE clicking
            if (!window.refreshFixInstalled) {
                window.refreshFixInstalled = true;
                
                // Override navigation methods
                window._origPushState = history.pushState;
                history.pushState = function() {
                    if (window.commercialAutoClicked) {
                        console.log('[FIX] Blocked pushState');
                        return;
                    }
                    return window._origPushState.apply(history, arguments);
                };
                
                // Intercept all clicks on Commercial Auto elements
                document.addEventListener('click', function(e) {
                    var target = e.target;
                    while (target) {
                        if (target.textContent && 
                            (target.textContent.includes('Commercial Auto') || 
                             target.textContent.includes('Trucking'))) {
                            
                            // Check if it's a link that would navigate
                            if (target.tagName === 'A' && target.href && 
                                target.href !== '#' && 
                                target.href !== 'javascript:void(0)' &&
                                !target.href.includes('javascript:')) {
                                
                                e.preventDefault();
                                e.stopPropagation();
                                console.log('[FIX] Prevented navigation on Commercial Auto click');
                                
                                // Mark as active without navigation
                                target.classList.add('active', 'selected');
                                window.commercialAutoClicked = true;
                                
                                // Visual feedback
                                target.style.backgroundColor = '#4CAF50';
                                target.style.color = 'white';
                                
                                // Fire any onclick handlers
                                if (target.onclick) {
                                    target.onclick(e);
                                }
                                
                                return false;
                            }
                        }
                        target = target.parentElement;
                    }
                }, true);
                
                console.log('[FIX] Refresh prevention installed');
            }
            
            // Now proceed with normal detection and clicking
            var hasCheckbox = false;
            var hasTab = false;
            var clicked = false;
            
            // Check for checkbox
            var labels = document.querySelectorAll('label');
            for (var i = 0; i < labels.length; i++) {
                if (labels[i].textContent.includes('Commercial Auto/Trucking')) {
                    hasCheckbox = true;
                    // Click the checkbox
                    labels[i].click();
                    clicked = true;
                    
                    // Submit form after delay
                    setTimeout(function() {
                        var form = document.querySelector('form');
                        if (form) form.submit();
                    }, 500);
                    break;
                }
            }
            
            if (!clicked) {
                // Look for tab elements
                var tabs = document.querySelectorAll('a[role="tab"], button[role="tab"], div[role="tab"], li[role="tab"], [class*="tab"], a, button');
                for (var i = 0; i < tabs.length; i++) {
                    if ((tabs[i].textContent.includes('Commercial Auto') || 
                         tabs[i].textContent.includes('Auto/Trucking')) &&
                        !tabs[i].textContent.includes('checkbox')) {
                        
                        hasTab = true;
                        
                        // Special handling for links
                        if (tabs[i].tagName === 'A' && tabs[i].href && 
                            tabs[i].href !== '#' && 
                            tabs[i].href !== 'javascript:void(0)') {
                            
                            // Don't use normal click for navigation links
                            tabs[i].classList.add('active', 'selected');
                            tabs[i].style.backgroundColor = '#4CAF50';
                            tabs[i].style.color = 'white';
                            window.commercialAutoClicked = true;
                            
                            // Try to handle without navigation
                            if (tabs[i].onclick) {
                                tabs[i].onclick(new Event('click'));
                            }
                            
                            clicked = true;
                        } else {
                            // Safe to click non-navigation elements
                            tabs[i].click();
                            tabs[i].style.backgroundColor = '#4CAF50';
                            window.commercialAutoClicked = true;
                            clicked = true;
                        }
                        break;
                    }
                }
            }
            
            // Start monitoring to maintain selection
            if (clicked && !window.tabMonitor) {
                window.tabMonitor = setInterval(function() {
                    // Re-apply active state if lost
                    var tabs = document.querySelectorAll('a, button, li, div');
                    var found = false;
                    for (var i = 0; i < tabs.length; i++) {
                        var text = tabs[i].textContent || '';
                        if ((text.includes('Commercial Auto') || text.includes('Trucking')) && 
                            !text.includes('checkbox')) {
                            if (!tabs[i].classList.contains('active')) {
                                tabs[i].classList.add('active', 'selected');
                                tabs[i].style.backgroundColor = '#4CAF50';
                                tabs[i].style.color = 'white';
                            }
                            found = true;
                            break;
                        }
                    }
                    if (!found) {
                        clearInterval(window.tabMonitor);
                    }
                }, 1000);
            }
            
            return {clicked: clicked, hasCheckbox: hasCheckbox, hasTab: hasTab};
        """)
        
        if result['clicked']:
            if result['hasCheckbox']:
                current_status = "Commercial Auto checkbox clicked!"
                return jsonify({'status': 'success', 'message': 'Commercial Auto checkbox clicked! Form will submit.'})
            else:
                current_status = "Commercial Auto tab selected (no refresh)"
                return jsonify({'status': 'success', 'message': 'Commercial Auto tab selected without refresh!'})
        else:
            return jsonify({'status': 'error', 'message': 'Could not find Commercial Auto element'})
'''
    
    # Find the end of the current execute_script block
    js_end_line = js_start_line
    for i in range(js_start_line, len(lines)):
        if '""")' in lines[i]:
            js_end_line = i
            break
    
    # Find the end of the route (next route or end of file)
    route_end_line = len(lines) - 1
    for i in range(route_start_line + 1, len(lines)):
        if '@app.route' in lines[i] or 'def ' in lines[i] and lines[i][0] != ' ':
            route_end_line = i - 1
            break
    
    # Replace the JavaScript and the result handling
    new_lines = lines[:js_start_line] + [new_js_code + '\n'] + lines[route_end_line:]
    
    # Write the patched file
    patched_file = scanner_file.replace('.py', '_PATCHED_NO_REFRESH.py')
    with open(patched_file, 'w') as f:
        f.writelines(new_lines)
    
    print(f"[SUCCESS] Created patched scanner: {patched_file}")
    print("\n[INSTRUCTIONS]")
    print("1. Stop the current scanner")
    print(f"2. Run: python3 {patched_file}")
    print("3. The Commercial Auto tab will now stay selected without refreshing!")
    
    return True

if __name__ == "__main__":
    apply_refresh_fix()