#!/usr/bin/env python3
"""
Loading Animation Module - Utility untuk animasi loading yang keren
Menyediakan berbagai style loading animation untuk semua module

Author: Ramaerik97
Version: 1.0.0
"""

import time
import threading
import sys
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class LoadingAnimation:
    """
    Class untuk berbagai macam loading animation yang keren
    """
    
    def __init__(self):
        self.is_loading = False
        self.loading_thread = None
        self.animation_type = 'spinner'
        self.message = 'Loading...'
        self.color = Fore.CYAN
        
    def set_config(self, animation_type='spinner', message='Loading...', color=Fore.CYAN):
        """
        Set konfigurasi loading animation
        
        Args:
            animation_type (str): Tipe animasi ('spinner', 'dots', 'progress', 'pulse', 'wave')
            message (str): Pesan yang ditampilkan
            color (str): Warna dari colorama
        """
        self.animation_type = animation_type
        self.message = message
        self.color = color
    
    def _spinner_animation(self):
        """
        Animasi spinner klasik
        """
        spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        i = 0
        while self.is_loading:
            sys.stdout.write(f'\r{self.color}{spinner_chars[i]} {self.message}{Style.RESET_ALL}')
            sys.stdout.flush()
            i = (i + 1) % len(spinner_chars)
            time.sleep(0.1)
    
    def _dots_animation(self):
        """
        Animasi dots bergerak
        """
        dots = ['   ', '.  ', '.. ', '...']
        i = 0
        while self.is_loading:
            sys.stdout.write(f'\r{self.color}{self.message}{dots[i]}{Style.RESET_ALL}')
            sys.stdout.flush()
            i = (i + 1) % len(dots)
            time.sleep(0.5)
    
    def _progress_animation(self, total_steps=20):
        """
        Animasi progress bar
        """
        step = 0
        direction = 1
        while self.is_loading:
            progress = '█' * step + '░' * (total_steps - step)
            percentage = (step / total_steps) * 100
            sys.stdout.write(f'\r{self.color}{self.message} [{progress}] {percentage:.0f}%{Style.RESET_ALL}')
            sys.stdout.flush()
            
            step += direction
            if step >= total_steps or step <= 0:
                direction *= -1
            
            time.sleep(0.1)
    
    def _pulse_animation(self):
        """
        Animasi pulse dengan intensitas berubah
        """
        pulse_chars = ['●', '◐', '◑', '◒', '◓', '◔', '◕', '◖', '◗']
        i = 0
        while self.is_loading:
            sys.stdout.write(f'\r{self.color}{pulse_chars[i]} {self.message} {pulse_chars[i]}{Style.RESET_ALL}')
            sys.stdout.flush()
            i = (i + 1) % len(pulse_chars)
            time.sleep(0.15)
    
    def _wave_animation(self):
        """
        Animasi wave yang smooth
        """
        wave_chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█', '▇', '▆', '▅', '▄', '▃', '▂']
        i = 0
        while self.is_loading:
            wave = ''.join([wave_chars[(i + j) % len(wave_chars)] for j in range(8)])
            sys.stdout.write(f'\r{self.color}{wave} {self.message} {wave}{Style.RESET_ALL}')
            sys.stdout.flush()
            i = (i + 1) % len(wave_chars)
            time.sleep(0.1)
    
    def start(self):
        """
        Mulai loading animation
        """
        if self.is_loading:
            return
        
        self.is_loading = True
        
        # Pilih animasi berdasarkan type
        if self.animation_type == 'spinner':
            animation_func = self._spinner_animation
        elif self.animation_type == 'dots':
            animation_func = self._dots_animation
        elif self.animation_type == 'progress':
            animation_func = self._progress_animation
        elif self.animation_type == 'pulse':
            animation_func = self._pulse_animation
        elif self.animation_type == 'wave':
            animation_func = self._wave_animation
        else:
            animation_func = self._spinner_animation
        
        self.loading_thread = threading.Thread(target=animation_func)
        self.loading_thread.daemon = True
        self.loading_thread.start()
    
    def stop(self, success_message=None, error_message=None):
        """
        Stop loading animation
        
        Args:
            success_message (str): Pesan sukses (opsional)
            error_message (str): Pesan error (opsional)
        """
        if not self.is_loading:
            return
        
        self.is_loading = False
        
        if self.loading_thread:
            self.loading_thread.join(timeout=0.5)
        
        # Clear loading line
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()
        
        # Show result message
        if success_message:
            print(f"{Fore.GREEN}✅ {success_message}{Style.RESET_ALL}")
        elif error_message:
            print(f"{Fore.RED}❌ {error_message}{Style.RESET_ALL}")
    
    def update_message(self, new_message):
        """
        Update pesan loading tanpa restart animasi
        
        Args:
            new_message (str): Pesan baru
        """
        self.message = new_message


class ProgressTracker:
    """
    Class untuk tracking progress dengan loading animation
    """
    
    def __init__(self, total_steps, description="Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = time.time()
        
    def update(self, step_description=None):
        """
        Update progress
        
        Args:
            step_description (str): Deskripsi step saat ini
        """
        self.current_step += 1
        percentage = (self.current_step / self.total_steps) * 100
        elapsed_time = time.time() - self.start_time
        
        # Estimasi waktu tersisa
        if self.current_step > 0:
            eta = (elapsed_time / self.current_step) * (self.total_steps - self.current_step)
            eta_str = f" | ETA: {eta:.1f}s" if eta > 1 else ""
        else:
            eta_str = ""
        
        # Progress bar visual
        bar_length = 30
        filled_length = int(bar_length * self.current_step // self.total_steps)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        # Current step description
        step_desc = f" | {step_description}" if step_description else ""
        
        # Display progress
        progress_line = f"\r{Fore.CYAN}{self.description} [{bar}] {percentage:.1f}% ({self.current_step}/{self.total_steps}){eta_str}{step_desc}{Style.RESET_ALL}"
        sys.stdout.write(progress_line)
        sys.stdout.flush()
        
        # New line when complete
        if self.current_step >= self.total_steps:
            print(f"\n{Fore.GREEN}✅ {self.description} completed in {elapsed_time:.2f}s{Style.RESET_ALL}")


# Context manager untuk loading animation yang mudah dipakai
class LoadingContext:
    """
    Context manager untuk loading animation
    
    Usage:
        with LoadingContext("Downloading files...", "wave"):
            # Do some work
            time.sleep(3)
    """
    
    def __init__(self, message="Loading...", animation_type="spinner", color=Fore.CYAN):
        self.loader = LoadingAnimation()
        self.loader.set_config(animation_type, message, color)
        self.success_message = None
        self.error_message = None
    
    def __enter__(self):
        self.loader.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.loader.stop(success_message=self.success_message)
        else:
            self.loader.stop(error_message=self.error_message or f"Error: {exc_val}")
    
    def set_success_message(self, message):
        """Set pesan sukses yang akan ditampilkan ketika selesai"""
        self.success_message = message
    
    def set_error_message(self, message):
        """Set pesan error yang akan ditampilkan jika ada error"""
        self.error_message = message
    
    def update_message(self, message):
        """Update pesan loading"""
        self.loader.update_message(message)


# Demo function untuk testing
def demo_animations():
    """
    Demo semua jenis animasi loading
    """
    animations = [
        ('spinner', 'Loading with spinner...', Fore.CYAN),
        ('dots', 'Loading with dots', Fore.YELLOW),
        ('progress', 'Loading with progress', Fore.GREEN),
        ('pulse', 'Loading with pulse', Fore.MAGENTA),
        ('wave', 'Loading with wave', Fore.BLUE)
    ]
    
    for anim_type, message, color in animations:
        print(f"\n{Fore.WHITE}Demo: {anim_type.upper()}{Style.RESET_ALL}")
        
        with LoadingContext(message, anim_type, color) as loader:
            loader.set_success_message(f"{anim_type.capitalize()} animation completed!")
            time.sleep(2)
    
    print(f"\n{Fore.WHITE}Demo: Progress Tracker{Style.RESET_ALL}")
    tracker = ProgressTracker(5, "Processing items")
    for i in range(5):
        time.sleep(0.5)
        tracker.update(f"Processing item {i+1}")


if __name__ == "__main__":
    demo_animations()