#!/usr/bin/env python3
"""
Security Scanner Module - Tools untuk security analysis website
Mendeteksi vulnerabilities, security headers, dan isu keamanan
Memberikan security score dan actionable recommendations

Author: Ramaerik97
Version: 1.0.0
"""

import requests
import ssl
import socket
import re
import json
import time
import sys
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from colorama import Fore, Style
from loading_animation import LoadingContext, ProgressTracker
import OpenSSL


class SecurityScanner:
    """
    Class utama untuk security scanning website
    """
    
    def __init__(self, timeout=30):
        """
        Inisialisasi SecurityScanner
        
        Args:
            timeout (int): Timeout untuk request dalam detik
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Security headers yang harus dicek
        self.security_headers = {
            'Strict-Transport-Security': {
                'name': 'HTTP Strict Transport Security (HSTS)',
                'description': 'Enforces HTTPS connection',
                'weight': 10,
                'recommended': 'max-age=31536000; includeSubDomains'
            },
            'Content-Security-Policy': {
                'name': 'Content Security Policy (CSP)',
                'description': 'Prevents XSS attacks',
                'weight': 10,
                'recommended': 'default-src \'self\''
            },
            'X-Frame-Options': {
                'name': 'X-Frame-Options',
                'description': 'Prevents clickjacking',
                'weight': 8,
                'recommended': 'DENY or SAMEORIGIN'
            },
            'X-Content-Type-Options': {
                'name': 'X-Content-Type-Options',
                'description': 'Prevents MIME-type sniffing',
                'weight': 6,
                'recommended': 'nosniff'
            },
            'X-XSS-Protection': {
                'name': 'X-XSS-Protection',
                'description': 'XSS protection in older browsers',
                'weight': 4,
                'recommended': '1; mode=block'
            },
            'Referrer-Policy': {
                'name': 'Referrer Policy',
                'description': 'Controls referrer information',
                'weight': 4,
                'recommended': 'strict-origin-when-cross-origin'
            },
            'Permissions-Policy': {
                'name': 'Permissions Policy',
                'description': 'Controls browser features',
                'weight': 4,
                'recommended': 'geolocation=(), microphone=(), camera=()'
            }
        }
        
        # Common vulnerable paths untuk scanning
        self.vulnerable_paths = [
            '/admin',
            '/admin/login',
            '/wp-admin',
            '/phpmyadmin',
            '/.env',
            '/config.php',
            '/backup',
            '/.git/config',
            '/robots.txt',
            '/sitemap.xml'
        ]
        
        # Common security vulnerabilities patterns
        self.vulnerability_patterns = {
            'sql_injection': [
                r"error.*sql",
                r"mysql.*error",
                r"ora-[0-9]{5}",
                r"microsoft.*odbc.*error"
            ],
            'xss': [
                r"<script[^>]*>.*</script>",
                r"javascript:",
                r"onload\s*=",
                r"onerror\s*="
            ],
            'directory_listing': [
                r"index of/",
                r"directory listing",
                r"parent directory"
            ],
            'information_disclosure': [
                r"apache/[0-9]",
                r"nginx/[0-9]",
                r"php/[0-9]",
                r"server:"
            ]
        }
    
    def check_security_headers(self, url):
        """
        Mengecek security headers dari website
        
        Args:
            url (str): URL website yang akan di-scan
            
        Returns:
            dict: Hasil security headers analysis
        """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            headers = response.headers
            
            results = {
                'score': 0,
                'max_score': 0,
                'headers_found': {},
                'headers_missing': [],
                'recommendations': []
            }
            
            for header_name, header_info in self.security_headers.items():
                results['max_score'] += header_info['weight']
                
                if header_name in headers:
                    header_value = headers[header_name]
                    results['headers_found'][header_name] = {
                        'value': header_value,
                        'name': header_info['name'],
                        'description': header_info['description'],
                        'weight': header_info['weight']
                    }
                    results['score'] += header_info['weight']
                else:
                    results['headers_missing'].append({
                        'name': header_info['name'],
                        'description': header_info['description'],
                        'weight': header_info['weight'],
                        'recommended': header_info['recommended']
                    })
                    results['recommendations'].append(
                        f"Add {header_info['name']} header: {header_info['recommended']}"
                    )
            
            return results
            
        except Exception as e:
            return {'error': f'Failed to check security headers: {str(e)}'}
    
    def analyze_ssl_certificate(self, domain):
        """
        Menganalisis SSL/TLS certificate
        
        Args:
            domain (str): Domain yang akan dianalisis
            
        Returns:
            dict: Hasil SSL certificate analysis
        """
        try:
            context = ssl.create_default_context()
            
            with socket.create_connection((domain, 443), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    der_cert = ssock.getpeercert(binary_form=True)
                    x509_cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, der_cert)
                    
                    # Extract certificate information
                    results = {
                        'valid': True,
                        'subject': dict(x[0] for x in cert['subject']),
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'version': cert['version'],
                        'serial_number': cert['serialNumber'],
                        'not_before': cert['notBefore'],
                        'not_after': cert['notAfter'],
                        'signature_algorithm': cert['signatureAlgorithm'],
                        'days_until_expiry': None,
                        'is_self_signed': False,
                        'issues': []
                    }
                    
                    # Calculate days until expiry
                    expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    results['days_until_expiry'] = (expiry_date - datetime.utcnow()).days
                    
                    # Check if self-signed
                    if results['issuer'] == results['subject']:
                        results['is_self_signed'] = True
                        results['issues'].append('Certificate is self-signed')
                    
                    # Check expiry
                    if results['days_until_expiry'] < 30:
                        results['issues'].append(f'Certificate expires in {results["days_until_expiry"]} days')
                    elif results['days_until_expiry'] < 7:
                        results['issues'].append('Certificate expires very soon!')
                    
                    # Check certificate strength
                    public_key = x509_cert.get_pubkey()
                    key_size = public_key.bits()
                    
                    if key_size < 2048:
                        results['issues'].append(f'Weak key size: {key_size} bits (minimum 2048 recommended)')
                    
                    results['key_size'] = key_size
                    
                    return results
                    
        except Exception as e:
            return {
                'valid': False,
                'error': f'SSL certificate analysis failed: {str(e)}',
                'issues': [f'SSL/TLS connection failed: {str(e)}']
            }
    
    def scan_vulnerabilities(self, url):
        """
        Scan untuk common vulnerabilities
        
        Args:
            url (str): URL yang akan di-scan
            
        Returns:
            dict: Hasil vulnerability scanning
        """
        try:
            results = {
                'vulnerabilities_found': [],
                'risk_score': 0,
                'scanned_pages': 1,
                'recommendations': []
            }
            
            # Scan main page
            response = self.session.get(url, timeout=self.timeout)
            content = response.text.lower()
            
            # Check for vulnerability patterns
            for vuln_type, patterns in self.vulnerability_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        severity = self._get_vulnerability_severity(vuln_type)
                        results['vulnerabilities_found'].append({
                            'type': vuln_type,
                            'severity': severity,
                            'pattern': pattern,
                            'description': self._get_vulnerability_description(vuln_type)
                        })
                        results['risk_score'] += severity
            
            # Check for exposed sensitive information
            sensitive_patterns = [
                (r'password\s*[:=]\s*["\']?\w+', 'Potential password exposure'),
                (r'api[_-]?key\s*[:=]\s*["\']?\w+', 'Potential API key exposure'),
                (r'secret\s*[:=]\s*["\']?\w+', 'Potential secret exposure'),
                (r'token\s*[:=]\s*["\']?\w+', 'Potential token exposure')
            ]
            
            for pattern, description in sensitive_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    results['vulnerabilities_found'].append({
                        'type': 'information_disclosure',
                        'severity': 8,
                        'pattern': pattern,
                        'description': description
                    })
                    results['risk_score'] += 8
            
            # Generate recommendations based on findings
            if results['vulnerabilities_found']:
                results['recommendations'].extend([
                    'Implement proper input validation and sanitization',
                    'Use parameterized queries to prevent SQL injection',
                    'Implement Content Security Policy (CSP)',
                    'Regular security audits and penetration testing',
                    'Keep all software and dependencies updated'
                ])
            
            return results
            
        except Exception as e:
            return {
                'error': f'Vulnerability scanning failed: {str(e)}',
                'vulnerabilities_found': [],
                'risk_score': 0
            }
    
    def check_exposed_directories(self, base_url):
        """
        Check untuk exposed directories dan files
        
        Args:
            base_url (str): Base URL untuk scanning
            
        Returns:
            dict: Hasil directory scanning
        """
        try:
            results = {
                'exposed_paths': [],
                'risk_score': 0,
                'scanned_paths': len(self.vulnerable_paths)
            }
            
            for path in self.vulnerable_paths:
                full_url = urljoin(base_url, path)
                
                try:
                    response = self.session.get(full_url, timeout=10, allow_redirects=False)
                    
                    if response.status_code == 200:
                        risk_level = self._assess_path_risk(path, response)
                        results['exposed_paths'].append({
                            'path': path,
                            'url': full_url,
                            'status_code': response.status_code,
                            'content_type': response.headers.get('content-type', ''),
                            'risk_level': risk_level,
                            'size': len(response.content)
                        })
                        results['risk_score'] += risk_level
                    
                    elif response.status_code == 403:
                        # Path exists but forbidden - still worth noting
                        results['exposed_paths'].append({
                            'path': path,
                            'url': full_url,
                            'status_code': response.status_code,
                            'content_type': 'Forbidden',
                            'risk_level': 2,
                            'size': 0
                        })
                        results['risk_score'] += 2
                        
                except requests.exceptions.RequestException:
                    # Path doesn't exist or network error - ignore
                    continue
            
            return results
            
        except Exception as e:
            return {
                'error': f'Directory scanning failed: {str(e)}',
                'exposed_paths': [],
                'risk_score': 0
            }
    
    def generate_security_report(self, url, all_results):
        """
        Generate comprehensive security report
        
        Args:
            url (str): URL yang di-scan
            all_results (dict): Semua hasil scanning
            
        Returns:
            str: Format security report dalam Markdown
        """
        report = f"""
# 🔒 Security Analysis Report

## 📊 Scan Information
- **Target URL**: {url}
- **Scan Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Scanner**: Reescraping Security Scanner v1.0.0

---

## 🎯 Executive Summary

"""
        
        # Calculate overall security score
        security_score = 0
        max_score = 100
        
        # Security Headers Score (40% weight)
        if 'security_headers' in all_results and 'score' in all_results['security_headers']:
            headers_score = (all_results['security_headers']['score'] / all_results['security_headers']['max_score']) * 100
            security_score += headers_score * 0.4
            report += f"### 🔐 Security Headers Score: {headers_score:.1f}/100\n"
        
        # SSL Certificate Score (30% weight)
        ssl_score = 100
        if 'ssl_certificate' in all_results:
            if not all_results['ssl_certificate'].get('valid', False):
                ssl_score = 0
            elif 'issues' in all_results['ssl_certificate'] and all_results['ssl_certificate']['issues']:
                ssl_score = max(0, 100 - (len(all_results['ssl_certificate']['issues']) * 20))
            
            security_score += ssl_score * 0.3
            report += f"### 🔒 SSL/TLS Score: {ssl_score:.1f}/100\n"
        
        # Vulnerability Score (30% weight)
        vuln_score = 100
        if 'vulnerabilities' in all_results:
            risk_score = all_results['vulnerabilities'].get('risk_score', 0)
            vuln_score = max(0, 100 - risk_score)
            security_score += vuln_score * 0.3
            report += f"### 🛡️  Vulnerability Score: {vuln_score:.1f}/100\n"
        
        report += f"\n### 📈 Overall Security Score: {security_score:.1f}/100\n\n"
        
        # Security Grade
        if security_score >= 90:
            grade = "A+ (Excellent)"
            grade_color = "🟢"
        elif security_score >= 80:
            grade = "A (Very Good)"
            grade_color = "🟢"
        elif security_score >= 70:
            grade = "B (Good)"
            grade_color = "🟡"
        elif security_score >= 60:
            grade = "C (Fair)"
            grade_color = "🟡"
        elif security_score >= 50:
            grade = "D (Poor)"
            grade_color = "🟠"
        else:
            grade = "F (Critical)"
            grade_color = "🔴"
        
        report += f"### {grade_color} Security Grade: {grade}\n\n"
        
        # Detailed Results
        report += "---\n\n## 🔐 Security Headers Analysis\n\n"
        
        if 'security_headers' in all_results:
            headers_result = all_results['security_headers']
            
            if 'error' in headers_result:
                report += f"❌ **Error**: {headers_result['error']}\n\n"
            else:
                report += f"**Score**: {headers_result['score']}/{headers_result['max_score']}\n\n"
                
                if headers_result['headers_found']:
                    report += "### ✅ Headers Found:\n\n"
                    for header_name, header_info in headers_result['headers_found'].items():
                        report += f"- **{header_info['name']}**: `{header_info['value']}`\n"
                        report += f"  - *{header_info['description']}*\n\n"
                
                if headers_result['headers_missing']:
                    report += "### ❌ Missing Headers:\n\n"
                    for header in headers_result['headers_missing']:
                        report += f"- **{header['name']}** (Weight: {header['weight']})\n"
                        report += f"  - *{header['description']}*\n"
                        report += f"  - **Recommended**: `{header['recommended']}`\n\n"
        
        report += "---\n\n## 🔒 SSL/TLS Certificate Analysis\n\n"
        
        if 'ssl_certificate' in all_results:
            ssl_result = all_results['ssl_certificate']
            
            if not ssl_result.get('valid', False):
                report += f"❌ **SSL Certificate Invalid**: {ssl_result.get('error', 'Unknown error')}\n\n"
            else:
                report += f"**Valid**: ✅\n"
                report += f"**Subject**: {ssl_result.get('subject', {})}\n"
                report += f"**Issuer**: {ssl_result.get('issuer', {})}\n"
                report += f"**Expires**: {ssl_result.get('not_after', 'Unknown')}\n"
                report += f"**Days Until Expiry**: {ssl_result.get('days_until_expiry', 'Unknown')}\n"
                report += f"**Key Size**: {ssl_result.get('key_size', 'Unknown')} bits\n"
                
                if ssl_result.get('is_self_signed', False):
                    report += "⚠️  **Warning**: Self-signed certificate\n"
                
                if ssl_result.get('issues'):
                    report += "\n### ⚠️ Issues:\n\n"
                    for issue in ssl_result['issues']:
                        report += f"- {issue}\n"
                
                report += "\n"
        
        report += "---\n\n## 🛡️ Vulnerability Analysis\n\n"
        
        if 'vulnerabilities' in all_results:
            vuln_result = all_results['vulnerabilities']
            
            if 'error' in vuln_result:
                report += f"❌ **Error**: {vuln_result['error']}\n\n"
            else:
                report += f"**Risk Score**: {vuln_result.get('risk_score', 0)}\n"
                report += f"**Pages Scanned**: {vuln_result.get('scanned_pages', 0)}\n\n"
                
                if vuln_result.get('vulnerabilities_found'):
                    report += "### 🚨 Vulnerabilities Found:\n\n"
                    for vuln in vuln_result['vulnerabilities_found']:
                        severity_emoji = "🔴" if vuln['severity'] >= 8 else "🟡" if vuln['severity'] >= 5 else "🟢"
                        report += f"- {severity_emoji} **{vuln['type'].replace('_', ' ').title()}** (Severity: {vuln['severity']})\n"
                        report += f"  - {vuln['description']}\n"
                        report += f"  - Pattern: `{vuln['pattern']}`\n\n"
                else:
                    report += "✅ **No vulnerabilities detected**\n\n"
                
                if vuln_result.get('recommendations'):
                    report += "### 💡 Recommendations:\n\n"
                    for rec in vuln_result['recommendations']:
                        report += f"- {rec}\n"
                    report += "\n"
        
        report += "---\n\n## 📁 Exposed Directories Analysis\n\n"
        
        if 'exposed_directories' in all_results:
            dirs_result = all_results['exposed_directories']
            
            if 'error' in dirs_result:
                report += f"❌ **Error**: {dirs_result['error']}\n\n"
            else:
                report += f"**Risk Score**: {dirs_result.get('risk_score', 0)}\n"
                report += f"**Paths Scanned**: {dirs_result.get('scanned_paths', 0)}\n\n"
                
                if dirs_result.get('exposed_paths'):
                    report += "### 🚨 Exposed Paths Found:\n\n"
                    for path in dirs_result['exposed_paths']:
                        risk_emoji = "🔴" if path['risk_level'] >= 8 else "🟡" if path['risk_level'] >= 5 else "🟢"
                        report += f"- {risk_emoji} **{path['path']}** (Risk: {path['risk_level']})\n"
                        report += f"  - URL: {path['url']}\n"
                        report += f"  - Status: {path['status_code']}\n"
                        report += f"  - Content-Type: {path['content_type']}\n\n"
                else:
                    report += "✅ **No exposed directories detected**\n\n"
        
        # Overall Recommendations
        report += "---\n\n## 🎯 Priority Recommendations\n\n"
        
        recommendations = []
        
        # Collect all recommendations
        if 'security_headers' in all_results and 'recommendations' in all_results['security_headers']:
            recommendations.extend(all_results['security_headers']['recommendations'])
        
        if 'vulnerabilities' in all_results and 'recommendations' in all_results['vulnerabilities']:
            recommendations.extend(all_results['vulnerabilities']['recommendations'])
        
        # Add general recommendations based on score
        if security_score < 70:
            recommendations.extend([
                "Consider implementing a Web Application Firewall (WAF)",
                "Regular security audits and penetration testing",
                "Implement proper logging and monitoring",
                "Keep all software and dependencies updated"
            ])
        
        if recommendations:
            # Remove duplicates and prioritize
            unique_recommendations = list(set(recommendations))
            for i, rec in enumerate(unique_recommendations[:10], 1):
                report += f"{i}. {rec}\n"
        else:
            report += "✅ **No critical issues found - maintain good security practices!**\n"
        
        report += f"\n---\n\n*Report generated by Reescraping Security Scanner on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report
    
    def _get_vulnerability_severity(self, vuln_type):
        """Get severity score for vulnerability type"""
        severity_map = {
            'sql_injection': 10,
            'xss': 8,
            'directory_listing': 6,
            'information_disclosure': 4
        }
        return severity_map.get(vuln_type, 5)
    
    def _get_vulnerability_description(self, vuln_type):
        """Get description for vulnerability type"""
        descriptions = {
            'sql_injection': 'Potential SQL injection vulnerability detected',
            'xss': 'Potential Cross-Site Scripting (XSS) vulnerability detected',
            'directory_listing': 'Directory listing is enabled',
            'information_disclosure': 'Server information disclosure detected'
        }
        return descriptions.get(vuln_type, 'Security vulnerability detected')
    
    def _assess_path_risk(self, path, response):
        """Assess risk level for exposed path"""
        high_risk_paths = ['/admin', '/phpmyadmin', '/.env', '/config.php']
        medium_risk_paths = ['/backup', '/wp-admin']
        
        if any(risk_path in path for risk_path in high_risk_paths):
            return 10
        elif any(risk_path in path for risk_path in medium_risk_paths):
            return 6
        elif path in ['/robots.txt', '/sitemap.xml']:
            return 2
        else:
            return 4


class SecurityScannerModule:
    """
    Module interface untuk Security Scanner
    """
    
    def __init__(self):
        self.scanner = SecurityScanner()
    
    def run(self):
        """Run security scanner module dengan interactive interface"""
        print(f"\n{Fore.CYAN}🔒 Security Scanner Configuration{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Module untuk comprehensive security analysis website{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Fitur: Security Headers, SSL Certificate, Vulnerability Detection, Directory Scanning{Style.RESET_ALL}\n")
        
        while True:
            try:
                url = input(f"{Fore.CYAN}Masukkan URL website yang akan di-scan: {Style.RESET_ALL}").strip()
                
                if not url:
                    print(f"{Fore.RED}❌ URL tidak boleh kosong!{Style.RESET_ALL}")
                    continue
                
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                # Parse domain untuk SSL check
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                
                print(f"\n{Fore.YELLOW}🚀 Memulai security scanning untuk: {url}{Style.RESET_ALL}")
                
                all_results = {}
                
                # Security Headers Analysis
                with LoadingContext("Checking security headers...", "pulse") as loading:
                    loading.update_message("Analyzing HTTP security headers...")
                    all_results['security_headers'] = self.scanner.check_security_headers(url)
                    loading.update_message("Security headers analysis completed")
                
                # SSL Certificate Analysis  
                with LoadingContext("Analyzing SSL certificate...", "pulse") as loading:
                    loading.update_message("Checking SSL/TLS configuration...")
                    all_results['ssl_certificate'] = self.scanner.analyze_ssl_certificate(domain)
                    loading.update_message("SSL certificate analysis completed")
                
                # Vulnerability Scanning
                with LoadingContext("Scanning for vulnerabilities...", "pulse") as loading:
                    loading.update_message("Checking for common security vulnerabilities...")
                    all_results['vulnerabilities'] = self.scanner.scan_vulnerabilities(url)
                    loading.update_message("Vulnerability scanning completed")
                
                # Exposed Directories Check
                with LoadingContext("Checking exposed directories...", "pulse") as loading:
                    loading.update_message("Scanning for exposed directories and files...")
                    all_results['exposed_directories'] = self.scanner.check_exposed_directories(url)
                    loading.update_message("Directory scanning completed")
                
                # Generate Report
                with LoadingContext("Generating security report...", "pulse") as loading:
                    loading.update_message("Compiling comprehensive security report...")
                    report = self.scanner.generate_security_report(url, all_results)
                    loading.update_message("Security report generated")
                
                # Save Report
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_domain = domain.replace('https://', '').replace('http://', '').replace('/', '_')
                filename = f"security_report_{safe_domain}_{timestamp}.md"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                print(f"\n{Fore.GREEN}✅ Security scanning completed!{Style.RESET_ALL}")
                print(f"{Fore.WHITE}📄 Report disimpan: {filename}{Style.RESET_ALL}")
                
                # Show summary
                if 'security_headers' in all_results and 'score' in all_results['security_headers']:
                    headers_score = all_results['security_headers']['score']
                    headers_max = all_results['security_headers']['max_score']
                    print(f"{Fore.CYAN}🔐 Security Headers: {headers_score}/{headers_max}{Style.RESET_ALL}")
                
                if 'vulnerabilities' in all_results:
                    risk_score = all_results['vulnerabilities'].get('risk_score', 0)
                    vuln_count = len(all_results['vulnerabilities'].get('vulnerabilities_found', []))
                    color = Fore.RED if risk_score > 10 else Fore.YELLOW if risk_score > 0 else Fore.GREEN
                    print(f"{color}🛡️  Vulnerabilities: {vuln_count} found (Risk Score: {risk_score}){Style.RESET_ALL}")
                
                if 'exposed_directories' in all_results:
                    exposed_count = len(all_results['exposed_directories'].get('exposed_paths', []))
                    color = Fore.RED if exposed_count > 3 else Fore.YELLOW if exposed_count > 0 else Fore.GREEN
                    print(f"{color}📁 Exposed Paths: {exposed_count} found{Style.RESET_ALL}")
                
                break
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⚠️  Operasi dibatalkan{Style.RESET_ALL}")
                return
            except Exception as e:
                print(f"\n{Fore.RED}❌ Terjadi error: {str(e)}{Style.RESET_ALL}")
                continue
        
        input(f"\n{Fore.CYAN}Tekan Enter untuk kembali ke menu utama...{Style.RESET_ALL}")


if __name__ == "__main__":
    module = SecurityScannerModule()
    module.run()