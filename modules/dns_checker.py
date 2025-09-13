#!/usr/bin/env python3
"""
DNS Checker Module - Tools untuk mengecek status DNS dari website
Menganalisa DNS records, response time, dan informasi network
Memberikan laporan lengkap tentang konfigurasi DNS

Author: Ramaerik97
Version: 1.0.0
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
import logging
import sys
from .loading_animation import LoadingContext, ProgressTracker


class DNSChecker:
    """
    Class utama untuk checking DNS website
    """
    
    def setup_logging(self, log_level=logging.INFO):
        """
        Setup logging untuk debugging network issues
        
        Args:
            log_level: Level logging (DEBUG, INFO, WARNING, ERROR)
        """
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_network_diagnostics(self):
        """
        Dapatkan informasi diagnostik network untuk debugging
        
        Returns:
            dict: Network diagnostic information
        """
        diagnostics = {
            'system': platform.system(),
            'platform': platform.platform(),
            'dns_servers': [],
            'network_interfaces': [],
            'connectivity_test': None
        }
        
        try:
            # Get current DNS servers
            if hasattr(self.resolver, 'nameservers'):
                diagnostics['dns_servers'] = self.resolver.nameservers.copy()
            
            # Test basic connectivity
            try:
                socket.create_connection(('8.8.8.8', 53), timeout=5)
                diagnostics['connectivity_test'] = 'SUCCESS - Can reach Google DNS'
            except Exception as e:
                diagnostics['connectivity_test'] = f'FAILED - {str(e)}'
            
            # Get network interface info (basic)
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                diagnostics['local_hostname'] = hostname
                diagnostics['local_ip'] = local_ip
            except Exception as e:
                diagnostics['network_error'] = str(e)
                
        except Exception as e:
            diagnostics['diagnostic_error'] = str(e)
        
        return diagnostics
    
    def print_network_diagnostics(self):
        """
        Print network diagnostics untuk debugging
        """
        print(f"\n{Fore.CYAN}🔧 Network Diagnostics:{Style.RESET_ALL}")
        diagnostics = self.get_network_diagnostics()
        
        print(f"{Fore.WHITE}   • System: {diagnostics.get('system', 'Unknown')}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}   • Platform: {diagnostics.get('platform', 'Unknown')}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}   • DNS Servers: {', '.join(diagnostics.get('dns_servers', ['None']))}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}   • Local IP: {diagnostics.get('local_ip', 'Unknown')}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}   • Connectivity Test: {diagnostics.get('connectivity_test', 'Not tested')}{Style.RESET_ALL}")
        
        if 'diagnostic_error' in diagnostics:
            print(f"{Fore.RED}   • Diagnostic Error: {diagnostics['diagnostic_error']}{Style.RESET_ALL}")
        
        print()
    
    def __init__(self, timeout=10, debug=False):
        """
        Inisialisasi DNSChecker
        
        Args:
            timeout (int): Timeout untuk DNS queries dalam detik
            debug (bool): Enable debug logging
        """
        self.timeout = timeout
        self.debug = debug
        
        # Setup logging
        if debug:
            self.setup_logging(logging.DEBUG)
        else:
            self.setup_logging(logging.INFO)
        
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout
        
        # Fallback DNS servers untuk mengatasi DNS server lambat
        self.fallback_dns_servers = [
            '8.8.8.8',      # Google DNS
            '8.8.4.4',      # Google DNS Secondary
            '1.1.1.1',      # Cloudflare DNS
            '1.0.0.1',      # Cloudflare DNS Secondary
            '208.67.222.222', # OpenDNS
            '208.67.220.220'  # OpenDNS Secondary
        ]
        
        # Retry configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        # Error tracking
        self.error_log = []
        
        if debug:
            print(f"{Fore.CYAN}🔧 Debug mode enabled{Style.RESET_ALL}")
            self.print_network_diagnostics()
    
    def print_error_summary(self):
        """
        Print summary of all errors encountered during DNS checking
        """
        if not self.error_log:
            print(f"{Fore.GREEN}✅ No errors encountered during DNS checking{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.RED}🚨 Error Summary ({len(self.error_log)} errors):{Style.RESET_ALL}")
        for i, error in enumerate(self.error_log, 1):
            print(f"{Fore.RED}   {i}. {error}{Style.RESET_ALL}")
        print()
    
    def get_error_count(self):
        """
        Get total number of errors encountered
        
        Returns:
            int: Number of errors
        """
        return len(self.error_log)
    
    def clear_error_log(self):
        """
        Clear the error log
        """
        self.error_log.clear()
        
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
    
    def resolve_with_retry(self, domain, record_type, max_retries=None):
        """
        Resolve DNS dengan retry mechanism dan fallback DNS servers
        
        Args:
            domain (str): Domain name
            record_type (str): DNS record type
            max_retries (int): Maximum retry attempts
            
        Returns:
            dns.resolver.Answer: DNS answer atau None jika gagal
        """
        if max_retries is None:
            max_retries = self.max_retries
            
        # Setup loading animation
        loading_msg = f"Resolving {domain} ({record_type})"
        
        with LoadingContext(loading_msg, "spinner", Fore.CYAN) as loader:
            # Try dengan DNS server default dulu
            for attempt in range(max_retries):
                try:
                    loader.update_message(f"Resolving {domain} ({record_type}) - attempt {attempt + 1}/{max_retries}")
                    result = self.resolver.resolve(domain, record_type)
                    loader.set_success_message(f"DNS resolved: {record_type} records found")
                    return result
                except (dns.resolver.Timeout, dns.resolver.LifetimeTimeout) as e:
                    error_msg = f"DNS timeout for {record_type} record: {str(e)}"
                    self.error_log.append(error_msg)
                    if self.debug:
                        self.logger.debug(error_msg)
                    
                    if attempt < max_retries - 1:
                        loader.update_message(f"DNS timeout, retrying in {self.retry_delay}s...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        loader.update_message("Trying fallback DNS servers...")
                        break
                except Exception as e:
                    error_msg = f"DNS error for {record_type} record attempt {attempt + 1}: {str(e)}"
                    self.error_log.append(error_msg)
                    if self.debug:
                        self.logger.debug(error_msg)
                    
                    if attempt < max_retries - 1:
                        loader.update_message(f"DNS error, retrying in {self.retry_delay}s...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        raise e
            
            # Try dengan fallback DNS servers
            original_nameservers = self.resolver.nameservers.copy()
            
            for i, dns_server in enumerate(self.fallback_dns_servers):
                try:
                    loader.update_message(f"Trying fallback DNS {i+1}/{len(self.fallback_dns_servers)}: {dns_server}")
                    self.resolver.nameservers = [dns_server]
                    result = self.resolver.resolve(domain, record_type)
                    loader.set_success_message(f"Fallback DNS successful: {record_type} records found")
                    return result
                except Exception as e:
                    error_msg = f"Fallback DNS {dns_server} failed for {record_type}: {str(e)}"
                    self.error_log.append(error_msg)
                    if self.debug:
                        self.logger.debug(error_msg)
                    continue
            
            # Restore original nameservers
            self.resolver.nameservers = original_nameservers
            loader.set_error_message(f"DNS resolution failed for {domain}")
            return None
    
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
        
        # Progress tracker untuk DNS checks
        tracker = ProgressTracker(len(record_types), "Checking DNS Records")
        
        for record_type in record_types:
            tracker.update(f"Checking {record_type} records")
            
            try:
                print(f"{Fore.CYAN}🔍 Checking {record_type} records...{Style.RESET_ALL}")
                answers = self.resolve_with_retry(domain, record_type)
                
                if answers is None:
                    print(f"{Fore.RED}❌ Failed to resolve {record_type} records after all retries{Style.RESET_ALL}")
                    continue
                
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
        Perform traceroute to domain (Windows compatible) dengan fallback mechanism
        
        Args:
            domain (str): Domain name
            
        Returns:
            list: Traceroute hops
        """
        print(f"{Fore.CYAN}🛣️  Performing traceroute...{Style.RESET_ALL}")
        
        error_log = []
        
        if self.debug:
            print(f"{Fore.CYAN}🔧 Traceroute Debug Mode Enabled{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   • Target: {domain}{Style.RESET_ALL}")
            print(f"{Fore.WHITE}   • Platform: {platform.system()}{Style.RESET_ALL}")
            print()
        
        # Konfigurasi traceroute dengan timeout yang lebih optimal
        traceroute_configs = [
            # Config 1: Standard traceroute (15 hops, 60s timeout)
            {'hops': 15, 'timeout': 60, 'description': 'standard'},
            # Config 2: Reduced hops untuk network yang lambat (10 hops, 45s timeout)
            {'hops': 10, 'timeout': 45, 'description': 'reduced hops'},
            # Config 3: Minimal traceroute (5 hops, 30s timeout)
            {'hops': 5, 'timeout': 30, 'description': 'minimal'}
        ]
        
        if self.debug:
            print(f"{Fore.CYAN}🔧 Traceroute Configurations:{Style.RESET_ALL}")
            for i, config in enumerate(traceroute_configs, 1):
                if platform.system().lower() == 'windows':
                    cmd = ['tracert', '-h', str(config['hops']), '-w', '3000', domain]
                else:
                    cmd = ['traceroute', '-m', str(config['hops']), '-w', '3', domain]
                print(f"{Fore.WHITE}   {i}. {config['description']}: {' '.join(cmd)} (timeout: {config['timeout']}s){Style.RESET_ALL}")
            print()
        
        # Progress tracker untuk traceroute attempts
        tracker = ProgressTracker(len(traceroute_configs) + 1, "Performing Traceroute")
        
        for i, config in enumerate(traceroute_configs):
            tracker.update(f"Trying {config['description']} config")
            
            with LoadingContext(f"Running {config['description']} traceroute", "wave", Fore.YELLOW) as loader:
                try:
                    print(f"{Fore.CYAN}🔄 Trying traceroute config {i+1}/3 ({config['description']})...{Style.RESET_ALL}")
                    
                    if platform.system().lower() == 'windows':
                        cmd = ['tracert', '-h', str(config['hops']), '-w', '3000', domain]
                    else:
                        cmd = ['traceroute', '-m', str(config['hops']), '-w', '3', domain]
                    
                    if self.debug:
                        print(f"{Fore.WHITE}   Command: {' '.join(cmd)}{Style.RESET_ALL}")
                    
                    loader.update_message(f"Executing {config['description']} traceroute command...")
                    
                    start_time = time.time()
                    result = subprocess.run(
                        cmd, 
                        capture_output=True, 
                        text=True, 
                        timeout=config['timeout'],
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system().lower() == 'windows' else 0
                    )
                    execution_time = time.time() - start_time
                    
                    if self.debug:
                        print(f"{Fore.WHITE}   Execution time: {execution_time:.2f}s{Style.RESET_ALL}")
                        print(f"{Fore.WHITE}   Return code: {result.returncode}{Style.RESET_ALL}")
                        if result.stdout:
                            print(f"{Fore.WHITE}   Output length: {len(result.stdout)} chars{Style.RESET_ALL}")
                        if result.stderr:
                            print(f"{Fore.WHITE}   Error length: {len(result.stderr)} chars{Style.RESET_ALL}")
                    
                    if result.returncode == 0:
                        loader.update_message("Parsing traceroute results...")
                        
                        lines = result.stdout.strip().split('\n')
                        hops = []
                        
                        for line in lines:
                            line = line.strip()
                            if (line and 
                                not line.startswith('Tracing') and 
                                not line.startswith('over') and
                                not line.startswith('Trace complete')):
                                hops.append(line)
                        
                        if hops:
                            loader.set_success_message(f"Traceroute completed with {config['description']} config in {execution_time:.2f}s ({len(hops)} hops)")
                            print(f"{Fore.GREEN}✅ Traceroute completed with {config['description']} config in {execution_time:.2f}s ({len(hops)} hops){Style.RESET_ALL}")
                            return hops
                        else:
                            error_msg = f"No valid hops found with {config['description']} config"
                            error_log.append(error_msg)
                            loader.set_error_message(error_msg)
                            print(f"{Fore.YELLOW}⚠️  {error_msg}{Style.RESET_ALL}")
                            continue
                    else:
                        error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                        full_error_msg = f"Traceroute {config['description']} config failed (return code: {result.returncode}): {error_msg}"
                        error_log.append(full_error_msg)
                        loader.set_error_message(full_error_msg)
                        print(f"{Fore.YELLOW}⚠️  {full_error_msg}{Style.RESET_ALL}")
                        continue
                        
                except subprocess.TimeoutExpired:
                    timeout_msg = f"Traceroute {config['description']} config timed out after {config['timeout']}s"
                    error_log.append(timeout_msg)
                    loader.set_error_message(timeout_msg)
                    print(f"{Fore.YELLOW}⚠️  {timeout_msg}{Style.RESET_ALL}")
                    continue
                except Exception as e:
                    exception_msg = f"Traceroute {config['description']} config error: {str(e)}"
                    error_log.append(exception_msg)
                    loader.set_error_message(exception_msg)
                    print(f"{Fore.YELLOW}⚠️  {exception_msg}{Style.RESET_ALL}")
                    continue
        
        # Jika semua config gagal, coba ping sebagai fallback
        tracker.update("Trying ping fallback")
        print(f"{Fore.CYAN}🔄 All traceroute configs failed, trying ping as fallback...{Style.RESET_ALL}")
        
        if self.debug:
            print(f"{Fore.RED}🔧 Traceroute Error Summary:{Style.RESET_ALL}")
            for i, error in enumerate(error_log, 1):
                print(f"{Fore.RED}   {i}. {error}{Style.RESET_ALL}")
            print()
        
        return self._ping_fallback(domain)
    
    def _ping_fallback(self, domain):
        """
        Fallback ping test jika traceroute gagal
        
        Args:
            domain (str): Domain name
            
        Returns:
            list: Ping results sebagai fallback
        """
        with LoadingContext(f"Ping fallback to {domain}", "pulse", Fore.MAGENTA) as loader:
            try:
                if platform.system().lower() == 'windows':
                    cmd = ['ping', '-n', '4', domain]
                else:
                    cmd = ['ping', '-c', '4', domain]
                
                ping_timeout = 15
                print(f"{Fore.CYAN}🔄 Trying ping fallback: {' '.join(cmd)} (timeout: {ping_timeout}s){Style.RESET_ALL}")
                
                if self.debug:
                    print(f"{Fore.WHITE}   Platform: {platform.system()}{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}   Command: {' '.join(cmd)}{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}   Timeout: {ping_timeout}s{Style.RESET_ALL}")
                
                loader.update_message("Executing ping command...")
                
                start_time = time.time()
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=ping_timeout,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system().lower() == 'windows' else 0
                )
                execution_time = time.time() - start_time
                
                if self.debug:
                    print(f"{Fore.WHITE}   Execution time: {execution_time:.2f}s{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}   Return code: {result.returncode}{Style.RESET_ALL}")
                    print(f"{Fore.WHITE}   Output length: {len(result.stdout)} chars{Style.RESET_ALL}")
                    if result.stderr:
                        print(f"{Fore.WHITE}   Error length: {len(result.stderr)} chars{Style.RESET_ALL}")
                
                if result.returncode == 0:
                    loader.update_message("Parsing ping results...")
                    
                    lines = result.stdout.strip().split('\n')
                    ping_results = []
                    
                    for line in lines:
                        line = line.strip()
                        if ('Reply from' in line or 'bytes from' in line or 
                            'Ping statistics' in line or 'packets transmitted' in line):
                            ping_results.append(f"PING: {line}")
                    
                    if ping_results:
                        loader.set_success_message(f"Ping successful in {execution_time:.2f}s ({len(ping_results)} responses)")
                        print(f"{Fore.GREEN}✅ Ping fallback successful in {execution_time:.2f}s ({len(ping_results)} responses){Style.RESET_ALL}")
                        return ping_results
                
                error_msg = f"Ping fallback failed (return code: {result.returncode})"
                if self.debug:
                    print(f"{Fore.RED}   {error_msg}{Style.RESET_ALL}")
                    if result.stderr:
                        print(f"{Fore.RED}   Stderr: {result.stderr.strip()}{Style.RESET_ALL}")
                
                loader.set_error_message(error_msg)
                print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                return [f"Network connectivity test failed - both traceroute and ping unsuccessful. Error: {result.stderr.strip() if result.stderr else 'Unknown error'}"]
                
            except subprocess.TimeoutExpired:
                timeout_msg = f"Ping fallback timed out after {ping_timeout} seconds"
                if self.debug:
                    print(f"{Fore.RED}   {timeout_msg}{Style.RESET_ALL}")
                loader.set_error_message(timeout_msg)
                print(f"{Fore.RED}❌ {timeout_msg}{Style.RESET_ALL}")
                return [f"Network test timeout: {timeout_msg}"]
            except Exception as e:
                exception_msg = f"Ping fallback error: {str(e)}"
                if self.debug:
                    print(f"{Fore.RED}   {exception_msg}{Style.RESET_ALL}")
                loader.set_error_message(exception_msg)
                print(f"{Fore.RED}❌ {exception_msg}{Style.RESET_ALL}")
                return [f"Network test error: {str(e)}"]
    
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
- **Tool**: Reescraping DNS Checker v1.0.0

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
        
        report += "\n---\n*Generated by Reescraping DNS Checker v1.0.0*"
        
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
            
            # Print error summary jika ada error
            if self.debug or self.get_error_count() > 0:
                self.print_error_summary()
            
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
    
    def __init__(self, debug=False):
        self.debug = debug
        self.checker = DNSChecker(debug=debug)
        
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