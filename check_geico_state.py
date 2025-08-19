#!/usr/bin/env python3
"""
Check GEICO scanner state and help proceed
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

try:
    driver = webdriver.Chrome(options=chrome_options)
    
    print("\n" + "="*60)
    print("GEICO SCANNER STATE CHECK")
    print("="*60)
    
    current_url = driver.current_url
    print(f"\nCurrent URL: {current_url[:80]}...")
    
    # Check if Commercial Auto is selected
    if "CommercialAuto" in current_url:
        print("\n✓ COMMERCIAL AUTO IS ALREADY SELECTED!")
        print("  (See 'CommercialAuto' in the URL parameters)")
    else:
        print("\n✗ Commercial Auto not selected yet")
    
    # Get page title
    print(f"\nPage Title: {driver.title}")
    
    # Check what's visible on the page
    print("\nVisible elements on page:")
    
    # Check for any error messages
    errors = driver.find_elements(By.CLASS_NAME, "error")
    if errors:
        print("\n⚠️  ERROR MESSAGES FOUND:")
        for err in errors:
            if err.is_displayed() and err.text:
                print(f"  - {err.text}")
    
    # Look for input fields
    inputs = driver.find_elements(By.TAG_NAME, "input")
    visible_inputs = [inp for inp in inputs if inp.is_displayed() and inp.get_attribute("type") != "hidden"]
    
    if visible_inputs:
        print(f"\n📝 Found {len(visible_inputs)} input fields:")
        for inp in visible_inputs[:10]:
            inp_type = inp.get_attribute("type")
            inp_name = inp.get_attribute("name") or inp.get_attribute("id") or "unnamed"
            inp_placeholder = inp.get_attribute("placeholder") or ""
            print(f"  - {inp_type} field: {inp_name} {f'({inp_placeholder})' if inp_placeholder else ''}")
    
    # Look for buttons/links
    print("\n🔘 Action buttons/links:")
    
    # Buttons
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        if btn.is_displayed() and btn.text:
            print(f"  - Button: '{btn.text}'")
    
    # Submit inputs
    submits = driver.find_elements(By.XPATH, "//input[@type='submit']")
    for sub in submits:
        if sub.is_displayed():
            value = sub.get_attribute("value")
            if value:
                print(f"  - Submit: '{value}'")
    
    # Links that look like buttons
    links = driver.find_elements(By.TAG_NAME, "a")
    for link in links[:30]:
        if link.is_displayed() and link.text:
            text = link.text.strip()
            if any(word in text.lower() for word in ["continue", "next", "submit", "quote", "start"]):
                print(f"  - Link: '{text}'")
    
    # Check for form to fill
    print("\n📋 Forms on page:")
    forms = driver.find_elements(By.TAG_NAME, "form")
    print(f"  Found {len(forms)} form(s)")
    
    # Suggestions
    print("\n💡 SUGGESTIONS:")
    if "CommercialAuto" in current_url:
        print("  1. Commercial Auto is already selected ✓")
        print("  2. Look for a 'Continue' or 'Next' button to proceed")
        print("  3. You may need to fill in required fields (ZIP code, etc.)")
    else:
        print("  1. Click on 'Commercial Auto/Trucking' option")
        print("  2. Then click 'Continue' or 'Next'")
    
    # Save screenshot
    driver.save_screenshot("/tmp/geico_state_check.png")
    print("\n📸 Screenshot saved to: /tmp/geico_state_check.png")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("Make sure the GEICO scanner is running")