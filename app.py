import os
import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QFileDialog,
    QProgressBar, QMessageBox, QFrame, QScrollArea, QGridLayout
)
from PyQt5.QtCore import Qt, QSettings, pyqtSlot
from PyQt5.QtGui import QPixmap

# Import styling and backend threads
from style_sheets import DARK_STYLE
from downloader import MetadataFetcherThread, DownloadWorkerThread

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

class YouTubeDownloaderApp(QMainWindow):
    """
    Mobile-first responsive GUI window for YT Downloader by Youmeas.
    Lays out components in a vertical, touch-friendly scrollable stack
    and displays active/past downloads as beautiful cards.
    """
    def __init__(self):
        super().__init__()
        
        # Load user settings
        self.settings = QSettings("Antigravity", "YTDownloaderByYoumeas")
        
        # Configure window title
        self.setWindowTitle("YT Downloader by Youmeas")
        
        # Active downloads map: thread/mock-key -> dict containing card references
        self.active_downloads = {}
        
        # Current fetched video metadata
        self.current_metadata = None
        
        # Initialize UI
        self.init_ui()
        
        # Set theme stylesheet
        self.setStyleSheet(DARK_STYLE)
        
        # Load download history
        self.load_history()

        # Load and apply layout mode preference
        self.is_desktop_layout = self.settings.value("is_desktop_layout", False, type=bool)
        self.apply_layout_mode(self.is_desktop_layout)

        # Check for FFmpeg to present warm alert if missing
        import shutil
        self.ffmpeg_present = shutil.which("ffmpeg") is not None
        if not self.ffmpeg_present:
            self.status_bar_label.setText("Ready (⚠️ FFmpeg not detected: 1080p+ merging and MP3 conversion are disabled. Pre-merged fallback enabled.)")
            self.status_bar_label.setStyleSheet("color: #f59e0b;")

    def init_ui(self):
        # 1. Main outer layout - everything inside a QScrollArea for mobile responsiveness
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setStyleSheet("QScrollArea { border: none; background-color: #0f172a; }")
        self.setCentralWidget(main_scroll)
        
        container = QWidget()
        container.setObjectName("mobileContainer")
        container.setStyleSheet("QWidget#mobileContainer { background-color: #0f172a; }")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        main_scroll.setWidget(container)
        
        # =========================================================================
        # 1. HEADER SECTION
        # =========================================================================
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        # Logo Label
        logo_label = QLabel()
        logo_label.setFixedSize(48, 48)
        logo_path = resource_path("logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("📥")
            logo_label.setStyleSheet("font-size: 32px;")
        
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(1)
        
        title_label = QLabel("YT Downloader")
        title_label.setObjectName("titleLabel")
        title_label.setStyleSheet("font-size: 20px; font-weight: 800;")
        
        subtitle_label = QLabel("by Youmeas")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setStyleSheet("font-size: 11px; color: #38bdf8; font-weight: bold;")
        
        header_text_layout.addWidget(title_label)
        header_text_layout.addWidget(subtitle_label)
        
        # Layout Toggle Button (dynamic mobile <-> desktop switcher)
        self.layout_toggle_btn = QPushButton("💻 Switch to Desktop View")
        self.layout_toggle_btn.setObjectName("iconButton")
        self.layout_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.layout_toggle_btn.clicked.connect(self.on_layout_toggle_clicked)
        
        header_layout.addWidget(logo_label)
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        header_layout.addWidget(self.layout_toggle_btn)
        
        main_layout.addLayout(header_layout)
        
        # =========================================================================
        # 2. CONSOLE CARD (Download Center)
        # =========================================================================
        self.console_frame = QFrame()
        self.console_frame.setObjectName("cardFrame")
        console_layout = QVBoxLayout(self.console_frame)
        console_layout.setContentsMargins(14, 14, 14, 14)
        console_layout.setSpacing(12)
        
        console_title = QLabel("Download Center")
        console_title.setObjectName("sectionTitle")
        console_layout.addWidget(console_title)
        
        # URL Input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube, TikTok, or Facebook URL here...")
        self.url_input.textChanged.connect(self.on_url_changed)
        console_layout.addWidget(self.url_input)
        
        # URL actions horizontal row
        url_actions_layout = QHBoxLayout()
        url_actions_layout.setSpacing(8)
        
        self.paste_btn = QPushButton("📋 Paste")
        self.paste_btn.setObjectName("iconButton")
        self.paste_btn.setCursor(Qt.PointingHandCursor)
        self.paste_btn.setFixedHeight(38)
        self.paste_btn.clicked.connect(self.on_paste_clicked)
        
        self.clear_btn = QPushButton("❌ Clear")
        self.clear_btn.setObjectName("iconButton")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.setFixedHeight(38)
        self.clear_btn.clicked.connect(self.on_clear_clicked)
        
        url_actions_layout.addWidget(self.paste_btn)
        url_actions_layout.addWidget(self.clear_btn)
        console_layout.addLayout(url_actions_layout)
        
        # Fetch Info Button (Full Width for thumbs!)
        self.fetch_btn = QPushButton("🔍 Fetch Info")
        self.fetch_btn.setObjectName("primaryButton")
        self.fetch_btn.setCursor(Qt.PointingHandCursor)
        self.fetch_btn.setFixedHeight(44)
        self.fetch_btn.clicked.connect(self.on_fetch_clicked)
        console_layout.addWidget(self.fetch_btn)
        
        # =========================================================================
        # 3. VIDEO METADATA PREVIEW CARD (Hidden initially)
        # =========================================================================
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("cardFrame")
        self.preview_frame.setVisible(False)
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(12, 12, 12, 12)
        preview_layout.setSpacing(10)
        
        # Thumbnail scaled to mobile card size
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedHeight(180)
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("border-radius: 8px; background-color: #0f172a;")
        preview_layout.addWidget(self.thumbnail_label)
        
        # Video title and meta text details
        self.video_title_label = QLabel("Video Title")
        self.video_title_label.setObjectName("videoTitle")
        self.video_title_label.setWordWrap(True)
        
        self.video_meta_label = QLabel("Channel • Duration • Views")
        self.video_meta_label.setObjectName("videoMeta")
        self.video_meta_label.setWordWrap(True)
        
        preview_layout.addWidget(self.video_title_label)
        preview_layout.addWidget(self.video_meta_label)
        
        # Quality Selector Stack
        quality_layout = QVBoxLayout()
        quality_layout.setSpacing(4)
        quality_layout.addWidget(QLabel("Quality Format:"))
        self.quality_combo = QComboBox()
        self.quality_combo.setCursor(Qt.PointingHandCursor)
        self.quality_combo.setFixedHeight(38)
        quality_layout.addWidget(self.quality_combo)
        preview_layout.addLayout(quality_layout)
        
        # Save Folder Stack
        save_layout = QVBoxLayout()
        save_layout.setSpacing(4)
        save_layout.addWidget(QLabel("Save Folder:"))
        
        folder_row = QHBoxLayout()
        folder_row.setSpacing(6)
        self.save_dir_input = QLineEdit()
        default_dir = self.settings.value("download_directory", os.path.join(os.path.expanduser('~'), 'Downloads'))
        self.save_dir_input.setText(default_dir)
        self.save_dir_input.setReadOnly(True)
        self.save_dir_input.setFixedHeight(38)
        
        self.browse_btn = QPushButton("📁 Browse")
        self.browse_btn.setObjectName("iconButton")
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.setFixedHeight(38)
        self.browse_btn.clicked.connect(self.on_browse_clicked)
        
        folder_row.addWidget(self.save_dir_input)
        folder_row.addWidget(self.browse_btn)
        save_layout.addLayout(folder_row)
        preview_layout.addLayout(save_layout)
        
        # Big Download Button
        self.download_btn = QPushButton("📥 Start Download")
        self.download_btn.setObjectName("accentButton")
        self.download_btn.setCursor(Qt.PointingHandCursor)
        self.download_btn.setFixedHeight(44)
        self.download_btn.clicked.connect(self.on_download_clicked)
        preview_layout.addWidget(self.download_btn)
        
        console_layout.addWidget(self.preview_frame)
        
        # =========================================================================
        # 4. DOWNLOAD QUEUE & HISTORY SECTION
        # =========================================================================
        self.history_frame = QFrame()
        self.history_frame.setObjectName("cardFrame")
        history_layout = QVBoxLayout(self.history_frame)
        history_layout.setContentsMargins(14, 14, 14, 14)
        history_layout.setSpacing(10)
        
        history_header = QHBoxLayout()
        history_title = QLabel("Download Queue")
        history_title.setObjectName("sectionTitle")
        
        clear_history_btn = QPushButton("🧹 Clear Completed")
        clear_history_btn.setObjectName("iconButton")
        clear_history_btn.setCursor(Qt.PointingHandCursor)
        clear_history_btn.clicked.connect(self.on_clear_history_clicked)
        
        history_header.addWidget(history_title)
        history_header.addStretch()
        history_header.addWidget(clear_history_btn)
        history_layout.addLayout(history_header)
        
        # Vertical list widget to contain download cards
        self.history_list_widget = QWidget()
        self.history_list_layout = QVBoxLayout(self.history_list_widget)
        self.history_list_layout.setContentsMargins(0, 0, 0, 0)
        self.history_list_layout.setSpacing(10)
        self.history_list_layout.addStretch()  # Keep cards pushed to top
        
        history_layout.addWidget(self.history_list_widget)
        
        # Grid container for dynamic layout mode (Mobile / Desktop)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(16)
        
        main_layout.addWidget(self.grid_container)
        
        # Status Bar
        self.status_bar_label = QLabel("Ready")
        self.status_bar_label.setObjectName("subtitleLabel")
        self.status_bar_label.setWordWrap(True)
        main_layout.addWidget(self.status_bar_label)

    # =========================================================================
    # SLOT & CLIPBOARD HANDLERS
    # =========================================================================
    def apply_layout_mode(self, is_desktop):
        """Dynamically switches between stacked mobile layout and side-by-side desktop layout."""
        # Safely remove widgets from grid layout
        self.grid_layout.removeWidget(self.console_frame)
        self.grid_layout.removeWidget(self.history_frame)
        
        if is_desktop:
            # Side-by-side layout for Desktop
            self.grid_layout.addWidget(self.console_frame, 0, 0)
            self.grid_layout.addWidget(self.history_frame, 0, 1)
            
            # Configure grid stretches
            self.grid_layout.setColumnStretch(0, 4)
            self.grid_layout.setColumnStretch(1, 5)
            self.grid_layout.setRowStretch(0, 1)
            self.grid_layout.setRowStretch(1, 0)
            
            # Change window dimensions and allow resizes
            self.setMinimumSize(850, 600)
            self.setMaximumSize(16777215, 16777215)
            self.resize(950, 700)
            
            self.layout_toggle_btn.setText("📱 Switch to Mobile View")
            self.status_bar_label.setText("Ready • Desktop side-by-side layout active")
        else:
            # Stacked vertical layout for Mobile
            self.grid_layout.addWidget(self.console_frame, 0, 0)
            self.grid_layout.addWidget(self.history_frame, 1, 0)
            
            # Reset grid stretches
            self.grid_layout.setColumnStretch(0, 1)
            self.grid_layout.setColumnStretch(1, 0)
            self.grid_layout.setRowStretch(0, 0)
            self.grid_layout.setRowStretch(1, 1)
            
            # Constrain window to mobile aspect ratio
            self.setMinimumSize(360, 640)
            self.setMaximumSize(500, 900)
            self.resize(420, 750)
            
            self.layout_toggle_btn.setText("💻 Switch to Desktop View")
            self.status_bar_label.setText("Ready • Mobile stacked layout active")

    @pyqtSlot()
    def on_layout_toggle_clicked(self):
        """Toggle layout mode and persist in settings."""
        self.is_desktop_layout = not self.is_desktop_layout
        self.settings.setValue("is_desktop_layout", self.is_desktop_layout)
        
        self.apply_layout_mode(self.is_desktop_layout)
        
        # Re-apply FFmpeg warning style if it was active
        if not self.ffmpeg_present:
            self.status_bar_label.setText("Ready (⚠️ FFmpeg not detected: 1080p+ merging and MP3 conversion are disabled. Pre-merged fallback enabled.)")
            self.status_bar_label.setStyleSheet("color: #f59e0b;")

    @pyqtSlot()
    def on_url_changed(self):
        """Hide the details preview frame when the user starts typing a new URL."""
        if self.preview_frame.isVisible():
            self.preview_frame.setVisible(False)
            self.current_metadata = None

    @pyqtSlot()
    def on_paste_clicked(self):
        """Pastes the text from the system clipboard into the URL input field."""
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if text:
            self.url_input.setText(text)
            self.status_bar_label.setText("Pasted link from clipboard.")

    @pyqtSlot()
    def on_clear_clicked(self):
        """Clears the URL input field."""
        self.url_input.clear()
        self.status_bar_label.setText("Cleared link input.")

    @pyqtSlot()
    def on_fetch_clicked(self):
        """Spawns an asynchronous MetadataFetcherThread to query yt-dlp."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid YouTube video URL.")
            return

        self.fetch_thread = MetadataFetcherThread(url)
        self.fetch_thread.fetch_started.connect(self.on_fetch_started)
        self.fetch_thread.fetch_completed.connect(self.on_fetch_completed)
        self.fetch_thread.fetch_failed.connect(self.on_fetch_failed)
        self.fetch_thread.start()

    @pyqtSlot()
    def on_fetch_started(self):
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("⏳ Querying YouTube...")
        self.status_bar_label.setText("Querying YouTube metadata asynchronously...")

    @pyqtSlot(dict)
    def on_fetch_completed(self, data):
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("🔍 Fetch Info")
        self.status_bar_label.setText("Successfully loaded metadata.")
        
        self.current_metadata = data
        
        # Populate GUI preview details
        self.video_title_label.setText(data['title'])
        self.video_meta_label.setText(f"Duration: {data['duration']}   •   Views: {data['views']}\nChannel: {data['author']}")
        
        # Set Thumbnail
        pixmap = QPixmap()
        if data.get('thumbnail_bytes'):
            pixmap.loadFromData(data['thumbnail_bytes'])
        else:
            pixmap = QPixmap(200, 112)
            pixmap.fill(Qt.black)
        self.thumbnail_label.setPixmap(pixmap)
        
        # Populate resolutions dropdown
        self.quality_combo.clear()
        self.quality_combo.addItem("Best Quality")
        for h in data['resolutions']:
            self.quality_combo.addItem(f"{h}p")
        self.quality_combo.addItem("Audio Only (M4A)")
        self.quality_combo.addItem("Audio Only (MP3)")
        
        # Show video information card preview
        self.preview_frame.setVisible(True)

    @pyqtSlot(str)
    def on_fetch_failed(self, error):
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("🔍 Fetch Info")
        self.status_bar_label.setText("Fetch failed.")
        self.preview_frame.setVisible(False)
        self.current_metadata = None
        
        clean_error = error.split('\n')[0]
        QMessageBox.critical(self, "Metadata Fetch Failed", f"Failed to retrieve video details.\n\nError: {clean_error}")

    @pyqtSlot()
    def on_browse_clicked(self):
        """Open a directory chooser dialog and persist folder settings."""
        current_dir = self.save_dir_input.text()
        chosen_dir = QFileDialog.getExistingDirectory(self, "Select Download Directory", current_dir)
        if chosen_dir:
            self.save_dir_input.setText(chosen_dir)
            self.settings.setValue("download_directory", chosen_dir)

    @pyqtSlot()
    def on_download_clicked(self):
        """Spawns an asynchronous DownloadWorkerThread to download the video."""
        if not self.current_metadata:
            return
            
        url = self.current_metadata['url']
        title = self.current_metadata['title']
        output_dir = self.save_dir_input.text().strip()
        quality = self.quality_combo.currentText()
        
        # Validate output directory
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                QMessageBox.critical(self, "Folder Error", f"Could not create output directory:\n{str(e)}")
                return

        # Create download card and inject to layout
        card_widgets = self.create_download_card(title, quality)
        
        # Instantiate worker thread
        worker = DownloadWorkerThread(url, output_dir, quality, video_title=title)
        
        # Save record
        self.active_downloads[worker] = {
            'card_widget': card_widgets['card'],
            'title': title,
            'quality': quality,
            'output_dir': output_dir,
            'meta_label': card_widgets['meta_label'],
            'progress_bar': card_widgets['progress_bar'],
            'progress_text': card_widgets['status_text'],
            'open_btn': card_widgets['open_btn'],
            'delete_btn': card_widgets['delete_btn'],
            'saved_path': "",
            'status': "Downloading"
        }
        
        # Connect signals
        worker.download_progress.connect(lambda stats, w=worker: self.on_download_progress(w, stats))
        worker.download_completed.connect(lambda path, w=worker: self.on_download_completed(w, path))
        worker.download_failed.connect(lambda err, w=worker: self.on_download_failed(w, err))
        
        worker.start()
        
        self.status_bar_label.setText(f"Started downloading: {title}")
        
        # Reset fetch console input to allow concurrent downloads
        self.url_input.clear()
        self.preview_frame.setVisible(False)
        self.current_metadata = None

    # =========================================================================
    # MOBILE CARD GENERATION
    # =========================================================================
    def create_download_card(self, title, quality, size="Waiting...", status_desc="Connecting..."):
        """Generates a premium self-contained mobile QFrame card for queue layout."""
        card = QFrame()
        card.setObjectName("cardFrame")
        card.setStyleSheet("QFrame#cardFrame { background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; }")
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)
        
        # Title Label
        title_label = QLabel(title)
        title_label.setObjectName("videoTitle")
        title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #f1f5f9;")
        title_label.setWordWrap(True)
        
        # Meta info
        meta_label = QLabel(f"Format: {quality}   •   Size: {size}")
        meta_label.setObjectName("videoMeta")
        meta_label.setStyleSheet("font-size: 11px; color: #94a3b8;")
        
        # Progress Bar
        pbar = QProgressBar()
        pbar.setValue(0)
        pbar.setFixedHeight(12)
        
        # Status details
        status_text = QLabel(status_desc)
        status_text.setObjectName("subtitleLabel")
        status_text.setStyleSheet("font-size: 11px; color: #94a3b8;")
        status_text.setWordWrap(True)
        
        # Actions row
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)
        
        open_btn = QPushButton("📂 Open")
        open_btn.setObjectName("iconButton")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setFixedHeight(30)
        open_btn.setEnabled(False)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setObjectName("iconButton")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setFixedHeight(30)
        delete_btn.setEnabled(False)
        
        actions_layout.addWidget(open_btn)
        actions_layout.addWidget(delete_btn)
        actions_layout.addStretch()
        
        card_layout.addWidget(title_label)
        card_layout.addWidget(meta_label)
        card_layout.addWidget(pbar)
        card_layout.addWidget(status_text)
        card_layout.addLayout(actions_layout)
        
        # Insert card widget right before the bottom stretch (index 0)
        self.history_list_layout.insertWidget(0, card)
        
        return {
            'card': card,
            'meta_label': meta_label,
            'progress_bar': pbar,
            'status_text': status_text,
            'open_btn': open_btn,
            'delete_btn': delete_btn
        }

    # =========================================================================
    # PROGRESS & SIGNAL HANDLING
    # =========================================================================
    def on_download_progress(self, worker, stats):
        """Updates progress stats inside the specific download card."""
        if worker not in self.active_downloads:
            return
            
        data = self.active_downloads[worker]
        
        percent = int(stats['percentage'])
        data['progress_bar'].setValue(percent)
        
        speed = stats['speed']
        eta = stats['eta']
        data['progress_text'].setText(f"{percent}% Completed  •  {speed}  •  ETA: {eta}")
        data['meta_label'].setText(f"Format: {data['quality']}   •   Size: {stats['size_info']}")

    def on_download_completed(self, worker, filepath):
        """Updates download status, file metrics, and enables click actions on complete."""
        if worker not in self.active_downloads:
            return
            
        data = self.active_downloads[worker]
        
        # Update progress visual
        data['progress_bar'].setValue(100)
        data['progress_text'].setText("✓ Completed successfully")
        data['progress_text'].setStyleSheet("font-size: 11px; color: #10b981; font-weight: bold;")
        
        # Size calculations
        file_size_mb = "N/A"
        if os.path.exists(filepath):
            size_bytes = os.path.getsize(filepath)
            file_size_mb = f"{size_bytes / (1024 * 1024):.1f} MB"
        data['meta_label'].setText(f"Format: {data['quality']}   •   Size: {file_size_mb}")
        
        data['saved_path'] = filepath
        data['status'] = "Completed"
        
        # Enable action buttons
        data['open_btn'].setEnabled(True)
        data['open_btn'].clicked.connect(lambda checked=False, path=filepath: self.on_open_file_folder(path))
        
        data['delete_btn'].setEnabled(True)
        data['delete_btn'].clicked.connect(lambda checked=False, w=worker: self.on_delete_row(w))
        
        self.status_bar_label.setText(f"Completed download: {data['title']}")
        
        worker.deleteLater()
        self.save_history()

    def on_download_failed(self, worker, error):
        """Displays error details cleanly in the card frame."""
        if worker not in self.active_downloads:
            return
            
        data = self.active_downloads[worker]
        
        data['progress_bar'].setValue(0)
        data['progress_text'].setText(f"❌ Failed: {error.split('\n')[0]}")
        data['progress_text'].setStyleSheet("font-size: 11px; color: #f43f5e; font-weight: bold;")
        
        data['status'] = "Failed"
        data['delete_btn'].setEnabled(True)
        data['delete_btn'].clicked.connect(lambda checked=False, w=worker: self.on_delete_row(w))
        
        self.status_bar_label.setText(f"Download failed for: {data['title']}")
        
        worker.deleteLater()
        self.save_history()

    def on_open_file_folder(self, filepath):
        """Open the system directory containing the downloaded file."""
        if not filepath or not os.path.exists(filepath):
            QMessageBox.warning(self, "File Not Found", "The downloaded file could not be found.")
            return
            
        folder = os.path.dirname(filepath)
        if sys.platform == 'win32':
            os.startfile(folder)
        elif sys.platform == 'darwin':
            import subprocess
            subprocess.Popen(['open', folder])
        else: # Linux/Unix
            import subprocess
            subprocess.Popen(['xdg-open', folder])

    def on_delete_row(self, worker_key):
        """Removes a download card from the vertical list layout."""
        if worker_key not in self.active_downloads:
            return
            
        data = self.active_downloads[worker_key]
        
        # Remove from UI Layout
        card_widget = data['card_widget']
        self.history_list_layout.removeWidget(card_widget)
        card_widget.deleteLater()
        
        # Delete reference from dictionary
        self.active_downloads.pop(worker_key)
        self.save_history()

    def on_clear_history_clicked(self):
        """Clear all completed and failed history cards, keeping active tasks."""
        to_remove = []
        for w, stats in list(self.active_downloads.items()):
            if stats['status'] in ["Completed", "Failed"]:
                to_remove.append(w)
                
        if not to_remove:
            return
            
        for w in to_remove:
            self.on_delete_row(w)
            
        self.status_bar_label.setText("History cleared.")

    # =========================================================================
    # HISTORY PERSISTENCE
    # =========================================================================
    def save_history(self):
        """Serializes current download history list and writes it to QSettings."""
        history_list = []
        for w, stats in self.active_downloads.items():
            if stats['status'] in ["Completed", "Failed"]:
                size_str = stats['meta_label'].text().split("• Size:")[-1].strip()
                history_list.append({
                    'title': stats['title'],
                    'quality': stats['quality'],
                    'output_dir': stats['output_dir'],
                    'saved_path': stats['saved_path'],
                    'status': stats['status'],
                    'size': size_str
                })
        
        try:
            self.settings.setValue("download_history", json.dumps(history_list))
        except Exception:
            pass

    def load_history(self):
        """Deserializes and reconstructs the historical table rows from QSettings."""
        history_data = self.settings.value("download_history")
        if not history_data:
            return
            
        try:
            history_list = json.loads(history_data)
            
            for item in history_list:
                # Re-create card frame
                card_widgets = self.create_download_card(
                    item['title'], item['quality'], 
                    size=item['size'], status_desc="Completed" if item['status'] == "Completed" else "Failed"
                )
                
                # Setup statuses
                if item['status'] == "Completed":
                    card_widgets['progress_bar'].setValue(100)
                    card_widgets['status_text'].setText("✓ Completed")
                    card_widgets['status_text'].setStyleSheet("font-size: 11px; color: #10b981; font-weight: bold;")
                    card_widgets['open_btn'].setEnabled(True)
                    path = item['saved_path']
                    card_widgets['open_btn'].clicked.connect(lambda checked=False, p=path: self.on_open_file_folder(p))
                else:
                    card_widgets['progress_bar'].setValue(0)
                    card_widgets['status_text'].setText("❌ Failed")
                    card_widgets['status_text'].setStyleSheet("font-size: 11px; color: #f43f5e; font-weight: bold;")
                
                # Mock worker key for mapping card events
                class MockWorkerKey:
                    pass
                worker_key = MockWorkerKey()
                
                self.active_downloads[worker_key] = {
                    'card_widget': card_widgets['card'],
                    'title': item['title'],
                    'quality': item['quality'],
                    'output_dir': item['output_dir'],
                    'meta_label': card_widgets['meta_label'],
                    'progress_bar': card_widgets['progress_bar'],
                    'progress_text': card_widgets['status_text'],
                    'open_btn': card_widgets['open_btn'],
                    'delete_btn': card_widgets['delete_btn'],
                    'saved_path': item['saved_path'],
                    'status': item['status']
                }
                
                card_widgets['delete_btn'].setEnabled(True)
                card_widgets['delete_btn'].clicked.connect(lambda checked=False, w=worker_key: self.on_delete_row(w))
                
        except Exception:
            pass

    def closeEvent(self, event):
        """Ensure active download threads are safely completed before exiting."""
        active = [w for w, stats in self.active_downloads.items() if stats['status'] == "Downloading"]
        if active:
            reply = QMessageBox.question(
                self, 'Active Downloads',
                "There are active downloads in progress. Are you sure you want to exit? "
                "Exiting will terminate active downloads.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                # Force kill active threads
                for w in active:
                    try:
                        w.terminate()
                        w.wait()
                    except Exception:
                        pass
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    # Configure high-DPI scaling for crisp visual typography on mobile/high-res displays
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    
    window = YouTubeDownloaderApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
