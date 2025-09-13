#!/usr/bin/env python3
"""
Loading Animation Module untuk Reescraping
Menyediakan animasi loading yang smooth dan informatif

Author: Ramaerik97
Version: 1.0.0
"""

import time
import threading
import sys
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class LoadingContext:
    """
    Context manager untuk loading animation dengan berbagai style
    """
    
    def __init__(self, message="Loading...", style="dots", color=Fore.CYAN):
        self.message = message
        self.style = style
        self.color = color
        self.is_running = False
        self.thread = None
        self.current_message = message
        
        # Animation patterns
        self.patterns = {
            'dots': ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
            'pulse': ['●', '◐', '◑', '◒', '◓', '◔', '◕', '◖', '◗', '◘'],
            'spinner': ['|', '/', '-', '\\'],
            'arrow': ['←', '↖', '↑', '↗', '→', '↘', '↓', '↙'],
            'bounce': ['⠁', '⠂', '⠄', '⠂'],
            'wave': ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃', '▁']
        }
        
    def __enter__(self):
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        
    def start(self):
        """Mulai animasi loading"""
        self.is_running = True
        self.thread = threading.Thread(target=self._animate, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Hentikan animasi loading"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=0.1)
        # Clear the line
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()
        
    def update_message(self, new_message):
        """Update pesan loading"""
        self.current_message = new_message
        
    def _animate(self):
        """Fungsi animasi yang berjalan di thread terpisah"""
        pattern = self.patterns.get(self.style, self.patterns['dots'])
        i = 0
        
        while self.is_running:
            frame = pattern[i % len(pattern)]
            # Format output dengan warna dan animasi
            output = f"\r{self.color}{frame} {self.current_message}{Style.RESET_ALL}"
            sys.stdout.write(output)
            sys.stdout.flush()
            
            time.sleep(0.1)
            i += 1
            
class ProgressTracker:
    """
    Progress tracker untuk menampilkan kemajuan dengan persentase
    """
    
    def __init__(self, total_steps, task_name="Progress", color=Fore.GREEN):
        self.total_steps = total_steps
        self.current_step = 0
        self.task_name = task_name
        self.color = color
        self.start_time = time.time()
        
    def update(self, step, message=""):
        """Update progress"""
        self.current_step = step
        percentage = (step / self.total_steps) * 100
        
        # Create progress bar
        bar_length = 30
        filled_length = int(bar_length * step // self.total_steps)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        
        # Format output
        output = f"\r{self.color}[{bar}] {percentage:.1f}% - {self.task_name}"
        if message:
            output += f" | {message}"
        output += f" ({elapsed:.1f}s){Style.RESET_ALL}"
        
        sys.stdout.write(output)
        sys.stdout.flush()
        
    def complete(self, final_message="Completed!"):
        """Tandai sebagai selesai"""
        self.update(self.total_steps, final_message)
        print()  # New line after completion
        
class SimpleSpinner:
    """
    Simple spinner untuk operasi cepat
    """
    
    def __init__(self, message="Processing..."):
        self.message = message
        self.is_running = False
        self.thread = None
        
    def start(self):
        """Mulai spinner"""
        self.is_running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()
        
    def stop(self):
        """Hentikan spinner"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=0.1)
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        sys.stdout.flush()
        
    def _spin(self):
        """Fungsi spinner"""
        chars = ['|', '/', '-', '\\']
        i = 0
        while self.is_running:
            sys.stdout.write(f'\r{Fore.YELLOW}{chars[i]} {self.message}{Style.RESET_ALL}')
            sys.stdout.flush()
            time.sleep(0.1)
            i = (i + 1) % len(chars)
            
# Utility functions
def show_loading(message, duration=2, style="dots"):
    """Tampilkan loading untuk durasi tertentu"""
    with LoadingContext(message, style) as loading:
        time.sleep(duration)
        
def show_progress(steps, task_name="Task", delay=0.5):
    """Tampilkan progress untuk sejumlah langkah"""
    progress = ProgressTracker(steps, task_name)
    for i in range(1, steps + 1):
        time.sleep(delay)
        progress.update(i, f"Step {i}")
    progress.complete()
    
if __name__ == "__main__":
    # Demo loading animations
    print(f"{Fore.CYAN}🎬 Demo Loading Animations{Style.RESET_ALL}\n")
    
    # Test different styles
    styles = ['dots', 'pulse', 'spinner', 'arrow', 'bounce', 'wave']
    
    for style in styles:
        print(f"Testing {style} style...")
        show_loading(f"Loading with {style} animation...", 2, style)
        print(f"✅ {style} completed!\n")
        
    # Test progress tracker
    print("Testing Progress Tracker...")
    show_progress(10, "Demo Task", 0.3)
    
    print(f"\n{Fore.GREEN}🎉 All animations tested successfully!{Style.RESET_ALL}")