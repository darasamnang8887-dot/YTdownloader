import os
import time
import shutil
import uuid
import threading
from flask import Flask, render_template, request, jsonify, send_from_directory, abort
import yt_dlp

app = Flask(__name__)

# Directory where downloaded files are temporarily stored before being served to client
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Dictionary to store active download task statuses
active_tasks = {}

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

def get_best_thumbnail(info_dict):
    thumbnails = info_dict.get('thumbnails', [])
    if not thumbnails:
        return info_dict.get('thumbnail', '')
    valid_thumbnails = [t for t in thumbnails if t.get('width') is not None]
    if valid_thumbnails:
        sorted_thumbs = sorted(valid_thumbnails, key=lambda t: t.get('width', 0) * t.get('height', 0), reverse=True)
        return sorted_thumbs[0].get('url', '')
    return thumbnails[-1].get('url', '')

def clean_old_downloads():
    """Periodically deletes downloaded files older than 10 minutes to save disk space."""
    while True:
        try:
            now = time.time()
            for filename in os.listdir(DOWNLOAD_DIR):
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.isfile(filepath):
                    # Delete files older than 10 minutes
                    if now - os.path.getmtime(filepath) > 600:
                        os.remove(filepath)
        except Exception:
            pass
        time.sleep(180) # Check every 3 minutes

# Run cleanup in a background daemon thread
threading.Thread(target=clean_old_downloads, daemon=True).start()

# =========================================================================
# FLASK WEB ROUTES
# =========================================================================
@app.route('/')
def index():
    # Return index template
    return render_template('index.html')

@app.route('/fetch', methods=['POST'])
def fetch_info():
    """Extract YouTube video details and formats asynchronously from AJAX request."""
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'Please enter a valid YouTube URL.'}), 400
        
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
                raise Exception("Could not retrieve video details.")
                
            # Filter unique video heights
            heights = set()
            for f in info.get('formats', []):
                h = f.get('height')
                if h:
                    heights.add(h)
            
            # Fallback to top-level video height if formats were empty/unlisted
            if not heights and info.get('height'):
                heights.add(info['height'])
                
            sorted_resolutions = sorted(list(heights), reverse=True)
            
            # Pack metadata
            metadata = {
                'title': info.get('title', 'Unknown Title'),
                'author': info.get('uploader', 'Unknown Channel'),
                'duration': format_duration(info.get('duration')),
                'views': f"{info.get('view_count', 0):,}" if info.get('view_count') else "Unknown",
                'thumbnail': get_best_thumbnail(info),
                'resolutions': sorted_resolutions,
                'url': url
            }
            return jsonify(metadata)
            
    except Exception as e:
        return jsonify({'error': str(e).split('\n')[0]}), 500

@app.route('/download', methods=['POST'])
def download_video():
    """Triggers download on server side and returns download link token once ready."""
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    quality = data.get('quality', 'Best Quality').strip()
    
    if not url:
        return jsonify({'error': 'Please enter a valid URL.'}), 400
        
    # Check if FFmpeg is installed
    ffmpeg_present = shutil.which("ffmpeg") is not None
    
    # Determine format specifier
    postprocessors = []
    if quality == 'Audio Only (MP3)':
        if not ffmpeg_present:
            # Native M4A fallback
            format_spec = 'bestaudio[ext=m4a]/best'
        else:
            format_spec = 'bestaudio/best'
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
    elif quality == 'Audio Only (M4A)':
        format_spec = 'bestaudio[ext=m4a]/best'
    elif 'p' in str(quality):
        res = quality.replace('p', '')
        if ffmpeg_present:
            format_spec = f'bestvideo[height<={res}]+bestaudio/best[height<={res}]'
        else:
            format_spec = f'best[height<={res}]/best'
    else:
        # Best Quality
        format_spec = 'bestvideo+bestaudio/best' if ffmpeg_present else 'best'

    try:
        # Unique prefix identifier to prevent name collisions
        file_id = str(uuid.uuid4())[:8]
        outtmpl = os.path.join(DOWNLOAD_DIR, f"{file_id}_%(title)s.%(ext)s")
        
        ydl_opts = {
            'format': format_spec,
            'outtmpl': outtmpl,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'postprocessors': postprocessors
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Find the actual saved file path
            filename = ydl.prepare_filename(info)
            
            # If MP3 was processed, adjust extension name
            if quality == 'Audio Only (MP3)' and ffmpeg_present:
                base, _ = os.path.splitext(filename)
                filename = f"{base}.mp3"
                
            basename = os.path.basename(filename)
            
            # Return download link relative to web app
            return jsonify({
                'success': True,
                'download_url': f"/get_file/{basename}",
                'filename': basename
            })
            
    except Exception as e:
        return jsonify({'error': str(e).split('\n')[0]}), 500

@app.route('/get_file/<path:filename>', methods=['GET'])
def get_file(filename):
    """Serves the downloaded file back to browser for storage saving."""
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(filepath):
        abort(404)
    # Stream the file directly as attachment
    return send_from_directory(DOWNLOAD_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    # Bind to 0.0.0.0 and dynamically detect PORT environment variable (for Render/Heroku compatibility)
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print("YT Downloader Web Server Started successfully!")
    print(f"To open locally: http://127.0.0.1:{port}")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=port, debug=False)
