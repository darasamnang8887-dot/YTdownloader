# Premium QSS Style Sheets for YouTube Downloader
# Designed with a slate dark theme, neon gradients, and elegant hover animations

DARK_STYLE = """
/* Global Window Style */
QMainWindow {
    background-color: #0f172a;
}

QWidget {
    color: #f8fafc;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, sans-serif;
    font-size: 13px;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #0f172a;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #0f172a;
    height: 8px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #334155;
    min-width: 20px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #475569;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
    width: 0px;
}

/* Glassmorphism Panel Container */
QFrame#cardFrame {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
}

QFrame#statusCard {
    background-color: #1a2236;
    border: 1px dashed #475569;
    border-radius: 8px;
}

/* Typography Details */
QLabel#titleLabel {
    font-size: 24px;
    font-weight: 800;
    color: #f8fafc;
}

QLabel#subtitleLabel {
    font-size: 12px;
    color: #94a3b8;
}

QLabel#sectionTitle {
    font-size: 15px;
    font-weight: 700;
    color: #38bdf8;
    text-transform: uppercase;
    letter-spacing: 1px;
}

QLabel#videoTitle {
    font-size: 14px;
    font-weight: 700;
    color: #f1f5f9;
}

QLabel#videoMeta {
    font-size: 12px;
    color: #94a3b8;
}

QLabel#statusLabel {
    font-size: 12px;
    font-weight: 600;
}

/* Input Fields */
QLineEdit {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 10px 14px;
    color: #f8fafc;
    font-size: 13px;
    selection-background-color: #0284c7;
}

QLineEdit:focus {
    border: 1.5px solid #0ea5e9;
    background-color: #0f172a;
}

QLineEdit:disabled {
    background-color: #0f172a;
    color: #64748b;
    border: 1px solid #1e293b;
}

/* ComboBox */
QComboBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    color: #f8fafc;
    min-width: 120px;
}

QComboBox:focus {
    border: 1.5px solid #0ea5e9;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 30px;
    border-left-width: 0px;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

QComboBox::down-arrow {
    image: none;
    border: 5px solid transparent;
    border-top-color: #94a3b8;
    margin-top: 4px;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    color: #f8fafc;
    selection-background-color: #0ea5e9;
    selection-color: #ffffff;
    padding: 4px;
    outline: none;
}

/* Buttons */
QPushButton {
    background-color: #334155;
    border: 1px solid #475569;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    color: #f8fafc;
}

QPushButton:hover {
    background-color: #475569;
    border-color: #64748b;
}

QPushButton:pressed {
    background-color: #1e293b;
}

QPushButton:disabled {
    background-color: #0f172a;
    color: #475569;
    border: 1px solid #1e293b;
}

/* Premium Gradient Action Buttons */
QPushButton#primaryButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0ea5e9, stop:1 #2563eb);
    border: none;
    color: #ffffff;
    font-weight: 700;
    letter-spacing: 0.5px;
}

QPushButton#primaryButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #3b82f6);
}

QPushButton#primaryButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #1d4ed8);
}

QPushButton#primaryButton:disabled {
    background: #1e293b;
    color: #475569;
    border: 1px solid #334155;
}

QPushButton#accentButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
    border: none;
    color: #ffffff;
    font-weight: 700;
}

QPushButton#accentButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 #10b981);
}

QPushButton#accentButton:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #047857);
}

QPushButton#accentButton:disabled {
    background: #1e293b;
    color: #475569;
    border: 1px solid #334155;
}

/* Secondary Actions like Browse Folder */
QPushButton#iconButton {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
}

QPushButton#iconButton:hover {
    background-color: #334155;
    border-color: #475569;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #334155;
    background-color: #0f172a;
    border-radius: 6px;
    text-align: center;
    color: #f8fafc;
    font-weight: bold;
    font-size: 11px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0ea5e9, stop:1 #10b981);
    border-radius: 5px;
}

/* Modern Dynamic Table for History / Active Tasks */
QTableWidget {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    gridline-color: #334155;
    color: #e2e8f0;
}

QTableWidget::item {
    padding: 8px 12px;
    border-bottom: 1px solid #334155;
}

QTableWidget::item:selected {
    background-color: #334155;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #0f172a;
    color: #94a3b8;
    padding: 8px 12px;
    font-weight: 700;
    border: none;
    border-bottom: 1.5px solid #334155;
}

QTableCornerButton::section {
    background-color: #0f172a;
    border: none;
}

/* Badges / Tooltips */
QToolTip {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 4px;
    color: #f8fafc;
    padding: 5px;
}
"""
