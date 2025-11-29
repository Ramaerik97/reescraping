# Reescraping

Reescraping adalah multi-purpose web analysis toolkit yang saya buat untuk berbagai keperluan analisis website. Tools ini nggak cuma buat scraping doang, tapi juga bisa cloning website, DNS checking, dan tech stack analysis. Awalnya sih buat keperluan pribadi, tapi ternyata berguna banget jadi saya share.

## Fitur Utama

### 🕷️ Web Scraping
- Ngambil semua HTML dari website
- Extract CSS (internal & external)
- Ambil metadata lengkap (title, description, Open Graph, dll)
- Export ke format Markdown yang rapi
- Rate limiting & error handling

### 🌐 Web Cloning (✨ Enhanced v2.0.1)

**NEW:** Advanced deep web cloning dengan powerful features + **OFFLINE RENDERING FIX!** 🎉

- 🕸️ **Deep Crawling**: Clone seluruh website dengan BFS algorithm
- ⚡ **Parallel Downloads**: 5x lebih cepat dengan concurrent downloads
- 🎯 **Advanced Asset Detection**: 8 tipe asset (CSS, JS, images, fonts, videos, audios, dll)
- 💾 **Smart Deduplication**: Content-based dedup hemat 40% space
- 📱 **Responsive Image Support**: Srcset & picture element
- 🎬 **Video & Audio**: Complete media support
- 📊 **Comprehensive Reports**: Detailed stats & manifest
- 🔄 **Enhanced Retry**: Exponential backoff untuk reliability
- 📁 **Perfect Offline Viewing**: 100% working relative paths
- ✨ **NEW: Offline Rendering Fix**: Hasil clone sekarang bisa dibuka offline dengan sempurna!
  - Proper HTML structure (DOCTYPE, meta charset)
  - No more "weird text" - encoding UTF-8 yang benar
  - CSS & JavaScript berfungsi dengan baik
  - Inline styles di-update otomatis
  - Ready untuk double-click & view di browser

Fitur lengkap: Lihat [WEB_CLONER_ENHANCEMENT_DOCS.md](WEB_CLONER_ENHANCEMENT_DOCS.md)  
Perbaikan offline: Lihat [WEB_CLONER_OFFLINE_FIX.md](WEB_CLONER_OFFLINE_FIX.md)

### 🔍 DNS Checker
- Comprehensive DNS record analysis
- A, AAAA, MX, NS, TXT, CNAME records
- Reverse DNS lookup
- DNS propagation check
- Traceroute analysis
- Network diagnostics & troubleshooting

### ⚙️ Tech Stack Analyzer
- Detect teknologi yang digunakan website
- Framework detection (React, Vue, Angular, dll)
- CMS detection (WordPress, Drupal, dll)
- Server & hosting info
- Security headers analysis

### 🔒 Security Scanner (✨ NEW!)
**NEW:** Comprehensive security vulnerability analysis dengan professional-grade reporting! 🛡️

- 🛡️ **Security Headers Analysis**: HSTS, CSP, X-Frame-Options, dll
- 🔐 **SSL/TLS Certificate Check**: Certificate validity, expiry, key strength
- 🚨 **Vulnerability Detection**: SQL Injection, XSS, Directory Listing patterns
- 📁 **Exposed Directories Scanner**: Check for exposed admin panels & sensitive files
- 📊 **Security Scoring**: 0-100 security score dengan actionable recommendations
- 📋 **Professional Reports**: Detailed markdown security reports
- ⚡ **Real-time Analysis**: Interactive scanning dengan progress tracking

### ⚡ Performance Analyzer (✨ NEW!)
**NEW:** Advanced performance analysis dengan Core Web Vitals compliance! 📈

- ⏱️ **Page Load Time Analysis**: Multiple measurements dengan statistical analysis
- 📈 **Core Web Vitals**: LCP, FID, CLS metrics analysis
- 🔧 **Optimization Opportunities**: Image optimization, minification, compression checks
- 🚀 **Performance Scoring**: A-F grade performance assessment
- 📊 **Comprehensive Metrics**: Detailed performance breakdown
- 💡 **Actionable Recommendations**: Specific optimization suggestions
- 📋 **Professional Reports**: In-depth performance analysis reports

## Cara Install

Gampang kok, tinggal:

1. Download atau clone project ini
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

Library yang dipake:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast XML/HTML parser
- `dnspython` - DNS operations
- `builtwith` - Technology detection
- `whois` - Domain whois lookup
- `pyopenssl` - SSL/TLS certificate analysis
- `cryptography` - Security operations
- `colorama` - Terminal colors
- `tqdm` - Progress bars
- `pillow` - Image processing
- `selenium` - Browser automation
- `wget` - File downloading
- `urllib3`, `chardet`, `certifi` - Supporting libraries

## Cara Pakai

### Menu Utama (Recommended)

```bash
python main.py
```

Ini akan buka menu interaktif dengan pilihan:
1. 👤 Author Info
2. 🕷️ Web Scraping
3. 🌐 Web Cloning  
4. 🔍 DNS Checker
5. ⚙️ Tech Stack Analyzer
6. 🔒 **Security Scanner (NEW!)**
7. 🚪 Exit

### Manual Usage per Module

#### Web Scraping
```python
from modules.web_scraper import WebScrapingModule

scraper = WebScrapingModule()
result = scraper.scrape_website("https://example.com")
```

#### Web Cloning
```python
from modules.web_cloner import WebCloningModule

cloner = WebCloningModule()
result = cloner.clone_website("https://example.com")

# Hasil cloning bisa langsung dibuka di browser!
# File HTML yang dihasilkan sudah siap untuk viewing offline
```

**Cara membuka hasil cloning:**
```bash
# Method 1: Double-click file index.html (sudah berfungsi dengan sempurna!)
# Buka folder result, cari folder website yang di-clone, double-click index.html

# Method 2: Local server (recommended untuk website kompleks)
cd result/example_com_YYYYMMDD_HHMMSS
python -m http.server 8000
# Buka browser: http://localhost:8000
```

#### DNS Checker
```python
from modules.dns_checker import DNSCheckerModule

dns_checker = DNSCheckerModule()
result = dns_checker.check_dns("example.com")
```

#### Tech Stack Analyzer
```python
from modules.tech_analyzer import TechAnalyzerModule

analyzer = TechAnalyzerModule()
result = analyzer.analyze_website("https://example.com")
```

#### Security Scanner (NEW!)
```python
from modules.security_scanner import SecurityScannerModule

scanner = SecurityScannerModule()
result = scanner.run_security_scan("https://example.com")
```

#### Performance Analyzer (NEW!)
```python
from modules.performance_analyzer import PerformanceAnalyzerModule

analyzer = PerformanceAnalyzerModule()
result = analyzer.run_performance_analysis("https://example.com")
```

### Kalau mau custom setting

```python
from web_scraper import WebScraper

# Scraper dengan custom timeout dan delay
scraper = WebScraper(timeout=60, delay=2)

# Scraping dengan custom output directory
result = scraper.scrape_website(
    url="https://example.com",
    output_dir="my_scraping_results"
)
```

### Atau kalau mau manual step by step

```python
from web_scraper import WebScraper

scraper = WebScraper()
url = "https://example.com"

# Step 1: Ambil HTML
html_content, soup, status_code = scraper.get_html_content(url)

# Step 2: Ekstrak CSS
css_data = scraper.extract_css(soup, url)

# Step 3: Ekstrak metadata
metadata = scraper.extract_metadata(soup)

# Step 4: Simpan ke file
filepath = scraper.save_to_markdown(url, html_content, css_data, metadata)
```

## Quick Start

Buat yang mau langsung coba:

```bash
# Jalanin menu utama (recommended)
python main.py

# Atau jalanin contoh web scraping
python example.py
```

Atau kalau mau langsung pakai salah satu modul:
```python
# Web Scraping
from modules.web_scraper import WebScrapingModule
scraper = WebScrapingModule()
result = scraper.scrape_website("https://example.com")

# Web Cloning
from modules.web_cloner import WebCloningModule
cloner = WebCloningModule()
result = cloner.clone_website("https://example.com")
```

## Hasil Output

Hasil scraping bakal disimpan dalam format Markdown kayak gini:

```
# Website Scraping Report

## Informasi Umum
- URL: https://example.com
- Tanggal Scraping: 2024-01-15 10:30:45
- Title: Example Website
- Description: Website description...

## Metadata Website
| Field | Value |
|-------|-------|
| Title | Example Website |
| Description | Website description |
| Keywords | example, website, demo |
| Author | Website Author |
| Language | en |
| ... | ... |

## CSS Information
### Internal CSS
```css
body { margin: 0; padding: 0; }
```

### External CSS
```css
/* External CSS content */
```

## HTML Content
```html
<!DOCTYPE html>
<html>...
```
```

## Setting & Konfigurasi

### Parameter WebScraper

```python
scraper = WebScraper(
    timeout=30,    # Timeout request dalam detik (default: 30)
    delay=1        # Delay antar request dalam detik (default: 1)
)
```

### Parameter scrape_website

```python
result = scraper.scrape_website(
    url="https://example.com",     # URL website (wajib)
    output_dir="hasil"             # Directory output (default: "hasil")
)
```

## Return Value

Method `scrape_website()` bakal return dictionary kayak gini:

```python
{
    'url': 'https://example.com',
    'filepath': 'hasil/example_com_20240115_103045.md',
    'html_length': 15420,
    'css_count': 5,
    'metadata': {
        'title': 'Example Website',
        'description': 'Website description',
        'keywords': 'example, website',
        # ... metadata lainnya
    }
}
```

## Error Handling

Saya udah tambahin error handling buat berbagai kasus:

- Connection Error (timeout, network bermasalah)
- HTTP Error (404, 500, dll)
- Parsing Error (HTML/CSS yang rusak)
- File System Error (permission, disk penuh)

```python
try:
    result = scraper.scrape_website("https://example.com")
    if result:
        print("Scraping berhasil!")
    else:
        print("Scraping gagal - cek log untuk detail error")
except Exception as e:
    print(f"Error: {e}")
```

## Contoh Penggunaan Lanjutan

### Scraping Multiple Websites

```python
from web_scraper import WebScraper
import time

websites = [
    "https://example.com",
    "https://httpbin.org",
    "https://github.com"
]

scraper = WebScraper(delay=2)  # Delay lebih lama untuk multiple requests

for url in websites:
    print(f"Scraping: {url}")
    result = scraper.scrape_website(url)
    
    if result:
        print(f"✅ Berhasil: {result['filepath']}")
    else:
        print(f"❌ Gagal: {url}")
    
    time.sleep(3)  # Delay antar website
```

### Custom Output Processing

```python
from web_scraper import WebScraper

scraper = WebScraper()
url = "https://example.com"

# Ambil data mentah
html_content, soup, status_code = scraper.get_html_content(url)
css_data = scraper.extract_css(soup, url)
metadata = scraper.extract_metadata(soup)

# Process data sesuai kebutuhan
print(f"Website Title: {metadata['title']}")
print(f"CSS Files: {len(css_data['external_css'])}")
print(f"HTML Size: {len(html_content)} bytes")

# Simpan dengan custom processing
filepath = scraper.save_to_markdown(url, html_content, css_data, metadata, "custom_output")
```

## Hal Penting yang Perlu Diperhatikan

**Respect robots.txt**
Selalu cek robots.txt website dulu sebelum scraping (https://example.com/robots.txt)

**Jangan spam request**
Pake delay yang wajar, minimal 1-2 detik. Jangan sampe website-nya down gara-gara kita.

**Legal stuff**
Pastikan scraping yang dilakukan legal dan sesuai ToS website. Gunakan dengan bijak ya!

**User Agent**
Tools ini udah pake User-Agent yang proper, jangan diubah kecuali emang perlu.

## Troubleshooting

**Connection timeout**
- Coba naikin timeout: `WebScraper(timeout=60)`
- Cek koneksi internet
- Mungkin website-nya lagi down

**403 Forbidden**
- Website ngeblokir scraping
- Coba pake delay lebih lama
- Cek robots.txt

**File permission denied**
- Cek permission folder
- Pastikan disk space cukup
- Tutup file kalau lagi kebuka

**CSS nggak ke-extract**
- Website pake CSS dinamis (JavaScript)
- CSS di-load via AJAX
- Butuh tools kayak Selenium buat render JavaScript


## License

Lihat di File LICENSE

## About

Reescraping saya buat karena sering butuh scraping website buat berbagai keperluan. Kalau ada bug atau saran, feel free to reach out!

Happy scraping! 🕷️