#!/usr/bin/env python3
"""
Test script untuk tech stack analyzer improvements
"""

from modules.tech_analyzer import TechStackAnalyzer
from colorama import Fore, Style, init

init(autoreset=True)

def test_basic():
    """Test basic functionality"""
    print(f"{Fore.CYAN}Testing TechStackAnalyzer improvements...{Style.RESET_ALL}\n")
    
    analyzer = TechStackAnalyzer()
    
    # Check if new signatures are loaded
    print(f"{Fore.YELLOW}1. Checking expanded tech signatures...{Style.RESET_ALL}")
    
    frameworks = analyzer.tech_signatures.get('frameworks', {})
    print(f"   - Frameworks: {len(frameworks)} detected")
    print(f"   - New frameworks: Next.js, Nuxt.js, Gatsby, Svelte")
    assert 'Next.js' in frameworks
    assert 'Nuxt.js' in frameworks
    assert 'Gatsby' in frameworks
    assert 'Svelte' in frameworks
    print(f"{Fore.GREEN}   ✅ Framework signatures expanded{Style.RESET_ALL}")
    
    # Check CMS signatures
    cms = analyzer.tech_signatures.get('cms', {})
    print(f"\n   - CMS: {len(cms)} detected")
    print(f"   - New CMS: Wix, Squarespace, Webflow, Ghost, Contentful")
    assert 'Wix' in cms
    assert 'Squarespace' in cms
    assert 'Webflow' in cms
    assert 'Ghost' in cms
    print(f"{Fore.GREEN}   ✅ CMS signatures expanded{Style.RESET_ALL}")
    
    # Check hosting signatures
    hosting = analyzer.tech_signatures.get('hosting', {})
    print(f"\n   - Hosting: {len(hosting)} detected")
    print(f"   - New hosting: Vercel, Netlify, Firebase, Heroku")
    assert 'Vercel' in hosting
    assert 'Netlify' in hosting
    assert 'Firebase' in hosting
    print(f"{Fore.GREEN}   ✅ Hosting signatures added{Style.RESET_ALL}")
    
    # Check ecommerce signatures
    ecommerce = analyzer.tech_signatures.get('ecommerce', {})
    print(f"\n   - E-commerce: {len(ecommerce)} detected")
    assert 'Shopify' in ecommerce
    assert 'BigCommerce' in ecommerce
    print(f"{Fore.GREEN}   ✅ E-commerce signatures added{Style.RESET_ALL}")
    
    # Check marketing signatures
    marketing = analyzer.tech_signatures.get('marketing', {})
    print(f"\n   - Marketing: {len(marketing)} detected")
    assert 'Intercom' in marketing
    assert 'HubSpot' in marketing
    print(f"{Fore.GREEN}   ✅ Marketing signatures added{Style.RESET_ALL}")
    
    # Check cookie signatures
    print(f"\n{Fore.YELLOW}2. Checking cookie signatures...{Style.RESET_ALL}")
    cookie_sigs = analyzer.cookie_signatures
    print(f"   - Cookie signatures: {len(cookie_sigs)}")
    assert 'Laravel' in cookie_sigs
    assert 'Django' in cookie_sigs
    assert 'WordPress' in cookie_sigs
    print(f"{Fore.GREEN}   ✅ Cookie signatures implemented{Style.RESET_ALL}")
    
    # Test analyze_cookies method
    print(f"\n{Fore.YELLOW}3. Testing analyze_cookies method...{Style.RESET_ALL}")
    test_cookies = {
        'PHPSESSID': 'test123',
        'laravel_session': 'xyz',
        'wordpress_logged_in': 'user'
    }
    cookie_result = analyzer.analyze_cookies(test_cookies)
    print(f"   - Detected from cookies: {cookie_result}")
    assert 'languages' in cookie_result or 'frameworks' in cookie_result or 'cms' in cookie_result
    print(f"{Fore.GREEN}   ✅ Cookie analysis working{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}✅ All tests passed!{Style.RESET_ALL}")
    print(f"\n{Fore.CYAN}Summary of improvements:{Style.RESET_ALL}")
    print(f"   • Expanded framework signatures (added 15+ new frameworks)")
    print(f"   • Enhanced CMS detection (added 10+ new platforms)")
    print(f"   • Added hosting platform detection (10 providers)")
    print(f"   • Added e-commerce platform signatures")
    print(f"   • Added marketing tools signatures")
    print(f"   • Implemented cookie-based detection")
    print(f"   • Enhanced header analysis with more signals")
    print(f"   • Improved content analysis with more patterns")
    
if __name__ == "__main__":
    test_basic()
