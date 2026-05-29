import os
import time
import urllib.request
from PyQt5.QtCore import QThread, pyqtSignal
import yt_dlp

def format_duration(seconds):
    """Format duration in seconds to MM:SS or HH:MM:SS."""
    if not seconds:
        return "Unknown"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:d}:{secs:02d}"

def get_best_thumbnail(info_dict):
    """Extract the highest resolution thumbnail URL from info dict."""
    thumbnails = info_dict.get('thumbnails', [])
    if not thumbnails:
        return info_dict.get('thumbnail', '')
    
    # Filter thumbnails that have width information
    valid_thumbnails = [t for t in thumbnails if t.get('width') is not None]
    if valid_thumbnails:
        # Sort descending by width * height
        sorted_thumbs = sorted(
            valid_thumbnails,
            key=lambda t: t.get('width', 0) * t.get('height', 0),
            reverse=True
        )
        return sorted_thumbs[0].get('url', '')
    
    return thumbnails[-1].get('url', '')

class MetadataFetcherThread(QThread):
    """
    Asynchronously fetches YouTube video details using yt-dlp.
    Emits signals for fetch progress, completion, or failure.
    """
    fetch_started = pyqtSignal()
    fetch_completed = pyqtSignal(dict)
    fetch_failed = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        self.fetch_started.emit()
        try:
            ydl_opts = {
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract metadata
                info = ydl.extract_info(self.url, download=False)
                
                if not info:
                    raise Exception("Failed to retrieve video information.")
                
                # Identify available video heights/resolutions
                heights = set()
                formats = info.get('formats', [])
                for f in formats:
                    h = f.get('height')
                    if h:
                        heights.add(h)
                
                # Fallback to top-level video height if formats were empty/unlisted
                if not heights and info.get('height'):
                    heights.add(info['height'])
                
                sorted_resolutions = sorted(list(heights), reverse=True)
                
                # Compile a high-quality preview dictionary
                thumb_url = get_best_thumbnail(info)
                thumb_bytes = None
                if thumb_url:
                    try:
                        req = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=5) as response:
                            thumb_bytes = response.read()
                    except Exception:
                        pass

                preview_data = {
                    'title': info.get('title', 'Unknown Title'),
                    'author': info.get('uploader', info.get('author', 'Unknown Channel')),
                    'duration': format_duration(info.get('duration')),
                    'thumbnail': thumb_url,
                    'thumbnail_bytes': thumb_bytes,
                    'views': f"{info.get('view_count', 0):,}" if info.get('view_count') else "Unknown",
                    'resolutions': sorted_resolutions,
                    'url': self.url,
                    'raw_info': info
                }
                
                self.fetch_completed.emit(preview_data)
                
        except Exception as e:
            self.fetch_failed.emit(str(e))


class DownloadWorkerThread(QThread):
    """
    Asynchronously downloads a YouTube video using yt-dlp in a worker thread.
    Emits real-time progress details, speed, ETA, and final completion/error signals.
    """
    download_started = pyqtSignal(str)  # video title
    download_progress = pyqtSignal(dict)  # progress stats
    download_completed = pyqtSignal(str)  # final saved filepath
    download_failed = pyqtSignal(str)  # error description

    def __init__(self, url, output_dir, format_selection, video_title=""):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.format_selection = format_selection
        self.video_title = video_title
        self.last_progress_time = 0

    def run(self):
        self.download_started.emit(self.video_title or "YouTube Video")
        
        try:
            import shutil
            ffmpeg_present = shutil.which("ffmpeg") is not None

            # Build download format options based on selection
            postprocessors = []
            
            if self.format_selection == 'Audio Only (MP3)':
                if not ffmpeg_present:
                    raise RuntimeError(
                        "Converting to MP3 format requires FFmpeg. "
                        "Please select M4A (which does not require FFmpeg) or install FFmpeg on your system."
                    )
                format_spec = 'bestaudio/best'
                postprocessors = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            elif self.format_selection == 'Audio Only (M4A)':
                format_spec = 'bestaudio[ext=m4a]/best'
            elif 'p' in str(self.format_selection):
                # Specific resolution requested (e.g. "1080p", "720p")
                res = self.format_selection.replace('p', '')
                if ffmpeg_present:
                    # Choose best video up to selected height, merged with best audio
                    format_spec = f'bestvideo[height<={res}]+bestaudio/best[height<={res}]'
                else:
                    # Fall back to best pre-merged stream (avoids FFmpeg merge error)
                    format_spec = f'best[height<={res}]/best'
            else:
                # Default "Best Quality" selection
                if ffmpeg_present:
                    format_spec = 'bestvideo+bestaudio/best'
                else:
                    # Fall back to best pre-merged stream (avoids FFmpeg merge error)
                    format_spec = 'best'

            # Define standard yt-dlp options with progress hooks
            ydl_opts = {
                'format': format_spec,
                'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [self._progress_hook],
                'quiet': True,
                'no_warnings': True,
                'postprocessors': postprocessors if postprocessors else [],
            }
            
            # Avoid downloading playlists unless explicitly allowed
            ydl_opts['noplaylist'] = True

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)
                # Determine final file path
                filename = ydl.prepare_filename(info)
                
                # If postprocessor extracted audio to MP3, correct filename extension
                if self.format_selection == 'Audio Only (MP3)':
                    base, _ = os.path.splitext(filename)
                    filename = f"{base}.mp3"
                
                self.download_completed.emit(filename)
                
        except Exception as e:
            self.download_failed.emit(str(e))

    def _progress_hook(self, d):
        """Internal callback invoked by yt-dlp during download progress updates."""
        if d['status'] == 'downloading':
            current_time = time.time()
            # Limit signal updates to ~10 times per second to prevent UI lag
            if current_time - self.last_progress_time < 0.1:
                return
            self.last_progress_time = current_time

            total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes', 0)
            
            # Calculate percentage
            if total_bytes > 0:
                percent = (downloaded / total_bytes) * 100
            else:
                # Fallback to parsing percentage string
                pct_str = d.get('_percent_str', '0%').replace('%', '').strip()
                try:
                    percent = float(pct_str)
                except ValueError:
                    percent = 0.0

            # Collect nice formatting strings
            speed = d.get('_speed_str', 'N/A').strip()
            eta = d.get('_eta_str', 'N/A').strip()
            
            # Format size strings nicely
            total_size_mb = f"{total_bytes / (1024 * 1024):.1f} MB" if total_bytes > 0 else "Unknown"
            downloaded_mb = f"{downloaded / (1024 * 1024):.1f} MB"

            progress_stats = {
                'percentage': percent,
                'speed': speed,
                'eta': eta,
                'size_info': f"{downloaded_mb} / {total_size_mb}"
            }
            
            self.download_progress.emit(progress_stats)
        
        elif d['status'] == 'finished':
            # Complete signal is emitted at the end of the run() function
            # to make sure any post-processing is fully completed.
            pass
