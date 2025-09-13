#!/usr/bin/env python3
"""
Tech Stack Analysis Module - Tools untuk menganalisa teknologi yang digunakan website
Mengidentifikasi framework, library, CMS, server, database, dan teknologi lainnya
Memberikan laporan lengkap tentang tech stack website

Author: Ramaerik97
Version: 1.0.0
"""

import requests
import re
import os
import json
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from colorama import Fore, Style
import builtwith
import whois
import ssl
import socket
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from loading_animation import LoadingContext, ProgressTracker


class TechStackAnalyzer:
    """
    Class utama untuk analisis tech stack website
    """
    
    def __init__(self, timeout=15):
        """
        Inisialisasi TechStackAnalyzer
        
        Args:
            timeout (int): Timeout untuk HTTP requests dalam detik
        """
        self.timeout = timeout
        self.session = requests.Session()
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Common user agent
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Tech signatures untuk deteksi manual
        self.tech_signatures = {
            'frameworks': {
                'React': [r'react', r'_react', r'React\.createElement'],
                'Vue.js': [r'vue\.js', r'Vue\.', r'__vue__'],
                'Angular': [r'angular', r'ng-', r'@angular'],
                'jQuery': [r'jquery', r'\$\(', r'jQuery'],
                'Bootstrap': [r'bootstrap', r'btn-', r'container-fluid'],
                'Tailwind CSS': [r'tailwind', r'tw-', r'tailwindcss'],
                'Foundation': [r'foundation', r'zurb-foundation'],
                'Materialize': [r'materialize', r'material-icons'],
                'Bulma': [r'bulma', r'is-primary', r'column'],
                'Semantic UI': [r'semantic', r'ui segment', r'ui container']
            },
            'cms': {
                'WordPress': [r'wp-content', r'wp-includes', r'wordpress'],
                'Drupal': [r'drupal', r'sites/default', r'misc/drupal'],
                'Joomla': [r'joomla', r'option=com_', r'templates/'],
                'Magento': [r'magento', r'mage/', r'skin/frontend'],
                'Shopify': [r'shopify', r'cdn.shopify.com', r'myshopify.com'],
                'WooCommerce': [r'woocommerce', r'wc-', r'shop/'],
                'PrestaShop': [r'prestashop', r'ps_', r'themes/'],
                'OpenCart': [r'opencart', r'catalog/view', r'image/catalog']
            },
            'servers': {
                'Apache': [r'apache', r'server: apache'],
                'Nginx': [r'nginx', r'server: nginx'],
                'IIS': [r'iis', r'server: microsoft-iis'],
                'LiteSpeed': [r'litespeed', r'server: litespeed'],
                'Cloudflare': [r'cloudflare', r'cf-ray', r'__cfduid']
            },
            'languages': {
                'PHP': [r'\.php', r'<?php', r'PHPSESSID'],
                'ASP.NET': [r'\.aspx', r'__VIEWSTATE', r'asp.net'],
                'Node.js': [r'node\.js', r'express', r'__next'],
                'Python': [r'django', r'flask', r'wsgi'],
                'Ruby': [r'ruby', r'rails', r'rack'],
                'Java': [r'java', r'jsp', r'jsessionid'],
                'Go': [r'golang', r'go-', r'gorilla']
            },
            'analytics': {
                'Google Analytics': [r'google-analytics', r'gtag', r'ga\('],
                'Google Tag Manager': [r'googletagmanager', r'gtm\.js'],
                'Facebook Pixel': [r'facebook\.net/tr', r'fbq\('],
                'Hotjar': [r'hotjar', r'hj\('],
                'Mixpanel': [r'mixpanel', r'mp_'],
                'Adobe Analytics': [r'omniture', r'adobe\.com/.*analytics']
            },
            'cdn': {
                'Cloudflare': [r'cloudflare', r'cdnjs\.cloudflare'],
                'AWS CloudFront': [r'cloudfront', r'amazonaws'],
                'MaxCDN': [r'maxcdn', r'bootstrapcdn'],
                'jsDelivr': [r'jsdelivr', r'cdn\.jsdelivr'],
                'unpkg': [r'unpkg\.com'],
                'Google CDN': [r'googleapis\.com', r'gstatic\.com']
            }
        }
    
    def normalize_url(self, url):
        """
        Normalize URL dengan menambahkan protocol jika diperlukan
        
        Args:
            url (str): URL input
            
        Returns:
            str: Normalized URL
        """
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def get_website_content(self, url):
        """
        Mengambil konten website dan informasi response
        
        Args:
            url (str): URL website
            
        Returns:
            dict: Website content dan metadata
        """
        with LoadingContext("Mengambil konten website...", "pulse") as loading:
            try:
                loading.update_message("Mengirim HTTP request...")
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
                response.raise_for_status()
                
                loading.update_message("Memproses response...")
                content_info = {
                    'url': response.url,
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'content': response.text,
                    'encoding': response.encoding,
                    'cookies': dict(response.cookies)
                }
                
                loading.update_message(f"Konten berhasil diambil ({len(response.text)} chars)")
                print(f"{Fore.GREEN}✅ Konten berhasil diambil ({len(response.text)} chars){Style.RESET_ALL}")
                return content_info
                
            except Exception as e:
                loading.update_message(f"Error: {e}")
                print(f"{Fore.RED}❌ Error mengambil konten: {e}{Style.RESET_ALL}")
                return None
    
    def analyze_builtwith(self, url):
        """
        Menggunakan builtwith library untuk deteksi teknologi
        
        Args:
            url (str): URL website
            
        Returns:
            dict: Hasil analisis builtwith
        """
        with LoadingContext("Menganalisa dengan BuiltWith...", "pulse") as loading:
            try:
                loading.update_message("Menjalankan BuiltWith parser...")
                result = builtwith.parse(url)
                
                loading.update_message("Memproses hasil analisis...")
                # Clean up dan kategorisasi hasil
                cleaned_result = {}
                for category, technologies in result.items():
                    if technologies:  # Only include non-empty categories
                        cleaned_result[category] = technologies
                
                loading.update_message(f"BuiltWith analysis selesai ({len(cleaned_result)} categories)")
                print(f"{Fore.GREEN}✅ BuiltWith analysis selesai ({len(cleaned_result)} categories){Style.RESET_ALL}")
                return cleaned_result
                
            except Exception as e:
                loading.update_message(f"BuiltWith analysis gagal: {e}")
                print(f"{Fore.YELLOW}⚠️  BuiltWith analysis gagal: {e}{Style.RESET_ALL}")
                return {}
    
    def analyze_headers(self, headers):
        """
        Menganalisa HTTP headers untuk mendeteksi teknologi
        
        Args:
            headers (dict): HTTP response headers
            
        Returns:
            dict: Teknologi yang terdeteksi dari headers
        """
        with LoadingContext("Menganalisa HTTP headers...", "pulse") as loading:
            loading.update_message("Memproses header informasi...")
            
            detected_tech = {
                'servers': [],
                'frameworks': [],
                'languages': [],
                'cdn': [],
                'security': []
            }
        
            # Analyze server header
            loading.update_message("Menganalisa server header...")
            server = headers.get('server', '').lower()
            if 'apache' in server:
                detected_tech['servers'].append('Apache')
            elif 'nginx' in server:
                detected_tech['servers'].append('Nginx')
            elif 'iis' in server or 'microsoft' in server:
                detected_tech['servers'].append('Microsoft IIS')
            elif 'litespeed' in server:
                detected_tech['servers'].append('LiteSpeed')
            
            # Analyze X-Powered-By header
            loading.update_message("Menganalisa X-Powered-By header...")
            powered_by = headers.get('x-powered-by', '').lower()
            if 'php' in powered_by:
                detected_tech['languages'].append(f"PHP {powered_by.split('/')[-1] if '/' in powered_by else ''}")
            elif 'asp.net' in powered_by:
                detected_tech['frameworks'].append('ASP.NET')
            elif 'express' in powered_by:
                detected_tech['frameworks'].append('Express.js')
            
            # Check for CDN headers
            loading.update_message("Memeriksa CDN headers...")
            if 'cf-ray' in headers or 'cloudflare' in server:
                detected_tech['cdn'].append('Cloudflare')
            if 'x-amz-cf-id' in headers:
                detected_tech['cdn'].append('AWS CloudFront')
            
            # Security headers
            loading.update_message("Menganalisa security headers...")
            security_headers = [
                'strict-transport-security',
                'content-security-policy',
                'x-frame-options',
                'x-content-type-options',
                'x-xss-protection'
            ]
            
            for header in security_headers:
                if header in headers:
                    detected_tech['security'].append(header.replace('-', ' ').title())
            
            # Remove empty categories
            loading.update_message("Memproses hasil analisis...")
            detected_tech = {k: v for k, v in detected_tech.items() if v}
            
            loading.update_message("Header analysis selesai")
            print(f"{Fore.GREEN}✅ Header analysis selesai{Style.RESET_ALL}")
            return detected_tech
    
    def analyze_content(self, content):
        """
        Menganalisa konten HTML untuk mendeteksi teknologi
        
        Args:
            content (str): HTML content
            
        Returns:
            dict: Teknologi yang terdeteksi dari content
        """
        with LoadingContext("Menganalisa konten HTML...", "pulse") as loading:
            loading.update_message("Mempersiapkan analisis konten...")
            
            detected_tech = {
                'frameworks': [],
                'cms': [],
                'languages': [],
                'analytics': [],
                'cdn': [],
                'libraries': []
            }
            
            content_lower = content.lower()
            
            # Check against signatures
            loading.update_message("Mencocokkan signature teknologi...")
            progress = ProgressTracker(len(self.tech_signatures), "Analyzing Signatures")
            
            for i, (category, techs) in enumerate(self.tech_signatures.items()):
                progress.update(i + 1, f"Checking {category}")
                for tech_name, patterns in techs.items():
                    for pattern in patterns:
                        if re.search(pattern, content_lower, re.IGNORECASE):
                            if tech_name not in detected_tech.get(category, []):
                                detected_tech.setdefault(category, []).append(tech_name)
                            break
            progress.complete()
        
            # Parse HTML untuk analisis lebih detail
            loading.update_message("Parsing HTML untuk analisis detail...")
            try:
                soup = BeautifulSoup(content, 'html.parser')
                
                # Check meta tags
                loading.update_message("Menganalisa meta tags...")
                meta_generator = soup.find('meta', attrs={'name': 'generator'})
                if meta_generator and meta_generator.get('content'):
                    generator = meta_generator.get('content')
                    detected_tech.setdefault('cms', []).append(f"Generated by: {generator}")
                
                # Check script sources
                loading.update_message("Menganalisa script sources...")
                scripts = soup.find_all('script', src=True)
                for script in scripts:
                    src = script.get('src', '').lower()
                    
                    # Check for popular CDNs and libraries
                    if 'jquery' in src:
                        detected_tech.setdefault('libraries', []).append('jQuery')
                    elif 'bootstrap' in src:
                        detected_tech.setdefault('frameworks', []).append('Bootstrap')
                    elif 'react' in src:
                        detected_tech.setdefault('frameworks', []).append('React')
                    elif 'vue' in src:
                        detected_tech.setdefault('frameworks', []).append('Vue.js')
                    elif 'angular' in src:
                        detected_tech.setdefault('frameworks', []).append('Angular')
                    elif 'googleapis.com' in src:
                        detected_tech.setdefault('cdn', []).append('Google CDN')
                    elif 'cloudflare' in src or 'cdnjs' in src:
                        detected_tech.setdefault('cdn', []).append('Cloudflare CDN')
                
                # Check link tags (CSS)
                loading.update_message("Menganalisa CSS links...")
                links = soup.find_all('link', href=True)
                for link in links:
                    href = link.get('href', '').lower()
                    
                    if 'bootstrap' in href:
                        detected_tech.setdefault('frameworks', []).append('Bootstrap')
                    elif 'font-awesome' in href:
                        detected_tech.setdefault('libraries', []).append('Font Awesome')
                    elif 'googleapis.com' in href:
                        detected_tech.setdefault('cdn', []).append('Google Fonts')
                
            except Exception as e:
                loading.update_message(f"Error saat parsing HTML: {e}")
        
        # Remove duplicates and empty categories
        for category in detected_tech:
            detected_tech[category] = list(set(detected_tech[category]))
        detected_tech = {k: v for k, v in detected_tech.items() if v}
        
        print(f"{Fore.GREEN}✅ Content analysis selesai{Style.RESET_ALL}")
        return detected_tech
    
    def analyze_ssl_certificate(self, url):
        """
        Menganalisa SSL certificate
        
        Args:
            url (str): URL website
            
        Returns:
            dict: Informasi SSL certificate
        """
        print(f"{Fore.CYAN}🔒 Menganalisa SSL certificate...{Style.RESET_ALL}")
        
        try:
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
            
            if parsed_url.scheme != 'https':
                return {'error': 'Website tidak menggunakan HTTPS'}
            
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
            
            ssl_info = {
                'subject': dict(x[0] for x in cert['subject']),
                'issuer': dict(x[0] for x in cert['issuer']),
                'version': cert['version'],
                'serial_number': cert['serialNumber'],
                'not_before': cert['notBefore'],
                'not_after': cert['notAfter'],
                'signature_algorithm': cert.get('signatureAlgorithm', 'Unknown')
            }
            
            # Determine CA
            issuer_org = ssl_info['issuer'].get('organizationName', '')
            if 'Let\'s Encrypt' in issuer_org:
                ssl_info['ca_type'] = 'Let\'s Encrypt (Free)'
            elif 'DigiCert' in issuer_org:
                ssl_info['ca_type'] = 'DigiCert (Commercial)'
            elif 'Cloudflare' in issuer_org:
                ssl_info['ca_type'] = 'Cloudflare'
            else:
                ssl_info['ca_type'] = issuer_org or 'Unknown CA'
            
            print(f"{Fore.GREEN}✅ SSL analysis selesai{Style.RESET_ALL}")
            return ssl_info
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  SSL analysis gagal: {e}{Style.RESET_ALL}")
            return {'error': str(e)}
    
    def get_whois_info(self, url):
        """
        Mendapatkan informasi WHOIS domain
        
        Args:
            url (str): URL website
            
        Returns:
            dict: Informasi WHOIS
        """
        print(f"{Fore.CYAN}🔍 Mengambil informasi WHOIS...{Style.RESET_ALL}")
        
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.hostname
            
            w = whois.whois(domain)
            
            whois_info = {
                'domain_name': w.domain_name,
                'registrar': w.registrar,
                'creation_date': str(w.creation_date) if w.creation_date else None,
                'expiration_date': str(w.expiration_date) if w.expiration_date else None,
                'name_servers': w.name_servers if w.name_servers else [],
                'status': w.status if w.status else [],
                'country': w.country
            }
            
            print(f"{Fore.GREEN}✅ WHOIS info berhasil diambil{Style.RESET_ALL}")
            return whois_info
            
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  WHOIS lookup gagal: {e}{Style.RESET_ALL}")
            return {'error': str(e)}
    
    def generate_report(self, url, builtwith_result, header_analysis, content_analysis, ssl_info, whois_info):
        """
        Generate comprehensive tech stack report
        
        Args:
            url (str): Website URL
            builtwith_result (dict): BuiltWith analysis result
            header_analysis (dict): Header analysis result
            content_analysis (dict): Content analysis result
            ssl_info (dict): SSL certificate info
            whois_info (dict): WHOIS information
            
        Returns:
            str: Formatted report
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        parsed_url = urlparse(url)
        domain = parsed_url.hostname
        
        report = f"""# Tech Stack Analysis Report

## Website Information
- **URL**: {url}
- **Domain**: {domain}
- **Analysis Date**: {timestamp}
- **Tool**: Reescraping Tech Analyzer v1.0.0

## Executive Summary

This report provides a comprehensive analysis of the technology stack used by {domain}. The analysis includes web frameworks, content management systems, programming languages, servers, CDNs, analytics tools, and security implementations.

## Technology Stack Overview

### Web Frameworks & Libraries
"""
        
        # Combine frameworks from all sources
        all_frameworks = set()
        if 'frameworks' in builtwith_result:
            all_frameworks.update(builtwith_result['frameworks'])
        if 'frameworks' in header_analysis:
            all_frameworks.update(header_analysis['frameworks'])
        if 'frameworks' in content_analysis:
            all_frameworks.update(content_analysis['frameworks'])
        
        if all_frameworks:
            for framework in sorted(all_frameworks):
                report += f"- {framework}\n"
        else:
            report += "- No specific frameworks detected\n"
        
        # Programming Languages
        report += "\n### Programming Languages\n"
        all_languages = set()
        if 'languages' in builtwith_result:
            all_languages.update(builtwith_result['languages'])
        if 'languages' in header_analysis:
            all_languages.update(header_analysis['languages'])
        if 'languages' in content_analysis:
            all_languages.update(content_analysis['languages'])
        
        if all_languages:
            for language in sorted(all_languages):
                report += f"- {language}\n"
        else:
            report += "- Language detection inconclusive\n"
        
        # Web Servers
        report += "\n### Web Servers\n"
        all_servers = set()
        if 'servers' in builtwith_result:
            all_servers.update(builtwith_result['servers'])
        if 'servers' in header_analysis:
            all_servers.update(header_analysis['servers'])
        
        if all_servers:
            for server in sorted(all_servers):
                report += f"- {server}\n"
        else:
            report += "- Server information not available\n"
        
        # Content Management System
        report += "\n### Content Management System (CMS)\n"
        all_cms = set()
        if 'cms' in builtwith_result:
            all_cms.update(builtwith_result['cms'])
        if 'cms' in content_analysis:
            all_cms.update(content_analysis['cms'])
        
        if all_cms:
            for cms in sorted(all_cms):
                report += f"- {cms}\n"
        else:
            report += "- No CMS detected or custom-built website\n"
        
        # CDN & Hosting
        report += "\n### CDN & Hosting Services\n"
        all_cdn = set()
        if 'cdn' in builtwith_result:
            all_cdn.update(builtwith_result['cdn'])
        if 'cdn' in header_analysis:
            all_cdn.update(header_analysis['cdn'])
        if 'cdn' in content_analysis:
            all_cdn.update(content_analysis['cdn'])
        
        if all_cdn:
            for cdn in sorted(all_cdn):
                report += f"- {cdn}\n"
        else:
            report += "- No CDN services detected\n"
        
        # Analytics & Tracking
        report += "\n### Analytics & Tracking\n"
        all_analytics = set()
        if 'analytics' in builtwith_result:
            all_analytics.update(builtwith_result['analytics'])
        if 'analytics' in content_analysis:
            all_analytics.update(content_analysis['analytics'])
        
        if all_analytics:
            for analytics in sorted(all_analytics):
                report += f"- {analytics}\n"
        else:
            report += "- No analytics tools detected\n"
        
        # Security Analysis
        report += "\n## Security Analysis\n\n### SSL Certificate\n"
        if 'error' not in ssl_info:
            report += f"""- **Subject**: {ssl_info.get('subject', {}).get('commonName', 'N/A')}
- **Issuer**: {ssl_info.get('issuer', {}).get('organizationName', 'N/A')}
- **CA Type**: {ssl_info.get('ca_type', 'Unknown')}
- **Valid From**: {ssl_info.get('not_before', 'N/A')}
- **Valid Until**: {ssl_info.get('not_after', 'N/A')}
- **Signature Algorithm**: {ssl_info.get('signature_algorithm', 'N/A')}
"""
        else:
            report += f"- **Error**: {ssl_info['error']}\n"
        
        # Security Headers
        report += "\n### Security Headers\n"
        if 'security' in header_analysis:
            for header in header_analysis['security']:
                report += f"- ✅ {header}\n"
        else:
            report += "- ⚠️  No security headers detected\n"
        
        # Domain Information
        report += "\n## Domain Information\n"
        if 'error' not in whois_info:
            report += f"""- **Domain**: {whois_info.get('domain_name', 'N/A')}
- **Registrar**: {whois_info.get('registrar', 'N/A')}
- **Creation Date**: {whois_info.get('creation_date', 'N/A')}
- **Expiration Date**: {whois_info.get('expiration_date', 'N/A')}
- **Country**: {whois_info.get('country', 'N/A')}
"""
            
            if whois_info.get('name_servers'):
                report += "\n### Name Servers\n"
                for ns in whois_info['name_servers']:
                    report += f"- {ns}\n"
        else:
            report += f"- **Error**: {whois_info['error']}\n"
        
        # Detailed BuiltWith Results
        if builtwith_result:
            report += "\n## Detailed Technology Detection (BuiltWith)\n"
            for category, technologies in builtwith_result.items():
                if technologies:
                    report += f"\n### {category.replace('-', ' ').title()}\n"
                    for tech in technologies:
                        report += f"- {tech}\n"
        
        # Recommendations
        report += "\n## Recommendations\n\n### Security\n"
        
        if 'security' not in header_analysis or not header_analysis['security']:
            report += "- ⚠️  Consider implementing security headers (HSTS, CSP, X-Frame-Options)\n"
        
        if ssl_info.get('ca_type') == 'Let\'s Encrypt (Free)':
            report += "- ✅ Using Let's Encrypt SSL certificate (good for basic security)\n"
        elif 'error' in ssl_info:
            report += "- ❌ SSL certificate issues detected - consider fixing\n"
        
        report += "\n### Performance\n"
        if 'cdn' not in header_analysis and 'cdn' not in content_analysis:
            report += "- 💡 Consider using a CDN service for better performance\n"
        
        if 'Cloudflare' in str(all_cdn):
            report += "- ✅ Using Cloudflare CDN for performance optimization\n"
        
        report += "\n---\n*Generated by Reescraping Tech Analyzer v1.0.0*"
        
        return report
    
    def analyze_website(self, url, output_dir="hasil"):
        """
        Method utama untuk analisis tech stack website lengkap
        
        Args:
            url (str): URL website yang akan dianalisis
            output_dir (str): Directory output
            
        Returns:
            dict: Hasil analisis atau None jika gagal
        """
        with LoadingContext(f"Memulai tech stack analysis...", "pulse") as loading:
            url = self.normalize_url(url)
            parsed_url = urlparse(url)
            domain = parsed_url.hostname
            
            loading.update_message(f"Menganalisa website: {url}")
            
            try:
                # Get website content
                loading.update_message("Mengambil konten website...")
                content_info = self.get_website_content(url)
                if not content_info:
                    return None
                
                # Perform various analyses
                progress = ProgressTracker(5, "Tech Analysis")
                
                progress.update(1, "BuiltWith Analysis")
                builtwith_result = self.analyze_builtwith(url)
                
                progress.update(2, "Header Analysis")
                header_analysis = self.analyze_headers(content_info['headers'])
                
                progress.update(3, "Content Analysis")
                content_analysis = self.analyze_content(content_info['content'])
                
                progress.update(4, "SSL Certificate")
                ssl_info = self.analyze_ssl_certificate(url)
                
                progress.update(5, "WHOIS Information")
                whois_info = self.get_whois_info(url)
                
                progress.complete()
                
                # Generate comprehensive report
                loading.update_message("Membuat laporan komprehensif...")
                report = self.generate_report(url, builtwith_result, header_analysis, content_analysis, ssl_info, whois_info)
                
                # Save report
                loading.update_message("Menyimpan laporan...")
                os.makedirs(output_dir, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tech_analysis_{domain.replace('.', '_')}_{timestamp}.md"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                loading.update_message(f"✅ Analysis selesai! Report: {filepath}")
                
                return {
                    'url': url,
                    'domain': domain,
                    'filepath': filepath,
                    'builtwith_result': builtwith_result,
                    'header_analysis': header_analysis,
                    'content_analysis': content_analysis,
                    'ssl_info': ssl_info,
                    'whois_info': whois_info
                }
                
            except Exception as e:
                loading.update_message(f"❌ Error: {e}")
                return None


class TechAnalyzerModule:
    """
    Module interface untuk Tech Stack Analyzer yang terintegrasi dengan menu utama
    """
    
    def __init__(self):
        self.analyzer = TechStackAnalyzer()
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self):
        """Print header untuk tech analyzer module"""
        header = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                 {Fore.YELLOW}TECH STACK ANALYZER{Fore.CYAN}                     ║
║            {Fore.GREEN}Comprehensive Technology Detection{Fore.CYAN}            ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(header)
        
    def get_url_input(self):
        """Mendapatkan input URL dari user"""
        print(f"{Fore.WHITE}Masukkan URL website yang ingin dianalisis tech stack-nya:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Contoh: https://example.com atau example.com{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Tool akan menganalisa framework, CMS, server, database, dll{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Ketik 'back' untuk kembali ke menu utama{Style.RESET_ALL}\n")
        
        while True:
            user_input = input(f"{Fore.GREEN}Website URL: {Style.RESET_ALL}").strip()
            
            if user_input.lower() in ['back', 'kembali', 'b']:
                return None
            
            if not user_input:
                print(f"{Fore.RED}❌ Silakan masukkan URL yang valid.{Style.RESET_ALL}\n")
                continue
            
            return user_input
    
    def run(self):
        """Menjalankan tech analyzer module"""
        self.clear_screen()
        self.print_header()
        
        url = self.get_url_input()
        if not url:
            return
        
        with LoadingContext("Mempersiapkan tech stack analysis...", "pulse") as loading:
            loading.update_message("Memulai proses analisis...")
            result = self.analyzer.analyze_website(url)
        
        if result:
            print(f"\n{Fore.GREEN}🎉 Tech stack analysis berhasil!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 Ringkasan hasil:{Style.RESET_ALL}")
            
            # Show summary
            builtwith_result = result['builtwith_result']
            header_analysis = result['header_analysis']
            content_analysis = result['content_analysis']
            
            print(f"{Fore.WHITE}   • Website: {result['url']}{Style.RESET_ALL}")
            
            # Count detected technologies
            total_tech = 0
            for analysis in [builtwith_result, header_analysis, content_analysis]:
                for category, items in analysis.items():
                    total_tech += len(items) if isinstance(items, list) else 1
            
            print(f"{Fore.WHITE}   • Total Technologies Detected: {total_tech}{Style.RESET_ALL}")
            
            # Show key findings
            if 'frameworks' in content_analysis:
                print(f"{Fore.WHITE}   • Frameworks: {', '.join(content_analysis['frameworks'][:3])}{Style.RESET_ALL}")
            if 'cms' in content_analysis:
                print(f"{Fore.WHITE}   • CMS: {', '.join(content_analysis['cms'][:2])}{Style.RESET_ALL}")
            if 'servers' in header_analysis:
                print(f"{Fore.WHITE}   • Server: {', '.join(header_analysis['servers'])}{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}📁 Report lengkap disimpan di: {result['filepath']}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ Gagal melakukan tech stack analysis{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Tekan Enter untuk kembali ke menu utama...{Style.RESET_ALL}")


if __name__ == "__main__":
    # Standalone mode untuk testing
    module = TechAnalyzerModule()
    module.run()