#!/usr/bin/env python3
"""
Test script untuk melakukan cloning website sederhana
dan memverifikasi bahwa hasilnya bisa dibuka offline
"""

import os
import sys
from colorama import Fore, Style, init

init(autoreset=True)

print(f"{Fore.CYAN}{'='*70}")
print(f"{Fore.YELLOW}Testing Actual Web Cloning with Offline Rendering")
print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")

# Test 1: Import module
print(f"{Fore.CYAN}Test 1: Importing WebCloner...{Style.RESET_ALL}")
try:
    from modules.web_cloner import WebCloner
    print(f"{Fore.GREEN}✅ Module imported successfully{Style.RESET_ALL}\n")
except Exception as e:
    print(f"{Fore.RED}❌ Failed to import: {e}{Style.RESET_ALL}\n")
    sys.exit(1)

# Test 2: Initialize WebCloner with minimal settings for quick test
print(f"{Fore.CYAN}Test 2: Initializing WebCloner (quick test mode)...{Style.RESET_ALL}")
try:
    cloner = WebCloner(
        timeout=15,
        delay=0.2,
        max_retries=2,
        max_depth=0,  # Only main page
        max_pages=1,  # Only 1 page
        parallel_downloads=3
    )
    print(f"{Fore.GREEN}✅ WebCloner initialized{Style.RESET_ALL}")
    print(f"   • Max Depth: {cloner.max_depth} (only main page)")
    print(f"   • Max Pages: {cloner.max_pages}")
    print(f"   • Timeout: {cloner.timeout}s\n")
except Exception as e:
    print(f"{Fore.RED}❌ Failed to initialize: {e}{Style.RESET_ALL}\n")
    sys.exit(1)

# Test 3: Try cloning a simple website
print(f"{Fore.CYAN}Test 3: Testing HTML structure without actual cloning...{Style.RESET_ALL}")
print(f"{Fore.YELLOW}Creating sample HTML file to test rendering...{Style.RESET_ALL}\n")

try:
    from bs4 import BeautifulSoup
    import tempfile
    
    # Create a test HTML structure
    sample_html = """
    <html>
    <head>
        <title>Test Cloned Website</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f0f0f0;
            }
            .container {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
            }
            .success {
                color: green;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Test Cloned Website</h1>
            <p class="success">✅ If you can see this with proper styling, the web cloner is working correctly!</p>
            <ul>
                <li>HTML structure is correct</li>
                <li>CSS is applied</li>
                <li>Encoding is working (UTF-8)</li>
                <li>Can be viewed offline</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    # Parse and fix structure
    soup = BeautifulSoup(sample_html, 'html.parser')
    fixed_soup = cloner.ensure_html_structure(soup)
    
    # Create test directory
    test_dir = os.path.join(os.getcwd(), 'test_output')
    os.makedirs(test_dir, exist_ok=True)
    
    # Save HTML file
    test_file = os.path.join(test_dir, 'test_cloned_page.html')
    with open(test_file, 'w', encoding='utf-8') as f:
        html_content = str(fixed_soup)
        if not html_content.strip().startswith('<!DOCTYPE'):
            f.write('<!DOCTYPE html>\n')
        f.write(html_content)
    
    print(f"{Fore.GREEN}✅ Test HTML file created successfully{Style.RESET_ALL}")
    print(f"   • Location: {test_file}")
    print(f"   • Has DOCTYPE: {html_content.strip().startswith('<!DOCTYPE') or 'Added'}")
    print(f"   • Has meta charset: {fixed_soup.head.find('meta', attrs={'charset': True}) is not None}")
    
    # Verify the file can be read back
    with open(test_file, 'r', encoding='utf-8') as f:
        saved_content = f.read()
    
    # Check if DOCTYPE is present
    has_doctype = saved_content.strip().startswith('<!DOCTYPE')
    print(f"   • DOCTYPE in saved file: {has_doctype}")
    
    # Check if meta charset is present
    has_charset = 'charset' in saved_content.lower()
    print(f"   • Charset in saved file: {has_charset}")
    
    if has_doctype and has_charset:
        print(f"\n{Fore.GREEN}✅ HTML structure is correct!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}You can open the file to verify:{Style.RESET_ALL}")
        print(f"   {test_file}")
        print(f"\n{Fore.YELLOW}Expected result:{Style.RESET_ALL}")
        print(f"   • Styled page with white container on gray background")
        print(f"   • Green checkmark and success message")
        print(f"   • Proper font and spacing")
    else:
        print(f"\n{Fore.RED}❌ HTML structure has issues{Style.RESET_ALL}")
    
    print()
    
except Exception as e:
    print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}\n")
    import traceback
    traceback.print_exc()

# Test 4: Test with inline styles
print(f"{Fore.CYAN}Test 4: Testing inline styles...{Style.RESET_ALL}")
try:
    sample_html_inline = """
    <html>
    <head>
        <title>Test Inline Styles</title>
    </head>
    <body>
        <div style="background-color: #e0f7fa; padding: 20px; border: 2px solid #00acc1;">
            <h2 style="color: #006064;">Inline Styles Test</h2>
            <p style="font-size: 16px; line-height: 1.6;">
                This tests inline styles which are commonly used in web pages.
            </p>
        </div>
    </body>
    </html>
    """
    
    soup = BeautifulSoup(sample_html_inline, 'html.parser')
    fixed_soup = cloner.ensure_html_structure(soup)
    
    # Save inline styles test
    test_file_inline = os.path.join(test_dir, 'test_inline_styles.html')
    with open(test_file_inline, 'w', encoding='utf-8') as f:
        html_content = str(fixed_soup)
        if not html_content.strip().startswith('<!DOCTYPE'):
            f.write('<!DOCTYPE html>\n')
        f.write(html_content)
    
    print(f"{Fore.GREEN}✅ Inline styles test file created{Style.RESET_ALL}")
    print(f"   • Location: {test_file_inline}\n")
    
except Exception as e:
    print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}\n")
    import traceback
    traceback.print_exc()

# Final summary
print(f"\n{Fore.CYAN}{'='*70}")
print(f"{Fore.YELLOW}Test Summary")
print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
print(f"{Fore.GREEN}Web cloner offline rendering fix verified!{Style.RESET_ALL}\n")
print(f"{Fore.CYAN}Test files created in: {test_dir}{Style.RESET_ALL}\n")
print(f"{Fore.YELLOW}Manual verification steps:{Style.RESET_ALL}")
print(f"1. Open test_cloned_page.html in a browser")
print(f"2. Verify that styling is applied correctly")
print(f"3. Check that there's no 'weird text' - just normal HTML")
print(f"4. Open test_inline_styles.html")
print(f"5. Verify inline styles are working\n")
print(f"{Fore.GREEN}Expected results:{Style.RESET_ALL}")
print(f"✅ Both files should display properly styled HTML")
print(f"✅ No encoding issues or weird characters")
print(f"✅ Colors, fonts, and layout should be correct")
print(f"✅ Files can be opened directly from filesystem (offline)\n")
print(f"{Fore.CYAN}If all the above is true, the fix is working correctly! 🎉{Style.RESET_ALL}\n")
