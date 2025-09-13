#!/usr/bin/env python3
"""
Reescraping - Tools untuk scraping website lengkap
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
            print(f"Mengambil HTML dari: {url}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse dengan BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return response.text, soup, response.status_code
            
        except requests.exceptions.RequestException as e:
            print(f"Error saat mengambil HTML: {e}")
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
            
            print(f"Ditemukan {len(css_data['internal_css'])} internal CSS dan {len(css_data['external_css'])} external CSS")
            
        except Exception as e:
            print(f"Error saat mengekstrak CSS: {e}")
        
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
            print(f"Gagal mengambil CSS dari {css_url}: {e}")
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
            
            print("Metadata berhasil diekstrak")
            
        except Exception as e:
            print(f"Error saat mengekstrak metadata: {e}")
        
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
            
            print(f"Hasil scraping disimpan ke: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error saat menyimpan file: {e}")
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
|-------|-------|
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
        
        markdown += "\n---\n*Generated by Reescraping*"
        
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
        print(f"\n=== Memulai scraping website: {url} ===")
        
        # Ambil HTML content
        html_content, soup, status_code = self.get_html_content(url)
        if not html_content:
            print("Gagal mengambil HTML content")
            return None
        
        print(f"HTML berhasil diambil (Status: {status_code})")
        
        # Ekstrak CSS
        css_data = self.extract_css(soup, url)
        
        # Ekstrak metadata
        metadata = self.extract_metadata(soup)
        
        # Simpan ke file Markdown
        filepath = self.save_to_markdown(url, html_content, css_data, metadata, output_dir)
        
        if filepath:
            print(f"\n=== Scraping selesai! ===")
            print(f"File disimpan di: {filepath}")
            
            return {
                'url': url,
                'filepath': filepath,
                'html_length': len(html_content),
                'css_count': len(css_data.get('internal_css', [])) + len(css_data.get('external_css', [])),
                'metadata': metadata
            }
        
        return None


if __name__ == "__main__":
    import sys
    
    scraper = WebScraper()
    
    # Cek apakah ada argument URL dari command line
    if len(sys.argv) > 1:
        # Gunakan URL dari argument
        urls = sys.argv[1:]
        print(f"Scraping {len(urls)} website(s)...\n")
        
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] Scraping: {url}")
            result = scraper.scrape_website(url)
            
            if result:
                print(f"✅ Berhasil - File: {result['filepath']}")
                print(f"   Title: {result['metadata']['title']}")
            else:
                print(f"❌ Gagal scraping {url}")
            
            # Delay antar scraping
            if i < len(urls):
                time.sleep(scraper.delay)
            print()
    else:
        # Mode interaktif - minta input dari user
        print("=== Reescraping ===")
        print("Masukkan URL yang ingin di-scrape (pisahkan dengan spasi untuk multiple URLs):")
        print("Contoh: https://example.com https://httpbin.org/html")
        print("Atau ketik 'quit' untuk keluar\n")
        
        while True:
            user_input = input("URL(s): ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Terima kasih! 👋")
                break
            
            if not user_input:
                print("Silakan masukkan URL yang valid.\n")
                continue
            
            # Split URLs jika ada multiple
            urls = user_input.split()
            
            print(f"\nScraping {len(urls)} website(s)...\n")
            
            for i, url in enumerate(urls, 1):
                print(f"[{i}/{len(urls)}] Scraping: {url}")
                result = scraper.scrape_website(url)
                
                if result:
                    print(f"✅ Berhasil - File: {result['filepath']}")
                    print(f"   Title: {result['metadata']['title']}")
                    print(f"   HTML Length: {result['html_length']} characters")
                    print(f"   CSS Count: {result['css_count']} files/blocks")
                else:
                    print(f"❌ Gagal scraping {url}")
                
                # Delay antar scraping
                if i < len(urls):
                    time.sleep(scraper.delay)
                print()
            
            print("Scraping selesai! Ingin scraping lagi?\n")