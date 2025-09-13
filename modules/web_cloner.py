#!/usr/bin/env python3
"""
Web Cloner Module - Tools untuk cloning website 100% lengkap
Mengunduh semua assets (HTML, CSS, JS, images, fonts) dan membuat website berjalan local
Hasil disimpan dalam folder 'result' dengan struktur yang rapi

Author: Ramaerik97
Version: 2.0.0
"""

import requests
from bs4 import BeautifulSoup
import os
import re
import urllib.parse
from urllib.parse import urljoin, urlparse, unquote
import time
import mimetypes
from pathlib import Path
from colorama import Fore, Style
from tqdm import tqdm
import shutil


class WebCloner:
    """
    Class utama untuk cloning website lengkap
    """
    
    def __init__(self, timeout=30, delay=0.5, max_retries=3):
        """
        Inisialisasi WebCloner
        
        Args:
            timeout (int): Timeout untuk request dalam detik
            delay (float): Delay antar request dalam detik
            max_retries (int): Maksimal retry untuk failed requests
        """
        self.timeout = timeout
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.downloaded_files = set()
        self.failed_downloads = []
        
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
            return os.path.splitext(path)[1]
        
        # Coba dari content type
        if content_type:
            ext = mimetypes.guess_extension(content_type.split(';')[0])
            if ext:
                return ext
        
        # Default berdasarkan content type umum
        if content_type:
            if 'text/css' in content_type:
                return '.css'
            elif 'javascript' in content_type:
                return '.js'
            elif 'image/jpeg' in content_type:
                return '.jpg'
            elif 'image/png' in content_type:
                return '.png'
            elif 'image/gif' in content_type:
                return '.gif'
            elif 'image/svg' in content_type:
                return '.svg'
            elif 'font' in content_type:
                return '.woff'
        
        return ''
    
    def download_file(self, url, local_path, description=""):
        """
        Mengunduh file dari URL ke path lokal
        
        Args:
            url (str): URL file yang akan diunduh
            local_path (str): Path lokal untuk menyimpan file
            description (str): Deskripsi untuk progress bar
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        if url in self.downloaded_files:
            return True
            
        try:
            # Buat direktori jika belum ada
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            for attempt in range(self.max_retries):
                try:
                    response = self.session.get(url, timeout=self.timeout, stream=True)
                    response.raise_for_status()
                    
                    # Dapatkan ukuran file untuk progress bar
                    total_size = int(response.headers.get('content-length', 0))
                    
                    with open(local_path, 'wb') as f:
                        if total_size > 0:
                            with tqdm(total=total_size, unit='B', unit_scale=True, 
                                    desc=description, leave=False) as pbar:
                                for chunk in response.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                                        pbar.update(len(chunk))
                        else:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                    
                    self.downloaded_files.add(url)
                    time.sleep(self.delay)
                    return True
                    
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        print(f"{Fore.YELLOW}⚠️  Gagal download {url}: {e}{Style.RESET_ALL}")
                        self.failed_downloads.append({'url': url, 'error': str(e)})
                        return False
                    time.sleep(1)  # Wait before retry
                    
        except Exception as e:
            print(f"{Fore.RED}❌ Error download {url}: {e}{Style.RESET_ALL}")
            self.failed_downloads.append({'url': url, 'error': str(e)})
            return False
    
    def extract_assets_from_html(self, soup, base_url):
        """
        Mengekstrak semua asset URLs dari HTML
        
        Args:
            soup: BeautifulSoup object
            base_url (str): Base URL website
            
        Returns:
            dict: Dictionary berisi berbagai jenis assets
        """
        assets = {
            'css': [],
            'js': [],
            'images': [],
            'fonts': [],
            'other': []
        }
        
        # CSS files
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                assets['css'].append(full_url)
        
        # JavaScript files
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                full_url = urljoin(base_url, src)
                assets['js'].append(full_url)
        
        # Images
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src:
                full_url = urljoin(base_url, src)
                assets['images'].append(full_url)
        
        # Background images dari CSS inline
        for element in soup.find_all(style=True):
            style = element.get('style', '')
            bg_matches = re.findall(r'background-image:\s*url\(["\']?([^"\')]+)["\']?\)', style)
            for match in bg_matches:
                full_url = urljoin(base_url, match)
                assets['images'].append(full_url)
        
        # Favicon
        for link in soup.find_all('link', rel=['icon', 'shortcut icon', 'apple-touch-icon']):
            href = link.get('href')
            if href:
                full_url = urljoin(base_url, href)
                assets['images'].append(full_url)
        
        return assets
    
    def extract_css_assets(self, css_content, base_url):
        """
        Mengekstrak asset URLs dari CSS content
        
        Args:
            css_content (str): Content CSS
            base_url (str): Base URL untuk resolve relative URLs
            
        Returns:
            list: List of asset URLs
        """
        assets = []
        
        # Find all url() references in CSS
        url_pattern = r'url\(["\']?([^"\')]+)["\']?\)'
        matches = re.findall(url_pattern, css_content)
        
        for match in matches:
            if not match.startswith(('data:', 'http://', 'https://')):
                full_url = urljoin(base_url, match)
                assets.append(full_url)
            elif match.startswith(('http://', 'https://')):
                assets.append(match)
        
        return assets
    
    def update_html_paths(self, soup, base_url, output_dir):
        """
        Update semua paths di HTML untuk mengarah ke file lokal
        
        Args:
            soup: BeautifulSoup object
            base_url (str): Base URL website
            output_dir (str): Directory output
            
        Returns:
            BeautifulSoup: Updated soup object
        """
        # Update CSS links
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                local_path = self.url_to_local_path(urljoin(base_url, href), output_dir)
                relative_path = os.path.relpath(local_path, output_dir)
                link['href'] = relative_path.replace('\\', '/')
        
        # Update JavaScript sources
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                local_path = self.url_to_local_path(urljoin(base_url, src), output_dir)
                relative_path = os.path.relpath(local_path, output_dir)
                script['src'] = relative_path.replace('\\', '/')
        
        # Update image sources
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src:
                local_path = self.url_to_local_path(urljoin(base_url, src), output_dir)
                relative_path = os.path.relpath(local_path, output_dir)
                img['src'] = relative_path.replace('\\', '/')
        
        # Update favicon and icons
        for link in soup.find_all('link', rel=['icon', 'shortcut icon', 'apple-touch-icon']):
            href = link.get('href')
            if href:
                local_path = self.url_to_local_path(urljoin(base_url, href), output_dir)
                relative_path = os.path.relpath(local_path, output_dir)
                link['href'] = relative_path.replace('\\', '/')
        
        return soup
    
    def update_css_paths(self, css_content, base_url, output_dir):
        """
        Update semua paths di CSS untuk mengarah ke file lokal
        
        Args:
            css_content (str): Content CSS
            base_url (str): Base URL
            output_dir (str): Directory output
            
        Returns:
            str: Updated CSS content
        """
        def replace_url(match):
            url = match.group(1)
            if not url.startswith(('data:', 'http://', 'https://')):
                full_url = urljoin(base_url, url)
                local_path = self.url_to_local_path(full_url, output_dir)
                relative_path = os.path.relpath(local_path, output_dir)
                return f'url("{relative_path.replace(chr(92), "/")}")'  # chr(92) is backslash
            return match.group(0)
        
        url_pattern = r'url\(["\']?([^"\')]+)["\']?\)'
        updated_css = re.sub(url_pattern, replace_url, css_content)
        
        return updated_css
    
    def url_to_local_path(self, url, output_dir):
        """
        Konversi URL ke path lokal
        
        Args:
            url (str): URL file
            output_dir (str): Directory output
            
        Returns:
            str: Path lokal
        """
        parsed_url = urlparse(url)
        path = unquote(parsed_url.path)
        
        # Tentukan subdirectory berdasarkan jenis file
        if path.endswith('.css'):
            subdir = 'css'
        elif path.endswith(('.js', '.jsx', '.ts', '.tsx')):
            subdir = 'js'
        elif path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico')):
            subdir = 'images'
        elif path.endswith(('.woff', '.woff2', '.ttf', '.eot', '.otf')):
            subdir = 'fonts'
        else:
            subdir = 'assets'
        
        # Buat nama file yang aman
        filename = os.path.basename(path) or 'index.html'
        filename = self.sanitize_filename(filename)
        
        # Jika tidak ada ekstensi, coba deteksi dari URL
        if '.' not in filename:
            ext = self.get_file_extension(url)
            filename += ext
        
        return os.path.join(output_dir, subdir, filename)
    
    def clone_website(self, url, output_dir="result"):
        """
        Method utama untuk cloning website lengkap
        
        Args:
            url (str): URL website yang akan di-clone
            output_dir (str): Directory output utama
            
        Returns:
            dict: Hasil cloning atau None jika gagal
        """
        print(f"\n{Fore.CYAN}🌐 Memulai cloning website: {url}{Style.RESET_ALL}")
        
        # Buat nama folder berdasarkan domain
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        safe_domain = self.sanitize_filename(domain)
        
        site_output_dir = os.path.join(output_dir, safe_domain)
        
        try:
            # Buat direktori output
            os.makedirs(site_output_dir, exist_ok=True)
            
            # Download HTML utama
            print(f"{Fore.CYAN}📥 Mengunduh HTML utama...{Style.RESET_ALL}")
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ekstrak semua assets
            print(f"{Fore.CYAN}🔍 Menganalisa assets...{Style.RESET_ALL}")
            assets = self.extract_assets_from_html(soup, url)
            
            total_assets = sum(len(asset_list) for asset_list in assets.values())
            print(f"{Fore.GREEN}📊 Ditemukan {total_assets} assets untuk diunduh{Style.RESET_ALL}")
            
            # Download CSS files dan ekstrak assets dari CSS
            css_assets = []
            for css_url in tqdm(assets['css'], desc="Downloading CSS", colour="blue"):
                local_path = self.url_to_local_path(css_url, site_output_dir)
                if self.download_file(css_url, local_path, f"CSS: {os.path.basename(local_path)}"):
                    # Baca CSS dan ekstrak assets
                    try:
                        with open(local_path, 'r', encoding='utf-8') as f:
                            css_content = f.read()
                        
                        # Ekstrak assets dari CSS
                        css_asset_urls = self.extract_css_assets(css_content, css_url)
                        css_assets.extend(css_asset_urls)
                        
                        # Update paths di CSS
                        updated_css = self.update_css_paths(css_content, css_url, site_output_dir)
                        
                        # Simpan CSS yang sudah diupdate
                        with open(local_path, 'w', encoding='utf-8') as f:
                            f.write(updated_css)
                            
                    except Exception as e:
                        print(f"{Fore.YELLOW}⚠️  Error processing CSS {css_url}: {e}{Style.RESET_ALL}")
            
            # Download JavaScript files
            for js_url in tqdm(assets['js'], desc="Downloading JS", colour="yellow"):
                local_path = self.url_to_local_path(js_url, site_output_dir)
                self.download_file(js_url, local_path, f"JS: {os.path.basename(local_path)}")
            
            # Download images
            all_images = assets['images'] + css_assets
            for img_url in tqdm(set(all_images), desc="Downloading Images", colour="green"):
                local_path = self.url_to_local_path(img_url, site_output_dir)
                self.download_file(img_url, local_path, f"IMG: {os.path.basename(local_path)}")
            
            # Update HTML paths
            print(f"{Fore.CYAN}🔧 Memperbarui paths di HTML...{Style.RESET_ALL}")
            updated_soup = self.update_html_paths(soup, url, site_output_dir)
            
            # Simpan HTML yang sudah diupdate
            html_path = os.path.join(site_output_dir, 'index.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(str(updated_soup))
            
            # Buat file info
            self.create_info_file(url, site_output_dir, total_assets)
            
            print(f"\n{Fore.GREEN}🎉 Cloning selesai!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📁 Website disimpan di: {site_output_dir}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🌐 Buka file: {html_path}{Style.RESET_ALL}")
            
            return {
                'url': url,
                'output_dir': site_output_dir,
                'html_path': html_path,
                'total_assets': total_assets,
                'downloaded': len(self.downloaded_files),
                'failed': len(self.failed_downloads)
            }
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error saat cloning website: {e}{Style.RESET_ALL}")
            return None
    
    def create_info_file(self, url, output_dir, total_assets):
        """
        Membuat file info tentang hasil cloning
        
        Args:
            url (str): URL website
            output_dir (str): Directory output
            total_assets (int): Total assets yang ditemukan
        """
        info_content = f"""# Website Clone Info

**Original URL:** {url}
**Clone Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Total Assets Found:** {total_assets}
**Successfully Downloaded:** {len(self.downloaded_files)}
**Failed Downloads:** {len(self.failed_downloads)}

## How to View
1. Open `index.html` in your web browser
2. Or use a local web server for better compatibility:
   ```
   python -m http.server 8000
   ```
   Then visit: http://localhost:8000

## Failed Downloads
"""
        
        if self.failed_downloads:
            for failed in self.failed_downloads:
                info_content += f"- {failed['url']} - {failed['error']}\n"
        else:
            info_content += "None - All assets downloaded successfully!\n"
        
        info_content += "\n---\n*Generated by Reescraping Web Cloner v2.0.0*"
        
        info_path = os.path.join(output_dir, 'clone_info.md')
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(info_content)


class WebCloningModule:
    """
    Module interface untuk Web Cloning yang terintegrasi dengan menu utama
    """
    
    def __init__(self):
        self.cloner = WebCloner()
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self):
        """Print header untuk web cloning module"""
        header = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    {Fore.YELLOW}WEB CLONING MODULE{Fore.CYAN}                      ║
║              {Fore.GREEN}Clone Website 100% Lengkap{Fore.CYAN}                  ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(header)
        
    def get_url_input(self):
        """Mendapatkan input URL dari user"""
        print(f"{Fore.WHITE}Masukkan URL website yang ingin di-clone:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Contoh: https://example.com{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Website akan di-clone lengkap dengan semua assets{Style.RESET_ALL}")
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
    
    def run(self):
        """Menjalankan web cloning module"""
        self.clear_screen()
        self.print_header()
        
        url = self.get_url_input()
        if not url:
            return
        
        print(f"\n{Fore.CYAN}🚀 Memulai cloning website...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠️  Proses ini mungkin memakan waktu tergantung ukuran website{Style.RESET_ALL}\n")
        
        result = self.cloner.clone_website(url)
        
        if result:
            print(f"\n{Fore.GREEN}🎉 Website berhasil di-clone!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 Statistik:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   • Total assets: {result['total_assets']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   • Berhasil diunduh: {result['downloaded']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   • Gagal diunduh: {result['failed']}{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}📁 Lokasi file:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   • Folder: {result['output_dir']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   • HTML: {result['html_path']}{Style.RESET_ALL}")
            print(f"\n{Fore.GREEN}💡 Cara membuka:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   1. Double-click file index.html{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   2. Atau gunakan local server: python -m http.server 8000{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ Gagal melakukan cloning website{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Tekan Enter untuk kembali ke menu utama...{Style.RESET_ALL}")


if __name__ == "__main__":
    # Standalone mode untuk testing
    module = WebCloningModule()
    module.run()