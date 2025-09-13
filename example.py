#!/usr/bin/env python3
"""
Contoh Penggunaan Reescraping

File ini berisi berbagai contoh cara menggunakan WebScraper
untuk scraping website dengan berbagai skenario.

Author: Ramaerik97
"""

from web_scraper import WebScraper
import time


def example_basic_scraping():
    """
    Contoh dasar scraping website
    """
    print("\n" + "="*50)
    print("CONTOH 1: Basic Website Scraping")
    print("="*50)
    
    # Inisialisasi scraper
    scraper = WebScraper(timeout=30, delay=1)
    
    # URL yang akan di-scrape
    url = "https://httpbin.org/html"
    
    # Lakukan scraping
    result = scraper.scrape_website(url)
    
    if result:
        print(f"\n✅ Scraping berhasil!")
        print(f"📁 File disimpan: {result['filepath']}")
        print(f"📄 Panjang HTML: {result['html_length']} karakter")
        print(f"🎨 Jumlah CSS: {result['css_count']} file/block")
    else:
        print("❌ Scraping gagal!")


def example_multiple_websites():
    """
    Contoh scraping beberapa website sekaligus
    """
    print("\n" + "="*50)
    print("CONTOH 2: Multiple Websites Scraping")
    print("="*50)
    
    # Daftar website yang akan di-scrape
    websites = [
        "https://httpbin.org/html",
        "https://example.com",
        "https://httpbin.org/"
    ]
    
    # Inisialisasi scraper dengan delay lebih lama untuk menghindari rate limiting
    scraper = WebScraper(timeout=30, delay=2)
    
    results = []
    
    for i, url in enumerate(websites, 1):
        print(f"\n🔄 Scraping website {i}/{len(websites)}: {url}")
        
        result = scraper.scrape_website(url)
        
        if result:
            results.append(result)
            print(f"✅ Berhasil: {result['filepath']}")
        else:
            print(f"❌ Gagal scraping: {url}")
        
        # Delay antar website
        if i < len(websites):
            print("⏳ Menunggu sebelum scraping berikutnya...")
            time.sleep(3)
    
    print(f"\n📊 Ringkasan: {len(results)}/{len(websites)} website berhasil di-scrape")
    
    return results


def example_custom_output_directory():
    """
    Contoh scraping dengan custom output directory
    """
    print("\n" + "="*50)
    print("CONTOH 3: Custom Output Directory")
    print("="*50)
    
    scraper = WebScraper()
    
    # Scraping dengan custom directory
    custom_dir = "scraping_results"
    url = "https://httpbin.org/html"
    
    print(f"📁 Menyimpan hasil ke directory: {custom_dir}")
    
    result = scraper.scrape_website(url, output_dir=custom_dir)
    
    if result:
        print(f"✅ File disimpan di: {result['filepath']}")
    else:
        print("❌ Scraping gagal!")


def example_manual_scraping():
    """
    Contoh penggunaan manual (step by step)
    """
    print("\n" + "="*50)
    print("CONTOH 4: Manual Step-by-Step Scraping")
    print("="*50)
    
    scraper = WebScraper()
    url = "https://httpbin.org/html"
    
    print("🔄 Step 1: Mengambil HTML content...")
    html_content, soup, status_code = scraper.get_html_content(url)
    
    if not html_content:
        print("❌ Gagal mengambil HTML")
        return
    
    print(f"✅ HTML berhasil diambil (Status: {status_code})")
    print(f"📄 Panjang HTML: {len(html_content)} karakter")
    
    print("\n🔄 Step 2: Mengekstrak CSS...")
    css_data = scraper.extract_css(soup, url)
    print(f"🎨 Internal CSS: {len(css_data['internal_css'])} block")
    print(f"🎨 External CSS: {len(css_data['external_css'])} file")
    
    print("\n🔄 Step 3: Mengekstrak metadata...")
    metadata = scraper.extract_metadata(soup)
    print(f"📋 Title: {metadata.get('title', 'N/A')}")
    print(f"📋 Description: {metadata.get('description', 'N/A')[:100]}...")
    
    print("\n🔄 Step 4: Menyimpan ke file...")
    filepath = scraper.save_to_markdown(url, html_content, css_data, metadata)
    
    if filepath:
        print(f"✅ File disimpan: {filepath}")
    else:
        print("❌ Gagal menyimpan file")


def example_error_handling():
    """
    Contoh handling error untuk URL yang tidak valid
    """
    print("\n" + "="*50)
    print("CONTOH 5: Error Handling")
    print("="*50)
    
    scraper = WebScraper(timeout=10)
    
    # URL yang tidak valid atau tidak bisa diakses
    invalid_urls = [
        "https://website-yang-tidak-ada.com",
        "http://localhost:99999",
        "invalid-url"
    ]
    
    for url in invalid_urls:
        print(f"\n🔄 Mencoba scraping: {url}")
        result = scraper.scrape_website(url)
        
        if result:
            print(f"✅ Berhasil: {result['filepath']}")
        else:
            print(f"❌ Gagal scraping URL: {url}")


def main():
    """
    Fungsi utama untuk menjalankan semua contoh
    """
    print("🚀 Reescraping - Contoh Penggunaan")
    print("========================================")
    
    try:
        # Jalankan contoh-contoh
        example_basic_scraping()
        
        input("\n⏸️  Tekan Enter untuk melanjutkan ke contoh berikutnya...")
        example_multiple_websites()
        
        input("\n⏸️  Tekan Enter untuk melanjutkan ke contoh berikutnya...")
        example_custom_output_directory()
        
        input("\n⏸️  Tekan Enter untuk melanjutkan ke contoh berikutnya...")
        example_manual_scraping()
        
        input("\n⏸️  Tekan Enter untuk melanjutkan ke contoh berikutnya...")
        example_error_handling()
        
        print("\n🎉 Semua contoh selesai dijalankan!")
        print("📁 Cek folder 'hasil' dan 'scraping_results' untuk melihat file hasil scraping.")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Program dihentikan oleh user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()