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
from collections import defaultdict
from datetime import datetime
from bs4 import BeautifulSoup, Comment
from urllib.parse import urljoin, urlparse, urlunparse
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
        
        # Tech signatures untuk deteksi manual (expanded)
        self.tech_signatures = {
            'frameworks': {
                'React': [r'react', r'_react', r'React\.createElement', r'react-dom', r'__REACT_DEVTOOLS'],
                'Next.js': [r'next\.js', r'__next', r'_next/static', r'__NEXT_DATA__'],
                'Vue.js': [r'vue\.js', r'Vue\.', r'__vue__', r'vue-router', r'vuex'],
                'Nuxt.js': [r'nuxt', r'__nuxt', r'_nuxt/', r'nuxt\.js'],
                'Angular': [r'angular', r'ng-', r'@angular', r'angular\.min\.js'],
                'Svelte': [r'svelte', r'_svelte', r'svelte\.js'],
                'SvelteKit': [r'sveltekit', r'data-sveltekit'],
                'Gatsby': [r'gatsby', r'gatsby-', r'___gatsby'],
                'Astro': [r'astro-', r'astrojs', r'astro\.build'],
                'Remix': [r'remix-', r'@remix-run'],
                'Alpine.js': [r'alpinejs', r'x-data', r'alpine\.js'],
                'jQuery': [r'jquery', r'\$\(', r'jQuery'],
                'Bootstrap': [r'bootstrap', r'btn-', r'container-fluid', r'bootstrap\.min'],
                'Tailwind CSS': [r'tailwind', r'tw-', r'tailwindcss'],
                'Foundation': [r'foundation', r'zurb-foundation'],
                'Materialize': [r'materialize', r'material-icons'],
                'Bulma': [r'bulma', r'is-primary', r'column'],
                'Semantic UI': [r'semantic', r'ui segment', r'ui container'],
                'Material-UI': [r'material-ui', r'@mui/', r'mui\.com'],
                'Ant Design': [r'antd', r'ant-design', r'@ant-design'],
                'Chakra UI': [r'chakra-ui', r'@chakra-ui'],
                'Express.js': [r'express', r'x-powered-by.*express'],
                'Laravel': [r'laravel', r'laravel_session', r'XSRF-TOKEN'],
                'Django': [r'django', r'csrftoken', r'__admin__'],
                'Flask': [r'flask', r'werkzeug'],
                'Ruby on Rails': [r'rails', r'ruby on rails', r'_session_id'],
                'Spring': [r'spring', r'jsessionid', r'spring framework'],
                'ASP.NET Core': [r'asp\.net core', r'aspnetcore', r'\.aspnetcore\.']
            },
            'cms': {
                'WordPress': [r'wp-content', r'wp-includes', r'wordpress', r'/wp-json/'],
                'Drupal': [r'drupal', r'sites/default', r'misc/drupal', r'/sites/all/'],
                'Joomla': [r'joomla', r'option=com_', r'templates/', r'/media/jui/'],
                'Magento': [r'magento', r'mage/', r'skin/frontend', r'Mage\.Cookies'],
                'Shopify': [r'shopify', r'cdn.shopify.com', r'myshopify.com', r'Shopify\.theme'],
                'WooCommerce': [r'woocommerce', r'wc-', r'shop/', r'woocommerce-'],
                'PrestaShop': [r'prestashop', r'ps_', r'themes/', r'prestashop\.com'],
                'OpenCart': [r'opencart', r'catalog/view', r'image/catalog', r'route='],
                'Wix': [r'wix\.com', r'wixsite\.com', r'static\.wixstatic'],
                'Squarespace': [r'squarespace', r'sqsp\.net', r'static1\.squarespace'],
                'Webflow': [r'webflow', r'webflow\.com', r'assets\.website-files'],
                'Ghost': [r'ghost', r'ghost\.org', r'ghost-', r'/ghost/api/'],
                'Contentful': [r'contentful', r'cdn\.contentful\.com'],
                'Strapi': [r'strapi', r'strapi\.io', r'/api/'],
                'Blogger': [r'blogger', r'blogspot\.com', r'blogger\.js'],
                'Medium': [r'medium\.com', r'medium-', r'apollo-'],
                'Notion': [r'notion', r'notion\.so', r'notion-static']
            },
            'ecommerce': {
                'Shopify': [r'shopify', r'cdn.shopify.com', r'myshopify.com'],
                'WooCommerce': [r'woocommerce', r'wc-', r'add-to-cart'],
                'Magento': [r'magento', r'mage/', r'checkout/cart'],
                'BigCommerce': [r'bigcommerce', r'cdn\d+\.bigcommerce'],
                'PrestaShop': [r'prestashop', r'ps_', r'add-to-cart'],
                'OpenCart': [r'opencart', r'route=checkout', r'image/catalog'],
                'Salesforce Commerce Cloud': [r'demandware', r'salesforce\.com'],
                'Stripe': [r'stripe', r'js\.stripe\.com', r'Stripe\('],
                'PayPal': [r'paypal', r'paypalobjects\.com'],
                'Square': [r'square', r'squareup\.com', r'squarecdn']
            },
            'servers': {
                'Apache': [r'apache', r'server: apache'],
                'Nginx': [r'nginx', r'server: nginx'],
                'IIS': [r'iis', r'server: microsoft-iis'],
                'LiteSpeed': [r'litespeed', r'server: litespeed'],
                'Cloudflare': [r'cloudflare', r'cf-ray', r'__cfduid'],
                'Varnish': [r'varnish', r'x-varnish', r'via:.*varnish'],
                'Caddy': [r'caddy', r'server: caddy'],
                'Tomcat': [r'tomcat', r'apache-coyote'],
                'Gunicorn': [r'gunicorn', r'server: gunicorn'],
                'Passenger': [r'phusion passenger', r'passenger']
            },
            'hosting': {
                'Vercel': [r'vercel', r'x-vercel-', r'vercel\.app'],
                'Netlify': [r'netlify', r'x-nf-', r'netlify\.app'],
                'AWS': [r'amazonaws\.com', r'cloudfront', r'elasticbeanstalk'],
                'Google Cloud': [r'googleapis\.com', r'gcp\.', r'appspot\.com'],
                'Azure': [r'azure', r'azurewebsites', r'windows\.net'],
                'Heroku': [r'heroku', r'herokuapp\.com'],
                'DigitalOcean': [r'digitalocean', r'digitaloceanspaces'],
                'GitHub Pages': [r'github\.io', r'pages\.github'],
                'Firebase': [r'firebase', r'firebaseapp\.com', r'googleapis\.com/firebase'],
                'Cloudflare Pages': [r'pages\.dev', r'cloudflare-pages']
            },
            'languages': {
                'PHP': [r'\.php', r'<?php', r'PHPSESSID'],
                'ASP.NET': [r'\.aspx', r'__VIEWSTATE', r'asp\.net'],
                'Node.js': [r'node\.js', r'express', r'__next'],
                'Python': [r'django', r'flask', r'wsgi'],
                'Ruby': [r'ruby', r'rails', r'rack'],
                'Java': [r'java', r'jsp', r'jsessionid'],
                'Go': [r'golang', r'go-', r'gorilla'],
                'Rust': [r'actix', r'rocket', r'warp'],
                'TypeScript': [r'typescript', r'\.ts', r'tsc'],
                'Perl': [r'perl', r'\.pl', r'mod_perl']
            },
            'analytics': {
                'Google Analytics': [r'google-analytics', r'gtag', r'ga\(', r'analytics\.js'],
                'Google Tag Manager': [r'googletagmanager', r'gtm\.js'],
                'Facebook Pixel': [r'facebook\.net/tr', r'fbq\(', r'connect\.facebook'],
                'Hotjar': [r'hotjar', r'hj\(', r'static\.hotjar'],
                'Mixpanel': [r'mixpanel', r'mp_', r'cdn\.mxpnl'],
                'Adobe Analytics': [r'omniture', r'adobe\.com/.*analytics', r'omtr'],
                'Segment': [r'segment\.io', r'segment\.com', r'analytics\.min\.js'],
                'Matomo': [r'matomo', r'piwik', r'matomo\.js'],
                'Plausible': [r'plausible', r'plausible\.io'],
                'Fathom': [r'fathom', r'usefathom\.com'],
                'Amplitude': [r'amplitude', r'cdn\.amplitude']
            },
            'cdn': {
                'Cloudflare': [r'cloudflare', r'cdnjs\.cloudflare'],
                'AWS CloudFront': [r'cloudfront', r'amazonaws'],
                'MaxCDN': [r'maxcdn', r'bootstrapcdn'],
                'jsDelivr': [r'jsdelivr', r'cdn\.jsdelivr'],
                'unpkg': [r'unpkg\.com'],
                'Google CDN': [r'googleapis\.com', r'gstatic\.com'],
                'Fastly': [r'fastly', r'fastly\.net'],
                'Akamai': [r'akamai', r'akamaized\.net'],
                'Bunny CDN': [r'bunny\.net', r'b-cdn\.net'],
                'KeyCDN': [r'keycdn', r'kxcdn\.com'],
                'StackPath': [r'stackpath', r'stackpathcdn']
            },
            'marketing': {
                'Mailchimp': [r'mailchimp', r'list-manage\.com', r'mc\.js'],
                'HubSpot': [r'hubspot', r'hs-scripts\.com', r'hsforms'],
                'Intercom': [r'intercom', r'intercom\.io', r'widget\.intercom'],
                'Drift': [r'drift', r'drift\.com', r'driftt\.com'],
                'Zendesk': [r'zendesk', r'zdassets\.com'],
                'LiveChat': [r'livechat', r'livechatinc\.com'],
                'Crisp': [r'crisp', r'crisp\.chat']
            },
            'seo': {
                'Yoast SEO': [r'yoast', r'yoast seo'],
                'Rank Math': [r'rank-math', r'rankmath'],
                'All in One SEO': [r'aioseo', r'all in one seo'],
                'Schema.org': [r'schema\.org', r'application/ld\+json'],
                'Open Graph': [r'og:', r'property="og:']
            }
        }
        
        # Cookie signatures for tech detection
        self.cookie_signatures = {
            'PHP': ['PHPSESSID', 'phpsessid'],
            'ASP.NET': ['ASP.NET_SessionId', 'ASPSESSIONID'],
            'Java': ['JSESSIONID', 'jsessionid'],
            'Laravel': ['laravel_session', 'XSRF-TOKEN'],
            'Django': ['sessionid', 'csrftoken'],
            'Ruby on Rails': ['_session_id', '_csrf_token'],
            'WordPress': ['wordpress_', 'wp-settings'],
            'Drupal': ['SESS', 'SSESS'],
            'Joomla': ['joomla_'],
            'Express.js': ['connect.sid'],
            'ColdFusion': ['CFID', 'CFTOKEN'],
            'Flask': ['session'],
            'Cloudflare': ['__cfduid', 'cf_clearance']
        }
    
    def normalize_url(self, url):
        """
        Normalize URL dengan menambahkan protocol jika diperlukan
        
        Args:
            url (str): URL input
            
        Returns:
            str: Normalized URL
        """
        if not url:
            return url
        url = url.strip()
        if not url:
            return url
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9+\-.]*://', url):
            url = f'https://{url}'
        parsed = urlparse(url)
        scheme = parsed.scheme or 'https'
        netloc = parsed.netloc
        path = parsed.path
        if not netloc and parsed.path:
            netloc = parsed.path
            path = ''
        normalized = urlunparse((scheme, netloc, path, parsed.params, parsed.query, parsed.fragment))
        return normalized
    
    def get_website_content(self, url):
        """
        Mengambil konten website dan informasi response
        
        Args:
            url (str): URL website
            
        Returns:
            dict: Website content dan metadata
        """
        with LoadingContext("Mengambil konten website...", "pulse") as loading:
            normalized_url = self.normalize_url(url)
            parsed = urlparse(normalized_url)
            hostname = parsed.netloc
            attempt_urls = [normalized_url]
            
            if hostname and parsed.scheme != 'http':
                attempt_urls.append(urlunparse(('http', hostname, parsed.path, parsed.params, parsed.query, parsed.fragment)))
            
            if hostname and not hostname.startswith('www.'):
                attempt_urls.append(urlunparse((parsed.scheme or 'https', f'www.{hostname}', parsed.path, parsed.params, parsed.query, parsed.fragment)))
                attempt_urls.append(urlunparse(('http', f'www.{hostname}', parsed.path, parsed.params, parsed.query, parsed.fragment)))
            
            attempt_urls = list(dict.fromkeys([u for u in attempt_urls if u]))
            last_error = None
            
            for attempt in attempt_urls:
                try:
                    loading.update_message(f"Mengirim HTTP request ke {attempt}...")
                    response = self.session.get(attempt, timeout=self.timeout, allow_redirects=True)
                    response.raise_for_status()
                    
                    loading.update_message("Memproses response...")
                    content_info = {
                        'requested_url': attempt,
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
                    last_error = e
                    loading.update_message(f"Gagal mencoba {attempt}: {e}")
                    print(f"{Fore.YELLOW}⚠️  Gagal mengambil konten dari {attempt}: {e}{Style.RESET_ALL}")
            
            loading.update_message("Tidak dapat mengambil konten dari semua percobaan")
            print(f"{Fore.RED}❌ Error mengambil konten: {last_error}{Style.RESET_ALL}")
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
            normalized_url = self.normalize_url(url)
            parsed = urlparse(normalized_url)
            hostname = parsed.netloc
            attempts = [normalized_url]
            
            if hostname and parsed.scheme != 'http':
                attempts.append(urlunparse(('http', hostname, parsed.path, parsed.params, parsed.query, parsed.fragment)))
            
            if hostname:
                attempts.append(hostname)
                attempts.append(f'https://{hostname}')
                attempts.append(f'http://{hostname}')
            
            attempts = list(dict.fromkeys([a for a in attempts if a]))
            aggregated = defaultdict(set)
            last_error = None
            
            for attempt in attempts:
                try:
                    loading.update_message(f"BuiltWith: {attempt}")
                    result = builtwith.parse(attempt)
                    for category, technologies in result.items():
                        if technologies:
                            aggregated[category].update(technologies)
                except Exception as e:
                    last_error = e
                    continue
            
            if aggregated:
                cleaned_result = {category: sorted(values) for category, values in aggregated.items() if values}
                loading.update_message(f"BuiltWith analysis selesai ({len(cleaned_result)} categories)")
                print(f"{Fore.GREEN}✅ BuiltWith analysis selesai ({len(cleaned_result)} categories){Style.RESET_ALL}")
                return cleaned_result
            
            loading.update_message("BuiltWith tidak menemukan teknologi")
            if last_error:
                print(f"{Fore.YELLOW}⚠️  BuiltWith analysis gagal: {last_error}{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️  BuiltWith analysis tidak menemukan teknologi{Style.RESET_ALL}")
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
                'hosting': [],
                'security': [],
                'cms': []
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
            elif 'caddy' in server:
                detected_tech['servers'].append('Caddy')
            elif 'cloudflare' in server:
                detected_tech['servers'].append('Cloudflare')
            
            # Analyze X-Powered-By header
            loading.update_message("Menganalisa X-Powered-By header...")
            powered_by = headers.get('x-powered-by', '').lower()
            if 'php' in powered_by:
                detected_tech['languages'].append(f"PHP {powered_by.split('/')[-1] if '/' in powered_by else ''}")
            elif 'asp.net' in powered_by:
                detected_tech['frameworks'].append('ASP.NET')
            elif 'express' in powered_by:
                detected_tech['frameworks'].append('Express.js')
            elif 'next.js' in powered_by:
                detected_tech['frameworks'].append('Next.js')
            
            # Check for hosting/platform specific headers
            loading.update_message("Memeriksa platform headers...")
            if any(k.startswith('x-vercel-') for k in headers.keys()):
                detected_tech['hosting'].append('Vercel')
            if any(k.startswith('x-nf-') for k in headers.keys()):
                detected_tech['hosting'].append('Netlify')
            if 'x-shopify-stage' in headers:
                detected_tech['cms'].append('Shopify')
            if 'x-drupal-cache' in headers or 'x-drupal-dynamic-cache' in headers:
                detected_tech['cms'].append('Drupal')
            if 'x-wix-request-id' in headers:
                detected_tech['cms'].append('Wix')
            if 'x-github-request-id' in headers:
                detected_tech['hosting'].append('GitHub Pages')
            
            # Check for CDN headers
            loading.update_message("Memeriksa CDN headers...")
            if 'cf-ray' in headers or 'cloudflare' in server:
                detected_tech['cdn'].append('Cloudflare')
            if 'x-amz-cf-id' in headers or 'x-amz-cf-pop' in headers:
                detected_tech['cdn'].append('AWS CloudFront')
            if 'x-fastly-request-id' in headers:
                detected_tech['cdn'].append('Fastly')
            if 'x-akamai-transformed' in headers:
                detected_tech['cdn'].append('Akamai')
            if 'x-cache' in headers and 'varnish' in headers.get('x-cache', '').lower():
                detected_tech['cdn'].append('Varnish')
            
            # Check Via header for proxies/CDN
            loading.update_message("Memeriksa Via header...")
            via = headers.get('via', '').lower()
            if 'varnish' in via:
                detected_tech['cdn'].append('Varnish')
            if 'cloudflare' in via:
                detected_tech['cdn'].append('Cloudflare')
            
            # Check for generator headers
            loading.update_message("Memeriksa generator headers...")
            generator = headers.get('x-generator', '').lower()
            if generator:
                if 'drupal' in generator:
                    detected_tech['cms'].append('Drupal')
                elif 'wordpress' in generator:
                    detected_tech['cms'].append('WordPress')
                elif 'joomla' in generator:
                    detected_tech['cms'].append('Joomla')
                else:
                    detected_tech['cms'].append(f"Generated by: {generator}")
            
            # Security headers
            loading.update_message("Menganalisa security headers...")
            security_headers = [
                'strict-transport-security',
                'content-security-policy',
                'x-frame-options',
                'x-content-type-options',
                'x-xss-protection',
                'permissions-policy',
                'referrer-policy'
            ]
            
            for header in security_headers:
                if header in headers:
                    detected_tech['security'].append(header.replace('-', ' ').title())
            
            # Remove empty categories and duplicates
            loading.update_message("Memproses hasil analisis...")
            for category in detected_tech:
                detected_tech[category] = list(set(detected_tech[category]))
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
                
                # Check for additional meta tags
                for meta in soup.find_all('meta'):
                    meta_content = str(meta.get('content', '')).lower()
                    meta_name = str(meta.get('name', '')).lower()
                    
                    if 'wix' in meta_content or 'wix' in meta_name:
                        detected_tech.setdefault('cms', []).append('Wix')
                    elif 'shopify' in meta_content or 'shopify' in meta_name:
                        detected_tech.setdefault('cms', []).append('Shopify')
                    elif 'wordpress' in meta_content:
                        detected_tech.setdefault('cms', []).append('WordPress')
                
                # Check HTML comments for clues
                loading.update_message("Menganalisa HTML comments...")
                comments = soup.find_all(string=lambda text: isinstance(text, Comment))
                for comment in comments:
                    comment_lower = comment.lower()
                    if 'wordpress' in comment_lower:
                        detected_tech.setdefault('cms', []).append('WordPress')
                    elif 'drupal' in comment_lower:
                        detected_tech.setdefault('cms', []).append('Drupal')
                    elif 'joomla' in comment_lower:
                        detected_tech.setdefault('cms', []).append('Joomla')
                    elif 'shopify' in comment_lower:
                        detected_tech.setdefault('cms', []).append('Shopify')
                    elif 'wix' in comment_lower:
                        detected_tech.setdefault('cms', []).append('Wix')
                    elif 'squarespace' in comment_lower:
                        detected_tech.setdefault('cms', []).append('Squarespace')
                
                # Check script sources
                loading.update_message("Menganalisa script sources...")
                scripts = soup.find_all('script', src=True)
                for script in scripts:
                    src = script.get('src', '').lower()
                    
                    # Check for popular frameworks and libraries
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
                    elif 'next' in src and ('static' in src or 'chunk' in src):
                        detected_tech.setdefault('frameworks', []).append('Next.js')
                    elif 'nuxt' in src:
                        detected_tech.setdefault('frameworks', []).append('Nuxt.js')
                    elif 'gatsby' in src:
                        detected_tech.setdefault('frameworks', []).append('Gatsby')
                    elif 'svelte' in src:
                        detected_tech.setdefault('frameworks', []).append('Svelte')
                    elif 'googleapis.com' in src:
                        detected_tech.setdefault('cdn', []).append('Google CDN')
                    elif 'cloudflare' in src or 'cdnjs' in src:
                        detected_tech.setdefault('cdn', []).append('Cloudflare CDN')
                    elif 'jsdelivr' in src:
                        detected_tech.setdefault('cdn', []).append('jsDelivr')
                    elif 'unpkg' in src:
                        detected_tech.setdefault('cdn', []).append('unpkg')
                
                # Check inline scripts for framework markers
                loading.update_message("Menganalisa inline scripts...")
                inline_scripts = soup.find_all('script', src=False)
                for script in inline_scripts:
                    script_text = script.string or ''
                    script_lower = script_text.lower()
                    
                    if '__NEXT_DATA__' in script_text or 'next.js' in script_lower:
                        detected_tech.setdefault('frameworks', []).append('Next.js')
                    elif '__nuxt' in script_lower or 'nuxt' in script_lower:
                        detected_tech.setdefault('frameworks', []).append('Nuxt.js')
                    elif 'gatsby' in script_lower:
                        detected_tech.setdefault('frameworks', []).append('Gatsby')
                    elif 'react' in script_lower and ('reactdom' in script_lower or 'react.render' in script_lower):
                        detected_tech.setdefault('frameworks', []).append('React')
                    elif 'vue' in script_lower and ('new vue' in script_lower or 'vue.createapp' in script_lower):
                        detected_tech.setdefault('frameworks', []).append('Vue.js')
                
                # Check link tags (CSS)
                loading.update_message("Menganalisa CSS links...")
                links = soup.find_all('link', href=True)
                for link in links:
                    href = link.get('href', '').lower()
                    
                    if 'bootstrap' in href:
                        detected_tech.setdefault('frameworks', []).append('Bootstrap')
                    elif 'tailwind' in href:
                        detected_tech.setdefault('frameworks', []).append('Tailwind CSS')
                    elif 'font-awesome' in href:
                        detected_tech.setdefault('libraries', []).append('Font Awesome')
                    elif 'googleapis.com' in href:
                        detected_tech.setdefault('cdn', []).append('Google Fonts')
                    elif 'material-icons' in href or 'material-ui' in href:
                        detected_tech.setdefault('frameworks', []).append('Material-UI')
                
                # Check for data attributes that indicate frameworks
                loading.update_message("Menganalisa data attributes...")
                if soup.find(attrs={'data-reactroot': True}) or soup.find(attrs={'data-reactid': True}):
                    detected_tech.setdefault('frameworks', []).append('React')
                if soup.find(attrs={'data-v-': re.compile('.*')}):
                    detected_tech.setdefault('frameworks', []).append('Vue.js')
                if soup.find(attrs={'ng-app': True}) or soup.find(attrs={'ng-version': True}):
                    detected_tech.setdefault('frameworks', []).append('Angular')
                
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
    
    def analyze_cookies(self, cookies):
        """
        Menganalisa cookies untuk mendeteksi teknologi
        
        Args:
            cookies (dict): Cookies from response
            
        Returns:
            dict: Teknologi yang terdeteksi dari cookies
        """
        with LoadingContext("Menganalisa cookies...", "pulse") as loading:
            loading.update_message("Memproses cookie informasi...")
            
            detected_tech = {
                'frameworks': [],
                'languages': [],
                'cms': []
            }
            
            # Check cookies against signatures
            loading.update_message("Mencocokkan cookie signatures...")
            for tech_name, cookie_patterns in self.cookie_signatures.items():
                for cookie_name in cookies.keys():
                    for pattern in cookie_patterns:
                        if pattern.lower() in cookie_name.lower():
                            # Determine category
                            if tech_name in ['PHP', 'ASP.NET', 'Java', 'Python', 'Ruby']:
                                if tech_name not in detected_tech['languages']:
                                    detected_tech['languages'].append(tech_name)
                            elif tech_name in ['Laravel', 'Django', 'Ruby on Rails', 'Express.js', 'Flask']:
                                if tech_name not in detected_tech['frameworks']:
                                    detected_tech['frameworks'].append(tech_name)
                            elif tech_name in ['WordPress', 'Drupal', 'Joomla']:
                                if tech_name not in detected_tech['cms']:
                                    detected_tech['cms'].append(tech_name)
                            break
            
            # Remove empty categories
            loading.update_message("Memproses hasil analisis...")
            detected_tech = {k: v for k, v in detected_tech.items() if v}
            
            if detected_tech:
                loading.update_message("Cookie analysis selesai")
                print(f"{Fore.GREEN}✅ Cookie analysis selesai{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}⚠️  Tidak ada teknologi terdeteksi dari cookies{Style.RESET_ALL}")
            
            return detected_tech
    
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
    
    def generate_report(self, url, builtwith_result, header_analysis, content_analysis, cookie_analysis, ssl_info, whois_info):
        """
        Generate comprehensive tech stack report
        
        Args:
            url (str): Website URL
            builtwith_result (dict): BuiltWith analysis result
            header_analysis (dict): Header analysis result
            content_analysis (dict): Content analysis result
            cookie_analysis (dict): Cookie analysis result
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
        if 'frameworks' in cookie_analysis:
            all_frameworks.update(cookie_analysis['frameworks'])
        
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
        if 'languages' in cookie_analysis:
            all_languages.update(cookie_analysis['languages'])
        
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
        if 'cms' in header_analysis:
            all_cms.update(header_analysis['cms'])
        if 'cms' in content_analysis:
            all_cms.update(content_analysis['cms'])
        if 'cms' in cookie_analysis:
            all_cms.update(cookie_analysis['cms'])
        
        if all_cms:
            for cms in sorted(all_cms):
                report += f"- {cms}\n"
        else:
            report += "- No CMS detected or custom-built website\n"
        
        # Hosting Platforms
        report += "\n### Hosting & Cloud Platforms\n"
        all_hosting = set()
        if 'hosting' in builtwith_result:
            all_hosting.update(builtwith_result['hosting'])
        if 'hosting' in header_analysis:
            all_hosting.update(header_analysis['hosting'])
        if 'hosting' in content_analysis:
            all_hosting.update(content_analysis['hosting'])
        
        if all_hosting:
            for hosting in sorted(all_hosting):
                report += f"- {hosting}\n"
        else:
            report += "- Hosting platform not identified\n"
        
        # CDN Services
        report += "\n### CDN Services\n"
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
        
        # E-commerce Platforms
        if 'ecommerce' in content_analysis or 'ecommerce' in builtwith_result:
            report += "\n### E-commerce Platforms\n"
            all_ecommerce = set()
            if 'ecommerce' in builtwith_result:
                all_ecommerce.update(builtwith_result['ecommerce'])
            if 'ecommerce' in content_analysis:
                all_ecommerce.update(content_analysis['ecommerce'])
            
            for ecomm in sorted(all_ecommerce):
                report += f"- {ecomm}\n"
        
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
        
        # Marketing Tools
        if 'marketing' in content_analysis or 'marketing' in builtwith_result:
            report += "\n### Marketing & Communication Tools\n"
            all_marketing = set()
            if 'marketing' in builtwith_result:
                all_marketing.update(builtwith_result['marketing'])
            if 'marketing' in content_analysis:
                all_marketing.update(content_analysis['marketing'])
            
            for marketing in sorted(all_marketing):
                report += f"- {marketing}\n"
        
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
                progress = ProgressTracker(6, "Tech Analysis")
                
                progress.update(1, "BuiltWith Analysis")
                builtwith_result = self.analyze_builtwith(url)
                
                progress.update(2, "Header Analysis")
                header_analysis = self.analyze_headers(content_info['headers'])
                
                progress.update(3, "Content Analysis")
                content_analysis = self.analyze_content(content_info['content'])
                
                progress.update(4, "Cookie Analysis")
                cookie_analysis = self.analyze_cookies(content_info['cookies'])
                
                progress.update(5, "SSL Certificate")
                ssl_info = self.analyze_ssl_certificate(url)
                
                progress.update(6, "WHOIS Information")
                whois_info = self.get_whois_info(url)
                
                progress.complete()
                
                # Generate comprehensive report
                loading.update_message("Membuat laporan komprehensif...")
                report = self.generate_report(url, builtwith_result, header_analysis, content_analysis, cookie_analysis, ssl_info, whois_info)
                
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
                                         'cookie_analysis': cookie_analysis,
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
            cookie_analysis = result.get('cookie_analysis', {})
            
            print(f"{Fore.WHITE}   • Website: {result['url']}{Style.RESET_ALL}")
            
            # Count detected technologies across all sources
            total_tech = 0
            for analysis in [builtwith_result, header_analysis, content_analysis, cookie_analysis]:
                if not isinstance(analysis, dict):
                    continue
                for category, items in analysis.items():
                    if isinstance(items, (list, tuple, set)):
                        total_tech += len(items)
                    elif items:
                        total_tech += 1
            
            print(f"{Fore.WHITE}   • Total Technologies Detected: {total_tech}{Style.RESET_ALL}")
            
            # Aggregate key findings
            frameworks = set(content_analysis.get('frameworks', []))
            frameworks.update(header_analysis.get('frameworks', []))
            frameworks.update(cookie_analysis.get('frameworks', []))
            if frameworks:
                print(f"{Fore.WHITE}   • Frameworks: {', '.join(sorted(frameworks)[:3])}{Style.RESET_ALL}")
            
            cms_set = set(content_analysis.get('cms', []))
            cms_set.update(header_analysis.get('cms', []))
            cms_set.update(cookie_analysis.get('cms', []))
            if cms_set:
                print(f"{Fore.WHITE}   • CMS: {', '.join(sorted(cms_set)[:3])}{Style.RESET_ALL}")
            
            if header_analysis.get('servers'):
                print(f"{Fore.WHITE}   • Server: {', '.join(sorted(header_analysis['servers']))}{Style.RESET_ALL}")
            
            hosting = set(header_analysis.get('hosting', []))
            hosting.update(content_analysis.get('hosting', []))
            if hosting:
                print(f"{Fore.WHITE}   • Hosting: {', '.join(sorted(hosting)[:2])}{Style.RESET_ALL}")
            
            cdn_set = set(header_analysis.get('cdn', []))
            cdn_set.update(content_analysis.get('cdn', []))
            if cdn_set:
                print(f"{Fore.WHITE}   • CDN: {', '.join(sorted(cdn_set)[:2])}{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}📁 Report lengkap disimpan di: {result['filepath']}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ Gagal melakukan tech stack analysis{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Tekan Enter untuk kembali ke menu utama...{Style.RESET_ALL}")


if __name__ == "__main__":
    # Standalone mode untuk testing
    module = TechAnalyzerModule()
    module.run()