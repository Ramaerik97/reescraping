#!/usr/bin/env python3
"""
Reescraping Module - Tools untuk scraping website lengkap
Mengambil HTML, CSS, dan informasi metadata dari website
Hasil disimpan dalam format Markdown

Author: Ramaerik97
Version: 1.0.0
"""

import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import urljoin, urlparse
from datetime import datetime
import time
import sys
from colorama import Fore, Style


class WebScraper:
    """
    Class utama untuk scraping website
    """
    
    def __init__(self, timeout=30, delay=1):
        """
        Inisialisasi WebScraper
        
        Args:
            timeout (int): Timeout untuk request dalam detik
            delay (int): Delay antar request dalam detik
        """
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_html_content(self, url):
        """
        Mengambil HTML content dari website
        
        Args:
            url (str): URL website yang akan di-scrape
            
        Returns:
            tuple: (html_content, soup_object, status_code)
        """
        try:
            print(f"{Fore.CYAN}📥 Mengambil HTML dari: {url}{Style.RESET_ALL}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse dengan BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return response.text, soup, response.status_code
            
        except requests.exceptions.RequestException as e:
            print(f"{Fore.RED}❌ Error saat mengambil HTML: {e}{Style.RESET_ALL}")
            return None, None, None
    
    def extract_css(self, soup, base_url):
        """
        Mengekstrak CSS dari website (internal dan external)
        
        Args:
            soup: BeautifulSoup object
            base_url (str): Base URL website
            
        Returns:
            dict: Dictionary berisi internal_css dan external_css
        """
        css_data = {
            'internal_css': [],
            'external_css': []
        }
        
        try:
            # Ambil internal CSS (style tags)
            style_tags = soup.find_all('style')
            for style in style_tags:
                if style.string:
                    css_data['internal_css'].append(style.string.strip())
            
            # Ambil external CSS (link tags)
            link_tags = soup.find_all('link', rel='stylesheet')
            for link in link_tags:
                href = link.get('href')
                if href:
                    css_url = urljoin(base_url, href)
                    css_content = self._fetch_external_css(css_url)
                    if css_content:
                        css_data['external_css'].append({
                            'url': css_url,
                            'content': css_content
                        })
            
            print(f"{Fore.GREEN}🎨 Ditemukan {len(css_data['internal_css'])} internal CSS dan {len(css_data['external_css'])} external CSS{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error saat mengekstrak CSS: {e}{Style.RESET_ALL}")
        
        return css_data
    
    def _fetch_external_css(self, css_url):
        """
        Mengambil content dari external CSS file
        
        Args:
            css_url (str): URL file CSS
            
        Returns:
            str: Content CSS atau None jika gagal
        """
        try:
            time.sleep(self.delay)  # Delay untuk menghindari rate limiting
            response = self.session.get(css_url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  Gagal mengambil CSS dari {css_url}: {e}{Style.RESET_ALL}")
            return None
    
    def extract_metadata(self, soup):
        """
        Mengekstrak metadata dari website
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            dict: Dictionary berisi metadata website
        """
        metadata = {
            'title': '',
            'description': '',
            'keywords': '',
            'author': '',
            'og_title': '',
            'og_description': '',
            'og_image': '',
            'canonical_url': '',
            'lang': '',
            'charset': ''
        }
        
        try:
            # Title
            title_tag = soup.find('title')
            if title_tag:
                metadata['title'] = title_tag.get_text().strip()
            
            # Meta tags
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                name = meta.get('name', '').lower()
                property_attr = meta.get('property', '').lower()
                content = meta.get('content', '')
                
                if name == 'description':
                    metadata['description'] = content
                elif name == 'keywords':
                    metadata['keywords'] = content
                elif name == 'author':
                    metadata['author'] = content
                elif property_attr == 'og:title':
                    metadata['og_title'] = content
                elif property_attr == 'og:description':
                    metadata['og_description'] = content
                elif property_attr == 'og:image':
                    metadata['og_image'] = content
                elif meta.get('charset'):
                    metadata['charset'] = meta.get('charset')
            
            # Canonical URL
            canonical = soup.find('link', rel='canonical')
            if canonical:
                metadata['canonical_url'] = canonical.get('href', '')
            
            # Language
            html_tag = soup.find('html')
            if html_tag:
                metadata['lang'] = html_tag.get('lang', '')
            
            print(f"{Fore.GREEN}📋 Metadata berhasil diekstrak{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error saat mengekstrak metadata: {e}{Style.RESET_ALL}")
        
        return metadata
    
    def generate_filename(self, url):
        """
        Generate nama file berdasarkan URL website
        
        Args:
            url (str): URL website
            
        Returns:
            str: Nama file yang aman untuk sistem file
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Bersihkan karakter yang tidak aman untuk nama file
        safe_name = re.sub(r'[^\w\-_.]', '_', domain)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"{safe_name}_{timestamp}.md"
    
    def save_to_markdown(self, url, html_content, css_data, metadata, output_dir="hasil"):
        """
        Menyimpan hasil scraping ke file Markdown
        
        Args:
            url (str): URL website
            html_content (str): HTML content
            css_data (dict): Data CSS
            metadata (dict): Metadata website
            output_dir (str): Directory output
            
        Returns:
            str: Path file yang disimpan
        """
        try:
            # Buat directory jika belum ada
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate nama file
            filename = self.generate_filename(url)
            filepath = os.path.join(output_dir, filename)
            
            # Buat content Markdown
            markdown_content = self._create_markdown_content(url, html_content, css_data, metadata)
            
            # Simpan ke file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"{Fore.GREEN}💾 Hasil scraping disimpan ke: {filepath}{Style.RESET_ALL}")
            return filepath
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error saat menyimpan file: {e}{Style.RESET_ALL}")
            return None
    
    def _create_markdown_content(self, url, html_content, css_data, metadata):
        """
        Membuat content Markdown dari hasil scraping
        
        Args:
            url (str): URL website
            html_content (str): HTML content
            css_data (dict): Data CSS
            metadata (dict): Metadata website
            
        Returns:
            str: Content Markdown
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown = f"""# Website Scraping Report

## Informasi Umum
- **URL**: {url}
- **Tanggal Scraping**: {timestamp}
- **Title**: {metadata.get('title', 'N/A')}
- **Description**: {metadata.get('description', 'N/A')}

## Metadata Website

| Field | Value |
|----------|-------|
| Title | {metadata.get('title', 'N/A')} |
| Description | {metadata.get('description', 'N/A')} |
| Keywords | {metadata.get('keywords', 'N/A')} |
| Author | {metadata.get('author', 'N/A')} |
| Language | {metadata.get('lang', 'N/A')} |
| Charset | {metadata.get('charset', 'N/A')} |
| Canonical URL | {metadata.get('canonical_url', 'N/A')} |
| OG Title | {metadata.get('og_title', 'N/A')} |
| OG Description | {metadata.get('og_description', 'N/A')} |
| OG Image | {metadata.get('og_image', 'N/A')} |

## CSS Information

### Internal CSS
{len(css_data.get('internal_css', []))} internal CSS blocks ditemukan.

"""
        
        # Tambahkan internal CSS
        for i, css in enumerate(css_data.get('internal_css', []), 1):
            markdown += f"\n#### Internal CSS Block {i}\n```css\n{css}\n```\n"
        
        # Tambahkan external CSS
        markdown += f"\n### External CSS\n{len(css_data.get('external_css', []))} external CSS files ditemukan.\n"
        
        for i, css_file in enumerate(css_data.get('external_css', []), 1):
            markdown += f"\n#### External CSS {i}: {css_file['url']}\n```css\n{css_file['content'][:1000]}{'...' if len(css_file['content']) > 1000 else ''}\n```\n"
        
        # Tambahkan HTML content (dipotong jika terlalu panjang)
        html_preview = html_content[:2000] + '...' if len(html_content) > 2000 else html_content
        markdown += f"\n## HTML Content\n\n```html\n{html_preview}\n```\n"
        
        markdown += "\n---\n*Generated by Reescraping v1.0.0*"
        
        return markdown
    
    def scrape_website(self, url, output_dir="hasil"):
        """
        Method utama untuk scraping website lengkap
        
        Args:
            url (str): URL website yang akan di-scrape
            output_dir (str): Directory output
            
        Returns:
            dict: Hasil scraping atau None jika gagal
        """
        print(f"\n{Fore.CYAN}=== Memulai scraping website: {url} ==={Style.RESET_ALL}")
        
        # Ambil HTML content
        html_content, soup, status_code = self.get_html_content(url)
        if not html_content:
            print(f"{Fore.RED}❌ Gagal mengambil HTML content{Style.RESET_ALL}")
            return None
        
        print(f"{Fore.GREEN}✅ HTML berhasil diambil (Status: {status_code}){Style.RESET_ALL}")
        
        # Ekstrak CSS
        css_data = self.extract_css(soup, url)
        
        # Ekstrak metadata
        metadata = self.extract_metadata(soup)
        
        # Simpan ke file Markdown
        filepath = self.save_to_markdown(url, html_content, css_data, metadata, output_dir)
        
        if filepath:
            print(f"\n{Fore.GREEN}=== Scraping selesai! ==={Style.RESET_ALL}")
            print(f"{Fore.CYAN}📁 File disimpan di: {filepath}{Style.RESET_ALL}")
            
            return {
                'url': url,
                'filepath': filepath,
                'html_length': len(html_content),
                'css_count': len(css_data.get('internal_css', [])) + len(css_data.get('external_css', [])),
                'metadata': metadata
            }
        
        return None


class WebScrapingModule:
    """
    Module interface untuk Web Scraping yang terintegrasi dengan menu utama
    """
    
    def __init__(self):
        self.scraper = WebScraper()
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self):
        """Print header untuk web scraping module"""
        header = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    {Fore.YELLOW}WEB SCRAPING MODULE{Fore.CYAN}                     ║
║              {Fore.GREEN}Extract HTML, CSS & Metadata{Fore.CYAN}                ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(header)
        
    def get_urls_input(self):
        """Mendapatkan input URL dari user"""
        print(f"{Fore.WHITE}Masukkan URL yang ingin di-scrape:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Untuk single URL: https://example.com{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Untuk multiple URLs: https://site1.com https://site2.com{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Ketik 'back' untuk kembali ke menu utama{Style.RESET_ALL}\n")
        
        while True:
            user_input = input(f"{Fore.GREEN}URL(s): {Style.RESET_ALL}").strip()
            
            if user_input.lower() in ['back', 'kembali', 'b']:
                return None
            
            if not user_input:
                print(f"{Fore.RED}❌ Silakan masukkan URL yang valid.{Style.RESET_ALL}\n")
                continue
            
            # Validasi URL sederhana
            urls = user_input.split()
            valid_urls = []
            
            for url in urls:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                valid_urls.append(url)
            
            return valid_urls
    
    def run(self):
        """Menjalankan web scraping module"""
        self.clear_screen()
        self.print_header()
        
        urls = self.get_urls_input()
        if not urls:
            return
        
        print(f"\n{Fore.CYAN}🚀 Memulai scraping {len(urls)} website(s)...{Style.RESET_ALL}\n")
        
        results = []
        
        for i, url in enumerate(urls, 1):
            print(f"{Fore.MAGENTA}[{i}/{len(urls)}] Scraping: {url}{Style.RESET_ALL}")
            result = self.scraper.scrape_website(url)
            
            if result:
                results.append(result)
                print(f"{Fore.GREEN}✅ Berhasil - File: {result['filepath']}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   📄 Title: {result['metadata']['title'][:50]}{'...' if len(result['metadata']['title']) > 50 else ''}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   📊 HTML Length: {result['html_length']} characters{Style.RESET_ALL}")
                print(f"{Fore.CYAN}   🎨 CSS Count: {result['css_count']} files/blocks{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Gagal scraping {url}{Style.RESET_ALL}")
            
            # Delay antar scraping
            if i < len(urls):
                time.sleep(self.scraper.delay)
            print()
        
        # Summary
        print(f"{Fore.GREEN}🎉 Scraping selesai!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📊 Berhasil: {len(results)}/{len(urls)} website(s){Style.RESET_ALL}")
        
        if results:
            print(f"\n{Fore.YELLOW}📁 File hasil scraping tersimpan di folder 'hasil':{Style.RESET_ALL}")
            for result in results:
                print(f"{Fore.WHITE}   • {os.path.basename(result['filepath'])}{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Tekan Enter untuk kembali ke menu utama...{Style.RESET_ALL}")


if __name__ == "__main__":
    # Standalone mode untuk testing
    module = WebScrapingModule()
    module.run()