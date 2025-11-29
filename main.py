#!/usr/bin/env python3
"""
Reescraping - Multi-Purpose Web Analysis Tool
Powerful toolkit untuk web scraping, cloning, DNS checking, dan tech stack analysis

Author: Ramaerik97
Version: 1.0.0
"""

import os
import sys
from colorama import init, Fore, Back, Style
from datetime import datetime

# Initialize colorama for Windows compatibility
init(autoreset=True)

# Import modules
try:
    from modules.web_scraper import WebScrapingModule
    from modules.web_cloner import WebCloningModule
    from modules.dns_checker import DNSCheckerModule
    from modules.tech_analyzer import TechAnalyzerModule
    from modules.security_scanner import SecurityScannerModule
    from loading_animation import LoadingContext, ProgressTracker
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Pastikan semua dependencies sudah terinstall dengan: pip install -r requirements.txt")
    sys.exit(1)

class MainMenu:
    """
    Main menu controller untuk Reescraping
    """
    
    def __init__(self):
        self.version = "1.0.0"
        self.author = "Ramaerik97"
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_banner(self):
        """Print aplikasi banner"""
        banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    {Fore.YELLOW}REESCRAPING{Fore.CYAN}                      ║
║              {Fore.GREEN}Multi-Purpose Web Analysis Tool{Fore.CYAN}              ║
║                                                              ║
║  {Fore.MAGENTA}🕷️  Web Scraping    🌐 Web Cloning    🔍 DNS Checker{Fore.CYAN}     ║
║  {Fore.MAGENTA}⚙️  Tech Analysis   🔒 Security Scan   📊 Reports{Fore.CYAN}      ║
║                                                              ║
║  {Fore.WHITE}Version: {self.version}                    Author: {self.author}{Fore.CYAN}     ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(banner)
        
    def print_menu(self):
        """Print main menu options"""
        menu = f"""
{Fore.WHITE}┌─────────────────────────────────────────────────────────────┐
│                        {Fore.YELLOW}MAIN MENU{Fore.WHITE}                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  {Fore.GREEN}1.{Fore.WHITE} 👤 Author Info        - Tentang pembuat tools ini     │
│  {Fore.GREEN}2.{Fore.WHITE} 🕷️  Web Scraping      - Extract HTML, CSS, metadata  │
│  {Fore.GREEN}3.{Fore.WHITE} 🌐 Web Cloning        - Clone website 100% lengkap   │
│  {Fore.GREEN}4.{Fore.WHITE} 🔍 DNS Checker        - Cek status DNS website       │
│  {Fore.GREEN}5.{Fore.WHITE} ⚙️  Tech Stack Analysis - Analisa teknologi website │
│  {Fore.GREEN}6.{Fore.WHITE} 🔒 Security Scanner    - Security vulnerability scan │
│  {Fore.GREEN}7.{Fore.WHITE} 🚪 Exit               - Keluar dari aplikasi         │
│                                                             │
└─────────────────────────────────────────────────────────────┘{Style.RESET_ALL}
        """
        print(menu)
        
    def show_author_info(self):
        """Tampilkan informasi author"""
        self.clear_screen()
        self.print_banner()
        
        author_info = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                        {Fore.YELLOW}AUTHOR INFO{Fore.CYAN}                          ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.WHITE}👤 {Fore.YELLOW}Nama Developer:{Fore.WHITE} Ramaerik97

{Fore.GREEN}📝 Tentang Tools Ini:
{Fore.WHITE}Reescraping adalah toolkit powerful yang dikembangkan untuk
membantu developer, security researcher, dan web analyst dalam
menganalisa website secara komprehensif.

{Fore.GREEN}🚀 Fitur Utama:
{Fore.WHITE}• Web Scraping - Extract konten website (HTML, CSS, metadata)
• Web Cloning - Clone website lengkap untuk analisa offline
• DNS Checker - Monitoring status DNS dan network info
• Tech Stack Analysis - Deteksi teknologi yang digunakan website
• Security Scanner - Analisa keamanan dan vulnerability detection

{Fore.GREEN}💡 Tujuan Pengembangan:
{Fore.WHITE}Tools ini dibuat untuk mempermudah proses research dan analisa
website dengan satu aplikasi yang terintegrasi, menghemat waktu
dan meningkatkan efisiensi kerja.

{Fore.GREEN}🔧 Teknologi yang Digunakan:
{Fore.WHITE}• Python 3.x sebagai bahasa utama
• Beautiful Soup untuk parsing HTML
• Requests untuk HTTP client
• DNS Python untuk DNS analysis
• Selenium untuk dynamic content
• BuiltWith untuk technology detection
• Pillow untuk image processing
• Dan berbagai library powerful lainnya

{Fore.GREEN}📧 Kontak:
{Fore.WHITE}Untuk feedback, bug report, atau kolaborasi:
• GitHub: Ramaerik97
• Email: Available on GitHub profile

{Fore.YELLOW}Terima kasih telah menggunakan Reescraping! 🙏{Style.RESET_ALL}
        """
        
        print(author_info)
        input(f"\n{Fore.CYAN}Tekan Enter untuk kembali ke menu utama...{Style.RESET_ALL}")
        
    def run_web_scraping(self):
        """Jalankan web scraping module"""
        with LoadingContext("Memuat Web Scraping Module...", "pulse") as loading:
            loading.update_message("Menginisialisasi scraper...")
            scraper = WebScrapingModule()
            loading.update_message("Siap memulai Web Scraping...")
        
        scraper.run()
            
    def run_web_cloning(self):
        """Jalankan web cloning module"""
        with LoadingContext("Memuat Web Cloning Module...", "pulse") as loading:
            loading.update_message("Menginisialisasi cloner...")
            cloner = WebCloningModule()
            loading.update_message("Siap memulai Web Cloning...")
        
        cloner.run()
            
    def run_dns_checker(self):
        """Jalankan DNS checker module"""
        print(f"\n{Fore.CYAN}🔍 DNS Checker Configuration{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Pilih mode operasi:{Style.RESET_ALL}")
        print(f"{Fore.GREEN}1. Normal Mode{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}2. Debug Mode (detailed logging untuk troubleshooting){Style.RESET_ALL}")
        
        while True:
            try:
                choice = input(f"\n{Fore.CYAN}Pilih mode (1-2): {Style.RESET_ALL}").strip()
                
                if choice == '1':
                    with LoadingContext("Memuat DNS Checker Module...", "pulse") as loading:
                        loading.update_message("Menginisialisasi DNS checker (Normal Mode)...")
                        dns_checker = DNSCheckerModule(debug=False)
                        loading.update_message("Memulai DNS Checker...")
                    break
                elif choice == '2':
                    print(f"{Fore.YELLOW}🔧 Debug mode akan menampilkan informasi detail untuk troubleshooting network issues{Style.RESET_ALL}")
                    with LoadingContext("Memuat DNS Checker Module...", "pulse") as loading:
                        loading.update_message("Menginisialisasi DNS checker (Debug Mode)...")
                        dns_checker = DNSCheckerModule(debug=True)
                        loading.update_message("Memulai DNS Checker...")
                    break
                else:
                    print(f"{Fore.RED}❌ Pilihan tidak valid. Masukkan 1 atau 2.{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⚠️  Operasi dibatalkan{Style.RESET_ALL}")
                return
        
        dns_checker.run()
            
    def run_tech_analysis(self):
        """Jalankan tech stack analysis module"""
        with LoadingContext("Memuat Tech Stack Analyzer...", "pulse") as loading:
            loading.update_message("Menginisialisasi analyzer...")
            analyzer = TechAnalyzerModule()
            loading.update_message("Siap memulai Tech Stack Analysis...")
        
        analyzer.run()
    
    def run_security_scanner(self):
        """Jalankan security scanner module"""
        with LoadingContext("Memuat Security Scanner...", "pulse") as loading:
            loading.update_message("Menginisialisasi security scanner...")
            scanner = SecurityScannerModule()
            loading.update_message("Siap memulai Security Scanning...")
        
        scanner.run()
    
    def run(self):
        """Main application loop"""
        while True:
            self.clear_screen()
            self.print_banner()
            self.print_menu()
            
            try:
                choice = input(f"\n{Fore.YELLOW}Pilih menu (1-7): {Style.RESET_ALL}").strip()
                
                if choice == '1':
                    self.show_author_info()
                elif choice == '2':
                    self.run_web_scraping()
                elif choice == '3':
                    self.run_web_cloning()
                elif choice == '4':
                    self.run_dns_checker()
                elif choice == '5':
                    self.run_tech_analysis()
                elif choice == '6':
                    self.run_security_scanner()
                elif choice == '7':
                    with LoadingContext("Menutup aplikasi...", "pulse") as loading:
                        loading.update_message("Menyimpan konfigurasi...")
                        loading.update_message("Membersihkan cache...")
                        loading.update_message("Selesai!")
                    
                    self.clear_screen()
                    print(f"{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗")
                    print(f"║                    {Fore.YELLOW}TERIMA KASIH!{Fore.CYAN}                        ║")
                    print(f"║              {Fore.WHITE}Reescraping v{self.version}{Fore.CYAN}                  ║")
                    print(f"║                  {Fore.GREEN}by {self.author}{Fore.CYAN}                      ║")
                    print(f"║                                                              ║")
                    print(f"║  {Fore.WHITE}Terima kasih telah menggunakan Reescraping!{Fore.CYAN}              ║")
                    print(f"║  {Fore.WHITE}Semoga tools ini bermanfaat untuk project Anda.{Fore.CYAN}         ║")
                    print(f"║                                                              ║")
                    print(f"║  {Fore.YELLOW}🚀 Happy Scraping & Analysis!{Fore.CYAN}                        ║")
                    print(f"╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}")
                    print(f"\n{Fore.GREEN}👋 Sampai jumpa lagi!{Style.RESET_ALL}\n")
                    sys.exit(0)
                else:
                    print(f"\n{Fore.RED}❌ Pilihan tidak valid! Silakan pilih 1-7.{Style.RESET_ALL}")
                    input(f"{Fore.CYAN}Tekan Enter untuk melanjutkan...{Style.RESET_ALL}")
                    
            except KeyboardInterrupt:
                self.clear_screen()
                print(f"\n{Fore.YELLOW}Program dihentikan oleh user. Sampai jumpa! 👋{Style.RESET_ALL}")
                sys.exit(0)
            except Exception as e:
                print(f"\n{Fore.RED}❌ Terjadi error: {str(e)}{Style.RESET_ALL}")
                input(f"{Fore.CYAN}Tekan Enter untuk melanjutkan...{Style.RESET_ALL}")


if __name__ == "__main__":
    # Cek apakah semua dependencies terinstall
    try:
        import requests
        import bs4
        import colorama
        import dns
        import tqdm
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nSilakan install dependencies dengan perintah:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    # Jalankan aplikasi utama
    app = MainMenu()
    app.run()