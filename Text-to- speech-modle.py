import gtts
import os
import pygame
import pyttsx3
import speech_recognition as sr
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from threading import Thread
import json
import tempfile
import shutil
import time
import random

class AdvancedTextToSpeechConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("🎵 Ultimate TTS Converter Pro")
        self.root.geometry("1100x750")
        
        # Initialize pygame mixer with proper settings
        try:
            pygame.mixer.quit()
            time.sleep(0.5)
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        except Exception as e:
            print(f"Pygame init warning: {e}")

        self.recognizer = sr.Recognizer()
        
        # Initialize pyttsx3 engine for offline TTS
        self.offline_engine = None
        self.current_voice_id = None
        self.initialize_offline_engine()

        # Load settings and history
        self.settings = self.load_settings()
        self.history = self.load_history()

        # Current audio file and playback control
        self.current_audio_file = None
        self.is_playing = False
        self.current_theme = self.settings.get("theme", "dark")
        self.is_processing = False

        # Initialize variables with safe defaults
        self.engine_var = tk.StringVar(value=self.settings.get("tts_engine", "offline"))
        self.voice_var = tk.StringVar(value=self.settings.get("default_voice", "male"))
        self.voice_tone_var = tk.StringVar(value=self.settings.get("voice_tone", "standard"))
        self.rate_var = tk.StringVar(value=self.settings.get("speech_rate", "normal"))
        self.volume_var = tk.DoubleVar(value=self.settings.get("volume", 1.0))
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "dark"))
        self.accent_color_var = tk.StringVar(value=self.settings.get("accent_color", "#00798c"))

        # Theme colors with enhanced color schemes
        self.theme_colors = {
            "dark": {
                "bg": "#1a1a2e",
                "fg": "#ffffff",
                "sidebar_bg": "#16213e",
                "text_bg": "#0f3460",
                "button_bg": "#1f4068",
                "accent": "#00798c",
                "highlight": "#00b4d8",
                "card_bg": "#2c3e50",
                "hover_bg": "#34495e",
                "border": "#3498db"
            },
            "light": {
                "bg": "#f8f9fa",
                "fg": "#2c3e50",
                "sidebar_bg": "#e9ecef",
                "text_bg": "#ffffff",
                "button_bg": "#dee2e6",
                "accent": "#197278",
                "highlight": "#1abc9c",
                "card_bg": "#ffffff",
                "hover_bg": "#e9ecef",
                "border": "#bdc3c7"
            }
        }

        self.setup_ui()
        self.apply_theme()

    def initialize_offline_engine(self):
        """Initialize or reinitialize the offline TTS engine"""
        try:
            if self.offline_engine:
                try:
                    self.offline_engine.stop()
                    del self.offline_engine
                except:
                    pass
            
            self.offline_engine = pyttsx3.init()
            self.offline_engine.setProperty('rate', 175)
            self.offline_engine.setProperty('volume', 0.9)
            self.current_voice_id = None
            print("Offline engine initialized successfully")
            return True
        except Exception as e:
            print(f"Offline engine init error: {e}")
            self.offline_engine = None
            return False

    def load_settings(self):
        """Load settings with proper error handling"""
        try:
            with open('tts_settings.json', 'r') as f:
                settings = json.load(f)
                # Ensure all required keys exist
                default_settings = {
                    "output_folder": ".",
                    "default_voice": "male",
                    "voice_tone": "standard",
                    "speech_rate": "normal",
                    "volume": 1.0,
                    "output_format": "wav",
                    "auto_play": True,
                    "theme": "dark",
                    "tts_engine": "offline",
                    "accent_color": "#00798c",
                    "auto_save": False,
                    "playback_speed": 1.0
                }
                # Merge with defaults for any missing keys
                for key, value in default_settings.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except:
            # Return default settings if file doesn't exist or is corrupted
            return {
                "output_folder": ".",
                "default_voice": "male",
                "voice_tone": "standard",
                "speech_rate": "normal",
                "volume": 1.0,
                "output_format": "wav",
                "auto_play": True,
                "theme": "dark",
                "tts_engine": "offline",
                "accent_color": "#00798c",
                "auto_save": False,
                "playback_speed": 1.0
            }

    def save_settings(self):
        try:
            # Update current settings with current values
            self.settings.update({
                "default_voice": self.voice_var.get(),
                "voice_tone": self.voice_tone_var.get(),
                "speech_rate": self.rate_var.get(),
                "volume": self.volume_var.get(),
                "theme": self.theme_var.get(),
                "tts_engine": self.engine_var.get(),
                "accent_color": self.accent_color_var.get()
            })
            
            with open('tts_settings.json', 'w') as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False

    def load_history(self):
        """Load history with proper error handling and ensure timestamp field exists"""
        try:
            with open('tts_history.json', 'r') as f:
                history = json.load(f)
                # Ensure each history entry has required fields including timestamp
                for entry in history:
                    if 'voice' not in entry:
                        entry['voice'] = 'male'
                    if 'tone' not in entry:
                        entry['tone'] = 'standard'
                    if 'timestamp' not in entry:
                        entry['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return history
        except:
            return []

    def save_history(self):
        try:
            with open('tts_history.json', 'w') as f:
                json.dump(self.history[-50:], f, indent=4)
        except Exception as e:
            print(f"Error saving history: {e}")

    def safe_stop_audio(self):
        """Safely stop any currently playing audio"""
        try:
            self.is_playing = False
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            time.sleep(0.2)
        except Exception as e:
            print(f"Error stopping audio: {e}")

    def play_audio_safe(self, audio_file):
        """Safe audio playback with proper cleanup"""
        try:
            self.safe_stop_audio()
            
            if not os.path.exists(audio_file):
                print("Audio file does not exist")
                return False
                
            file_size = os.path.getsize(audio_file)
            if file_size < 1000:
                print(f"Audio file too small: {file_size} bytes")
                return False
                
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.set_volume(self.volume_var.get())
            pygame.mixer.music.play()
            
            self.is_playing = True
            print("Audio playback started")
            
            def monitor_playback():
                try:
                    start_time = time.time()
                    while self.is_playing and time.time() - start_time < 60:
                        if not pygame.mixer.music.get_busy():
                            break
                        time.sleep(0.1)
                    self.is_playing = False
                    print("Playback finished")
                except Exception as e:
                    print(f"Playback monitoring error: {e}")
                    self.is_playing = False
            
            Thread(target=monitor_playback, daemon=True).start()
            return True
            
        except Exception as e:
            print(f"Playback error: {e}")
            self.is_playing = False
            return False

    def get_voice_id(self, voice_type, voice_tone="standard"):
        """Get voice ID for the specified voice type and tone"""
        if not self.offline_engine:
            if not self.initialize_offline_engine():
                return None
        
        try:
            voices = self.offline_engine.getProperty('voices')
            print(f"Available voices: {[voice.name for voice in voices]}")
            
            voice_preferences = {
                "male": {
                    "standard": ['david', 'mark', 'microsoft david desktop'],
                    "deep": ['david', 'mark'],
                    "warm": ['david'],
                    "crystal": ['mark']
                },
                "female": {
                    "standard": ['zira', 'eva', 'hazel'],
                    "peach": ['hazel', 'eva', 'zira'],
                    "soothing": ['hazel', 'eva'],
                    "crystal": ['zira', 'hazel'],
                    "soft": ['hazel', 'eva']
                }
            }
            
            preferred_voices = voice_preferences.get(voice_type, {}).get(voice_tone, [])
            
            # First try preferred voices for this tone
            for preferred in preferred_voices:
                for voice in voices:
                    if preferred in voice.name.lower():
                        print(f"Found preferred {voice_type} voice for {voice_tone} tone: {voice.name}")
                        return voice.id
            
            # Fallback to any voice of the requested gender
            for voice in voices:
                if voice_type == "male" and any(indicator in voice.name.lower() for indicator in ['male', 'david', 'mark']):
                    print(f"Found fallback male voice: {voice.name}")
                    return voice.id
                elif voice_type == "female" and any(indicator in voice.name.lower() for indicator in ['female', 'zira', 'hazel', 'eva']):
                    print(f"Found fallback female voice: {voice.name}")
                    return voice.id
            
            # Ultimate fallback
            if len(voices) > 0:
                print(f"Using ultimate fallback voice: {voices[0].name}")
                return voices[0].id
            
            return None
        except Exception as e:
            print(f"Error getting voice ID: {e}")
            return None

    def apply_voice_tone_settings(self, voice_tone):
        """Apply specific settings based on voice tone selection"""
        if not self.offline_engine:
            return
            
        base_rate = 175
        base_volume = self.volume_var.get()
        
        tone_settings = {
            "standard": {"rate": base_rate, "volume": base_volume},
            "peach": {"rate": base_rate - 25, "volume": base_volume},
            "soothing": {"rate": base_rate - 40, "volume": base_volume - 0.1},
            "crystal": {"rate": base_rate + 15, "volume": base_volume + 0.1},
            "deep": {"rate": base_rate - 15, "volume": base_volume + 0.05},
            "soft": {"rate": base_rate - 30, "volume": base_volume - 0.15},
            "warm": {"rate": base_rate - 20, "volume": base_volume}
        }
        
        settings = tone_settings.get(voice_tone, tone_settings["standard"])
        self.offline_engine.setProperty('rate', settings["rate"])
        self.offline_engine.setProperty('volume', max(0.1, min(1.0, settings["volume"])))

    def generate_with_offline_tts(self, text, voice_type, output_file, voice_tone="standard"):
        """Use pyttsx3 for offline TTS with proper voice selection and tone settings"""
        try:
            # Get voice ID for the requested voice type and tone
            voice_id = self.get_voice_id(voice_type, voice_tone)
            if not voice_id:
                print(f"No voice found for type: {voice_type}")
                return False
            
            # Reinitialize engine to ensure clean state
            if not self.initialize_offline_engine():
                return False
            
            # Set voice properties
            self.offline_engine.setProperty('voice', voice_id)
            
            # Apply voice tone settings
            self.apply_voice_tone_settings(voice_tone)
            
            # Apply speech rate on top of tone settings
            base_rate = self.offline_engine.getProperty('rate')
            rate_setting = self.rate_var.get()
            if rate_setting == "slow":
                self.offline_engine.setProperty('rate', max(80, base_rate - 40))
            elif rate_setting == "fast":
                self.offline_engine.setProperty('rate', base_rate + 40)
            
            # Ensure WAV format
            if not output_file.endswith('.wav'):
                output_file = output_file.rsplit('.', 1)[0] + '.wav'
            
            print(f"Generating {voice_type} voice with {voice_tone} tone for text: {text[:50]}...")
            
            # Generate audio
            self.offline_engine.save_to_file(text, output_file)
            self.offline_engine.runAndWait()
            
            # Wait for file to be written
            time.sleep(1.0)
            
            # Verify file
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"Audio file created: {output_file} ({file_size} bytes)")
                return file_size > 1000
            else:
                print("Audio file was not created")
                return False
                
        except Exception as e:
            print(f"Offline TTS error: {e}")
            return False

    def setup_ui(self):
        main_container = tk.Frame(self.root, bg=self.theme_colors[self.current_theme]["bg"])
        main_container.pack(fill=tk.BOTH, expand=True)

        self.setup_sidebar(main_container)
        self.setup_main_content(main_container)
        self.setup_status_bar()

    def create_hover_button(self, parent, text, command, bg_color, hover_color, **kwargs):
        """Create a button with hover effect"""
        btn = tk.Button(parent, text=text, command=command, bg=bg_color, 
                       fg='white', font=('Segoe UI', 10, 'bold'),
                       relief=tk.RAISED, bd=2, cursor='hand2', **kwargs)
        
        def on_enter(e):
            btn.configure(bg=hover_color, relief=tk.SUNKEN)
        
        def on_leave(e):
            btn.configure(bg=bg_color, relief=tk.RAISED)
            
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn

    def setup_sidebar(self, parent):
        colors = self.theme_colors[self.current_theme]
        sidebar = tk.Frame(parent, width=220, bg=colors["sidebar_bg"])
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        sidebar.pack_propagate(False)

        title_label = tk.Label(sidebar, text="🎵 TTS Pro Ultra", font=('Segoe UI', 16, 'bold'),
                               bg=colors["sidebar_bg"], fg=colors["fg"])
        title_label.pack(fill=tk.X, pady=(15, 20))

        nav_buttons = [
            ("🎤 Text-to-Speech", self.show_tts_tab, '#3498db', '#2980b9'),
            ("🎭 Voice Studio", self.show_voice_tab, '#9b59b6', '#8e44ad'),
            ("📜 History", self.show_history_tab, '#e67e22', '#d35400'),
            ("⚙️ Settings", self.show_settings_tab, '#95a5a6', '#7f8c8d'),
            ("⚡ Quick Actions", self.show_quick_actions, '#f39c12', '#e67e22')
        ]
        for text, command, color, hover_color in nav_buttons:
            btn = self.create_hover_button(sidebar, text, command, color, hover_color)
            btn.configure(anchor='w', font=('Segoe UI', 11))
            btn.pack(fill=tk.X, pady=3, padx=8)

    def setup_main_content(self, parent):
        colors = self.theme_colors[self.current_theme]
        
        # Style configuration for ttk widgets
        style = ttk.Style()
        style.theme_use('clam')  # Use a basic theme that works on all systems
        
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.setup_tts_tab()
        self.setup_voice_tab()
        self.setup_history_tab()
        self.setup_settings_tab()

    def setup_tts_tab(self):
        colors = self.theme_colors[self.current_theme]
        tts_tab = tk.Frame(self.notebook, bg=colors["bg"])
        self.notebook.add(tts_tab, text="🎤 Text-to-Speech")

        # Text input with enhanced styling
        input_frame = tk.Frame(tts_tab, bg=colors["bg"], pady=10)
        input_frame.pack(fill=tk.BOTH, expand=True)

        text_label = tk.Label(input_frame, text="Enter your text below:", font=('Segoe UI', 11, 'bold'),
                             bg=colors["bg"], fg=colors["fg"])
        text_label.pack(anchor='w', padx=10, pady=(0, 5))

        self.text_area = scrolledtext.ScrolledText(input_frame, height=15, font=('Segoe UI', 12), 
                                                   wrap=tk.WORD, bg=colors["text_bg"], fg=colors["fg"], 
                                                   insertbackground=colors["fg"], selectbackground=colors["accent"],
                                                   relief=tk.RAISED, bd=2)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.text_area.insert(tk.END, "Enter your text here and click Generate & Play. You can type anything you want to convert to speech.")

        # Control buttons frame
        control_frame = tk.Frame(tts_tab, bg=colors["bg"])
        control_frame.pack(fill=tk.X, padx=10, pady=10)

        # Main action buttons
        button_frame = tk.Frame(control_frame, bg=colors["bg"])
        button_frame.pack(fill=tk.X, pady=5)

        buttons = [
            ("🎵 Generate & Play", self.generate_and_play, '#27ae60', '#229954'),
            ("▶️ Play", self.play_audio, '#2980b9', '#2471a3'),
            ("⏹ Stop", self.stop_audio, '#c0392b', '#a93226'),
            ("💾 Save Audio", self.save_audio, '#8e44ad', '#7d3c98'),
        ]
        for text, command, color, hover_color in buttons:
            btn = self.create_hover_button(button_frame, text, command, color, hover_color)
            btn.pack(side=tk.LEFT, padx=4, pady=4)

        # Quick text buttons
        quick_text_frame = tk.Frame(control_frame, bg=colors["bg"])
        quick_text_frame.pack(fill=tk.X, pady=5)

        tk.Label(quick_text_frame, text="Quick Text:", font=('Segoe UI', 10, 'bold'),
                bg=colors["bg"], fg=colors["fg"]).pack(side=tk.LEFT, padx=(0, 10))

        quick_texts = [
            ("Hello World", "Hello, welcome to the ultimate text to speech converter!"),
            ("Test Voice", "This is a test of the current voice settings and tone quality."),
            ("Long Text", "This is a longer text to test how the text to speech converter handles extended content with proper pacing and natural sounding speech."),
            ("Clear", "")
        ]
        
        for text, content in quick_texts:
            btn = self.create_hover_button(quick_text_frame, text, 
                                         lambda c=content: self.insert_quick_text(c),
                                         colors["button_bg"], colors["hover_bg"])
            btn.configure(font=('Segoe UI', 8), fg=colors["fg"])
            btn.pack(side=tk.LEFT, padx=2)

    def setup_settings_tab(self):
        colors = self.theme_colors[self.current_theme]
        settings_tab = tk.Frame(self.notebook, bg=colors["bg"])
        self.notebook.add(settings_tab, text="⚙️ Settings")

        # Create scrollable frame for settings
        canvas = tk.Canvas(settings_tab, bg=colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(settings_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=colors["bg"])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # App Theme Section
        theme_frame = tk.LabelFrame(scrollable_frame, text="🎨 App Theme & Colors", font=('Segoe UI', 12, 'bold'),
                                  bg=colors["card_bg"], fg=colors["fg"], padx=15, pady=15,
                                  relief=tk.RAISED, bd=2)
        theme_frame.pack(fill=tk.X, padx=20, pady=10)

        # Theme selection
        theme_selection_frame = tk.Frame(theme_frame, bg=colors["card_bg"])
        theme_selection_frame.pack(fill=tk.X, pady=10)

        tk.Label(theme_selection_frame, text="App Theme:", bg=colors["card_bg"], fg=colors["fg"],
                font=('Segoe UI', 10)).pack(side=tk.LEFT)

        themes = [("🌙 Dark Mode", "dark"), ("☀️ Light Mode", "light")]
        for text, theme in themes:
            rb = tk.Radiobutton(theme_selection_frame, text=text, variable=self.theme_var, value=theme,
                               bg=colors["card_bg"], fg=colors["fg"], selectcolor=colors["highlight"], 
                               font=('Segoe UI', 10), command=self.apply_theme)
            rb.pack(side=tk.LEFT, padx=15)

        # Accent Color Selection
        color_frame = tk.Frame(theme_frame, bg=colors["card_bg"])
        color_frame.pack(fill=tk.X, pady=15)

        tk.Label(color_frame, text="Accent Color:", bg=colors["card_bg"], fg=colors["fg"],
                font=('Segoe UI', 10)).pack(side=tk.LEFT)

        # Color options with your specified colors
        color_options = [
            ("#00798c", "Ocean Blue"),
            ("#b392ac", "Lavender Purple"), 
            ("#197278", "Forest Green"),
            ("#e5989b", "Blush Pink"),
            ("#f4a261", "Sunset Orange"),
            ("#2a9d8f", "Jungle Green")
        ]

        color_buttons_frame = tk.Frame(color_frame, bg=colors["card_bg"])
        color_buttons_frame.pack(side=tk.LEFT, padx=10)

        for color_code, color_name in color_options:
            color_btn = tk.Radiobutton(color_buttons_frame, text=color_name, 
                                      variable=self.accent_color_var, value=color_code,
                                      bg=colors["card_bg"], fg=color_code, selectcolor=color_code,
                                      font=('Segoe UI', 9),
                                      command=self.apply_accent_color)
            color_btn.pack(side=tk.LEFT, padx=8)

            # Add color preview
            preview_frame = tk.Frame(color_buttons_frame, width=20, height=20, bg=color_code,
                                   relief='raised', bd=1)
            preview_frame.pack(side=tk.LEFT, padx=2)
            preview_frame.pack_propagate(False)

        # Color Preview
        preview_frame = tk.Frame(theme_frame, bg=colors["card_bg"])
        preview_frame.pack(fill=tk.X, pady=10)

        tk.Label(preview_frame, text="Preview:", bg=colors["card_bg"], fg=colors["fg"],
                font=('Segoe UI', 10)).pack(side=tk.LEFT)

        self.color_preview = tk.Frame(preview_frame, width=100, height=30, 
                                     bg=self.accent_color_var.get(), relief='sunken', bd=2)
        self.color_preview.pack(side=tk.LEFT, padx=10)
        self.color_preview.pack_propagate(False)

        tk.Label(self.color_preview, text="Accent Color", bg=self.accent_color_var.get(), 
                fg='white', font=('Segoe UI', 9, 'bold')).pack(expand=True)

        # Audio Settings Section
        audio_frame = tk.LabelFrame(scrollable_frame, text="🔊 Audio Settings", font=('Segoe UI', 12, 'bold'),
                                  bg=colors["card_bg"], fg=colors["fg"], padx=15, pady=15,
                                  relief=tk.RAISED, bd=2)
        audio_frame.pack(fill=tk.X, padx=20, pady=10)

        # Volume control
        volume_setting_frame = tk.Frame(audio_frame, bg=colors["card_bg"])
        volume_setting_frame.pack(fill=tk.X, pady=8)

        tk.Label(volume_setting_frame, text="Master Volume:", bg=colors["card_bg"], fg=colors["fg"],
                font=('Segoe UI', 10)).pack(side=tk.LEFT)

        volume_scale = tk.Scale(volume_setting_frame, from_=0.1, to=1.0, resolution=0.1,
                               orient=tk.HORIZONTAL, variable=self.volume_var,
                               bg=colors["card_bg"], fg=colors["fg"], highlightthickness=0,
                               length=200, showvalue=True, troughcolor=colors["sidebar_bg"])
        volume_scale.pack(side=tk.LEFT, padx=10)

        # Auto-play setting
        auto_play_var = tk.BooleanVar(value=self.settings.get("auto_play", True))
        
        auto_play_frame = tk.Frame(audio_frame, bg=colors["card_bg"])
        auto_play_frame.pack(fill=tk.X, pady=8)

        cb = tk.Checkbutton(auto_play_frame, text="Auto-play after generation", 
                           variable=auto_play_var, bg=colors["card_bg"], fg=colors["fg"],
                           selectcolor=colors["highlight"], font=('Segoe UI', 10))
        cb.pack(side=tk.LEFT)

        # Application Settings Section
        app_frame = tk.LabelFrame(scrollable_frame, text="📱 Application Settings", font=('Segoe UI', 12, 'bold'),
                                bg=colors["card_bg"], fg=colors["fg"], padx=15, pady=15,
                                relief=tk.RAISED, bd=2)
        app_frame.pack(fill=tk.X, padx=20, pady=10)

        # Output format
        format_frame = tk.Frame(app_frame, bg=colors["card_bg"])
        format_frame.pack(fill=tk.X, pady=8)

        tk.Label(format_frame, text="Output Format:", bg=colors["card_bg"], fg=colors["fg"],
                font=('Segoe UI', 10)).pack(side=tk.LEFT)

        format_var = tk.StringVar(value=self.settings.get("output_format", "wav"))
        formats = [("WAV", "wav"), ("MP3", "mp3")]
        for text, fmt in formats:
            rb = tk.Radiobutton(format_frame, text=text, variable=format_var, value=fmt,
                               bg=colors["card_bg"], fg=colors["fg"], selectcolor=colors["highlight"],
                               font=('Segoe UI', 9))
            rb.pack(side=tk.LEFT, padx=10)

        # Auto-save setting
        auto_save_var = tk.BooleanVar(value=self.settings.get("auto_save", False))
        
        auto_save_frame = tk.Frame(app_frame, bg=colors["card_bg"])
        auto_save_frame.pack(fill=tk.X, pady=8)

        cb = tk.Checkbutton(auto_save_frame, text="Auto-save generated audio", 
                           variable=auto_save_var, bg=colors["card_bg"], fg=colors["fg"],
                           selectcolor=colors["highlight"], font=('Segoe UI', 10))
        cb.pack(side=tk.LEFT)

        # Reset Settings Section
        reset_frame = tk.LabelFrame(scrollable_frame, text="🔄 Reset & Actions", font=('Segoe UI', 12, 'bold'),
                                  bg=colors["card_bg"], fg=colors["fg"], padx=15, pady=15,
                                  relief=tk.RAISED, bd=2)
        reset_frame.pack(fill=tk.X, padx=20, pady=10)

        # Action buttons
        action_buttons_frame = tk.Frame(reset_frame, bg=colors["card_bg"])
        action_buttons_frame.pack(fill=tk.X, pady=10)

        actions = [
            ("💾 Save Settings", self.save_settings, '#27ae60', '#229954'),
            ("🔄 Reset to Defaults", self.reset_settings, '#e74c3c', '#c0392b'),
            ("🗑️ Clear All History", self.clear_all_history, '#f39c12', '#e67e22'),
            ("📊 Export Settings", self.export_settings, '#3498db', '#2980b9')
        ]

        for i, (text, command, color, hover_color) in enumerate(actions):
            btn = self.create_hover_button(action_buttons_frame, text, command, color, hover_color)
            btn.configure(font=('Segoe UI', 9, 'bold'))
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky='ew')
            action_buttons_frame.columnconfigure(i%2, weight=1)

        # Settings status
        self.settings_status = tk.Label(scrollable_frame, text="Settings will be applied automatically", 
                                       bg=colors["bg"], fg='#2ecc71', font=('Segoe UI', 10))
        self.settings_status.pack(pady=10)

    def apply_accent_color(self):
        """Apply the selected accent color"""
        color = self.accent_color_var.get()
        self.color_preview.config(bg=color)
        for widget in self.color_preview.winfo_children():
            widget.config(bg=color)
        self.save_settings()
        self.settings_status.config(text="✓ Accent color updated!")

    def apply_theme(self):
        """Apply the selected theme to all widgets"""
        theme = self.theme_var.get()
        self.current_theme = theme
        colors = self.theme_colors[theme]
        
        print(f"Applying {theme} theme...")
        
        # Apply to main window and main container
        self.root.configure(bg=colors["bg"])
        
        # Update all frames and widgets
        self.update_widget_colors(self.root, colors)
        
        # Save theme preference
        self.save_settings()
        self.settings_status.config(text="✓ Theme updated!")
        
        print(f"Theme applied: {theme}")

    def update_widget_colors(self, parent, colors):
        """Recursively update colors for all widgets"""
        try:
            # Get all children of the parent widget
            children = parent.winfo_children()
            
            for child in children:
                widget_type = child.winfo_class()
                
                # Update Frame widgets
                if widget_type in ['Frame', 'Labelframe', 'LabelFrame', 'TFrame']:
                    try:
                        if 'card' in str(child).lower() or hasattr(child, '_is_card'):
                            child.configure(bg=colors["card_bg"])
                        else:
                            child.configure(bg=colors["bg"])
                    except:
                        pass
                
                # Update Label widgets
                elif widget_type == 'Label':
                    try:
                        # Don't change button labels or special labels
                        if not hasattr(child, 'is_button_label'):
                            if 'card' in str(child.winfo_parent()).lower():
                                child.configure(bg=colors["card_bg"], fg=colors["fg"])
                            else:
                                child.configure(bg=colors["bg"], fg=colors["fg"])
                    except:
                        pass
                
                # Update Text widgets
                elif widget_type == 'Text':
                    try:
                        child.configure(bg=colors["text_bg"], fg=colors["fg"],
                                      insertbackground=colors["fg"])
                    except:
                        pass
                
                # Update Button widgets
                elif widget_type == 'Button':
                    # Buttons keep their original colors, only update if they use theme colors
                    try:
                        current_bg = child.cget('bg')
                        if current_bg in ['#34495e', '#2c3e50', '#95a5a6', '#dee2e6']:
                            child.configure(bg=colors["button_bg"], fg=colors["fg"])
                    except:
                        pass
                
                # Update Checkbutton and Radiobutton widgets
                elif widget_type in ['Checkbutton', 'Radiobutton']:
                    try:
                        if 'card' in str(child.winfo_parent()).lower():
                            child.configure(bg=colors["card_bg"], fg=colors["fg"],
                                          selectcolor=colors["highlight"])
                        else:
                            child.configure(bg=colors["bg"], fg=colors["fg"],
                                          selectcolor=colors["highlight"])
                    except:
                        pass
                
                # Update Scale widgets
                elif widget_type == 'Scale':
                    try:
                        child.configure(bg=colors["bg"], fg=colors["fg"], 
                                       troughcolor=colors["sidebar_bg"])
                    except:
                        pass
                
                # Update Canvas widgets
                elif widget_type == 'Canvas':
                    try:
                        child.configure(bg=colors["bg"])
                    except:
                        pass
                
                # Recursively update children
                self.update_widget_colors(child, colors)
                
        except Exception as e:
            print(f"Error updating widget colors: {e}")

    def reset_settings(self):
        """Reset all settings to default"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to default?"):
            self.voice_var.set("male")
            self.voice_tone_var.set("standard")
            self.rate_var.set("normal")
            self.volume_var.set(1.0)
            self.theme_var.set("dark")
            self.engine_var.set("offline")
            self.accent_color_var.set("#00798c")
            
            self.apply_theme()
            self.apply_accent_color()
            self.save_settings()
            
            self.settings_status.config(text="✓ All settings reset to defaults!")

    def clear_all_history(self):
        """Clear all history"""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all history? This cannot be undone."):
            self.history.clear()
            self.save_history()
            self.refresh_history_display()
            self.settings_status.config(text="✓ All history cleared!")

    def export_settings(self):
        """Export settings to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Settings"
        )
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.settings, f, indent=4)
                self.settings_status.config(text=f"✓ Settings exported to {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Could not export settings: {e}")

    def insert_quick_text(self, text):
        """Insert quick text into text area"""
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, text)

    def setup_voice_tab(self):
        colors = self.theme_colors[self.current_theme]
        voice_tab = tk.Frame(self.notebook, bg=colors["bg"])
        self.notebook.add(voice_tab, text="🎭 Voice Studio")

        # Create scrollable frame for voice settings
        canvas = tk.Canvas(voice_tab, bg=colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(voice_tab, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=colors["bg"])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Voice Type Selection
        voice_frame = tk.LabelFrame(self.scrollable_frame, text="🎙️ Voice Type", font=('Segoe UI', 12, 'bold'), 
                                  bg=colors["card_bg"], fg=colors["fg"], padx=15, pady=15,
                                  relief=tk.RAISED, bd=2)
        voice_frame.pack(fill=tk.X, padx=20, pady=10)

        voices = [
            ("👨 Male Voice", "male", "Deep and clear masculine voice"),
            ("👩 Female Voice", "female", "Soft and clear feminine voice")
        ]
        
        for i, (text, val, desc) in enumerate(voices):
            frame = tk.Frame(voice_frame, bg=colors["card_bg"])
            frame.grid(row=i, column=0, sticky='w', pady=8)
            
            rb = tk.Radiobutton(frame, text=text, variable=self.voice_var, value=val,
                                bg=colors["card_bg"], fg=colors["fg"], selectcolor=colors["highlight"], 
                                font=('Segoe UI', 11), anchor='w')
            rb.pack(side=tk.LEFT)
            
            desc_label = tk.Label(frame, text=desc, bg=colors["card_bg"], fg='lightgray',
                                 font=('Segoe UI', 9))
            desc_label.pack(side=tk.LEFT, padx=(10, 0))

        # Voice Tone Selection - Enhanced
        tone_frame = tk.LabelFrame(self.scrollable_frame, text="🎨 Voice Tone & Style", font=('Segoe UI', 12, 'bold'), 
                                 bg=colors["card_bg"], fg=colors["fg"], padx=15, pady=15,
                                 relief=tk.RAISED, bd=2)
        tone_frame.pack(fill=tk.X, padx=20, pady=10)

        tones = [
            ("🔊 Standard", "standard", "Balanced natural voice", "#3498db"),
            ("🍑 Peach Soft", "peach", "Warm and gentle tone", "#e74c3c"),
            ("💆 Soothing", "soothing", "Calm and relaxing voice", "#9b59b6"),
            ("💎 Crystal Clear", "crystal", "Sharp and clear pronunciation", "#1abc9c"),
            ("🌙 Deep Voice", "deep", "Rich and deep tone", "#34495e"),
            ("☁️ Soft Whisper", "soft", "Soft and gentle whisper-like", "#95a5a6")
        ]
        
        # Create 2 columns for tones
        tone_col1 = tk.Frame(tone_frame, bg=colors["card_bg"])
        tone_col1.grid(row=0, column=0, padx=10, pady=5, sticky='w')
        
        tone_col2 = tk.Frame(tone_frame, bg=colors["card_bg"])
        tone_col2.grid(row=0, column=1, padx=10, pady=5, sticky='w')
        
        for i, (text, tone, desc, color) in enumerate(tones):
            col = tone_col1 if i < 3 else tone_col2
            row = i % 3
            
            frame = tk.Frame(col, bg=colors["card_bg"])
            frame.pack(fill='x', pady=8)
            
            rb = tk.Radiobutton(frame, text=text, variable=self.voice_tone_var, value=tone,
                               bg=colors["card_bg"], fg=color, selectcolor=colors["highlight"], 
                               font=('Segoe UI', 10, 'bold'), anchor='w')
            rb.pack(side=tk.LEFT)
            
            desc_label = tk.Label(frame, text=desc, bg=colors["card_bg"], fg='lightgray',
                                 font=('Segoe UI', 8))
            desc_label.pack(side=tk.LEFT, padx=(8, 0))

        # Engine selection
        engine_frame = tk.LabelFrame(self.scrollable_frame, text="🚀 TTS Engine", font=('Segoe UI', 12, 'bold'), 
                                   bg=colors["card_bg"], fg=colors["fg"], padx=15, pady=15,
                                   relief=tk.RAISED, bd=2)
        engine_frame.pack(fill=tk.X, padx=20, pady=10)

        engines = [
            ("🌐 Online (gTTS)", "online", "High quality cloud-based voices"),
            ("💻 Offline (System)", "offline", "Fast system voices with tone control")
        ]
        
        for i, (text, engine, desc) in enumerate(engines):
            frame = tk.Frame(engine_frame, bg=colors["card_bg"])
            frame.grid(row=i, column=0, sticky='w', pady=8)
            
            rb = tk.Radiobutton(frame, text=text, variable=self.engine_var, value=engine,
                               bg=colors["card_bg"], fg=colors["fg"], selectcolor=colors["highlight"], 
                               font=('Segoe UI', 11), anchor='w')
            rb.pack(side=tk.LEFT)
            
            desc_label = tk.Label(frame, text=desc, bg=colors["card_bg"], fg='lightgray',
                                 font=('Segoe UI', 9))
            desc_label.pack(side=tk.LEFT, padx=(10, 0))

        # Voice Controls Frame
        controls_frame = tk.LabelFrame(self.scrollable_frame, text="🎛️ Voice Controls", font=('Segoe UI', 12, 'bold'),
                                     bg=colors["card_bg"], fg=colors["fg"], padx=15, pady=15,
                                     relief=tk.RAISED, bd=2)
        controls_frame.pack(fill=tk.X, padx=20, pady=10)

        # Speech rate selection
        rate_frame = tk.Frame(controls_frame, bg=colors["card_bg"])
        rate_frame.pack(fill=tk.X, pady=8)

        tk.Label(rate_frame, text="Speech Speed:", bg=colors["card_bg"], fg=colors["fg"],
                font=('Segoe UI', 10)).pack(side=tk.LEFT)

        speeds = [("🐢 Slow", "slow"), ("🚶 Normal", "normal"), ("🐇 Fast", "fast")]
        for text, val in speeds:
            rb = tk.Radiobutton(rate_frame, text=text, variable=self.rate_var, value=val,
                               bg=colors["card_bg"], fg=colors["fg"], selectcolor=colors["highlight"], 
                               font=('Segoe UI', 9))
            rb.pack(side=tk.LEFT, padx=15)

        # Volume control
        volume_frame = tk.Frame(controls_frame, bg=colors["card_bg"])
        volume_frame.pack(fill=tk.X, pady=8)

        tk.Label(volume_frame, text="Volume:", bg=colors["card_bg"], fg=colors["fg"],
                font=('Segoe UI', 10)).pack(side=tk.LEFT)

        volume_scale = tk.Scale(volume_frame, from_=0.1, to=1.0, resolution=0.1,
                               orient=tk.HORIZONTAL, variable=self.volume_var,
                               bg=colors["card_bg"], fg=colors["fg"], highlightthickness=0,
                               length=200, troughcolor=colors["sidebar_bg"])
        volume_scale.pack(side=tk.LEFT, padx=10)
        volume_scale.set(self.volume_var.get())

        # Test buttons frame
        test_frame = tk.LabelFrame(self.scrollable_frame, text="🔊 Voice Testing", font=('Segoe UI', 12, 'bold'),
                                 bg=colors["card_bg"], fg=colors["fg"], padx=15, pady=15,
                                 relief=tk.RAISED, bd=2)
        test_frame.pack(fill=tk.X, padx=20, pady=10)

        test_buttons = [
            ("🔊 Test Current Voice", self.test_current_voice, '#3498db', '#2980b9'),
            ("🍑 Test Peach Tone", lambda: self.test_specific_tone("peach"), '#e74c3c', '#c0392b'),
            ("💆 Test Soothing", lambda: self.test_specific_tone("soothing"), '#9b59b6', '#8e44ad'),
            ("💎 Test Crystal", lambda: self.test_specific_tone("crystal"), '#1abc9c', '#16a085'),
            ("🔄 Reset Engine", self.initialize_offline_engine, '#f39c12', '#e67e22')
        ]

        test_btn_frame = tk.Frame(test_frame, bg=colors["card_bg"])
        test_btn_frame.pack(fill=tk.X)

        for i, (text, command, color, hover_color) in enumerate(test_buttons):
            btn = self.create_hover_button(test_btn_frame, text, command, color, hover_color)
            btn.configure(font=('Segoe UI', 9, 'bold'))
            btn.grid(row=i//3, column=i%3, padx=5, pady=5, sticky='ew')
            test_btn_frame.columnconfigure(i%3, weight=1)

        self.test_status = tk.Label(test_frame, text="🎯 Select settings and test different voice tones", 
                                   bg=colors["card_bg"], fg='#f1c40f', font=('Segoe UI', 10, 'bold'))
        self.test_status.pack(pady=10)

        # Info frame
        info_frame = tk.LabelFrame(self.scrollable_frame, text="💡 Pro Tips", font=('Segoe UI', 12, 'bold'),
                                 bg=colors["card_bg"], fg=colors["fg"], padx=15, pady=15,
                                 relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        info_text = """• 🍑 Peach Tone: Perfect for storytelling and gentle narration
• 💆 Soothing: Ideal for meditation, sleep, or relaxation content  
• 💎 Crystal: Best for educational content and clear instructions
• 🌙 Deep Voice: Great for professional presentations
• ☁️ Soft Whisper: Excellent for ASMR and intimate content
• Use Offline engine for instant results with tone control
• Use Online engine for highest quality cloud-based voices"""
        
        info_label = tk.Label(info_frame, text=info_text, bg=colors["card_bg"], fg='lightblue', 
                             font=('Segoe UI', 9), justify=tk.LEFT)
        info_label.pack()

    def setup_history_tab(self):
        colors = self.theme_colors[self.current_theme]
        history_tab = tk.Frame(self.notebook, bg=colors["bg"])
        self.notebook.add(history_tab, text="📜 History")
        
        # Header with controls
        header_frame = tk.Frame(history_tab, bg=colors["bg"])
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        history_label = tk.Label(header_frame, text="📜 Generation History", font=('Segoe UI', 16, 'bold'),
                               bg=colors["bg"], fg=colors["fg"])
        history_label.pack(side=tk.LEFT)
        
        # Refresh button
        refresh_btn = self.create_hover_button(header_frame, "🔄 Refresh", self.refresh_history_display, 
                                             colors["accent"], colors["highlight"])
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # Clear button
        clear_btn = self.create_hover_button(header_frame, "🗑️ Clear", self.clear_history, 
                                           '#e74c3c', '#c0392b')
        clear_btn.pack(side=tk.RIGHT, padx=5)
        
        # History content frame
        content_frame = tk.Frame(history_tab, bg=colors["bg"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create a canvas for scrollable history cards
        self.history_canvas = tk.Canvas(content_frame, bg=colors["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.history_canvas.yview)
        self.history_scrollable_frame = tk.Frame(self.history_canvas, bg=colors["bg"])
        
        self.history_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
        )
        
        self.history_canvas.create_window((0, 0), window=self.history_scrollable_frame, anchor="nw")
        self.history_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.history_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        self.history_canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        # Initial history display
        self.refresh_history_display()

    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling for history canvas"""
        self.history_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def refresh_history_display(self):
        """Refresh the history display with current data"""
        # Clear existing history cards
        for widget in self.history_scrollable_frame.winfo_children():
            widget.destroy()
        
        colors = self.theme_colors[self.current_theme]
        
        if not self.history:
            # Show empty state
            empty_frame = tk.Frame(self.history_scrollable_frame, bg=colors["bg"], pady=50)
            empty_frame.pack(fill=tk.X, expand=True)
            
            empty_label = tk.Label(empty_frame, text="📝 No history yet", 
                                 font=('Segoe UI', 14, 'bold'), bg=colors["bg"], fg=colors["fg"])
            empty_label.pack(pady=10)
            
            empty_desc = tk.Label(empty_frame, text="Generate some speech to see your history here!",
                                font=('Segoe UI', 11), bg=colors["bg"], fg='lightgray')
            empty_desc.pack()
            
            return
        
        # Display history entries in reverse order (newest first)
        for i, entry in enumerate(reversed(self.history)):
            self.create_history_card(entry, i, colors)

    def create_history_card(self, entry, index, colors):
        """Create a history card for a single entry"""
        card_frame = tk.Frame(self.history_scrollable_frame, bg=colors["card_bg"], 
                            relief=tk.RAISED, bd=1, padx=15, pady=10)
        card_frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Add hover effect to card
        def on_enter(e):
            card_frame.configure(bg=colors["hover_bg"])
            for child in card_frame.winfo_children():
                if hasattr(child, 'winfo_class') and child.winfo_class() == 'Frame':
                    child.configure(bg=colors["hover_bg"])
                elif hasattr(child, 'winfo_class') and child.winfo_class() == 'Label':
                    if 'card' in str(child):
                        child.configure(bg=colors["hover_bg"])
        
        def on_leave(e):
            card_frame.configure(bg=colors["card_bg"])
            for child in card_frame.winfo_children():
                if hasattr(child, 'winfo_class') and child.winfo_class() == 'Frame':
                    child.configure(bg=colors["card_bg"])
                elif hasattr(child, 'winfo_class') and child.winfo_class() == 'Label':
                    if 'card' in str(child):
                        child.configure(bg=colors["card_bg"])
        
        card_frame.bind("<Enter>", on_enter)
        card_frame.bind("<Leave>", on_leave)
        
        # Top row: Text preview and timestamp
        top_frame = tk.Frame(card_frame, bg=colors["card_bg"])
        top_frame.pack(fill=tk.X)
        
        text_label = tk.Label(top_frame, text=entry["text"], font=('Segoe UI', 10, 'bold'),
                            bg=colors["card_bg"], fg=colors["fg"], wraplength=600, justify=tk.LEFT)
        text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Safely get timestamp with fallback
        timestamp = entry.get('timestamp', 'Unknown date')
        timestamp_label = tk.Label(top_frame, text=timestamp, font=('Segoe UI', 8),
                                 bg=colors["card_bg"], fg='lightgray')
        timestamp_label.pack(side=tk.RIGHT)
        
        # Bottom row: Voice details and actions
        bottom_frame = tk.Frame(card_frame, bg=colors["card_bg"])
        bottom_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Voice details with safe access
        voice_type = entry.get('voice', 'male')
        tone_name = entry.get('tone', 'standard')
        
        details_label = tk.Label(bottom_frame, 
                               text=f"🎙️ {voice_type.title()} • 🎨 {tone_name}",
                               font=('Segoe UI', 9), bg=colors["card_bg"], fg='lightblue')
        details_label.pack(side=tk.LEFT)
        
        # Action buttons
        action_frame = tk.Frame(bottom_frame, bg=colors["card_bg"])
        action_frame.pack(side=tk.RIGHT)
        
        # Play button
        play_btn = self.create_hover_button(action_frame, "▶️ Play", 
                                          lambda e=entry: self.play_history_audio(e),
                                          '#27ae60', '#229954')
        play_btn.configure(font=('Segoe UI', 8))
        play_btn.pack(side=tk.LEFT, padx=2)
        
        # Delete button
        delete_btn = self.create_hover_button(action_frame, "🗑️ Delete", 
                                            lambda e=entry: self.delete_history_entry(e),
                                            '#e74c3c', '#c0392b')
        delete_btn.configure(font=('Segoe UI', 8))
        delete_btn.pack(side=tk.LEFT, padx=2)

    def play_history_audio(self, entry):
        """Play audio from history entry"""
        if os.path.exists(entry["file"]):
            self.current_audio_file = entry["file"]
            self.play_audio()
        else:
            messagebox.showwarning("File Not Found", 
                                 "The audio file for this entry no longer exists.")

    def delete_history_entry(self, entry):
        """Delete a history entry"""
        if messagebox.askyesno("Delete Entry", "Are you sure you want to delete this history entry?"):
            self.history = [e for e in self.history if e != entry]
            self.save_history()
            self.refresh_history_display()
            self.settings_status.config(text="✓ History entry deleted!")

    def clear_history(self):
        """Clear all history with confirmation"""
        if messagebox.askyesno("Clear History", 
                             "Are you sure you want to clear all history? This cannot be undone."):
            self.history.clear()
            self.save_history()
            self.refresh_history_display()
            self.settings_status.config(text="✓ All history cleared!")

    def show_quick_actions(self):
        """Show quick actions dialog"""
        messagebox.showinfo("Quick Actions", 
                          "🚀 Quick Actions:\n\n"
                          "• Press Ctrl+G to Generate & Play\n"
                          "• Press Ctrl+P to Play last audio\n" 
                          "• Press Ctrl+S to Stop playback\n"
                          "• Use Quick Text buttons for testing\n"
                          "• Adjust volume for better experience")

    def setup_status_bar(self):
        colors = self.theme_colors[self.current_theme]
        self.status_var = tk.StringVar(value="🎯 Ready - Enter text and click Generate & Play")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bg=colors["sidebar_bg"], fg=colors["fg"],
                              font=('Segoe UI', 10), relief=tk.SUNKEN, anchor='w', padx=10)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def get_tone_name(self):
        """Get display name for current tone"""
        tone_names = {
            "standard": "Standard",
            "peach": "Peach Soft", 
            "soothing": "Soothing",
            "crystal": "Crystal Clear",
            "deep": "Deep Voice",
            "soft": "Soft Whisper"
        }
        return tone_names.get(self.voice_tone_var.get(), "Standard")

    def test_specific_tone(self, tone):
        """Test a specific voice tone"""
        self.voice_tone_var.set(tone)
        self.test_current_voice()

    def test_current_voice(self):
        """Test the current voice settings with selected tone"""
        if self.is_processing:
            self.test_status.config(text="⏳ Please wait...")
            return
            
        def test_thread():
            try:
                self.is_processing = True
                voice_type = self.voice_var.get()
                voice_tone = self.voice_tone_var.get()
                tone_name = self.get_tone_name()
                
                self.test_status.config(text=f"🎵 Testing {voice_type} voice with {tone_name} tone...")
                
                self.safe_stop_audio()
                time.sleep(0.5)
                
                # Different test texts for different tones
                test_texts = {
                    "standard": "Hello, this is the standard voice tone. Clear and natural sounding.",
                    "peach": "Welcome to the peach soft tone. Warm and gentle like a summer breeze.",
                    "soothing": "This is the soothing voice tone. Perfect for relaxation and calm moments.",
                    "crystal": "Crystal clear voice tone. Sharp pronunciation for perfect understanding.",
                    "deep": "This is the deep voice tone. Rich and powerful for professional use.",
                    "soft": "Soft whisper tone. Gentle and intimate for personal content."
                }
                
                test_text = test_texts.get(voice_tone, test_texts["standard"])
                filename = f"test_{voice_type}_{voice_tone}_{datetime.now().strftime('%H%M%S')}.wav"
                path = os.path.join(os.getcwd(), filename)
                
                success = False
                if self.engine_var.get() == "online":
                    try:
                        tts = gtts.gTTS(text=test_text, lang='en')
                        tts.save(path)
                        success = True
                    except Exception as e:
                        self.test_status.config(text=f"❌ Online TTS failed: {e}")
                else:
                    success = self.generate_with_offline_tts(test_text, voice_type, path, voice_tone)
                
                if success and os.path.exists(path):
                    self.test_status.config(text=f"🔊 Playing {tone_name} tone...")
                    if self.play_audio_safe(path):
                        self.test_status.config(text=f"✅ {tone_name} tone test successful!")
                        self.status_var.set(f"🎉 {voice_type.capitalize()} voice with {tone_name} tone test completed")
                    else:
                        self.test_status.config(text=f"⚠️ {tone_name} tone generated but playback failed")
                else:
                    self.test_status.config(text=f"❌ {tone_name} tone generation failed")
                
                # Cleanup
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except:
                    pass
                    
            except Exception as e:
                self.test_status.config(text=f"❌ Error: {str(e)}")
            finally:
                self.is_processing = False
                
        Thread(target=test_thread, daemon=True).start()

    def generate_and_play(self):
        """Generate speech and play immediately"""
        text = self.text_area.get(1.0, tk.END).strip()
        if not text or text == "Enter your text here and click Generate & Play. You can type anything you want to convert to speech.":
            messagebox.showwarning("Warning", "Please enter some text first.")
            return
        
        if self.is_processing:
            messagebox.showwarning("Warning", "Please wait, processing previous request...")
            return
        
        self.status_var.set("🔄 Generating speech...")
        Thread(target=self._generate_and_play_thread, args=(text,), daemon=True).start()

    def _generate_and_play_thread(self, text):
        """Background thread for speech generation and playback"""
        try:
            self.is_processing = True
            
            self.safe_stop_audio()
            time.sleep(0.5)
            
            voice_type = self.voice_var.get()
            voice_tone = self.voice_tone_var.get()
            engine = self.engine_var.get()
            
            filename = f"speech_{voice_type}_{voice_tone}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            path = os.path.join(os.getcwd(), filename)
            
            success = False
            if engine == "online":
                try:
                    tts = gtts.gTTS(text=text, lang='en')
                    tts.save(path)
                    success = True
                    print("✅ Online TTS generation successful")
                except Exception as e:
                    print(f"❌ Online TTS error: {e}")
                    messagebox.showerror("Error", f"Online TTS failed: {e}")
            else:
                success = self.generate_with_offline_tts(text, voice_type, path, voice_tone)
                if success:
                    print(f"✅ Offline TTS generation successful with {voice_tone} tone")
                else:
                    print("❌ Offline TTS generation failed")
            
            if success and os.path.exists(path):
                self.current_audio_file = path
                tone_name = self.get_tone_name()
                
                # Add to history with all required fields including timestamp
                history_entry = {
                    "text": text[:100] + "..." if len(text) > 100 else text,
                    "voice": voice_type,
                    "tone": tone_name,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "file": path
                }
                self.history.append(history_entry)
                self.save_history()
                
                # Refresh history display if we're on the history tab
                if self.notebook.index(self.notebook.select()) == 2:  # History tab index
                    self.refresh_history_display()
                
                self.status_var.set(f"🎵 {tone_name} tone speech generated! Playing now...")
                
                if self.play_audio_safe(path):
                    self.status_var.set("✅ Audio playing successfully!")
                else:
                    self.status_var.set("⚠️ Generation successful but playback failed")
            else:
                self.status_var.set("❌ Speech generation failed")
                messagebox.showerror("Error", "Could not generate speech file")
                
        except Exception as e:
            messagebox.showerror("Error", f"Speech generation failed: {str(e)}")
            self.status_var.set("❌ Generation error")
        finally:
            self.is_processing = False

    def play_audio(self):
        """Play the generated audio"""
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            try:
                self.safe_stop_audio()
                time.sleep(0.5)
                
                self.status_var.set("🔊 Playing audio...")
                if self.play_audio_safe(self.current_audio_file):
                    self.status_var.set("✅ Audio playing successfully!")
                else:
                    self.status_var.set("❌ Playback failed")
            except Exception as e:
                messagebox.showerror("Error", f"Playback error: {str(e)}")
        else:
            messagebox.showwarning("Warning", "No audio file available. Please generate speech first.")

    def stop_audio(self):
        """Stop audio playback"""
        self.safe_stop_audio()
        self.status_var.set("⏹️ Audio stopped")

    def save_audio(self):
        """Save audio file to desired location"""
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            filename = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav"), ("MP3 files", "*.mp3"), ("All files", "*.*")],
                title="Save Audio File"
            )
            if filename:
                try:
                    shutil.copy2(self.current_audio_file, filename)
                    messagebox.showinfo("Success", f"Audio saved successfully!\n{filename}")
                    self.status_var.set(f"💾 Audio saved: {os.path.basename(filename)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Could not save file: {e}")
        else:
            messagebox.showwarning("Warning", "No audio file available to save.")

    def show_tts_tab(self): 
        self.notebook.select(0)
    def show_voice_tab(self): 
        self.notebook.select(1)
    def show_history_tab(self): 
        self.notebook.select(2)
        self.refresh_history_display()
    def show_settings_tab(self):
        self.notebook.select(3)

def main():
    try:
        root = tk.Tk()
        app = AdvancedTextToSpeechConverter(root)
        root.mainloop()
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Error", f"Application failed to start: {e}")

if __name__ == "__main__":
    main()