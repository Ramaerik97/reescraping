#!/usr/bin/env python3
"""
DNS Checker Module - Tools untuk mengecek status DNS dari website
Menganalisa DNS records, response time, dan informasi network
Memberikan laporan lengkap tentang konfigurasi DNS

Author: Ramaerik97
Version: 2.0.0
"""

import dns.resolver
import dns.reversename
import socket
import time
import requests
import os
from datetime import datetime
from colorama import Fore, Style
import subprocess
import platform


class DNSChecker:
    """
    Class utama untuk checking DNS website
    """
    
    def __init__(self, timeout=10):
        """
        Inisialisasi DNSChecker
        
        Args:
            timeout (int): Timeout untuk DNS queries dalam detik
        """
        self.timeout = timeout
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout
        
    def extract_domain(self, url):
        """
        Ekstrak domain dari URL
        
        Args:
            url (str): URL lengkap atau domain
            
        Returns:
            str: Domain name
        """
        if url.startswith(('http://', 'https://')):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        return url.strip()
    
    def check_dns_records(self, domain):
        """
        Mengecek berbagai DNS records untuk domain
        
        Args:
            domain (str): Domain name
            
        Returns:
            dict: Dictionary berisi DNS records
        """
        dns_records = {
            'A': [],
            'AAAA': [],
            'CNAME': [],
            'MX': [],
            'NS': [],
            'TXT': [],
            'SOA': []
        }
        
        record_types = ['A', 'AAAA', 'CNAME', 'MX', 'NS', 'TXT', 'SOA']
        
        for record_type in record_types:
            try:
                print(f"{Fore.CYAN}🔍 Checking {record_type} records...{Style.RESET_ALL}")
                answers = self.resolver.resolve(domain, record_type)
                
                for answer in answers:
                    if record_type == 'MX':
                        dns_records[record_type].append({
                            'priority': answer.preference,
                            'exchange': str(answer.exchange)
                        })
                    elif record_type == 'SOA':
                        dns_records[record_type].append({
                            'mname': str(answer.mname),
                            'rname': str(answer.rname),
                            'serial': answer.serial,
                            'refresh': answer.refresh,
                            'retry': answer.retry,
                            'expire': answer.expire,
                            'minimum': answer.minimum
                        })
                    else:
                        dns_records[record_type].append(str(answer))
                        
            except dns.resolver.NXDOMAIN:
                print(f"{Fore.YELLOW}⚠️  Domain tidak ditemukan untuk {record_type}{Style.RESET_ALL}")
            except dns.resolver.NoAnswer:
                print(f"{Fore.YELLOW}⚠️  Tidak ada {record_type} record{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Error checking {record_type}: {e}{Style.RESET_ALL}")
        
        return dns_records
    
    def check_response_time(self, domain, count=4):
        """
        Mengecek response time ke domain
        
        Args:
            domain (str): Domain name
            count (int): Jumlah ping
            
        Returns:
            dict: Response time statistics
        """
        print(f"{Fore.CYAN}⏱️  Checking response time...{Style.RESET_ALL}")
        
        response_times = []
        
        for i in range(count):
            try:
                start_time = time.time()
                socket.gethostbyname(domain)
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to ms
                response_times.append(response_time)
                print(f"{Fore.GREEN}✅ Ping {i+1}: {response_time:.2f}ms{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Ping {i+1} failed: {e}{Style.RESET_ALL}")
        
        if response_times:
            return {
                'min': min(response_times),
                'max': max(response_times),
                'avg': sum(response_times) / len(response_times),
                'count': len(response_times),
                'success_rate': (len(response_times) / count) * 100
            }
        else:
            return {
                'min': 0,
                'max': 0,
                'avg': 0,
                'count': 0,
                'success_rate': 0
            }
    
    def check_http_status(self, domain):
        """
        Mengecek HTTP status dari domain
        
        Args:
            domain (str): Domain name
            
        Returns:
            dict: HTTP status information
        """
        http_info = {
            'http': {'status': None, 'response_time': None, 'error': None},
            'https': {'status': None, 'response_time': None, 'error': None}
        }
        
        for protocol in ['http', 'https']:
            try:
                print(f"{Fore.CYAN}🌐 Checking {protocol.upper()} status...{Style.RESET_ALL}")
                url = f"{protocol}://{domain}"
                start_time = time.time()
                response = requests.get(url, timeout=self.timeout, allow_redirects=True)
                end_time = time.time()
                
                http_info[protocol] = {
                    'status': response.status_code,
                    'response_time': (end_time - start_time) * 1000,
                    'final_url': response.url,
                    'headers': dict(response.headers)
                }
                
                print(f"{Fore.GREEN}✅ {protocol.upper()}: {response.status_code} ({http_info[protocol]['response_time']:.2f}ms){Style.RESET_ALL}")
                
            except Exception as e:
                http_info[protocol]['error'] = str(e)
                print(f"{Fore.RED}❌ {protocol.upper()} failed: {e}{Style.RESET_ALL}")
        
        return http_info
    
    def check_nameservers(self, domain):
        """
        Mengecek nameservers dan response time mereka
        
        Args:
            domain (str): Domain name
            
        Returns:
            list: List of nameserver information
        """
        print(f"{Fore.CYAN}🏢 Checking nameservers...{Style.RESET_ALL}")
        
        nameservers = []
        
        try:
            ns_answers = self.resolver.resolve(domain, 'NS')
            
            for ns in ns_answers:
                ns_name = str(ns)
                ns_info = {'name': ns_name, 'ip': None, 'response_time': None}
                
                try:
                    # Get IP of nameserver
                    start_time = time.time()
                    ns_ip = socket.gethostbyname(ns_name)
                    end_time = time.time()
                    
                    ns_info['ip'] = ns_ip
                    ns_info['response_time'] = (end_time - start_time) * 1000
                    
                    print(f"{Fore.GREEN}✅ {ns_name} -> {ns_ip} ({ns_info['response_time']:.2f}ms){Style.RESET_ALL}")
                    
                except Exception as e:
                    ns_info['error'] = str(e)
                    print(f"{Fore.YELLOW}⚠️  {ns_name}: {e}{Style.RESET_ALL}")
                
                nameservers.append(ns_info)
                
        except Exception as e:
            print(f"{Fore.RED}❌ Error getting nameservers: {e}{Style.RESET_ALL}")
        
        return nameservers
    
    def check_reverse_dns(self, domain):
        """
        Mengecek reverse DNS lookup
        
        Args:
            domain (str): Domain name
            
        Returns:
            dict: Reverse DNS information
        """
        print(f"{Fore.CYAN}🔄 Checking reverse DNS...{Style.RESET_ALL}")
        
        reverse_info = {'ip': None, 'reverse_dns': None, 'error': None}
        
        try:
            # Get IP first
            ip = socket.gethostbyname(domain)
            reverse_info['ip'] = ip
            
            # Perform reverse lookup
            reverse_name = dns.reversename.from_address(ip)
            reverse_answers = self.resolver.resolve(reverse_name, 'PTR')
            
            reverse_info['reverse_dns'] = [str(answer) for answer in reverse_answers]
            
            print(f"{Fore.GREEN}✅ {ip} -> {', '.join(reverse_info['reverse_dns'])}{Style.RESET_ALL}")
            
        except Exception as e:
            reverse_info['error'] = str(e)
            print(f"{Fore.YELLOW}⚠️  Reverse DNS failed: {e}{Style.RESET_ALL}")
        
        return reverse_info
    
    def traceroute(self, domain):
        """
        Perform traceroute to domain (Windows compatible)
        
        Args:
            domain (str): Domain name
            
        Returns:
            list: Traceroute hops
        """
        print(f"{Fore.CYAN}🛣️  Performing traceroute...{Style.RESET_ALL}")
        
        try:
            if platform.system().lower() == 'windows':
                cmd = ['tracert', '-h', '15', domain]
            else:
                cmd = ['traceroute', '-m', '15', domain]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                hops = []
                
                for line in lines:
                    if line.strip() and not line.startswith('Tracing') and not line.startswith('over'):
                        hops.append(line.strip())
                
                print(f"{Fore.GREEN}✅ Traceroute completed ({len(hops)} hops){Style.RESET_ALL}")
                return hops
            else:
                print(f"{Fore.RED}❌ Traceroute failed: {result.stderr}{Style.RESET_ALL}")
                return []
                
        except Exception as e:
            print(f"{Fore.RED}❌ Traceroute error: {e}{Style.RESET_ALL}")
            return []
    
    def generate_report(self, domain, dns_records, response_time, http_info, nameservers, reverse_info, traceroute_hops):
        """
        Generate comprehensive DNS report
        
        Args:
            domain (str): Domain name
            dns_records (dict): DNS records
            response_time (dict): Response time stats
            http_info (dict): HTTP status info
            nameservers (list): Nameserver info
            reverse_info (dict): Reverse DNS info
            traceroute_hops (list): Traceroute hops
            
        Returns:
            str: Formatted report
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# DNS Analysis Report

## Domain Information
- **Domain**: {domain}
- **Analysis Date**: {timestamp}
- **Tool**: Reescraping DNS Checker v2.0.0

## DNS Records

### A Records (IPv4)
"""
        
        if dns_records['A']:
            for record in dns_records['A']:
                report += f"- {record}\n"
        else:
            report += "- No A records found\n"
        
        report += "\n### AAAA Records (IPv6)\n"
        if dns_records['AAAA']:
            for record in dns_records['AAAA']:
                report += f"- {record}\n"
        else:
            report += "- No AAAA records found\n"
        
        report += "\n### CNAME Records\n"
        if dns_records['CNAME']:
            for record in dns_records['CNAME']:
                report += f"- {record}\n"
        else:
            report += "- No CNAME records found\n"
        
        report += "\n### MX Records (Mail Exchange)\n"
        if dns_records['MX']:
            for record in dns_records['MX']:
                report += f"- Priority: {record['priority']}, Exchange: {record['exchange']}\n"
        else:
            report += "- No MX records found\n"
        
        report += "\n### NS Records (Name Servers)\n"
        if dns_records['NS']:
            for record in dns_records['NS']:
                report += f"- {record}\n"
        else:
            report += "- No NS records found\n"
        
        report += "\n### TXT Records\n"
        if dns_records['TXT']:
            for record in dns_records['TXT']:
                report += f"- {record}\n"
        else:
            report += "- No TXT records found\n"
        
        report += "\n### SOA Record (Start of Authority)\n"
        if dns_records['SOA']:
            soa = dns_records['SOA'][0]
            report += f"""- **Primary NS**: {soa['mname']}
- **Admin Email**: {soa['rname']}
- **Serial**: {soa['serial']}
- **Refresh**: {soa['refresh']} seconds
- **Retry**: {soa['retry']} seconds
- **Expire**: {soa['expire']} seconds
- **Minimum TTL**: {soa['minimum']} seconds
"""
        else:
            report += "- No SOA record found\n"
        
        report += f"""\n## Response Time Analysis
- **Average**: {response_time['avg']:.2f}ms
- **Minimum**: {response_time['min']:.2f}ms
- **Maximum**: {response_time['max']:.2f}ms
- **Success Rate**: {response_time['success_rate']:.1f}%
- **Tests Performed**: {response_time['count']}/{4}

## HTTP Status Check

### HTTP (Port 80)
"""
        
        if http_info['http']['status']:
            report += f"""- **Status Code**: {http_info['http']['status']}
- **Response Time**: {http_info['http']['response_time']:.2f}ms
- **Final URL**: {http_info['http'].get('final_url', 'N/A')}
"""
        else:
            report += f"- **Error**: {http_info['http'].get('error', 'Unknown error')}\n"
        
        report += "\n### HTTPS (Port 443)\n"
        if http_info['https']['status']:
            report += f"""- **Status Code**: {http_info['https']['status']}
- **Response Time**: {http_info['https']['response_time']:.2f}ms
- **Final URL**: {http_info['https'].get('final_url', 'N/A')}
"""
        else:
            report += f"- **Error**: {http_info['https'].get('error', 'Unknown error')}\n"
        
        report += "\n## Nameserver Analysis\n"
        if nameservers:
            for ns in nameservers:
                report += f"""### {ns['name']}
- **IP Address**: {ns.get('ip', 'N/A')}
- **Response Time**: {ns.get('response_time', 0):.2f}ms
"""
                if 'error' in ns:
                    report += f"- **Error**: {ns['error']}\n"
                report += "\n"
        else:
            report += "- No nameservers found\n"
        
        report += "\n## Reverse DNS Lookup\n"
        if reverse_info['reverse_dns']:
            report += f"""- **IP Address**: {reverse_info['ip']}
- **Reverse DNS**: {', '.join(reverse_info['reverse_dns'])}
"""
        else:
            report += f"- **IP Address**: {reverse_info.get('ip', 'N/A')}\n"
            report += f"- **Error**: {reverse_info.get('error', 'No reverse DNS found')}\n"
        
        report += "\n## Network Route (Traceroute)\n"
        if traceroute_hops:
            report += "```\n"
            for hop in traceroute_hops:
                report += f"{hop}\n"
            report += "```\n"
        else:
            report += "- Traceroute data not available\n"
        
        report += "\n---\n*Generated by Reescraping DNS Checker v2.0.0*"
        
        return report
    
    def check_domain(self, domain, output_dir="hasil"):
        """
        Method utama untuk checking DNS domain lengkap
        
        Args:
            domain (str): Domain atau URL yang akan dicek
            output_dir (str): Directory output
            
        Returns:
            dict: Hasil checking atau None jika gagal
        """
        domain = self.extract_domain(domain)
        print(f"\n{Fore.CYAN}🔍 Memulai DNS analysis untuk: {domain}{Style.RESET_ALL}")
        
        try:
            # Check DNS records
            dns_records = self.check_dns_records(domain)
            
            # Check response time
            response_time = self.check_response_time(domain)
            
            # Check HTTP status
            http_info = self.check_http_status(domain)
            
            # Check nameservers
            nameservers = self.check_nameservers(domain)
            
            # Check reverse DNS
            reverse_info = self.check_reverse_dns(domain)
            
            # Perform traceroute
            traceroute_hops = self.traceroute(domain)
            
            # Generate report
            report = self.generate_report(domain, dns_records, response_time, http_info, nameservers, reverse_info, traceroute_hops)
            
            # Save report
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dns_analysis_{domain.replace('.', '_')}_{timestamp}.md"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"\n{Fore.GREEN}🎉 DNS analysis selesai!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📁 Report disimpan di: {filepath}{Style.RESET_ALL}")
            
            return {
                'domain': domain,
                'filepath': filepath,
                'dns_records': dns_records,
                'response_time': response_time,
                'http_info': http_info,
                'nameservers': nameservers,
                'reverse_info': reverse_info
            }
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error saat DNS analysis: {e}{Style.RESET_ALL}")
            return None


class DNSCheckerModule:
    """
    Module interface untuk DNS Checker yang terintegrasi dengan menu utama
    """
    
    def __init__(self):
        self.checker = DNSChecker()
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def print_header(self):
        """Print header untuk DNS checker module"""
        header = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════╗
║                    {Fore.YELLOW}DNS CHECKER MODULE{Fore.CYAN}                      ║
║              {Fore.GREEN}Comprehensive DNS Analysis{Fore.CYAN}                  ║
╚══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(header)
        
    def get_domain_input(self):
        """Mendapatkan input domain dari user"""
        print(f"{Fore.WHITE}Masukkan domain atau URL yang ingin dicek DNS-nya:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Contoh: example.com atau https://example.com{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Tool akan menganalisa DNS records, response time, dan network info{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}• Ketik 'back' untuk kembali ke menu utama{Style.RESET_ALL}\n")
        
        while True:
            user_input = input(f"{Fore.GREEN}Domain/URL: {Style.RESET_ALL}").strip()
            
            if user_input.lower() in ['back', 'kembali', 'b']:
                return None
            
            if not user_input:
                print(f"{Fore.RED}❌ Silakan masukkan domain yang valid.{Style.RESET_ALL}\n")
                continue
            
            return user_input
    
    def run(self):
        """Menjalankan DNS checker module"""
        self.clear_screen()
        self.print_header()
        
        domain = self.get_domain_input()
        if not domain:
            return
        
        print(f"\n{Fore.CYAN}🚀 Memulai DNS analysis...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠️  Proses ini mungkin memakan waktu beberapa menit{Style.RESET_ALL}\n")
        
        result = self.checker.check_domain(domain)
        
        if result:
            print(f"\n{Fore.GREEN}🎉 DNS analysis berhasil!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📊 Ringkasan hasil:{Style.RESET_ALL}")
            
            # Show summary
            dns_records = result['dns_records']
            response_time = result['response_time']
            http_info = result['http_info']
            
            print(f"{Fore.WHITE}   • Domain: {result['domain']}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   • A Records: {len(dns_records['A'])}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   • MX Records: {len(dns_records['MX'])}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   • NS Records: {len(dns_records['NS'])}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   • Avg Response Time: {response_time['avg']:.2f}ms{Style.RESET_ALL}")
            
            if http_info['https']['status']:
                print(f"{Fore.WHITE}   • HTTPS Status: {http_info['https']['status']}{Style.RESET_ALL}")
            if http_info['http']['status']:
                print(f"{Fore.WHITE}   • HTTP Status: {http_info['http']['status']}{Style.RESET_ALL}")
            
            print(f"\n{Fore.CYAN}📁 Report lengkap disimpan di: {result['filepath']}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ Gagal melakukan DNS analysis{Style.RESET_ALL}")
        
        input(f"\n{Fore.CYAN}Tekan Enter untuk kembali ke menu utama...{Style.RESET_ALL}")


if __name__ == "__main__":
    # Standalone mode untuk testing
    module = DNSCheckerModule()
    module.run()