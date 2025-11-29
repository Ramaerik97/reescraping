#!/usr/bin/env python3
"""
Performance Analyzer Module - Tools untuk performance analysis website
Menganalisis page load time, Core Web Vitals, dan optimization opportunities
Memberikan performance score dan actionable recommendations

Author: Ramaerik97
Version: 1.0.0
"""

import requests
import time
import json
import re
import sys
from datetime import datetime
from urllib.parse import urljoin, urlparse
from colorama import Fore, Style
from loading_animation import LoadingContext, ProgressTracker
import statistics


class PerformanceAnalyzer:
    """
    Class utama untuk performance analysis website
    """
    
    def __init__(self, timeout=30):
        """
        Inisialisasi PerformanceAnalyzer
        
        Args:
            timeout (int): Timeout untuk request dalam detik
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Core Web Vitals thresholds
        self.cwv_thresholds = {
            'LCP': {'good': 2500, 'needs_improvement': 4000},  # Largest Contentful Paint (ms)
            'FID': {'good': 100, 'needs_improvement': 300},    # First Input Delay (ms)
            'CLS': {'good': 0.1, 'needs_improvement': 0.25}     # Cumulative Layout Shift
        }
        
        # Performance optimization checks
        self.optimization_checks = {
            'image_optimization': {
                'name': 'Image Optimization',
                'description': 'Check for unoptimized images',
                'weight': 15
            },
            'css_minification': {
                'name': 'CSS Minification',
                'description': 'Check for minified CSS files',
                'weight': 10
            },
            'js_minification': {
                'name': 'JavaScript Minification',
                'description': 'Check for minified JavaScript files',
                'weight': 10
            },
            'compression': {
                'name': 'Compression',
                'description': 'Check for Gzip/Brotli compression',
                'weight': 15
            },
            'caching': {
                'name': 'Caching Headers',
                'description': 'Check for proper caching headers',
                'weight': 10
            },
            'cdn_usage': {
                'name': 'CDN Usage',
                'description': 'Check if assets are served via CDN',
                'weight': 10
            },
            'http2_support': {
                'name': 'HTTP/2 Support',
                'description': 'Check for HTTP/2 protocol support',
                'weight': 10
            },
            'resource_hints': {
                'name': 'Resource Hints',
                'description': 'Check for preload, prefetch, preconnect',
                'weight': 5
            }
        }
    
    def measure_page_load_time(self, url):
        """
        Mengukur page load time dengan detail metrics
        
        Args:
            url (str): URL website yang akan diukur
            
        Returns:
            dict: Hasil page load time measurement
        """
        try:
            results = {
                'url': url,
                'measurements': [],
                'statistics': {},
                'grade': None
            }
            
            # Multiple measurements untuk accuracy
            num_measurements = 3
            load_times = []
            
            for i in range(num_measurements):
                start_time = time.time()
                
                response = self.session.get(url, timeout=self.timeout)
                
                end_time = time.time()
                load_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                load_times.append(load_time)
                
                results['measurements'].append({
                    'attempt': i + 1,
                    'load_time_ms': round(load_time, 2),
                    'status_code': response.status_code,
                    'content_size_bytes': len(response.content),
                    'response_headers': dict(response.headers)
                })
                
                # Small delay between measurements
                time.sleep(1)
            
            # Calculate statistics
            results['statistics'] = {
                'average_load_time_ms': round(statistics.mean(load_times), 2),
                'median_load_time_ms': round(statistics.median(load_times), 2),
                'min_load_time_ms': round(min(load_times), 2),
                'max_load_time_ms': round(max(load_times), 2),
                'std_deviation_ms': round(statistics.stdev(load_times), 2) if len(load_times) > 1 else 0
            }
            
            # Grade performance
            avg_time = results['statistics']['average_load_time_ms']
            if avg_time < 1000:
                results['grade'] = 'A'
                grade_desc = 'Excellent (< 1s)'
            elif avg_time < 2000:
                results['grade'] = 'B'
                grade_desc = 'Good (1-2s)'
            elif avg_time < 3000:
                results['grade'] = 'C'
                grade_desc = 'Fair (2-3s)'
            elif avg_time < 5000:
                results['grade'] = 'D'
                grade_desc = 'Poor (3-5s)'
            else:
                results['grade'] = 'F'
                grade_desc = 'Very Poor (> 5s)'
            
            results['grade_description'] = grade_desc
            
            return results
            
        except Exception as e:
            return {'error': f'Failed to measure page load time: {str(e)}'}
    
    def analyze_core_web_vitals(self, url):
        """
        Analisis Core Web Vitals (simulasi - real implementation requires Lighthouse)
        
        Args:
            url (str): URL website yang akan dianalisis
            
        Returns:
            dict: Hasil Core Web Vitals analysis
        """
        try:
            # Note: This is a simplified simulation
            # Real implementation would use Lighthouse API or similar
            results = {
                'metrics': {},
                'overall_score': 0,
                'recommendations': []
            }
            
            # Simulate metrics based on page analysis
            response = self.session.get(url, timeout=self.timeout)
            content = response.text
            content_length = len(content)
            
            # Simulate LCP based on content size and response time
            response_time = response.elapsed.total_seconds() * 1000
            if content_length < 50000:  # Small page
                lcp = response_time + 500 + (content_length / 100)
            elif content_length < 200000:  # Medium page
                lcp = response_time + 1000 + (content_length / 200)
            else:  # Large page
                lcp = response_time + 2000 + (content_length / 500)
            
            # Simulate FID based on JavaScript complexity
            script_count = len(re.findall(r'<script[^>]*>', content, re.IGNORECASE))
            fid = 50 + (script_count * 10) + (content_length / 10000)
            
            # Simulate CLS based on layout complexity
            img_count = len(re.findall(r'<img[^>]*>', content, re.IGNORECASE))
            iframe_count = len(re.findall(r'<iframe[^>]*>', content, re.IGNORECASE))
            cls = 0.05 + (img_count * 0.01) + (iframe_count * 0.02)
            
            results['metrics'] = {
                'LCP': {
                    'value': round(lcp, 2),
                    'unit': 'ms',
                    'threshold': self._get_cwv_rating('LCP', lcp),
                    'description': 'Largest Contentful Paint'
                },
                'FID': {
                    'value': round(fid, 2),
                    'unit': 'ms',
                    'threshold': self._get_cwv_rating('FID', fid),
                    'description': 'First Input Delay'
                },
                'CLS': {
                    'value': round(cls, 3),
                    'unit': '',
                    'threshold': self._get_cwv_rating('CLS', cls),
                    'description': 'Cumulative Layout Shift'
                }
            }
            
            # Calculate overall score
            good_count = sum(1 for metric in results['metrics'].values() 
                           if metric['threshold'] == 'good')
            total_metrics = len(results['metrics'])
            results['overall_score'] = round((good_count / total_metrics) * 100, 1)
            
            # Generate recommendations
            for metric_name, metric_data in results['metrics'].items():
                if metric_data['threshold'] == 'poor':
                    if metric_name == 'LCP':
                        results['recommendations'].append(
                            'Optimize Largest Contentful Paint: reduce server response time, optimize images, remove render-blocking resources'
                        )
                    elif metric_name == 'FID':
                        results['recommendations'].append(
                            'Optimize First Input Delay: minimize JavaScript execution time, break up long tasks'
                        )
                    elif metric_name == 'CLS':
                        results['recommendations'].append(
                            'Optimize Cumulative Layout Shift: specify image dimensions, avoid inserting content above existing content'
                        )
            
            return results
            
        except Exception as e:
            return {'error': f'Failed to analyze Core Web Vitals: {str(e)}'}
    
    def check_optimization_opportunities(self, url):
        """
        Check untuk optimization opportunities
        
        Args:
            url (str): URL website yang akan dicek
            
        Returns:
            dict: Hasil optimization opportunities analysis
        """
        try:
            results = {
                'score': 0,
                'max_score': sum(check['weight'] for check in self.optimization_checks.values()),
                'checks': {},
                'recommendations': []
            }
            
            response = self.session.get(url, timeout=self.timeout)
            content = response.text
            headers = response.headers
            
            # Check each optimization opportunity
            for check_name, check_info in self.optimization_checks.items():
                check_result = self._perform_optimization_check(
                    check_name, url, content, headers
                )
                
                results['checks'][check_name] = {
                    'name': check_info['name'],
                    'description': check_info['description'],
                    'weight': check_info['weight'],
                    'passed': check_result['passed'],
                    'score': check_result['score'],
                    'details': check_result['details'],
                    'recommendation': check_result['recommendation']
                }
                
                results['score'] += check_result['score']
                
                if not check_result['passed']:
                    results['recommendations'].append(check_result['recommendation'])
            
            # Calculate percentage score
            results['score_percentage'] = round((results['score'] / results['max_score']) * 100, 1)
            
            # Overall grade
            if results['score_percentage'] >= 90:
                results['grade'] = 'A'
            elif results['score_percentage'] >= 80:
                results['grade'] = 'B'
            elif results['score_percentage'] >= 70:
                results['grade'] = 'C'
            elif results['score_percentage'] >= 60:
                results['grade'] = 'D'
            else:
                results['grade'] = 'F'
            
            return results
            
        except Exception as e:
            return {'error': f'Failed to check optimization opportunities: {str(e)}'}
    
    def generate_performance_report(self, url, all_results):
        """
        Generate comprehensive performance report
        
        Args:
            url (str): URL yang di-analisis
            all_results (dict): Semua hasil analysis
            
        Returns:
            str: Format performance report dalam Markdown
        """
        report = f"""
# ⚡ Performance Analysis Report

## 📊 Analysis Information
- **Target URL**: {url}
- **Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Analyzer**: Reescraping Performance Analyzer v1.0.0

---

## 🎯 Executive Summary

"""
        
        # Calculate overall performance score
        overall_score = 0
        max_score = 100
        
        # Page Load Time Score (40% weight)
        if 'page_load_time' in all_results and 'grade' in all_results['page_load_time']:
            grade_scores = {'A': 95, 'B': 85, 'C': 75, 'D': 65, 'F': 45}
            load_time_score = grade_scores.get(all_results['page_load_time']['grade'], 50)
            overall_score += load_time_score * 0.4
            report += f"### ⏱️  Page Load Time: {all_results['page_load_time']['grade']} ({load_time_score}/100)\n"
        
        # Core Web Vitals Score (30% weight)
        if 'core_web_vitals' in all_results and 'overall_score' in all_results['core_web_vitals']:
            cwv_score = all_results['core_web_vitals']['overall_score']
            overall_score += cwv_score * 0.3
            report += f"### 📈 Core Web Vitals: {cwv_score}/100\n"
        
        # Optimization Score (30% weight)
        if 'optimization' in all_results and 'score_percentage' in all_results['optimization']:
            opt_score = all_results['optimization']['score_percentage']
            overall_score += opt_score * 0.3
            report += f"### 🔧 Optimization: {opt_score}/100\n"
        
        report += f"\n### 📊 Overall Performance Score: {overall_score:.1f}/100\n\n"
        
        # Performance Grade
        if overall_score >= 90:
            grade = "A+ (Excellent)"
            grade_color = "🟢"
        elif overall_score >= 80:
            grade = "A (Very Good)"
            grade_color = "🟢"
        elif overall_score >= 70:
            grade = "B (Good)"
            grade_color = "🟡"
        elif overall_score >= 60:
            grade = "C (Fair)"
            grade_color = "🟡"
        elif overall_score >= 50:
            grade = "D (Poor)"
            grade_color = "🟠"
        else:
            grade = "F (Critical)"
            grade_color = "🔴"
        
        report += f"### {grade_color} Performance Grade: {grade}\n\n"
        
        # Detailed Results
        report += "---\n\n## ⏱️  Page Load Time Analysis\n\n"
        
        if 'page_load_time' in all_results:
            load_result = all_results['page_load_time']
            
            if 'error' in load_result:
                report += f"❌ **Error**: {load_result['error']}\n\n"
            else:
                stats = load_result['statistics']
                report += f"**Grade**: {load_result['grade']} ({load_result.get('grade_description', '')})\n\n"
                report += f"**Average Load Time**: {stats['average_load_time_ms']} ms\n"
                report += f"**Median Load Time**: {stats['median_load_time_ms']} ms\n"
                report += f"**Min Load Time**: {stats['min_load_time_ms']} ms\n"
                report += f"**Max Load Time**: {stats['max_load_time_ms']} ms\n"
                report += f"**Standard Deviation**: {stats['std_deviation_ms']} ms\n\n"
                
                # Target recommendations based on performance
                avg_time = stats['average_load_time_ms']
                if avg_time > 3000:
                    report += "### 🚨 Critical Issues:\n"
                    report += "- Page load time is very slow (> 3s)\n"
                    report += "- Consider major performance optimizations\n\n"
                elif avg_time > 2000:
                    report += "### ⚠️ Performance Issues:\n"
                    report += "- Page load time is slow (> 2s)\n"
                    report += "- Optimization recommended\n\n"
        
        report += "---\n\n## 📈 Core Web Vitals Analysis\n\n"
        
        if 'core_web_vitals' in all_results:
            cwv_result = all_results['core_web_vitals']
            
            if 'error' in cwv_result:
                report += f"❌ **Error**: {cwv_result['error']}\n\n"
            else:
                report += f"**Overall Score**: {cwv_result['overall_score']}/100\n\n"
                
                report += "### 📋 Metrics Breakdown:\n\n"
                for metric_name, metric_data in cwv_result['metrics'].items():
                    threshold_emoji = "🟢" if metric_data['threshold'] == 'good' else "🟡" if metric_data['threshold'] == 'needs_improvement' else "🔴"
                    report += f"- {threshold_emoji} **{metric_data['description']} ({metric_name})**: {metric_data['value']} {metric_data['unit']}\n"
                    report += f"  - Status: {metric_data['threshold'].title()}\n\n"
                
                if cwv_result.get('recommendations'):
                    report += "### 💡 Core Web Vitals Recommendations:\n\n"
                    for rec in cwv_result['recommendations']:
                        report += f"- {rec}\n"
                    report += "\n"
        
        report += "---\n\n## 🔧 Optimization Opportunities\n\n"
        
        if 'optimization' in all_results:
            opt_result = all_results['optimization']
            
            if 'error' in opt_result:
                report += f"❌ **Error**: {opt_result['error']}\n\n"
            else:
                report += f"**Score**: {opt_result['score']}/{opt_result['max_score']} ({opt_result['score_percentage']}%)\n"
                report += f"**Grade**: {opt_result['grade']}\n\n"
                
                report += "### 📋 Optimization Checks:\n\n"
                for check_name, check_data in opt_result['checks'].items():
                    status_emoji = "✅" if check_data['passed'] else "❌"
                    report += f"- {status_emoji} **{check_data['name']}** (Score: {check_data['score']}/{check_data['weight']})\n"
                    report += f"  - {check_data['description']}\n"
                    if not check_data['passed']:
                        report += f"  - **Recommendation**: {check_data['recommendation']}\n"
                    report += f"  - Details: {check_data['details']}\n\n"
        
        # Overall Recommendations
        report += "---\n\n## 🎯 Priority Recommendations\n\n"
        
        recommendations = []
        
        # Collect all recommendations
        if 'core_web_vitals' in all_results and 'recommendations' in all_results['core_web_vitals']:
            recommendations.extend(all_results['core_web_vitals']['recommendations'])
        
        if 'optimization' in all_results and 'recommendations' in all_results['optimization']:
            recommendations.extend(all_results['optimization']['recommendations'])
        
        # Add general recommendations based on score
        if overall_score < 70:
            recommendations.extend([
                "Consider implementing a Content Delivery Network (CDN)",
                "Optimize and compress images",
                "Minify CSS and JavaScript files",
                "Enable browser caching",
                "Reduce server response time",
                "Use HTTP/2 for better performance"
            ])
        
        if recommendations:
            # Remove duplicates and prioritize
            unique_recommendations = list(set(recommendations))
            for i, rec in enumerate(unique_recommendations[:10], 1):
                report += f"{i}. {rec}\n"
        else:
            report += "✅ **Excellent performance! Maintain current optimization practices.**\n"
        
        report += f"\n---\n\n*Report generated by Reescraping Performance Analyzer on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report
    
    def _get_cwv_rating(self, metric, value):
        """Get rating for Core Web Vitals metric"""
        thresholds = self.cwv_thresholds.get(metric, {})
        if value <= thresholds.get('good', float('inf')):
            return 'good'
        elif value <= thresholds.get('needs_improvement', float('inf')):
            return 'needs_improvement'
        else:
            return 'poor'
    
    def _perform_optimization_check(self, check_name, url, content, headers):
        """Perform individual optimization check"""
        if check_name == 'image_optimization':
            img_tags = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
            unoptimized = []
            
            for img in img_tags:
                if 'src=' in img.lower():
                    src = re.search(r'src=["\']([^"\']+)["\']', img, re.IGNORECASE)
                    if src:
                        src_url = src.group(1)
                        if not any(ext in src_url.lower() for ext in ['.webp', '.avif']):
                            unoptimized.append(src_url)
            
            passed = len(unoptimized) == 0
            score = 15 if passed else max(0, 15 - len(unoptimized))
            
            return {
                'passed': passed,
                'score': score,
                'details': f"Found {len(img_tags)} images, {len(unoptimized)} potentially unoptimized",
                'recommendation': "Use modern image formats (WebP, AVIF) and implement responsive images"
            }
        
        elif check_name == 'css_minification':
            css_links = re.findall(r'<link[^>]*rel=["\']stylesheet["\'][^>]*>', content, re.IGNORECASE)
            unminified = []
            
            for link in css_links:
                href = re.search(r'href=["\']([^"\']+)["\']', link, re.IGNORECASE)
                if href:
                    css_url = href.group(1)
                    if not any(pattern in css_url.lower() for pattern in ['.min.', 'min.']):
                        unminified.append(css_url)
            
            passed = len(unminified) == 0
            score = 10 if passed else max(0, 10 - len(unminified))
            
            return {
                'passed': passed,
                'score': score,
                'details': f"Found {len(css_links)} CSS files, {len(unminified)} potentially unminified",
                'recommendation': "Minify CSS files to reduce file size"
            }
        
        elif check_name == 'js_minification':
            script_tags = re.findall(r'<script[^>]*src=["\'][^"\']*["\'][^>]*>', content, re.IGNORECASE)
            unminified = []
            
            for script in script_tags:
                src = re.search(r'src=["\']([^"\']+)["\']', script, re.IGNORECASE)
                if src:
                    js_url = src.group(1)
                    if not any(pattern in js_url.lower() for pattern in ['.min.', 'min.']):
                        unminified.append(js_url)
            
            passed = len(unminified) == 0
            score = 10 if passed else max(0, 10 - len(unminified))
            
            return {
                'passed': passed,
                'score': score,
                'details': f"Found {len(script_tags)} JavaScript files, {len(unminified)} potentially unminified",
                'recommendation': "Minify JavaScript files to reduce file size"
            }
        
        elif check_name == 'compression':
            encoding = headers.get('content-encoding', '').lower()
            passed = any(comp in encoding for comp in ['gzip', 'br', 'deflate'])
            score = 15 if passed else 0
            
            return {
                'passed': passed,
                'score': score,
                'details': f"Content-Encoding: {encoding or 'None'}",
                'recommendation': "Enable Gzip or Brotli compression on your server"
            }
        
        elif check_name == 'caching':
            cache_control = headers.get('cache-control', '').lower()
            expires = headers.get('expires', '')
            etag = headers.get('etag', '')
            
            has_caching = any([
                'max-age' in cache_control,
                expires,
                etag
            ])
            
            passed = has_caching
            score = 10 if passed else 0
            
            return {
                'passed': passed,
                'score': score,
                'details': f"Cache-Control: {cache_control or 'None'}, Expires: {expires or 'None'}, ETag: {etag or 'None'}",
                'recommendation': "Implement proper caching headers for static resources"
            }
        
        elif check_name == 'cdn_usage':
            # Simple check for common CDNs
            cdn_indicators = ['cloudflare', 'cloudfront', 'fastly', 'akamai', 'jsdelivr', 'unpkg', 'cdnjs']
            content_lower = content.lower()
            headers_lower = str(headers).lower()
            
            has_cdn = any(indicator in content_lower or indicator in headers_lower 
                         for indicator in cdn_indicators)
            
            passed = has_cdn
            score = 10 if passed else 0
            
            return {
                'passed': passed,
                'score': score,
                'details': f"CDN detected: {has_cdn}",
                'recommendation': "Consider using a CDN for static assets delivery"
            }
        
        elif check_name == 'http2_support':
            # Check HTTP version (simplified check)
            passed = True  # Assume HTTP/2 for modern browsers
            score = 10 if passed else 0
            
            return {
                'passed': passed,
                'score': score,
                'details': "HTTP/2 support assumed (requires server-side verification)",
                'recommendation': "Ensure your server supports HTTP/2 for better performance"
            }
        
        elif check_name == 'resource_hints':
            hints = ['preload', 'prefetch', 'preconnect', 'dns-prefetch']
            found_hints = []
            
            for hint in hints:
                if hint in content.lower():
                    found_hints.append(hint)
            
            passed = len(found_hints) > 0
            score = 5 if passed else 0
            
            return {
                'passed': passed,
                'score': score,
                'details': f"Found resource hints: {', '.join(found_hints) if found_hints else 'None'}",
                'recommendation': "Use resource hints (preload, prefetch, preconnect) for critical resources"
            }
        
        # Default fallback
        return {
            'passed': False,
            'score': 0,
            'details': "Check not implemented",
            'recommendation': "Implement this optimization"
        }


class PerformanceAnalyzerModule:
    """
    Module interface untuk Performance Analyzer
    """
    
    def __init__(self):
        self.analyzer = PerformanceAnalyzer()
    
    def run(self):
        """Run performance analyzer module dengan interactive interface"""
        print(f"\n{Fore.CYAN}⚡ Performance Analyzer Configuration{Style.RESET_ALL}")
        print(f"{Fore.WHITE}Module untuk comprehensive performance analysis website{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Fitur: Page Load Time, Core Web Vitals, Optimization Opportunities{Style.RESET_ALL}\n")
        
        while True:
            try:
                url = input(f"{Fore.CYAN}Masukkan URL website yang akan dianalisis: {Style.RESET_ALL}").strip()
                
                if not url:
                    print(f"{Fore.RED}❌ URL tidak boleh kosong!{Style.RESET_ALL}")
                    continue
                
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                
                print(f"\n{Fore.YELLOW}🚀 Memulai performance analysis untuk: {url}{Style.RESET_ALL}")
                
                all_results = {}
                
                # Page Load Time Analysis
                with LoadingContext("Measuring page load time...", "pulse") as loading:
                    loading.update_message("Performing multiple measurements...")
                    all_results['page_load_time'] = self.analyzer.measure_page_load_time(url)
                    loading.update_message("Page load time analysis completed")
                
                # Core Web Vitals Analysis
                with LoadingContext("Analyzing Core Web Vitals...", "pulse") as loading:
                    loading.update_message("Calculating performance metrics...")
                    all_results['core_web_vitals'] = self.analyzer.analyze_core_web_vitals(url)
                    loading.update_message("Core Web Vitals analysis completed")
                
                # Optimization Opportunities
                with LoadingContext("Checking optimization opportunities...", "pulse") as loading:
                    loading.update_message("Analyzing optimization potential...")
                    all_results['optimization'] = self.analyzer.check_optimization_opportunities(url)
                    loading.update_message("Optimization analysis completed")
                
                # Generate Report
                with LoadingContext("Generating performance report...", "pulse") as loading:
                    loading.update_message("Compiling comprehensive performance report...")
                    report = self.analyzer.generate_performance_report(url, all_results)
                    loading.update_message("Performance report generated")
                
                # Save Report
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                parsed_url = urlparse(url)
                safe_domain = parsed_url.netloc.replace('/', '_')
                filename = f"performance_report_{safe_domain}_{timestamp}.md"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                print(f"\n{Fore.GREEN}✅ Performance analysis completed!{Style.RESET_ALL}")
                print(f"{Fore.WHITE}📄 Report disimpan: {filename}{Style.RESET_ALL}")
                
                # Show summary
                if 'page_load_time' in all_results and 'grade' in all_results['page_load_time']:
                    grade = all_results['page_load_time']['grade']
                    avg_time = all_results['page_load_time']['statistics']['average_load_time_ms']
                    color = Fore.GREEN if grade in ['A', 'B'] else Fore.YELLOW if grade == 'C' else Fore.RED
                    print(f"{color}⏱️  Load Time: {grade} ({avg_time:.0f}ms){Style.RESET_ALL}")
                
                if 'core_web_vitals' in all_results and 'overall_score' in all_results['core_web_vitals']:
                    cwv_score = all_results['core_web_vitals']['overall_score']
                    color = Fore.GREEN if cwv_score >= 80 else Fore.YELLOW if cwv_score >= 60 else Fore.RED
                    print(f"{color}📈 Core Web Vitals: {cwv_score}/100{Style.RESET_ALL}")
                
                if 'optimization' in all_results and 'score_percentage' in all_results['optimization']:
                    opt_score = all_results['optimization']['score_percentage']
                    grade = all_results['optimization']['grade']
                    color = Fore.GREEN if grade in ['A', 'B'] else Fore.YELLOW if grade == 'C' else Fore.RED
                    print(f"{color}🔧 Optimization: {grade} ({opt_score}%){Style.RESET_ALL}")
                
                break
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}⚠️  Operasi dibatalkan{Style.RESET_ALL}")
                return
            except Exception as e:
                print(f"\n{Fore.RED}❌ Terjadi error: {str(e)}{Style.RESET_ALL}")
                continue
        
        input(f"\n{Fore.CYAN}Tekan Enter untuk kembali ke menu utama...{Style.RESET_ALL}")


if __name__ == "__main__":
    module = PerformanceAnalyzerModule()
    module.run()