#!/usr/bin/env python3
"""
Web Cloner Module - Advanced Website Cloning Tool
Mengunduh semua assets (HTML, CSS, JS, images, fonts, videos) dengan deep crawling
Hasil disimpan dalam folder 'result' dengan struktur yang rapi

Author: Ramaerik97
Version: 2.0.0 - Enhanced with Deep Analysis & Powerful Features
"""

import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin, urlparse, unquote
import time
import mimetypes
from colorama import Fore, Style
from tqdm import tqdm
import hashlib
import json
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed


class WebCloner:
    """
    Enhanced WebCloner dengan fitur deep crawling dan analisa mendalam
    """
    
    def __init__(self, timeout=30, delay=0.3, max_retries=3, max_depth=2, max_pages=50, parallel_downloads=5):
        """
        Inisialisasi WebCloner dengan konfigurasi advanced
        
        Args:
            timeout (int): Timeout untuk request dalam detik
            delay (float): Delay antar request dalam detik
            max_retries (int): Maksimal retry untuk failed requests
            max_depth (int): Kedalaman maksimal untuk crawling (0 = hanya halaman utama)
            max_pages (int): Maksimal jumlah halaman yang di-crawl
            parallel_downloads (int): Jumlah download paralel
        """
        self.timeout = timeout
        self.delay = delay
        self.max_retries = max_retries
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.parallel_downloads = parallel_downloads
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Tracking sets
        self.downloaded_files = {}  # URL -> local_path mapping
        self.failed_downloads = []
        self.visited_urls = set()
        self.queued_urls = set()
        self.content_hashes = {}  # hash -> local_path (untuk deduplikasi)
        self.page_tree = {}  # Struktur tree untuk sitemap
        
        # Statistics
        self.stats = {
            'pages': 0,
            'css_files': 0,
            'js_files': 0,
            'images': 0,
            'fonts': 0,
            'videos': 0,
            'audios': 0,
            'other_assets': 0,
            'total_bytes': 0,
            'failed_downloads': 0
        }
        
    def reset_state(self):
        """Reset state untuk cloning baru"""
        self.downloaded_files = {}
        self.failed_downloads = []
        self.visited_urls = set()
        self.queued_urls = set()
        self.content_hashes = {}
        self.page_tree = {}
        self.stats = {
            'pages': 0,
            'css_files': 0,
            'js_files': 0,
            'images': 0,
            'fonts': 0,
            'videos': 0,
            'audios': 0,
            'other_assets': 0,
            'total_bytes': 0,
            'failed_downloads': 0
        }
    
    def sanitize_filename(self, filename):
        """
        Membersihkan nama file dari karakter yang tidak valid
        
        Args:
            filename (str): Nama file original
            
        Returns:
            str: Nama file yang aman
        """
        # Hapus karakter yang tidak aman untuk nama file
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.strip('. ')
        
        # Batasi panjang nama file
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
            
        return filename or 'unnamed_file'
    
    def get_content_hash(self, content):
        """
        Generate hash dari content untuk deduplikasi
        
        Args:
            content (bytes): Content file
            
        Returns:
            str: MD5 hash
        """
        return hashlib.md5(content).hexdigest()
    
    def get_file_extension(self, url, content_type=None):
        """
        Mendapatkan ekstensi file berdasarkan URL atau content type
        
        Args:
            url (str): URL file
            content_type (str): Content type dari response header
            
        Returns:
            str: Ekstensi file
        """
        # Coba dari URL terlebih dahulu
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)
        
        if '.' in os.path.basename(path):
            ext = os.path.splitext(path)[1]
            # Validasi ekstensi
            if len(ext) <= 10:  # Ekstensi yang wajar
                return ext
        
        # Coba dari content type
        if content_type:
            content_type_lower = content_type.lower().split(';')[0].strip()
            ext = mimetypes.guess_extension(content_type_lower)
            if ext:
                return ext
            
            # Manual mapping untuk tipe umum
            type_map = {
                'text/css': '.css',
                'text/javascript': '.js',
                'application/javascript': '.js',
                'application/x-javascript': '.js',
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/svg+xml': '.svg',
                'image/webp': '.webp',
                'image/x-icon': '.ico',
                'font/woff': '.woff',
                'font/woff2': '.woff2',
                'font/ttf': '.ttf',
                'font/otf': '.otf',
                'application/font-woff': '.woff',
                'application/font-woff2': '.woff2',
                'video/mp4': '.mp4',
                'video/webm': '.webm',
                'audio/mpeg': '.mp3',
                'audio/ogg': '.ogg'
            }
            
            return type_map.get(content_type_lower, '')
        
        return ''
    
    def is_same_domain(self, url, base_url):
        """
        Cek apakah URL masih dalam domain yang sama
        
        Args:
            url (str): URL yang akan dicek
            base_url (str): Base URL
            
        Returns:
            bool: True jika sama domain
        """
        parsed_url = urlparse(url)
        parsed_base = urlparse(base_url)
        return parsed_url.netloc == parsed_base.netloc
    
    def normalize_url(self, url):
        """
        Normalisasi URL untuk perbandingan
        
        Args:
            url (str): URL yang akan dinormalisasi
            
        Returns:
            str: URL yang dinormalisasi
        """
        parsed = urlparse(url)
        # Hapus fragment
        normalized = parsed._replace(fragment='').geturl()
        # Hapus trailing slash untuk perbandingan
        if normalized.endswith('/') and parsed.path != '/':
            normalized = normalized.rstrip('/')
        return normalized
    
    def download_file(self, url, local_path, file_type="asset"):
        """
        Mengunduh file dari URL ke path lokal dengan retry dan progress
        
        Args:
            url (str): URL file yang akan diunduh
            local_path (str): Path lokal untuk menyimpan file
            file_type (str): Tipe file untuk statistik
            
        Returns:
            tuple: (success: bool, content: bytes or None)
        """
        # Cek apakah sudah pernah diunduh
        if url in self.downloaded_files:
            return True, None
        
        filename = os.path.basename(local_path)
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    stream=True,
                    headers=self.session.headers
                )
                response.raise_for_status()
                
                # Buat direktori jika belum ada
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                collect_content = file_type in ('css', 'js')
                collected_chunks = [] if collect_content else None
                hasher = hashlib.md5()
                bytes_written = 0
                
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        f.write(chunk)
                        hasher.update(chunk)
                        bytes_written += len(chunk)
                        if collect_content:
                            collected_chunks.append(chunk)
                
                content_hash = hasher.hexdigest()
                if content_hash in self.content_hashes:
                    existing_path = self.content_hashes[content_hash]
                    if os.path.exists(local_path) and existing_path != local_path:
                        try:
                            os.remove(local_path)
                        except OSError:
                            pass
                    self.downloaded_files[url] = existing_path
                    time.sleep(self.delay)
                    if collect_content:
                        return True, b''.join(collected_chunks or [])
                    return True, None
                
                # Update tracking
                self.downloaded_files[url] = local_path
                self.content_hashes[content_hash] = local_path
                self.stats['total_bytes'] += bytes_written
                
                if file_type == 'css':
                    self.stats['css_files'] += 1
                elif file_type == 'js':
                    self.stats['js_files'] += 1
                elif file_type == 'image':
                    self.stats['images'] += 1
                elif file_type == 'font':
                    self.stats['fonts'] += 1
                elif file_type == 'video':
                    self.stats['videos'] += 1
                elif file_type == 'audio':
                    self.stats['audios'] += 1
                else:
                    self.stats['other_assets'] += 1
                
                time.sleep(self.delay)
                if collect_content:
                    return True, b''.join(collected_chunks or [])
                return True, None
                
            except Exception as e:
                if os.path.exists(local_path):
                    try:
                        os.remove(local_path)
                    except OSError:
                        pass
                if attempt == self.max_retries - 1:
                    self.failed_downloads.append({'url': url, 'error': str(e), 'type': file_type})
                    self.stats['failed_downloads'] += 1
                    return False, None
                # Exponential backoff
                wait_time = (2 ** attempt) * 0.5
                time.sleep(wait_time)
        
        return False, None
    
    def extract_assets_from_html(self, soup, base_url):
        """
        Mengekstrak semua asset URLs dari HTML dengan deteksi advanced
        
        Args:
            soup: BeautifulSoup object
            base_url (str): Base URL website
            
        Returns:
            dict: Dictionary berisi berbagai jenis assets
        """
        assets = {
            'css': set(),
            'js': set(),
            'images': set(),
            'fonts': set(),
            'videos': set(),
            'audios': set(),
            'links': set(),  # Internal links untuk crawling
            'other': set()
        }
        
        # CSS files (link dan style)
        for link in soup.find_all('link', rel=lambda x: x and 'stylesheet' in str(x).lower()):
            href = link.get('href')
            if href and not href.startswith('data:'):
                full_url = urljoin(base_url, href)
                assets['css'].add(full_url)
        
        # Inline styles dengan import
        for style in soup.find_all('style'):
            if style.string:
                imports = re.findall(r'@import\s+["\']([^"\']+)["\']', style.string)
                for imp in imports:
                    full_url = urljoin(base_url, imp)
                    assets['css'].add(full_url)
        
        # JavaScript files
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src and not src.startswith('data:'):
                full_url = urljoin(base_url, src)
                assets['js'].add(full_url)
        
        # Images dengan srcset support
        for img in soup.find_all('img'):
            # src attribute
            src = img.get('src')
            if src and not src.startswith('data:'):
                full_url = urljoin(base_url, src)
                assets['images'].add(full_url)
            
            # srcset attribute (responsive images)
            srcset = img.get('srcset')
            if srcset:
                srcset_urls = re.findall(r'(\S+\.(?:jpg|jpeg|png|gif|webp|svg))\s*(?:\d+[wx])?', srcset, re.IGNORECASE)
                for srcset_url in srcset_urls:
                    full_url = urljoin(base_url, srcset_url)
                    assets['images'].add(full_url)
            
            # data-src (lazy loading)
            data_src = img.get('data-src') or img.get('data-lazy-src')
            if data_src and not data_src.startswith('data:'):
                full_url = urljoin(base_url, data_src)
                assets['images'].add(full_url)
        
        # Picture element
        for picture in soup.find_all('picture'):
            for source in picture.find_all('source'):
                srcset = source.get('srcset')
                if srcset:
                    srcset_urls = re.findall(r'(\S+\.(?:jpg|jpeg|png|gif|webp))\s*(?:\d+[wx])?', srcset, re.IGNORECASE)
                    for srcset_url in srcset_urls:
                        full_url = urljoin(base_url, srcset_url)
                        assets['images'].add(full_url)
        
        # Background images dari inline styles
        for element in soup.find_all(style=True):
            style = element.get('style', '')
            bg_matches = re.findall(r'background(?:-image)?:\s*url\(["\']?([^"\')]+)["\']?\)', style)
            for match in bg_matches:
                if not match.startswith('data:'):
                    full_url = urljoin(base_url, match)
                    assets['images'].add(full_url)
        
        # Videos
        for video in soup.find_all('video'):
            src = video.get('src')
            if src and not src.startswith('data:'):
                full_url = urljoin(base_url, src)
                assets['videos'].add(full_url)
            
            poster = video.get('poster')
            if poster and not poster.startswith('data:'):
                full_url = urljoin(base_url, poster)
                assets['images'].add(full_url)
            
            for source in video.find_all('source'):
                src = source.get('src')
                if src and not src.startswith('data:'):
                    full_url = urljoin(base_url, src)
                    assets['videos'].add(full_url)
        
        # Audio
        for audio in soup.find_all('audio'):
            src = audio.get('src')
            if src and not src.startswith('data:'):
                full_url = urljoin(base_url, src)
                assets['audios'].add(full_url)
            
            for source in audio.find_all('source'):
                src = source.get('src')
                if src and not src.startswith('data:'):
                    full_url = urljoin(base_url, src)
                    assets['audios'].add(full_url)
        
        # Favicon dan icons
        for link in soup.find_all('link', rel=lambda x: x and ('icon' in str(x).lower() or 'apple-touch-icon' in str(x).lower())):
            href = link.get('href')
            if href and not href.startswith('data:'):
                full_url = urljoin(base_url, href)
                assets['images'].add(full_url)
        
        # Internal links untuk crawling
        parsed_base = urlparse(base_url)
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:')):
                full_url = urljoin(base_url, href)
                # Hanya link internal
                if self.is_same_domain(full_url, base_url):
                    normalized = self.normalize_url(full_url)
                    assets['links'].add(normalized)
        
        return assets
    
    def extract_css_assets(self, css_content, base_url):
        """
        Mengekstrak asset URLs dari CSS content (fonts, images, imports)
        
        Args:
            css_content (str): Content CSS
            base_url (str): Base URL untuk resolve relative URLs
            
        Returns:
            dict: Dictionary dengan keys 'images', 'fonts', 'imports'
        """
        assets = {
            'images': set(),
            'fonts': set(),
            'imports': set()
        }
        
        # Find all url() references in CSS
        url_pattern = r'url\(["\']?([^"\')]+)["\']?\)'
        matches = re.findall(url_pattern, css_content)
        
        for match in matches:
            if match.startswith('data:'):
                continue
            
            full_url = urljoin(base_url, match) if not match.startswith(('http://', 'https://')) else match
            
            # Klasifikasi berdasarkan ekstensi
            ext = os.path.splitext(urlparse(full_url).path)[1].lower()
            if ext in ['.woff', '.woff2', '.ttf', '.otf', '.eot']:
                assets['fonts'].add(full_url)
            elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp']:
                assets['images'].add(full_url)
            else:
                # Deteksi dari context (font-face vs background)
                # Cari context sekitar match
                idx = css_content.find(match)
                if idx > 0:
                    context = css_content[max(0, idx-200):idx]
                    if '@font-face' in context or 'font-family' in context:
                        assets['fonts'].add(full_url)
                    else:
                        assets['images'].add(full_url)
                else:
                    assets['images'].add(full_url)
        
        # Find @import statements
        import_pattern = r'@import\s+(?:url\()?["\']?([^"\')]+)["\']?\)?'
        imports = re.findall(import_pattern, css_content)
        for imp in imports:
            if not imp.startswith('data:'):
                full_url = urljoin(base_url, imp) if not imp.startswith(('http://', 'https://')) else imp
                assets['imports'].add(full_url)
        
        return assets
    
    def extract_js_assets(self, js_content, base_url):
        """
        Mengekstrak asset URLs dari JavaScript content (heuristic)
        
        Args:
            js_content (str): Content JavaScript
            base_url (str): Base URL untuk resolve relative URLs
            
        Returns:
            set: Set of asset URLs
        """
        assets = set()
        
        # Pattern untuk URL dalam string (heuristic, bisa false positive)
        # Cari string yang seperti path image/asset
        patterns = [
            r'["\']([^"\']+\.(?:jpg|jpeg|png|gif|svg|webp|ico))["\']',
            r'["\']([^"\']+\.(?:woff|woff2|ttf|otf|eot))["\']',
            r'["\']([^"\']+\.(?:mp4|webm|ogg|mp3))["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            for match in matches:
                # Filter false positives (terlalu pendek, atau berisi karakter aneh)
                if len(match) > 3 and not any(c in match for c in ['<', '>', '{', '}', '|', '^']):
                    try:
                        full_url = urljoin(base_url, match)
                        # Validasi bahwa ini URL yang valid
                        parsed = urlparse(full_url)
                        if parsed.scheme in ['http', 'https']:
                            assets.add(full_url)
                    except:
                        pass
        
        return assets
    
    def ensure_html_structure(self, soup):
        """
        Memastikan HTML memiliki struktur yang benar dengan DOCTYPE, html, head, dan body
        Serta menambahkan meta charset jika belum ada
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            BeautifulSoup: Updated soup object dengan struktur yang benar
        """
        # Pastikan ada tag html
        if not soup.html:
            html_tag = soup.new_tag('html')
            for child in list(soup.children):
                if child.name not in ['html', '[document]']:
                    html_tag.append(child.extract())
            soup.append(html_tag)
        
        # Pastikan ada tag head
        if not soup.head:
            head_tag = soup.new_tag('head')
            soup.html.insert(0, head_tag)
        
        # Pastikan ada meta charset di head
        charset_meta = soup.head.find('meta', attrs={'charset': True})
        if not charset_meta:
            # Cek meta dengan http-equiv="Content-Type"
            content_type_meta = soup.head.find('meta', attrs={'http-equiv': lambda x: x and x.lower() == 'content-type'})
            if not content_type_meta:
                # Tambahkan meta charset di awal head
                charset_meta = soup.new_tag('meta', charset='UTF-8')
                if soup.head.contents:
                    soup.head.insert(0, charset_meta)
                else:
                    soup.head.append(charset_meta)
        
        # Pastikan ada tag body
        if not soup.body:
            body_tag = soup.new_tag('body')
            # Pindahkan semua konten yang bukan di head ke body
            for child in list(soup.html.children):
                if child.name not in ['head', 'body', None] and child != soup.head:
                    body_tag.append(child.extract())
            soup.html.append(body_tag)
        
        return soup
    
    def update_html_paths(self, soup, base_url, output_dir, page_path):
        """
        Update semua paths di HTML untuk mengarah ke file lokal (relative paths)
        
        Args:
            soup: BeautifulSoup object
            base_url (str): Base URL website
            output_dir (str): Directory output
            page_path (str): Path file HTML ini
            
        Returns:
            BeautifulSoup: Updated soup object
        """
        page_dir = os.path.dirname(page_path)
        
        def get_relative_path(target_url):
            """Get relative path from page to target asset"""
            if target_url in self.downloaded_files:
                target_path = self.downloaded_files[target_url]
                rel_path = os.path.relpath(target_path, page_dir)
                return rel_path.replace('\\', '/')
            return None
        
        # Update CSS links
        for link in soup.find_all('link', rel=lambda x: x and 'stylesheet' in str(x).lower()):
            href = link.get('href')
            if href and not href.startswith('data:'):
                full_url = urljoin(base_url, href)
                rel_path = get_relative_path(full_url)
                if rel_path:
                    link['href'] = rel_path
        
        # Update JavaScript sources
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src and not src.startswith('data:'):
                full_url = urljoin(base_url, src)
                rel_path = get_relative_path(full_url)
                if rel_path:
                    script['src'] = rel_path
        
        # Update image sources
        for img in soup.find_all('img'):
            src = img.get('src')
            if src and not src.startswith('data:'):
                full_url = urljoin(base_url, src)
                rel_path = get_relative_path(full_url)
                if rel_path:
                    img['src'] = rel_path
            
            # Update srcset
            srcset = img.get('srcset')
            if srcset:
                new_srcset = []
                parts = srcset.split(',')
                for part in parts:
                    part = part.strip()
                    match = re.match(r'(\S+)\s*(.*)', part)
                    if match:
                        url, descriptor = match.groups()
                        full_url = urljoin(base_url, url)
                        rel_path = get_relative_path(full_url)
                        if rel_path:
                            new_srcset.append(f"{rel_path} {descriptor}".strip())
                        else:
                            new_srcset.append(part)
                if new_srcset:
                    img['srcset'] = ', '.join(new_srcset)
            
            # Update data-src
            data_src = img.get('data-src') or img.get('data-lazy-src')
            if data_src and not data_src.startswith('data:'):
                full_url = urljoin(base_url, data_src)
                rel_path = get_relative_path(full_url)
                if rel_path:
                    if img.get('data-src'):
                        img['data-src'] = rel_path
                    if img.get('data-lazy-src'):
                        img['data-lazy-src'] = rel_path
        
        # Update picture sources
        for picture in soup.find_all('picture'):
            for source in picture.find_all('source'):
                srcset = source.get('srcset')
                if srcset:
                    new_srcset = []
                    parts = srcset.split(',')
                    for part in parts:
                        part = part.strip()
                        match = re.match(r'(\S+)\s*(.*)', part)
                        if match:
                            url, descriptor = match.groups()
                            full_url = urljoin(base_url, url)
                            rel_path = get_relative_path(full_url)
                            if rel_path:
                                new_srcset.append(f"{rel_path} {descriptor}".strip())
                            else:
                                new_srcset.append(part)
                    if new_srcset:
                        source['srcset'] = ', '.join(new_srcset)
        
        # Update video sources
        for video in soup.find_all('video'):
            src = video.get('src')
            if src and not src.startswith('data:'):
                full_url = urljoin(base_url, src)
                rel_path = get_relative_path(full_url)
                if rel_path:
                    video['src'] = rel_path
            
            poster = video.get('poster')
            if poster and not poster.startswith('data:'):
                full_url = urljoin(base_url, poster)
                rel_path = get_relative_path(full_url)
                if rel_path:
                    video['poster'] = rel_path
            
            for source in video.find_all('source'):
                src = source.get('src')
                if src and not src.startswith('data:'):
                    full_url = urljoin(base_url, src)
                    rel_path = get_relative_path(full_url)
                    if rel_path:
                        source['src'] = rel_path
        
        # Update audio sources
        for audio in soup.find_all('audio'):
            src = audio.get('src')
            if src and not src.startswith('data:'):
                full_url = urljoin(base_url, src)
                rel_path = get_relative_path(full_url)
                if rel_path:
                    audio['src'] = rel_path
            
            for source in audio.find_all('source'):
                src = source.get('src')
                if src and not src.startswith('data:'):
                    full_url = urljoin(base_url, src)
                    rel_path = get_relative_path(full_url)
                    if rel_path:
                        source['src'] = rel_path
        
        # Update favicon and icons
        for link in soup.find_all('link', rel=lambda x: x and ('icon' in str(x).lower() or 'apple-touch-icon' in str(x).lower())):
            href = link.get('href')
            if href and not href.startswith('data:'):
                full_url = urljoin(base_url, href)
                rel_path = get_relative_path(full_url)
                if rel_path:
                    link['href'] = rel_path
        
        # Update internal links (a href)
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and not href.startswith(('#', 'javascript:', 'mailto:', 'tel:', 'data:')):
                full_url = urljoin(base_url, href)
                if self.is_same_domain(full_url, base_url):
                    normalized = self.normalize_url(full_url)
                    if normalized in self.downloaded_files:
                        target_path = self.downloaded_files[normalized]
                        rel_path = os.path.relpath(target_path, page_dir)
                        link['href'] = rel_path.replace('\\', '/')
        
        # Update inline styles dengan background images
        for element in soup.find_all(style=True):
            style_content = element.get('style', '')
            
            def replace_inline_url(match):
                url = match.group(1)
                if url.startswith('data:'):
                    return match.group(0)
                
                full_url = urljoin(base_url, url)
                rel_path = get_relative_path(full_url)
                
                if rel_path:
                    return f'url("{rel_path}")'
                return match.group(0)
            
            # Replace url() dalam inline style
            updated_style = re.sub(r'url\(["\']?([^"\')]+)["\']?\)', replace_inline_url, style_content)
            element['style'] = updated_style
        
        # Update inline style tags
        for style_tag in soup.find_all('style'):
            if style_tag.string:
                style_content = style_tag.string
                
                def replace_style_url(match):
                    url = match.group(1)
                    if url.startswith('data:'):
                        return match.group(0)
                    
                    full_url = urljoin(base_url, url)
                    rel_path = get_relative_path(full_url)
                    
                    if rel_path:
                        return f'url("{rel_path}")'
                    return match.group(0)
                
                # Replace url() dalam style tag
                updated_style = re.sub(r'url\(["\']?([^"\')]+)["\']?\)', replace_style_url, style_content)
                style_tag.string = updated_style
        
        return soup
    
    def update_css_paths(self, css_content, css_url, output_dir, css_path):
        """
        Update semua paths di CSS untuk mengarah ke file lokal (relative paths)
        
        Args:
            css_content (str): Content CSS
            css_url (str): URL asli CSS file
            output_dir (str): Directory output
            css_path (str): Path file CSS ini
            
        Returns:
            str: Updated CSS content
        """
        css_dir = os.path.dirname(css_path)
        
        def replace_url(match):
            url = match.group(1)
            if url.startswith('data:'):
                return match.group(0)
            
            full_url = urljoin(css_url, url) if not url.startswith(('http://', 'https://')) else url
            
            if full_url in self.downloaded_files:
                target_path = self.downloaded_files[full_url]
                rel_path = os.path.relpath(target_path, css_dir)
                return f'url("{rel_path.replace(chr(92), "/")}")'
            
            return match.group(0)
        
        url_pattern = r'url\(["\']?([^"\')]+)["\']?\)'
        updated_css = re.sub(url_pattern, replace_url, css_content)
        
        # Update @import
        def replace_import(match):
            url = match.group(1)
            if url.startswith('data:'):
                return match.group(0)
            
            full_url = urljoin(css_url, url) if not url.startswith(('http://', 'https://')) else url
            
            if full_url in self.downloaded_files:
                target_path = self.downloaded_files[full_url]
                rel_path = os.path.relpath(target_path, css_dir)
                return f'@import "{rel_path.replace(chr(92), "/")}"'
            
            return match.group(0)
        
        import_pattern = r'@import\s+["\']([^"\']+)["\']'
        updated_css = re.sub(import_pattern, replace_import, updated_css)
        
        return updated_css
    
    def url_to_local_path(self, url, output_dir):
        """
        Konversi URL ke path lokal dengan handling query parameters
        
        Args:
            url (str): URL file
            output_dir (str): Directory output
            
        Returns:
            str: Path lokal
        """
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)
        
        # Handle query parameters dengan hashing
        query_hash = ''
        if parsed_url.query:
            query_hash = '_' + hashlib.md5(parsed_url.query.encode()).hexdigest()[:8]
        
        # Tentukan subdirectory berdasarkan jenis file
        ext = os.path.splitext(path)[1].lower()
        
        if ext == '.css':
            subdir = 'css'
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            subdir = 'js'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico', '.bmp']:
            subdir = 'images'
        elif ext in ['.woff', '.woff2', '.ttf', '.eot', '.otf']:
            subdir = 'fonts'
        elif ext in ['.mp4', '.webm', '.ogg', '.avi']:
            subdir = 'videos'
        elif ext in ['.mp3', '.wav', '.m4a']:
            subdir = 'audios'
        elif ext in ['.html', '.htm']:
            subdir = 'pages'
        else:
            subdir = 'assets'
        
        # Buat nama file yang aman
        filename = os.path.basename(path) or 'index.html'
        filename = self.sanitize_filename(filename)
        
        # Jika tidak ada ekstensi, coba deteksi dari URL atau assign default
        if '.' not in filename or filename.startswith('.'):
            if subdir == 'pages':
                filename = filename + '.html' if filename else 'page.html'
            else:
                filename = filename + '.bin' if filename else 'asset.bin'
        
        # Tambahkan query hash jika ada
        if query_hash:
            name, ext = os.path.splitext(filename)
            filename = f"{name}{query_hash}{ext}"
        
        return os.path.join(output_dir, subdir, filename)
    
    def crawl_pages(self, start_url, output_dir):
        """
        Crawl pages dengan BFS hingga max_depth dan max_pages
        
        Args:
            start_url (str): URL halaman awal
            output_dir (str): Directory output
            
        Returns:
            list: List of (url, depth, parent_url) tuples untuk pages yang di-crawl
        """
        queue = deque([(start_url, 0, None)])  # (url, depth, parent)
        self.queued_urls.add(self.normalize_url(start_url))
        crawled_pages = []
        
        print(f"\n{Fore.CYAN}🔍 Memulai crawling website (max depth: {self.max_depth}, max pages: {self.max_pages})...{Style.RESET_ALL}")
        
        while queue and len(crawled_pages) < self.max_pages:
            url, depth, parent = queue.popleft()
            normalized_url = self.normalize_url(url)
            
            # Skip jika sudah diproses atau depth melebihi batas
            if normalized_url in self.visited_urls or depth > self.max_depth:
                continue
            
            self.visited_urls.add(normalized_url)
            
            try:
                print(f"{Fore.YELLOW}📄 Crawling [{depth}/{self.max_depth}]: {url}{Style.RESET_ALL}")
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                # Hanya proses HTML
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                crawled_pages.append((url, depth, parent, soup))
                self.stats['pages'] += 1
                
                # Extract links untuk crawling lebih lanjut (jika belum max depth)
                if depth < self.max_depth:
                    assets = self.extract_assets_from_html(soup, url)
                    for link in assets['links']:
                        normalized_link = self.normalize_url(link)
                        if normalized_link not in self.visited_urls and normalized_link not in self.queued_urls:
                            if len(self.queued_urls) + len(self.visited_urls) < self.max_pages:
                                queue.append((link, depth + 1, url))
                                self.queued_urls.add(normalized_link)
                
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"{Fore.RED}❌ Error crawling {url}: {e}{Style.RESET_ALL}")
                self.failed_downloads.append({'url': url, 'error': str(e), 'type': 'page'})
        
        print(f"{Fore.GREEN}✅ Crawling selesai: {len(crawled_pages)} halaman ditemukan{Style.RESET_ALL}\n")
        return crawled_pages
    
    def download_assets_parallel(self, assets_list, output_dir, asset_type="asset"):
        """
        Download multiple assets secara paralel
        
        Args:
            assets_list (list): List of asset URLs
            output_dir (str): Directory output
            asset_type (str): Type of assets
            
        Returns:
            list: List of (url, local_path, content) tuples yang berhasil didownload
        """
        if not assets_list:
            return []
        
        downloaded = []
        
        with ThreadPoolExecutor(max_workers=self.parallel_downloads) as executor:
            # Submit download tasks
            future_to_url = {}
            for asset_url in assets_list:
                if asset_url not in self.downloaded_files:
                    local_path = self.url_to_local_path(asset_url, output_dir)
                    future = executor.submit(self.download_file, asset_url, local_path, asset_type)
                    future_to_url[future] = (asset_url, local_path)
            
            if not future_to_url:
                return downloaded
            
            # Collect results dengan progress bar
            with tqdm(total=len(future_to_url), desc=f"Downloading {asset_type}", unit="file", 
                     bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
                for future in as_completed(future_to_url):
                    asset_url, local_path = future_to_url[future]
                    try:
                        success, content = future.result()
                        if success:
                            downloaded.append((asset_url, local_path, content))
                    except Exception as e:
                        print(f"{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")
                    pbar.update(1)
        
        return downloaded
    
    def clone_website(self, url, output_dir="result"):
        """
        Method utama untuk cloning website lengkap dengan deep crawling
        
        Args:
            url (str): URL website yang akan di-clone
            output_dir (str): Directory output utama
            
        Returns:
            dict: Hasil cloning atau None jika gagal
        """
        start_time = time.time()
        self.reset_state()  # Reset state untuk cloning baru
        
        print(f"\n{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🚀 MEMULAI DEEP WEB CLONING{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Target URL: {url}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Max Depth: {self.max_depth} | Max Pages: {self.max_pages}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}\n")
        
        try:
            # Buat nama folder berdasarkan domain
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            safe_domain = self.sanitize_filename(domain)
            
            site_output_dir = os.path.join(output_dir, safe_domain)
            
            # Buat direktori output
            print(f"{Fore.CYAN}📁 Membuat struktur direktori...{Style.RESET_ALL}")
            os.makedirs(site_output_dir, exist_ok=True)
            for subdir in ['pages', 'css', 'js', 'images', 'fonts', 'videos', 'audios', 'assets']:
                os.makedirs(os.path.join(site_output_dir, subdir), exist_ok=True)
            
            # STEP 1: Crawl semua pages
            print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}STEP 1: CRAWLING PAGES{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            
            crawled_pages = self.crawl_pages(url, site_output_dir)
            
            if not crawled_pages:
                print(f"{Fore.RED}❌ Tidak ada halaman yang berhasil di-crawl{Style.RESET_ALL}")
                return None
            
            # STEP 2: Extract all assets dari semua pages
            print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}STEP 2: EXTRACTING ASSETS{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            
            all_css = set()
            all_js = set()
            all_images = set()
            all_fonts = set()
            all_videos = set()
            all_audios = set()
            
            print(f"{Fore.CYAN}🔍 Menganalisa assets dari {len(crawled_pages)} halaman...{Style.RESET_ALL}")
            
            for page_url, depth, parent, soup in crawled_pages:
                assets = self.extract_assets_from_html(soup, page_url)
                all_css.update(assets['css'])
                all_js.update(assets['js'])
                all_images.update(assets['images'])
                all_fonts.update(assets['fonts'])
                all_videos.update(assets['videos'])
                all_audios.update(assets['audios'])
            
            print(f"{Fore.GREEN}✅ Asset extraction selesai:{Style.RESET_ALL}")
            print(f"   • CSS: {len(all_css)}")
            print(f"   • JavaScript: {len(all_js)}")
            print(f"   • Images: {len(all_images)}")
            print(f"   • Fonts: {len(all_fonts)}")
            print(f"   • Videos: {len(all_videos)}")
            print(f"   • Audios: {len(all_audios)}")
            
            # STEP 3: Download CSS dan extract assets dari CSS
            print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}STEP 3: DOWNLOADING CSS FILES{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            
            downloaded_css = self.download_assets_parallel(list(all_css), site_output_dir, 'css')
            
            # Extract assets dari CSS files
            print(f"\n{Fore.CYAN}🔍 Extracting assets dari CSS files...{Style.RESET_ALL}")
            css_images = set()
            css_fonts = set()
            css_imports = set()
            
            for css_url, css_path, content in downloaded_css:
                if content:
                    try:
                        css_content = content.decode('utf-8', errors='ignore')
                        css_assets = self.extract_css_assets(css_content, css_url)
                        css_images.update(css_assets['images'])
                        css_fonts.update(css_assets['fonts'])
                        css_imports.update(css_assets['imports'])
                    except Exception as e:
                        print(f"{Fore.YELLOW}⚠️  Error processing CSS {css_url}: {e}{Style.RESET_ALL}")
            
            # Download imported CSS
            if css_imports:
                print(f"\n{Fore.CYAN}📥 Downloading imported CSS files ({len(css_imports)})...{Style.RESET_ALL}")
                imported_css = self.download_assets_parallel(list(css_imports), site_output_dir, 'css')
            
            all_images.update(css_images)
            all_fonts.update(css_fonts)
            
            # STEP 4: Download JavaScript dan extract assets
            print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}STEP 4: DOWNLOADING JAVASCRIPT FILES{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            
            downloaded_js = self.download_assets_parallel(list(all_js), site_output_dir, 'js')
            
            # Extract assets dari JS files (heuristic)
            print(f"\n{Fore.CYAN}🔍 Extracting assets dari JS files (heuristic)...{Style.RESET_ALL}")
            js_assets = set()
            
            for js_url, js_path, content in downloaded_js:
                if content:
                    try:
                        js_content = content.decode('utf-8', errors='ignore')
                        js_found = self.extract_js_assets(js_content, js_url)
                        js_assets.update(js_found)
                    except Exception as e:
                        pass  # Silent fail untuk JS parsing
            
            if js_assets:
                print(f"{Fore.GREEN}✅ Found {len(js_assets)} potential assets dari JS{Style.RESET_ALL}")
                all_images.update(js_assets)
            
            # STEP 5: Download Images
            print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}STEP 5: DOWNLOADING IMAGES ({len(all_images)}){Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            
            self.download_assets_parallel(list(all_images), site_output_dir, 'image')
            
            # STEP 6: Download Fonts
            if all_fonts:
                print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}STEP 6: DOWNLOADING FONTS ({len(all_fonts)}){Style.RESET_ALL}")
                print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
                
                self.download_assets_parallel(list(all_fonts), site_output_dir, 'font')
            
            # STEP 7: Download Videos
            if all_videos:
                print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}STEP 7: DOWNLOADING VIDEOS ({len(all_videos)}){Style.RESET_ALL}")
                print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
                
                self.download_assets_parallel(list(all_videos), site_output_dir, 'video')
            
            # STEP 8: Download Audios
            if all_audios:
                print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}STEP 8: DOWNLOADING AUDIOS ({len(all_audios)}){Style.RESET_ALL}")
                print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
                
                self.download_assets_parallel(list(all_audios), site_output_dir, 'audio')
            
            # STEP 9: Update paths di CSS files
            print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}STEP 9: UPDATING PATHS IN CSS FILES{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            
            for css_url in all_css.union(css_imports):
                if css_url in self.downloaded_files:
                    css_path = self.downloaded_files[css_url]
                    try:
                        with open(css_path, 'r', encoding='utf-8', errors='ignore') as f:
                            css_content = f.read()
                        
                        updated_css = self.update_css_paths(css_content, css_url, site_output_dir, css_path)
                        
                        with open(css_path, 'w', encoding='utf-8') as f:
                            f.write(updated_css)
                    except Exception as e:
                        print(f"{Fore.YELLOW}⚠️  Error updating CSS {css_url}: {e}{Style.RESET_ALL}")
            
            # STEP 10: Save HTML pages dengan updated paths
            print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}STEP 10: SAVING HTML PAGES{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            
            normalized_start_url = self.normalize_url(url)
            main_html_path = os.path.join(site_output_dir, 'index.html')
            page_paths = {}
            
            # Precompute local paths for each page and register mapping
            for page_url, _, _, _ in crawled_pages:
                normalized_page_url = self.normalize_url(page_url)
                if normalized_page_url == normalized_start_url:
                    page_path = main_html_path
                else:
                    parsed = urlparse(page_url)
                    page_filename = os.path.basename(parsed.path) or 'index'
                    if not page_filename.endswith(('.html', '.htm')):
                        page_filename = f"{page_filename}.html"
                    page_filename = self.sanitize_filename(page_filename)
                    
                    if parsed.query:
                        query_hash = hashlib.md5(parsed.query.encode()).hexdigest()[:8]
                        name, ext = os.path.splitext(page_filename)
                        page_filename = f"{name}_{query_hash}{ext}"
                    
                    page_path = os.path.join(site_output_dir, 'pages', page_filename)
                
                page_paths[normalized_page_url] = page_path
                self.downloaded_files[normalized_page_url] = page_path
            
            # Save HTML pages with updated paths
            for page_url, depth, parent, soup in tqdm(crawled_pages, desc="Saving pages", unit="page"):
                normalized_url = self.normalize_url(page_url)
                page_path = page_paths[normalized_url]
                
                # Pastikan struktur HTML yang benar
                soup = self.ensure_html_structure(soup)
                
                # Update paths ke file lokal
                updated_soup = self.update_html_paths(soup, page_url, site_output_dir, page_path)
                
                # Simpan HTML dengan DOCTYPE yang benar
                os.makedirs(os.path.dirname(page_path), exist_ok=True)
                with open(page_path, 'w', encoding='utf-8') as f:
                    # Tambahkan DOCTYPE jika belum ada
                    html_content = str(updated_soup)
                    if not html_content.strip().startswith('<!DOCTYPE'):
                        f.write('<!DOCTYPE html>\n')
                    f.write(html_content)
            
            # STEP 11: Generate info & manifest
            print(f"\n{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}STEP 11: GENERATING REPORTS{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{'='*70}{Style.RESET_ALL}")
            
            elapsed_time = time.time() - start_time
            self.create_info_file(url, site_output_dir, elapsed_time, crawled_pages)
            self.create_manifest(site_output_dir, crawled_pages)
            
            # Success!
            print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}🎉 CLONING SELESAI!{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 Statistik Lengkap:{Style.RESET_ALL}")
            print(f"   • Halaman: {self.stats['pages']}")
            print(f"   • CSS: {self.stats['css_files']}")
            print(f"   • JavaScript: {self.stats['js_files']}")
            print(f"   • Images: {self.stats['images']}")
            print(f"   • Fonts: {self.stats['fonts']}")
            print(f"   • Videos: {self.stats['videos']}")
            print(f"   • Audios: {self.stats['audios']}")
            print(f"   • Other Assets: {self.stats['other_assets']}")
            print(f"   • Total Size: {self.stats['total_bytes'] / (1024*1024):.2f} MB")
            print(f"   • Failed: {self.stats['failed_downloads']}")
            print(f"   • Time: {elapsed_time:.2f}s")
            print(f"\n{Fore.CYAN}📁 Lokasi:{Style.RESET_ALL}")
            print(f"   • Folder: {site_output_dir}")
            print(f"   • Main HTML: {main_html_path}")
            print(f"\n{Fore.GREEN}💡 Cara membuka:{Style.RESET_ALL}")
            print(f"   1. Double-click: {main_html_path}")
            print(f"   2. Local server: cd {site_output_dir} && python -m http.server 8000")
            print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}\n")
            
            return {
                'url': url,
                'output_dir': site_output_dir,
                'html_path': main_html_path,
                'stats': self.stats,
                'elapsed_time': elapsed_time
            }
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error saat cloning website: {e}{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_info_file(self, url, output_dir, elapsed_time, crawled_pages):
        """
        Membuat file info lengkap tentang hasil cloning
        
        Args:
            url (str): URL website
            output_dir (str): Directory output
            elapsed_time (float): Waktu yang dibutuhkan
            crawled_pages (list): List of crawled pages
        """
        info_content = f"""# Website Clone Report

## 🌐 Website Information
**Original URL:** {url}  
**Clone Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}  
**Clone Duration:** {elapsed_time:.2f} seconds  

## 📊 Cloning Statistics
| Category | Count |
|----------|-------|
| Pages | {self.stats['pages']} |
| CSS Files | {self.stats['css_files']} |
| JavaScript Files | {self.stats['js_files']} |
| Images | {self.stats['images']} |
| Fonts | {self.stats['fonts']} |
| Videos | {self.stats['videos']} |
| Audios | {self.stats['audios']} |
| Other Assets | {self.stats['other_assets']} |
| **Total Assets** | **{sum([self.stats[k] for k in ['pages', 'css_files', 'js_files', 'images', 'fonts', 'videos', 'audios', 'other_assets']])}** |
| Failed Downloads | {self.stats['failed_downloads']} |

**Total Downloaded Size:** {self.stats['total_bytes'] / (1024*1024):.2f} MB

## 🔗 Crawled Pages
"""
        
        # List semua pages yang di-crawl
        for i, (page_url, depth, parent, _) in enumerate(crawled_pages, 1):
            info_content += f"{i}. [{depth}] {page_url}\n"
        
        info_content += f"""
## 📁 Directory Structure
```
{os.path.basename(output_dir)}/
├── index.html          (Main page)
├── pages/              (Additional pages)
├── css/                (Stylesheets)
├── js/                 (JavaScript files)
├── images/             (Images)
├── fonts/              (Fonts)
├── videos/             (Videos)
├── audios/             (Audio files)
├── assets/             (Other assets)
├── clone_info.md       (This file)
└── site_manifest.json  (Machine-readable manifest)
```

## 🚀 How to View Cloned Website

### Method 1: Direct Open
Simply double-click `index.html` to open in your default browser.

### Method 2: Local Web Server (Recommended)
```bash
cd {output_dir}
python -m http.server 8000
```
Then visit: http://localhost:8000

### Method 3: Using PHP
```bash
cd {output_dir}
php -S localhost:8000
```
Then visit: http://localhost:8000

## ⚠️ Failed Downloads
"""
        
        if self.failed_downloads:
            for failed in self.failed_downloads:
                info_content += f"- **{failed['type']}**: {failed['url']}\n  Error: {failed['error']}\n\n"
        else:
            info_content += "*None - All assets downloaded successfully!* ✅\n"
        
        info_content += f"""
## 🛠️ Technical Details
- **Crawl Depth:** {self.max_depth}
- **Max Pages:** {self.max_pages}
- **Parallel Downloads:** {self.parallel_downloads}
- **User Agent:** Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0
- **Timeout:** {self.timeout}s
- **Delay:** {self.delay}s
- **Max Retries:** {self.max_retries}

## 💡 Features Used
- ✅ Deep web crawling with BFS
- ✅ Parallel asset downloading
- ✅ Duplicate detection by content hash
- ✅ Responsive image (srcset) support
- ✅ CSS @import extraction
- ✅ JavaScript asset extraction (heuristic)
- ✅ Video & audio support
- ✅ Font extraction from CSS
- ✅ Query parameter handling
- ✅ Relative path conversion for offline viewing
- ✅ Retry mechanism with exponential backoff

---
*Generated by **Reescraping Web Cloner v2.0.0***  
*Author: Ramaerik97*  
*Enhanced with Deep Analysis & Powerful Features*
"""
        
        info_path = os.path.join(output_dir, 'clone_info.md')
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(info_content)
    
    def create_manifest(self, output_dir, crawled_pages):
        """
        Membuat manifest JSON untuk site structure
        
        Args:
            output_dir (str): Directory output
            crawled_pages (list): List of crawled pages
        """
        manifest = {
            'version': '2.0.0',
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'statistics': self.stats,
            'pages': [],
            'assets': {
                'css': [],
                'js': [],
                'images': [],
                'fonts': [],
                'videos': [],
                'audios': [],
                'other': []
            },
            'failed_downloads': self.failed_downloads
        }
        
        # Add pages
        for page_url, depth, parent, _ in crawled_pages:
            normalized = self.normalize_url(page_url)
            manifest['pages'].append({
                'url': page_url,
                'depth': depth,
                'parent': parent,
                'local_path': self.downloaded_files.get(normalized)
            })
        
        # Add assets
        for url, local_path in self.downloaded_files.items():
            if url in [self.normalize_url(p[0]) for p in crawled_pages]:
                continue  # Skip pages
            
            asset_info = {
                'url': url,
                'local_path': local_path
            }
            
            if '/css/' in local_path:
                manifest['assets']['css'].append(asset_info)
            elif '/js/' in local_path:
                manifest['assets']['js'].append(asset_info)
            elif '/images/' in local_path:
                manifest['assets']['images'].append(asset_info)
            elif '/fonts/' in local_path:
                manifest['assets']['fonts'].append(asset_info)
            elif '/videos/' in local_path:
                manifest['assets']['videos'].append(asset_info)
            elif '/audios/' in local_path:
                manifest['assets']['audios'].append(asset_info)
            else:
                manifest['assets']['other'].append(asset_info)
        
        manifest_path = os.path.join(output_dir, 'site_manifest.json')
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)


class WebCloningModule:
    """
    Module interface untuk Web Cloning yang terintegrasi dengan menu utama
    """
    
    def __init__(self):
        self.cloner = None
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self):
        """Print header untuk web cloning module"""
        header = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                 {Fore.YELLOW}ADVANCED WEB CLONING MODULE{Fore.CYAN}                 ║
║           {Fore.GREEN}Clone Website with Deep Crawling & Analysis{Fore.CYAN}        ║
║                   {Fore.MAGENTA}Version 2.0.0 - Enhanced{Fore.CYAN}                   ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(header)
        
    def get_url_input(self):
        """Mendapatkan input URL dari user"""
        print(f"{Fore.WHITE}Masukkan URL website yang ingin di-clone:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Contoh: https://example.com{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Website akan di-clone dengan deep crawling{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Semua assets (CSS, JS, images, fonts, videos) akan diunduh{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Hasil akan disimpan di folder 'result'/{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Ketik 'back' untuk kembali ke menu utama{Style.RESET_ALL}\n")
        
        while True:
            user_input = input(f"{Fore.GREEN}URL: {Style.RESET_ALL}").strip()
            
            if user_input.lower() in ['back', 'kembali', 'b']:
                return None
            
            if not user_input:
                print(f"{Fore.RED}❌ Silakan masukkan URL yang valid.{Style.RESET_ALL}\n")
                continue
            
            # Validasi dan normalisasi URL
            if not user_input.startswith(('http://', 'https://')):
                user_input = 'https://' + user_input
            
            return user_input
    
    def get_config_input(self):
        """Get configuration from user"""
        print(f"\n{Fore.CYAN}⚙️  Konfigurasi Cloning{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Sesuaikan pengaturan atau tekan Enter untuk default{Style.RESET_ALL}\n")
        
        # Max depth
        while True:
            depth_input = input(f"{Fore.GREEN}Max crawl depth [0-5] (default: 2): {Style.RESET_ALL}").strip()
            if not depth_input:
                max_depth = 2
                break
            try:
                max_depth = int(depth_input)
                if 0 <= max_depth <= 5:
                    break
                else:
                    print(f"{Fore.RED}❌ Masukkan angka antara 0-5{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}❌ Masukkan angka yang valid{Style.RESET_ALL}")
        
        # Max pages
        while True:
            pages_input = input(f"{Fore.GREEN}Max pages [1-200] (default: 50): {Style.RESET_ALL}").strip()
            if not pages_input:
                max_pages = 50
                break
            try:
                max_pages = int(pages_input)
                if 1 <= max_pages <= 200:
                    break
                else:
                    print(f"{Fore.RED}❌ Masukkan angka antara 1-200{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}❌ Masukkan angka yang valid{Style.RESET_ALL}")
        
        # Parallel downloads
        while True:
            parallel_input = input(f"{Fore.GREEN}Parallel downloads [1-10] (default: 5): {Style.RESET_ALL}").strip()
            if not parallel_input:
                parallel_downloads = 5
                break
            try:
                parallel_downloads = int(parallel_input)
                if 1 <= parallel_downloads <= 10:
                    break
                else:
                    print(f"{Fore.RED}❌ Masukkan angka antara 1-10{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}❌ Masukkan angka yang valid{Style.RESET_ALL}")
        
        return max_depth, max_pages, parallel_downloads
    
    def run(self):
        """Menjalankan web cloning module"""
        self.clear_screen()
        self.print_header()
        
        url = self.get_url_input()
        if not url:
            return
        
        max_depth, max_pages, parallel_downloads = self.get_config_input()
        
        print(f"\n{Fore.CYAN}🚀 Memulai advanced web cloning...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠️  Proses ini mungkin memakan waktu tergantung ukuran website{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Config: depth={max_depth}, max_pages={max_pages}, parallel={parallel_downloads}{Style.RESET_ALL}\n")
        
        # Initialize cloner dengan config
        self.cloner = WebCloner(
            timeout=30,
            delay=0.3,
            max_retries=3,
            max_depth=max_depth,
            max_pages=max_pages,
            parallel_downloads=parallel_downloads
        )
        
        result = self.cloner.clone_website(url)
        
        if result:
            print(f"\n{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}✅ CLONING BERHASIL!{Style.RESET_ALL}")
            print(f"{Fore.GREEN}{'='*70}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ Gagal melakukan cloning website{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Tekan Enter untuk kembali ke menu utama...{Style.RESET_ALL}")


if __name__ == "__main__":
    # Standalone mode untuk testing
    module = WebCloningModule()
    module.run()
