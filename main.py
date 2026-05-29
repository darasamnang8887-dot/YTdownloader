import os
import sys
import time
import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.image import AsyncImage
from kivy.uix.spinner import Spinner
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard

import yt_dlp

# Set default background color to premium slate-dark
Window.clearcolor = get_color_from_hex('#0f172a')

def format_duration(seconds):
    if not seconds:
        return "Unknown"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:d}:{secs:02d}"

class DownloadCard(BoxLayout):
    """A touchscreen-friendly card displaying active download progress and actions."""
    def __init__(self, title, quality, on_delete_callback, **kwargs):
        super().__init__(orientation='vertical', spacing=6, padding=12, size_hint_y=None, height=170, **kwargs)
        
        # Slate card background styling
        self.canvas.before.clear()
        with self.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*get_color_from_hex('#1e293b'))
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[8])
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        self.on_delete_callback = on_delete_callback
        
        # Title Label
        self.title_label = Label(text=title, font_size='13sp', bold=True, size_hint_y=None, height=36, color=get_color_from_hex('#f1f5f9'))
        self.title_label.text_size = (self.width, None)
        self.bind(width=lambda s, w: setattr(self.title_label, 'text_size', (w - 24, None)))
        
        # Meta info row
        self.meta_label = Label(text=f"Format: {quality}   •   Size: Waiting...", font_size='11sp', color=get_color_from_hex('#94a3b8'), size_hint_y=None, height=20)
        self.meta_label.bind(width=lambda s, w: setattr(self.meta_label, 'text_size', (w - 24, None)))
        
        # Progress Bar
        self.pbar = ProgressBar(max=100, value=0, size_hint_y=None, height=14)
        
        # Status details
        self.status_label = Label(text="Connecting...", font_size='11sp', color=get_color_from_hex('#94a3b8'), size_hint_y=None, height=20)
        self.status_label.bind(width=lambda s, w: setattr(self.status_label, 'text_size', (w - 24, None)))
        
        # Action Buttons
        actions_layout = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=None, height=36)
        
        self.open_btn = Button(text="📂 Open Folder", font_size='11sp', size_hint_x=0.5, disabled=True,
                               background_color=get_color_from_hex('#334155'), background_normal='')
        
        self.delete_btn = Button(text="🗑️ Delete", font_size='11sp', size_hint_x=0.5, disabled=True,
                                 background_color=get_color_from_hex('#ef4444'), background_normal='')
        self.delete_btn.bind(on_press=self.on_delete_press)
        
        actions_layout.addWidget(self.open_btn)
        actions_layout.addWidget(self.delete_btn)
        
        self.addWidget(self.title_label)
        self.addWidget(self.meta_label)
        self.addWidget(self.pbar)
        self.addWidget(self.status_label)
        self.addWidget(actions_layout)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_delete_press(self, instance):
        if self.on_delete_callback:
            self.on_delete_callback(self)


class YTDownloaderMobileApp(App):
    """Touchscreen mobile downloader application built using Kivy and compiled via Buildozer."""
    def build(self):
        self.title = "YT Downloader by Youmeas"
        
        # Core parent layout
        self.root_layout = BoxLayout(orientation='vertical', padding=12, spacing=12)
        
        # 1. HEADER
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        header_text = BoxLayout(orientation='vertical', spacing=2)
        title = Label(text="YT Downloader", font_size='20sp', bold=True, color=get_color_from_hex('#f8fafc'), halign='left')
        title.bind(width=lambda s, w: setattr(title, 'text_size', (w, None)))
        
        subtitle = Label(text="by Youmeas", font_size='11sp', bold=True, color=get_color_from_hex('#38bdf8'), halign='left')
        subtitle.bind(width=lambda s, w: setattr(subtitle, 'text_size', (w, None)))
        
        header_text.addWidget(title)
        header_text.addWidget(subtitle)
        header.addWidget(header_text)
        self.root_layout.addWidget(header)
        
        # 2. CONSOLE FRAME
        console_frame = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=180, padding=10)
        
        # Frame Background styling
        with console_frame.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*get_color_from_hex('#1e293b'))
            self.con_rect = RoundedRectangle(pos=console_frame.pos, size=console_frame.size, radius=[10])
        console_frame.bind(pos=self.update_console_rect, size=self.update_console_rect)
        
        console_title = Label(text="DOWNLOAD CENTER", font_size='12sp', bold=True, color=get_color_from_hex('#38bdf8'), size_hint_y=None, height=20)
        console_title.bind(width=lambda s, w: setattr(console_title, 'text_size', (w - 20, None)))
        console_frame.addWidget(console_title)
        
        # URL TextInput
        self.url_input = TextInput(hint_text="Paste YouTube, TikTok, or Facebook URL here...", multiline=False, font_size='13sp',
                                   background_color=get_color_from_hex('#0f172a'), foreground_color=get_color_from_hex('#f8fafc'),
                                   hint_text_color=get_color_from_hex('#64748b'), size_hint_y=None, height=40, padding=[10, 10])
        console_frame.addWidget(self.url_input)
        
        # Action Buttons Row
        actions_row = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=None, height=36)
        
        paste_btn = Button(text="📋 Paste Link", font_size='11sp', bold=True, background_color=get_color_from_hex('#334155'), background_normal='')
        paste_btn.bind(on_press=self.on_paste_link)
        
        clear_btn = Button(text="❌ Clear", font_size='11sp', bold=True, background_color=get_color_from_hex('#334155'), background_normal='')
        clear_btn.bind(on_press=self.on_clear_link)
        
        actions_row.addWidget(paste_btn)
        actions_row.addWidget(clear_btn)
        console_frame.addWidget(actions_row)
        
        # Fetch Button
        self.fetch_btn = Button(text="🔍 Fetch Video Details", font_size='13sp', bold=True, size_hint_y=None, height=40,
                                background_color=get_color_from_hex('#0ea5e9'), background_normal='')
        self.fetch_btn.bind(on_press=self.on_fetch_details)
        console_frame.addWidget(self.fetch_btn)
        
        self.root_layout.addWidget(console_frame)
        
        # 3. METADATA PREVIEW (Hidden initially by size_hint_y=0, opacity=0)
        self.preview_frame = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=0, opacity=0, padding=10)
        with self.preview_frame.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*get_color_from_hex('#1a2236'))
            self.prev_rect = RoundedRectangle(pos=self.preview_frame.pos, size=self.preview_frame.size, radius=[8])
        self.preview_frame.bind(pos=self.update_preview_rect, size=self.update_preview_rect)
        
        # Video Details
        self.preview_title = Label(text="Video Title", font_size='13sp', bold=True, size_hint_y=None, height=36, color=get_color_from_hex('#f1f5f9'))
        self.preview_title.bind(width=lambda s, w: setattr(self.preview_title, 'text_size', (w - 20, None)))
        
        self.preview_meta = Label(text="Duration • Channel", font_size='11sp', color=get_color_from_hex('#94a3b8'), size_hint_y=None, height=20)
        self.preview_meta.bind(width=lambda s, w: setattr(self.preview_meta, 'text_size', (w - 20, None)))
        
        # Quality spinner/dropdown
        spinner_row = BoxLayout(orientation='horizontal', spacing=8, size_hint_y=None, height=36)
        spinner_row.addWidget(Label(text="Quality:", size_hint_x=0.3, font_size='12sp'))
        
        self.quality_spinner = Spinner(text="Best Quality", values=("Best Quality", "Audio Only (M4A)"), size_hint_x=0.7,
                                       background_color=get_color_from_hex('#334155'), background_normal='')
        spinner_row.addWidget(self.quality_spinner)
        
        # Download Button
        self.download_btn = Button(text="📥 Start Download", font_size='13sp', bold=True, size_hint_y=None, height=40,
                                   background_color=get_color_from_hex('#10b981'), background_normal='')
        self.download_btn.bind(on_press=self.on_start_download)
        
        self.preview_frame.addWidget(self.preview_title)
        self.preview_frame.addWidget(self.preview_meta)
        self.preview_frame.addWidget(spinner_row)
        self.preview_frame.addWidget(self.download_btn)
        
        self.root_layout.addWidget(self.preview_frame)
        
        # 4. DOWNLOAD QUEUE (Scroll View)
        queue_title = Label(text="ACTIVE & COMPLETED QUEUE", font_size='12sp', bold=True, color=get_color_from_hex('#38bdf8'), size_hint_y=None, height=20)
        queue_title.bind(width=lambda s, w: setattr(queue_title, 'text_size', (w, None)))
        self.root_layout.addWidget(queue_title)
        
        scroll = ScrollView(size_hint=(1, 1))
        self.queue_list = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.queue_list.bind(minimum_height=self.queue_list.setter('height'))
        scroll.add_widget(self.queue_list)
        
        self.root_layout.addWidget(scroll)
        
        # Status bar note
        self.status_bar = Label(text="Ready • FFmpeg pre-merged fallback enabled", font_size='10sp', color=get_color_from_hex('#94a3b8'), size_hint_y=None, height=20)
        self.status_bar.bind(width=lambda s, w: setattr(self.status_bar, 'text_size', (w, None)))
        self.root_layout.addWidget(self.status_bar)
        
        self.current_metadata = None
        
        return self.root_layout

    def update_console_rect(self, instance, value):
        self.con_rect.pos = instance.pos
        self.con_rect.size = instance.size

    def update_preview_rect(self, instance, value):
        self.prev_rect.pos = instance.pos
        self.prev_rect.size = instance.size

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def on_paste_link(self, instance):
        text = Clipboard.paste().strip()
        if text:
            self.url_input.text = text
            self.status_bar.text = "Pasted link from clipboard."

    def on_clear_link(self, instance):
        self.url_input.text = ""
        self.status_bar.text = "Cleared link input."
        self.hide_preview()

    def on_fetch_details(self, instance):
        url = self.url_input.text.strip()
        if not url:
            self.status_bar.text = "Error: Please enter a valid URL."
            return
            
        self.fetch_btn.disabled = True
        self.fetch_btn.text = "⏳ Querying YouTube..."
        self.status_bar.text = "Fetching video details asynchronously..."
        
        # Start background thread to query yt-dlp metadata
        threading.Thread(target=self._async_fetch_thread, args=(url,), daemon=True).start()

    def _async_fetch_thread(self, url):
        try:
            ydl_opts = {
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    raise Exception("Failed to retrieve metadata.")
                
                # Fetch resolutions list
                heights = set()
                for f in info.get('formats', []):
                    h = f.get('height')
                    if h:
                        heights.add(h)
                if not heights and info.get('height'):
                    heights.add(info['height'])
                sorted_resolutions = sorted(list(heights), reverse=True)
                
                # Pack info
                preview_data = {
                    'title': info.get('title', 'Unknown Title'),
                    'author': info.get('uploader', info.get('uploader_id', 'Unknown Channel')),
                    'duration': format_duration(info.get('duration')),
                    'resolutions': sorted_resolutions,
                    'url': url
                }
                
                # Dispatch completion back to Main GUI thread safely using Kivy Clock
                Clock.schedule_once(lambda dt: self._on_fetch_completed(preview_data))
                
        except Exception as e:
            err = str(e).split('\n')[0]
            Clock.schedule_once(lambda dt: self._on_fetch_failed(err))

    def _on_fetch_completed(self, data):
        self.fetch_btn.disabled = False
        self.fetch_btn.text = "🔍 Fetch Video Details"
        self.status_bar.text = "Successfully loaded video metadata."
        self.current_metadata = data
        
        # Populate Preview Card
        self.preview_title.text = data['title']
        self.preview_meta.text = f"Duration: {data['duration']}   •   Channel: {data['author']}"
        
        # Populate Quality spinner
        spinner_values = ["Best Quality"]
        for r in data['resolutions']:
            spinner_values.append(f"{r}p")
        spinner_values.append("Audio Only (M4A)")
        
        self.quality_spinner.values = spinner_values
        self.quality_spinner.text = "Best Quality"
        
        # Animate Preview card open (change size and opacity)
        self.preview_frame.height = 160
        self.preview_frame.opacity = 1

    def _on_fetch_failed(self, error):
        self.fetch_btn.disabled = False
        self.fetch_btn.text = "🔍 Fetch Video Details"
        self.status_bar.text = f"Error fetching details: {error}"
        self.hide_preview()

    def hide_preview(self):
        self.preview_frame.height = 0
        self.preview_frame.opacity = 0
        self.current_metadata = None

    def on_start_download(self, instance):
        if not self.current_metadata:
            return
            
        url = self.current_metadata['url']
        title = self.current_metadata['title']
        quality = self.quality_spinner.text
        
        # Default Mobile download folder (Internal storage Download directory)
        # On Android 10 to 15+, writing directly to /sdcard/Download will raise Permission Denied.
        # We use standard scoped app-specific external download folder which doesn't require permissions.
        if sys.platform == 'android':
            try:
                from jnius import autoclass
                Environment = autoclass('android.os.Environment')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                context = PythonActivity.mActivity
                download_dir = context.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS).getPath()
            except Exception:
                try:
                    from android.storage import primary_external_storage_path
                    download_dir = os.path.join(primary_external_storage_path(), 'Download')
                except Exception:
                    download_dir = '/sdcard/Download'
        else:
            download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            
        if not os.path.exists(download_dir):
            try:
                os.makedirs(download_dir)
            except Exception:
                pass
                
        # Instantiate Card in Layout list
        card = DownloadCard(title, quality, on_delete_callback=self.on_delete_card)
        self.queue_list.add_widget(card)
        
        # Reset fetch inputs
        self.url_input.text = ""
        self.hide_preview()
        
        # Start download in background thread
        threading.Thread(target=self._async_download_thread, args=(url, download_dir, quality, card), daemon=True).start()

    def _async_download_thread(self, url, download_dir, quality, card):
        # Format specifier
        format_spec = 'best' # Mobile default pre-merged (avoids FFmpeg errors!)
        if 'p' in str(quality):
            res = quality.replace('p', '')
            format_spec = f'best[height<={res}]/best'
        elif 'M4A' in str(quality):
            format_spec = 'bestaudio[ext=m4a]/best'
            
        try:
            # Custom progress hook wrapper
            def progress_hook(d):
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                    downloaded = d.get('downloaded_bytes', 0)
                    pct = (downloaded / total * 100) if total > 0 else 0
                    
                    speed = d.get('_speed_str', 'N/A').strip()
                    eta = d.get('_eta_str', 'N/A').strip()
                    
                    total_mb = f"{total / (1024*1024):.1f} MB" if total > 0 else "Unknown"
                    downloaded_mb = f"{downloaded / (1024*1024):.1f} MB"
                    
                    # Update card progress elements safely on GUI thread
                    Clock.schedule_once(lambda dt: self._update_card_progress(
                        card, pct, f"Format: {quality}   •   Size: {downloaded_mb} / {total_mb}",
                        f"{int(pct)}% Completed  •  {speed}  •  ETA: {eta}"
                    ))
                    
            ydl_opts = {
                'format': format_spec,
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [progress_hook],
                'quiet': True,
                'no_warnings': True,
                'noplaylist': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                
                # Verify downloaded size
                file_size_mb = "N/A"
                if os.path.exists(filename):
                    size_bytes = os.path.getsize(filename)
                    file_size_mb = f"{size_bytes / (1024*1024):.1f} MB"
                
                # Download success complete hook
                Clock.schedule_once(lambda dt: self._on_download_success(card, file_size_mb))
                
        except Exception as e:
            err = str(e).split('\n')[0]
            Clock.schedule_once(lambda dt: self._on_download_failed(card, err))

    def _update_card_progress(self, card, pct, meta_text, progress_text):
        card.pbar.value = int(pct)
        card.meta_label.text = meta_text
        card.status_label.text = progress_text

    def _on_download_success(self, card, size_str):
        card.pbar.value = 100
        card.meta_label.text = f"Format: {self.quality_spinner.text}   •   Size: {size_str}"
        card.status_label.text = "✓ Completed successfully"
        card.status_label.color = get_color_from_hex('#10b981')
        card.delete_btn.disabled = False
        self.status_bar.text = "Download completed."

    def _on_download_failed(self, card, error):
        card.pbar.value = 0
        card.status_label.text = f"❌ Failed: {error}"
        card.status_label.color = get_color_from_hex('#ef4444')
        card.delete_btn.disabled = False
        self.status_bar.text = f"Download failed: {error}"

    def on_delete_card(self, card):
        self.queue_list.remove_widget(card)
        self.status_bar.text = "Card removed from list."

if __name__ == "__main__":
    # Configure touch input emulation for desktop layout sizing tests
    Window.size = (380, 680)
    YTDownloaderMobileApp().run()
