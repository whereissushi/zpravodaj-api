#!/usr/bin/env python3
"""
PDF to Flipbook Converter - Cloud API Version
Konvertuje PDF zpravodaj na interaktivní HTML flipbook (PyMuPDF verze)
"""

import io
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image
import pytesseract
import json


class PDFToFlipbook:
    def __init__(self, pdf_bytes, title="Zpravodaj"):
        """
        Initialize converter with PDF bytes

        Args:
            pdf_bytes: PDF file as bytes
            title: Title for the flipbook
        """
        self.pdf_bytes = pdf_bytes
        self.title = title
        self.pages_images = []  # Full size JPEGs
        self.thumb_images = []  # Thumbnails
        self.page_texts = {}  # OCR extracted text

    def convert(self):
        """
        Main conversion function - returns dict with all assets

        Returns:
            dict with keys: 'html', 'css', 'js', 'pages', 'thumbs', 'search_data'
        """
        # Convert PDF to images
        self._convert_pdf_to_images()

        # Extract text with OCR
        self._extract_text_ocr()

        # Generate search data JSON
        search_data = json.dumps({
            "pages": self.page_texts
        }, ensure_ascii=False, indent=2)

        # Generate HTML/CSS/JS with embedded search data
        html = self._generate_html(len(self.pages_images), search_data)
        css = self._get_css()
        js = self._get_js()

        # Debug: Print sample of search data
        if self.page_texts:
            first_page = list(self.page_texts.keys())[0]
            sample_text = self.page_texts[first_page][:100] if self.page_texts[first_page] else "EMPTY"
            print(f"Search data sample (page {first_page}): {sample_text}...")
            print(f"Total pages with text: {len([t for t in self.page_texts.values() if t])}")

        return {
            'html': html,
            'css': css,
            'js': js,
            'pages': self.pages_images,  # List of bytes (JPEG)
            'thumbs': self.thumb_images,  # List of bytes (JPEG)
            'search_data': search_data,  # JSON string
            'page_count': len(self.pages_images),
            'pdf': self.pdf_bytes  # Original PDF for download
        }

    def _convert_pdf_to_images(self):
        """Convert PDF pages to images using PyMuPDF"""
        # Open PDF from bytes
        pdf_document = fitz.open(stream=self.pdf_bytes, filetype="pdf")

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]

            # Render page to image (150 DPI for full size)
            mat = fitz.Matrix(150/72, 150/72)  # 72 is default DPI
            pix = page.get_pixmap(matrix=mat, alpha=False)

            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Save full-size image to bytes
            page_bytes = io.BytesIO()
            img.save(page_bytes, 'JPEG', quality=85, optimize=True)
            self.pages_images.append(page_bytes.getvalue())

            # Create thumbnail
            thumb = img.copy()
            thumb.thumbnail((200, 300), Image.Resampling.LANCZOS)
            thumb_bytes = io.BytesIO()
            thumb.save(thumb_bytes, 'JPEG', quality=75)
            self.thumb_images.append(thumb_bytes.getvalue())

        pdf_document.close()

    def _extract_text_ocr(self):
        """Extract text from page images using OCR"""
        total = len(self.pages_images)
        print(f"Starting OCR extraction for {total} pages...")

        for i, page_bytes in enumerate(self.pages_images, start=1):
            try:
                # Open image from bytes
                img = Image.open(io.BytesIO(page_bytes))

                # Resize image to speed up OCR (max width 2000px)
                max_width = 2000
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_size = (max_width, int(img.height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)

                # Run OCR with Czech language
                text = pytesseract.image_to_string(img, lang='ces', config='--psm 1')
                self.page_texts[str(i)] = text.strip()

                # Progress logging
                if i % 5 == 0 or i == total:
                    print(f"  OCR progress: {i}/{total} pages ({int(i/total*100)}%)")
            except Exception as e:
                print(f"  WARNING: OCR failed on page {i}: {e}")
                self.page_texts[str(i)] = ""

    def _generate_html(self, page_count, search_data_json):
        """Generate HTML content with embedded search data"""
        return f'''<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>{self.title}</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <!-- Local JS libraries for offline support -->
    <script src="js/jquery-3.6.0.min.js"></script>
    <script src="js/turn.min.js"></script>
    <script src="js/qrcode.min.js"></script>
    <!-- Google Analytics -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', 'G-XXXXXXXXXX');
    </script>
    <!-- Version: 3.0 - Turn.js with Drag-to-Flip - 2025-10-31 -->
</head>
<body>
    <div id="flipbook-container">
        <!-- Modrý toolbar -->
        <div id="flipbook-toolbar">
            <button id="search-btn" class="toolbar-btn" title="Vyhledávání">
                <i class="fas fa-search"></i>
            </button>
            <button id="menu-btn" class="toolbar-btn" title="Obsah">
                <i class="fas fa-list"></i>
            </button>
            <button id="zoom-toggle-btn" class="toolbar-btn" title="Přiblížení">
                <i class="fas fa-search-plus"></i>
            </button>
            <button id="prev-page-btn" class="toolbar-btn" title="Předchozí">
                <i class="fas fa-chevron-left"></i>
            </button>
            <button id="next-page-btn" class="toolbar-btn" title="Další">
                <i class="fas fa-chevron-right"></i>
            </button>

            <div id="page-info">
                <span id="current-page">1</span> / {page_count}
            </div>

            <button id="first-page-btn" class="toolbar-btn" title="První stránka">
                <i class="fas fa-backward-step"></i>
            </button>
            <button id="last-page-btn" class="toolbar-btn" title="Poslední stránka">
                <i class="fas fa-forward-step"></i>
            </button>
            <button id="share-btn" class="toolbar-btn" title="Sdílet">
                <i class="fas fa-share-alt"></i>
            </button>
            <button id="fullscreen-btn" class="toolbar-btn" title="Celá obrazovka">
                <i class="fas fa-expand"></i>
            </button>
            <button id="download-pdf-btn" class="toolbar-btn" title="Stáhnout PDF">
                <i class="fas fa-file-pdf"></i>
            </button>
        </div>

        <!-- Thumbnail sidebar (toggled by menu button) -->
        <div id="thumbnail-sidebar" class="thumbnail-sidebar-hidden">
            <div id="thumbnail-sidebar-content">
                {''.join(f'<div class="thumbnail-item" data-page="{i}"><img src="files/thumb/{i}.jpg" alt="Stránka {i}"><span class="thumb-page-num">{i}</span></div>' for i in range(1, page_count + 1))}
            </div>
        </div>

        <div id="flipbook-viewer">
            <div id="flipbook">
                {''.join(f'<div class="page"><img src="files/pages/{i}.jpg" alt="Stránka {i}"></div>' for i in range(1, page_count + 1))}
            </div>
        </div>
    </div>

    <!-- Search overlay -->
    <div id="search-overlay" style="display: none;">
        <div class="search-modal">
            <h2>Vyhledávání</h2>
            <input type="text" id="search-input" placeholder="Zadejte hledaný text...">
            <div id="search-results"></div>
            <button id="search-close-btn">Zavřít</button>
        </div>
    </div>

    <!-- AI Summary overlay -->
    <div id="ai-summary-overlay" style="display: none;">
        <div class="search-modal">
            <h2>AI Shrnutí Zpravodaje</h2>
            <div id="ai-summary-content">
                <p style="text-align: center; color: #666;">
                    <i class="fas fa-spinner fa-spin" style="font-size: 24px;"></i><br>
                    Generuji shrnutí pomocí AI...
                </p>
            </div>
            <button id="ai-summary-close-btn">Zavřít</button>
        </div>
    </div>

    <!-- Menu overlay -->
    <div id="menu-overlay" style="display: none;">
        <div class="search-modal">
            <h2>Obsah</h2>
            <div id="menu-content"></div>
            <button id="menu-close-btn">Zavřít</button>
        </div>
    </div>

    <!-- Share overlay with QR code -->
    <div id="share-overlay" style="display: none;">
        <div class="search-modal share-modal">
            <h2>Sdílet</h2>
            <div id="share-content">
                <div id="qr-code-container" style="text-align: center; margin: 20px 0;">
                    <div id="qrcode"></div>
                    <p style="margin-top: 10px; font-size: 12px; color: #666;">QRCode</p>
                </div>
                <div style="margin: 20px 0;">
                    <label style="display: block; margin-bottom: 8px; font-weight: 500; color: #333;">Sdílet:</label>
                    <div style="display: flex; gap: 8px;">
                        <input type="text" id="share-url-input" readonly style="flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;">
                        <button id="copy-url-btn" style="padding: 10px 20px; background: #2563a6; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
                            Kopírovat
                        </button>
                    </div>
                </div>
            </div>
            <button id="share-close-btn">Zavřít</button>
        </div>
    </div>

    <!-- Simple zoom panel like Munipolis -->
    <div id="zoom-panel" style="display: none;">
        <button id="zoom-out" class="zoom-btn" title="Oddálit">
            <i class="fas fa-minus"></i>
        </button>
        <span id="zoom-value">100%</span>
        <button id="zoom-in" class="zoom-btn" title="Přiblížit">
            <i class="fas fa-plus"></i>
        </button>
        <button id="zoom-fit" class="zoom-btn" title="Přizpůsobit šířce">
            <i class="fas fa-expand-arrows-alt"></i>
        </button>
        <button id="zoom-reset" class="zoom-btn" title="Původní velikost">
            <i class="fas fa-compress-arrows-alt"></i>
        </button>
        <button id="pan-tool" class="zoom-btn" title="Posun obrazu">
            <i class="fas fa-hand"></i>
        </button>
    </div>

    <script>
        const totalPages = {page_count};
        // Embedded search data for offline use
        const searchDataEmbedded = {search_data_json};
    </script>
    <script src="js/flipbook.js?v=3"></script>
</body>
</html>'''

    def _get_css(self):
        """Return CSS content"""
        return '''* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: #e8e8e8;
    color: #333;
    overflow: hidden;
    height: 100vh;
}

#flipbook-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

/* Modrý toolbar inspirovaný Munipolis */
#flipbook-toolbar {
    background: #2563a6;
    padding: 8px 15px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 5px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    z-index: 100;
}

.toolbar-btn {
    background: transparent;
    color: white;
    border: none;
    padding: 8px 12px;
    cursor: pointer;
    border-radius: 3px;
    font-size: 16px;
    transition: background 0.2s;
}

.toolbar-btn:hover {
    background: rgba(255, 255, 255, 0.15);
}

.toolbar-btn:active {
    background: rgba(255, 255, 255, 0.25);
}

#page-info {
    background: white;
    color: #333;
    padding: 4px 12px;
    border-radius: 3px;
    font-size: 14px;
    margin: 0 10px;
    min-width: 60px;
    text-align: center;
}

#current-page {
    font-weight: 600;
}

#flipbook-viewer {
    flex: 1;
    position: relative;
    overflow: hidden; /* Default hidden, auto when zoomed via JS */
    background: #e8e8e8;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    margin: 0;
}

#flipbook-viewer.pan-mode {
    cursor: grab !important;
}

#flipbook-viewer.pan-mode:active {
    cursor: grabbing !important;
}

#flipbook-viewer.zoomed.pan-mode {
    cursor: move;
}

/* Zoom cursor mode - highest priority */
#flipbook-viewer.zoom-cursor-mode,
#flipbook-viewer.zoom-cursor-mode *,
#flipbook-viewer.zoom-cursor-mode .page,
#flipbook-viewer.zoom-cursor-mode.zoomed {
    cursor: zoom-in !important;
}

#zoom-container {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
}

#flipbook {
    position: relative;
    /* Dynamic sizing handled by JavaScript */
}

#flipbook .page {
    width: 50%;
    height: 100%;
    background-color: white;
    background-size: cover;
    background-position: center;
    pointer-events: auto;
    user-select: none;
    overflow: hidden;
}

#flipbook .page img {
    width: 100%;
    height: 100%;
    object-fit: cover; /* Changed from contain to cover to fill entire page */
    object-position: center;
    pointer-events: none;
    user-select: none;
}

/* Turn.js corner areas - make them bigger */
.turn-page-wrapper .corner {
    width: 100px !important;
    height: 100px !important;
}

/* Turn.js shadows */
#flipbook .even .gradient {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(to right, rgba(0,0,0,0) 0%, rgba(0,0,0,0.2) 100%);
}

#flipbook .odd .gradient {
    position: absolute;
    top: 0;
    right: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(to left, rgba(0,0,0,0) 0%, rgba(0,0,0,0.15) 100%);
}

/* Zoom container */
.zoomed-view {
    cursor: move;
    cursor: grab;
}

.zoomed-view:active {
    cursor: grabbing;
}

/* Thumbnail sidebar (left side) */
#thumbnail-sidebar {
    position: fixed;
    left: 0;
    top: 48px; /* Below toolbar */
    width: 180px;
    height: calc(100vh - 48px);
    background: #f8f9fa;
    border-right: 1px solid #ddd;
    overflow-y: auto;
    z-index: 50;
    transition: transform 0.3s ease;
}

#thumbnail-sidebar.thumbnail-sidebar-hidden {
    transform: translateX(-100%);
}

#thumbnail-sidebar-content {
    padding: 10px;
}

.thumbnail-item {
    position: relative;
    margin-bottom: 15px;
    cursor: pointer;
    border: 3px solid transparent;
    border-radius: 4px;
    overflow: hidden;
    transition: all 0.2s;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.thumbnail-item:hover {
    transform: translateX(5px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.thumbnail-item.active {
    border-color: #2563a6;
    background: #e3f2fd;
}

.thumbnail-item img {
    width: 100%;
    display: block;
}

.thumb-page-num {
    position: absolute;
    bottom: 5px;
    right: 5px;
    background: rgba(37, 99, 166, 0.9);
    color: white;
    padding: 3px 8px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: bold;
}

#thumbnail-sidebar::-webkit-scrollbar {
    width: 8px;
}

#thumbnail-sidebar::-webkit-scrollbar-track {
    background: #f1f1f1;
}

#thumbnail-sidebar::-webkit-scrollbar-thumb {
    background: #2563a6;
    border-radius: 4px;
}

#thumbnail-sidebar::-webkit-scrollbar-thumb:hover {
    background: #1e4f8a;
}

@media (max-width: 768px) {
    .toolbar-btn {
        padding: 6px 10px;
        font-size: 14px;
    }

    #page-info {
        font-size: 12px;
        padding: 3px 8px;
    }

    .nav-btn {
        font-size: 32px;
        padding: 15px 10px;
    }

    #thumbnail-sidebar {
        width: 140px;
    }

    #page-container {
        gap: 0;
        max-width: 100%;
    }

    .page-spread {
        width: 100%;
    }

    .page-left + .page-right {
        display: none;
    }
}

::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #1a1a1a;
}

::-webkit-scrollbar-thumb {
    background: #4a4a4a;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #5a5a5a;
}

/* All overlays - Munipolis style (no black background) */
#search-overlay,
#zoom-menu-overlay,
#share-overlay,
#ai-summary-overlay,
#menu-overlay {
    position: fixed;
    top: 48px; /* Under toolbar */
    right: 20px;
    z-index: 1000;
    display: flex;
    align-items: flex-start;
    justify-content: flex-end;
}

.search-modal {
    background: white;
    padding: 25px;
    border-radius: 12px;
    max-width: 500px;
    width: auto;
    min-width: 350px;
    max-height: calc(100vh - 80px);
    overflow-y: auto;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2), 0 2px 8px rgba(0,0,0,0.1);
    border: 1px solid #e0e0e0;
}

.search-modal h2 {
    margin-bottom: 20px;
    color: #2563a6;
}

#search-input {
    width: 100%;
    padding: 12px;
    border: 2px solid #2563a6;
    border-radius: 4px;
    font-size: 16px;
    margin-bottom: 15px;
}

#search-results {
    max-height: 400px;
    overflow-y: auto;
    margin: 15px 0;
}

.search-result-item {
    padding: 12px;
    margin: 8px 0;
    background: #f5f5f5;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s;
}

.search-result-item:hover {
    background: #e0e0e0;
}

.search-result-page {
    font-weight: bold;
    color: #2563a6;
    margin-bottom: 5px;
}

.search-result-snippet {
    font-size: 14px;
    color: #666;
}

.search-highlight {
    background: yellow;
    font-weight: bold;
}

#search-close-btn {
    background: #2563a6;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
}

#search-close-btn:hover {
    background: #1e4f8a;
}

/* AI Summary & Menu close buttons */
#ai-summary-close-btn, #menu-close-btn {
    background: #2563a6;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    margin-top: 15px;
}

#ai-summary-close-btn:hover, #menu-close-btn:hover {
    background: #1e4f8a;
}

/* AI Summary result styling */
.ai-summary-result {
    background: #f9f9f9;
    padding: 15px;
    border-radius: 6px;
    border-left: 4px solid #2563a6;
}

.ai-summary-result h3 {
    color: #2563a6;
    margin-bottom: 15px;
    font-size: 18px;
}

.ai-summary-result h4 {
    color: #333;
    margin-top: 15px;
    margin-bottom: 8px;
    font-size: 15px;
}

.ai-summary-result ul {
    margin-left: 20px;
    margin-bottom: 10px;
}

.ai-summary-result li {
    margin: 5px 0;
    color: #555;
    line-height: 1.5;
}

/* Menu item styling */
.menu-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 15px;
    margin: 8px 0;
    background: #f5f5f5;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    border-left: 3px solid transparent;
}

.menu-item:hover {
    background: #e0e0e0;
    border-left-color: #2563a6;
    transform: translateX(2px);
}

.menu-item-text {
    flex: 1;
    font-size: 14px;
    color: #333;
    font-weight: 500;
}

.menu-item-page {
    font-size: 13px;
    color: #2563a6;
    font-weight: bold;
    background: rgba(37, 99, 166, 0.1);
    padding: 4px 10px;
    border-radius: 12px;
    margin-left: 10px;
}

/* Menu content scrolling */
#menu-content {
    max-height: 400px;
    overflow-y: auto;
    margin: 15px 0;
}

#menu-content::-webkit-scrollbar {
    width: 8px;
}

#menu-content::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

#menu-content::-webkit-scrollbar-thumb {
    background: #2563a6;
    border-radius: 4px;
}

#menu-content::-webkit-scrollbar-thumb:hover {
    background: #1e4f8a;
}

/* AI summary content scrolling */
#ai-summary-content {
    max-height: 500px;
    overflow-y: auto;
}

#ai-summary-content::-webkit-scrollbar {
    width: 8px;
}

#ai-summary-content::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

#ai-summary-content::-webkit-scrollbar-thumb {
    background: #2563a6;
    border-radius: 4px;
}

#ai-summary-content::-webkit-scrollbar-thumb:hover {
    background: #1e4f8a;
}

/* New zoom panel styling - Munipolis style */
#zoom-panel {
    position: fixed;
    top: 60px;
    left: 50%;
    transform: translateX(-50%);
    background: white;
    border: 1px solid #ddd;
    border-radius: 4px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    z-index: 1001; /* Higher than overlays to always be visible */
    height: 36px;
}

#zoom-panel .zoom-btn {
    width: 28px;
    height: 28px;
    padding: 0;
    border: none;
    background: transparent;
    color: #555;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 3px;
    transition: background 0.2s;
}

#zoom-panel .zoom-btn:hover {
    background: #f0f0f0;
}

#zoom-panel .zoom-btn.active {
    background: #e0e0e0;
    color: #2563a6;
}

#zoom-panel #zoom-value {
    min-width: 50px;
    text-align: center;
    font-size: 13px;
    color: #333;
    font-weight: 500;
    padding: 0 4px;
    border-left: 1px solid #ddd;
    border-right: 1px solid #ddd;
}

/* Keep old zoom styling for backward compatibility */
.zoom-options {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin: 20px 0;
}

.zoom-option-btn {
    padding: 12px 16px;
    background: #f5f5f5;
    border: 2px solid transparent;
    border-radius: 6px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 500;
    color: #333;
    transition: all 0.2s;
}

.zoom-option-btn:hover {
    background: #e3f2fd;
    border-color: #2563a6;
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.zoom-option-btn.active {
    background: #2563a6;
    color: white;
    border-color: #2563a6;
}

#zoom-slider {
    -webkit-appearance: none;
    appearance: none;
    height: 8px;
    background: #ddd;
    border-radius: 5px;
    outline: none;
}

#zoom-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    background: #2563a6;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s;
}

#zoom-slider::-webkit-slider-thumb:hover {
    background: #1e4f8a;
    transform: scale(1.2);
}

#zoom-slider::-moz-range-thumb {
    width: 20px;
    height: 20px;
    background: #2563a6;
    border-radius: 50%;
    cursor: pointer;
    border: none;
}

#zoom-menu-close-btn {
    background: #2563a6;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    margin-top: 15px;
}

#zoom-menu-close-btn:hover {
    background: #1e4f8a;
}'''

    def _get_js(self):
        """Return JavaScript content"""
        return '''// Configuration
let zoomLevel = 1;
const isMobile = window.innerWidth <= 768;

// Elements
const flipbook = $('#flipbook');
const currentPageSpan = $('#current-page');
const thumbnailSidebar = $('#thumbnail-sidebar');
const thumbnailItems = $('.thumbnail-item');

// Toolbar buttons
const searchBtn = $('#search-btn');
const menuBtn = $('#menu-btn');
const zoomToggleBtn = $('#zoom-toggle-btn');
const prevPageBtn = $('#prev-page-btn');
const nextPageBtn = $('#next-page-btn');
const firstPageBtn = $('#first-page-btn');
const lastPageBtn = $('#last-page-btn');
const shareBtn = $('#share-btn');
const fullscreenBtn = $('#fullscreen-btn');
const downloadPdfBtn = $('#download-pdf-btn');

// Overlays
const aiSummaryOverlay = $('#ai-summary-overlay');
const aiSummaryContent = $('#ai-summary-content');
const aiSummaryCloseBtn = $('#ai-summary-close-btn');
const menuOverlay = $('#menu-overlay');
const menuContent = $('#menu-content');
const menuCloseBtn = $('#menu-close-btn');
const shareOverlay = $('#share-overlay');
const shareUrlInput = $('#share-url-input');
const copyUrlBtn = $('#copy-url-btn');
const shareCloseBtn = $('#share-close-btn');

// New zoom panel elements
const zoomPanel = $('#zoom-panel');
const zoomOutBtn = $('#zoom-out');
const zoomInBtn = $('#zoom-in');
const zoomValue = $('#zoom-value');
const zoomFitBtn = $('#zoom-fit');
const zoomResetBtn = $('#zoom-reset');
const panToolBtn = $('#pan-tool');
let isPanMode = false;
let isZoomCursorMode = false; // New: track if zoom cursor is active

// Search elements
const searchOverlay = $('#search-overlay');
const searchInput = $('#search-input');
const searchResults = $('#search-results');
const searchCloseBtn = $('#search-close-btn');

// Zoom state
let zoomActive = false;
let zoomClickX = 0;
let zoomClickY = 0;

// Search data - use embedded data from HTML
let searchData = typeof searchDataEmbedded !== 'undefined' ? searchDataEmbedded : null;

// Log search data status
if (searchData) {
    console.log('Search data loaded successfully (embedded)!');
    console.log('Total pages:', Object.keys(searchData.pages).length);
    const firstPageText = searchData.pages['1'] || '';
    console.log('Sample page 1 length:', firstPageText.length, 'characters');
    console.log('Sample text:', firstPageText.substring(0, 100) + '...');
} else {
    console.warn('Search data not available - searching will not work');
}

// Initialize turn.js
$(document).ready(function() {
    // Calculate dimensions based on viewport
    const viewportWidth = $(window).width();
    const viewportHeight = $(window).height() - 48; // Minus toolbar height

    // Dynamic sizing based on screen resolution
    let bookWidth, bookHeight;
    if (isMobile) {
        bookWidth = Math.min(400, viewportWidth * 0.9);
        bookHeight = Math.min(600, viewportHeight * 0.8);
    } else {
        // Scale based on viewport - better for all screen sizes
        if (viewportWidth <= 1920) {
            // Smaller screens (1920x1080 and below)
            bookWidth = Math.min(1600, viewportWidth * 0.95);
            bookHeight = Math.min(950, viewportHeight * 0.95);
        } else {
            // Larger screens (1440p and above)
            bookWidth = Math.min(1400, viewportWidth * 0.7);
            bookHeight = Math.min(990, viewportHeight * 0.85);
        }
    }

    flipbook.turn({
        width: bookWidth,
        height: bookHeight,
        elevation: 50,
        gradients: true,
        autoCenter: true,
        duration: 600,
        acceleration: true,
        display: isMobile ? 'single' : 'double',
        page: 1,
        corners: 'all', // Enable all corners for dragging (larger area)
        when: {
            turning: function(e, page, view) {
                // Block turning if pan mode is active OR actively panning
                if (isPanMode || isPanning) {
                    e.preventDefault();
                    return false;
                }
            },
            turned: function(e, page) {
                currentPageSpan.text(page);
                updateThumbnails(page);
                // Google Analytics
                if (typeof gtag !== 'undefined') {
                    gtag('event', 'page_turn', {
                        'page_number': page
                    });
                }
            },
            start: function(e, pageObject, corner) {
                // Prevent drag-to-flip when pan mode is active OR actively panning
                if (isPanMode || isPanning) {
                    e.preventDefault();
                    return false;
                }
            }
        }
    });

    // Update page display
    currentPageSpan.text(1);
    updateThumbnails(1);

    // Handle window resize for responsive behavior
    $(window).on('resize', function() {
        const newViewportWidth = $(window).width();
        const newViewportHeight = $(window).height() - 48;

        let newBookWidth, newBookHeight;
        if (isMobile) {
            newBookWidth = Math.min(400, newViewportWidth * 0.9);
            newBookHeight = Math.min(600, newViewportHeight * 0.8);
        } else {
            if (newViewportWidth <= 1920) {
                newBookWidth = Math.min(1600, newViewportWidth * 0.95);
                newBookHeight = Math.min(950, newViewportHeight * 0.95);
            } else {
                newBookWidth = Math.min(1400, newViewportWidth * 0.7);
                newBookHeight = Math.min(990, newViewportHeight * 0.85);
            }
        }

        // Update turn.js dimensions
        flipbook.turn('size', newBookWidth, newBookHeight);
    });

    // Enhanced drag-to-flip functionality for entire page area
    let isDragging = false;
    let dragStartX = 0;
    let dragStartY = 0;
    let dragStartTime = 0;

    // Desktop drag-to-flip
    flipbook.on('mousedown', function(e) {
        // ALWAYS skip if pan mode is active - no drag-to-flip when pan tool is on
        if (isPanMode) return;

        // Also skip if actively panning
        if (isPanning) return;

        isDragging = true;
        dragStartX = e.pageX;
        dragStartY = e.pageY;
        dragStartTime = new Date().getTime();
        e.preventDefault();
    });

    $(document).on('mousemove', function(e) {
        if (!isDragging || isPanMode || isPanning) return;

        const dragDistance = e.pageX - dragStartX;
        const dragDistanceY = Math.abs(e.pageY - dragStartY);

        // Only flip if horizontal drag is more than vertical
        if (Math.abs(dragDistance) > 30 && dragDistanceY < 100) {
            isDragging = false;

            if (dragDistance < 0) {
                flipbook.turn('next');
            } else {
                flipbook.turn('previous');
            }
        }
    });

    $(document).on('mouseup', function(e) {
        if (!isDragging) return;

        const dragEndTime = new Date().getTime();
        const dragDuration = dragEndTime - dragStartTime;
        const dragDistance = e.pageX - dragStartX;

        // Quick flick gesture
        if (dragDuration < 300 && Math.abs(dragDistance) > 20) {
            if (dragDistance < 0) {
                flipbook.turn('next');
            } else {
                flipbook.turn('previous');
            }
        }

        isDragging = false;
    });

    // Mobile touch events
    if (isMobile) {
        let touchStartX = 0;

        flipbook.on('touchstart', function(e) {
            if (!zoomActive) {
                touchStartX = e.touches[0].clientX;
            }
        });

        flipbook.on('touchend', function(e) {
            if (!zoomActive) {
                const touchEndX = e.changedTouches[0].clientX;
                const swipeDistance = touchEndX - touchStartX;

                // Swipe gestures for mobile
                if (swipeDistance < -50) {
                    flipbook.turn('next');
                } else if (swipeDistance > 50) {
                    flipbook.turn('previous');
                }
            }
        });
    }

    // Zoom toggle button - shows zoom panel and activates zoom cursor mode
    zoomToggleBtn.click(function() {
        isZoomCursorMode = !isZoomCursorMode;
        const viewer = $('#flipbook-viewer');

        if (isZoomCursorMode) {
            $(this).addClass('active');
            viewer.addClass('zoom-cursor-mode');
            zoomPanel.show(); // Show zoom panel
            // Disable pan mode if active
            if (isPanMode) {
                isPanMode = false;
                panToolBtn.removeClass('active');
                viewer.removeClass('pan-mode');
                disablePanning();
            }
        } else {
            $(this).removeClass('active');
            viewer.removeClass('zoom-cursor-mode');
            zoomPanel.hide(); // Hide zoom panel when cursor mode disabled
        }
    });

    zoomInBtn.click(function() {
        applyZoom(Math.min(3, zoomLevel + 0.25));
    });

    zoomOutBtn.click(function() {
        applyZoom(Math.max(0.5, zoomLevel - 0.25));
    });

    zoomFitBtn.click(function() {
        // Calculate zoom to fit width
        const viewerWidth = $('#flipbook-viewer').width();
        const bookWidth = flipbook.width();
        const fitZoom = viewerWidth / bookWidth;
        applyZoom(fitZoom);
    });

    zoomResetBtn.click(function() {
        applyZoom(1);
    });

    panToolBtn.click(function() {
        isPanMode = !isPanMode;
        $(this).toggleClass('active');

        const viewer = $('#flipbook-viewer');
        if (isPanMode) {
            viewer.addClass('pan-mode');
            // Always enable panning when pan tool is active
            enablePanning();
        } else {
            viewer.removeClass('pan-mode');
            disablePanning();
        }
    });
});

// Helper functions
function updateThumbnails(page) {
    thumbnailItems.removeClass('active');
    thumbnailItems.eq(page - 1).addClass('active');

    // Auto-scroll to active thumbnail
    const activeThumbnail = thumbnailItems.eq(page - 1)[0];
    if (activeThumbnail) {
        activeThumbnail.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }
}

function applyZoom(scale, clickX, clickY) {
    const previousZoom = zoomLevel;
    zoomLevel = Math.max(0.5, Math.min(3, scale));

    const viewer = $('#flipbook-viewer');
    const flipbookElement = $('#flipbook');

    // Calculate which point in the FLIPBOOK was clicked
    let flipbookPointX = null;
    let flipbookPointY = null;

    if (clickX !== undefined && clickY !== undefined) {
        const baseWidth = flipbookElement.width();
        const baseHeight = flipbookElement.height();

        if (previousZoom > 1) {
            // Already zoomed - calculate from scroll position
            const currentScrollX = viewer[0].scrollLeft || 0;
            const currentScrollY = viewer[0].scrollTop || 0;
            const oldPaddingX = baseWidth * previousZoom * 2;
            const oldPaddingY = baseHeight * previousZoom * 2;

            // Where in the OLD scaled flipbook?
            const posX = currentScrollX + clickX - oldPaddingX;
            const posY = currentScrollY + clickY - oldPaddingY;

            // Convert to unscaled flipbook coordinates
            flipbookPointX = posX / previousZoom;
            flipbookPointY = posY / previousZoom;
        } else {
            // Not zoomed yet - need to find where in flipbook was clicked
            // Get flipbook's actual position on screen
            const flipbookRect = flipbookElement[0].getBoundingClientRect();
            const viewerRect = viewer[0].getBoundingClientRect();

            // Click position in viewport
            const viewportClickX = clickX;
            const viewportClickY = clickY;

            // Position of flipbook top-left corner relative to viewer top-left
            const flipbookOffsetX = flipbookRect.left - viewerRect.left;
            const flipbookOffsetY = flipbookRect.top - viewerRect.top;

            // Click position relative to flipbook's top-left corner
            flipbookPointX = viewportClickX - flipbookOffsetX;
            flipbookPointY = viewportClickY - flipbookOffsetY;

            console.log('Flipbook offset from viewer:', flipbookOffsetX, flipbookOffsetY);
            console.log('Viewport click:', viewportClickX, viewportClickY);
        }

        console.log('Flipbook point clicked:', flipbookPointX, flipbookPointY);
    }

    // Update zoom active flag
    zoomActive = zoomLevel > 1;

    // Toggle zoomed class and overflow settings
    if (zoomActive) {
        viewer.addClass('zoomed');

        // Get viewport and flipbook dimensions
        const viewerWidth = viewer.width();
        const viewerHeight = viewer.height();
        const baseWidth = flipbookElement.width();
        const baseHeight = flipbookElement.height();

        // Calculate the scaled dimensions
        const scaledWidth = baseWidth * zoomLevel;
        const scaledHeight = baseHeight * zoomLevel;

        // Massive padding for truly unlimited panning
        const paddingX = scaledWidth * 2;
        const paddingY = scaledHeight * 2;

        // Total scrollable area
        const totalWidth = scaledWidth + paddingX * 2;
        const totalHeight = scaledHeight + paddingY * 2;

        // Apply zoom using transform (turn.js needs original dimensions)
        // But create a SPACER div to establish scrollable area
        if (!$('#zoom-spacer').length) {
            viewer.prepend('<div id="zoom-spacer" style="position: absolute; top: 0; left: 0; pointer-events: none;"></div>');
        }

        const spacer = $('#zoom-spacer');
        spacer.css({
            width: totalWidth + 'px',
            height: totalHeight + 'px'
        });

        // Position flipbook with padding offset using margin
        flipbookElement.css({
            transform: `scale(${zoomLevel})`,
            transformOrigin: 'top left',
            marginLeft: paddingX + 'px',
            marginTop: paddingY + 'px',
            position: 'relative'
        });

        // Enable scrolling on viewer
        viewer.css({
            'overflow': 'auto',
            'overflow-x': 'auto',
            'overflow-y': 'auto'
        });

        // Position the viewport based on where user clicked
        setTimeout(() => {
            if (flipbookPointX !== null && flipbookPointY !== null) {
                // The clicked point in the SCALED flipbook
                const scaledPointX = flipbookPointX * zoomLevel;
                const scaledPointY = flipbookPointY * zoomLevel;

                console.log('Flipbook point (unscaled):', flipbookPointX, flipbookPointY);
                console.log('Scaled point:', scaledPointX, scaledPointY);

                // Where should this point appear in the viewport?
                // Keep it at the SAME place where user clicked!
                const targetViewportX = clickX !== undefined ? clickX : viewerWidth / 2;
                const targetViewportY = clickY !== undefined ? clickY : viewerHeight / 2;

                console.log('Target viewport pos:', targetViewportX, targetViewportY);

                // NEW STRUCTURE: container > wrapper > flipbook
                // Wrapper is positioned at (paddingX, paddingY)
                // Scaled point is at (scaledPointX, scaledPointY) within wrapper
                // Total position in container: paddingX + scaledPointX
                // We want this to appear at targetViewportX/Y in viewport
                // So: scroll = (paddingX + scaledPointX) - targetViewportX

                const targetScrollX = paddingX + scaledPointX - targetViewportX;
                const targetScrollY = paddingY + scaledPointY - targetViewportY;

                console.log('Calculated scroll:', targetScrollX, targetScrollY);
                console.log('Padding:', paddingX, paddingY);
                console.log('Total container size:', totalWidth, totalHeight);
                console.log('Viewer size:', viewerWidth, viewerHeight);
                console.log('Scroll range:', viewer[0].scrollWidth, viewer[0].scrollHeight);
                console.log('Max scroll:', viewer[0].scrollWidth - viewerWidth, viewer[0].scrollHeight - viewerHeight);

                viewer[0].scrollLeft = targetScrollX;
                viewer[0].scrollTop = targetScrollY;

                console.log('Actual scroll after set:', viewer[0].scrollLeft, viewer[0].scrollTop);
            } else {
                // Center on first zoom
                viewer[0].scrollLeft = (totalWidth - viewerWidth) / 2;
                viewer[0].scrollTop = (totalHeight - viewerHeight) / 2;
            }
        }, 0);

        // Enable panning if pan tool is active
        if (isPanMode) {
            enablePanning();
        }
    } else {
        viewer.removeClass('zoomed');
        viewer.css({
            'overflow': 'hidden'
        });

        // Remove spacer and reset flipbook
        $('#zoom-spacer').remove();

        flipbookElement.css({
            transform: 'scale(1)',
            transformOrigin: 'center center',
            marginLeft: '',
            marginTop: '',
            position: 'relative'
        });

        disablePanning();

        // If zoom is reset to 1x, also deactivate pan mode
        if (isPanMode) {
            isPanMode = false;
            panToolBtn.removeClass('active');
            viewer.removeClass('pan-mode');
        }
    }

    // Stop any turn animation
    flipbook.turn('stop');

    // Update zoom display
    zoomValue.text(Math.round(zoomLevel * 100) + '%');

    // Update button states
    if (zoomLevel <= 0.5) {
        zoomOutBtn.prop('disabled', true);
    } else {
        zoomOutBtn.prop('disabled', false);
    }

    if (zoomLevel >= 3) {
        zoomInBtn.prop('disabled', true);
    } else {
        zoomInBtn.prop('disabled', false);
    }
}

// Panning support when zoomed
let isPanning = false;
let startPanX = 0;
let startPanY = 0;
let scrollLeft = 0;
let scrollTop = 0;

function enablePanning() {
    const viewer = $('#flipbook-viewer');

    // Remove any existing pan handlers first
    viewer.off('.pan');

    // Mouse down handler
    viewer.on('mousedown.pan', function(e) {
        if (!isPanMode || !zoomActive) return;

        isPanning = true;
        startPanX = e.clientX;
        startPanY = e.clientY;
        scrollLeft = this.scrollLeft;
        scrollTop = this.scrollTop;

        $(this).css('cursor', 'grabbing');
        e.preventDefault();
        e.stopPropagation(); // Prevent event bubbling
    });

    // Mouse move handler with improved scrolling
    viewer.on('mousemove.pan', function(e) {
        if (!isPanning) return;

        e.preventDefault();
        e.stopPropagation();

        const deltaX = e.clientX - startPanX;
        const deltaY = e.clientY - startPanY;

        // Apply smooth scrolling with proper boundaries
        const newScrollLeft = Math.max(0, Math.min(scrollLeft - deltaX, this.scrollWidth - this.clientWidth));
        const newScrollTop = Math.max(0, Math.min(scrollTop - deltaY, this.scrollHeight - this.clientHeight));

        this.scrollLeft = newScrollLeft;
        this.scrollTop = newScrollTop;
    });

    // Mouse up and leave handlers
    viewer.on('mouseup.pan mouseleave.pan', function(e) {
        if (isPanning) {
            isPanning = false;
            if (isPanMode) {
                $(this).css('cursor', 'grab');
            }
        }
    });

    // Add touch support for mobile devices
    viewer.on('touchstart.pan', function(e) {
        if (!isPanMode || !zoomActive) return;

        const touch = e.originalEvent.touches[0];
        isPanning = true;
        startPanX = touch.clientX;
        startPanY = touch.clientY;
        scrollLeft = this.scrollLeft;
        scrollTop = this.scrollTop;
        e.preventDefault();
    });

    viewer.on('touchmove.pan', function(e) {
        if (!isPanning) return;

        const touch = e.originalEvent.touches[0];
        e.preventDefault();

        const deltaX = touch.clientX - startPanX;
        const deltaY = touch.clientY - startPanY;

        const newScrollLeft = Math.max(0, Math.min(scrollLeft - deltaX, this.scrollWidth - this.clientWidth));
        const newScrollTop = Math.max(0, Math.min(scrollTop - deltaY, this.scrollHeight - this.clientHeight));

        this.scrollLeft = newScrollLeft;
        this.scrollTop = newScrollTop;
    });

    viewer.on('touchend.pan touchcancel.pan', function(e) {
        isPanning = false;
    });
}

function disablePanning() {
    const viewer = $('#flipbook-viewer');
    viewer.off('.pan'); // Remove all pan-related events
    isPanning = false;
    viewer.css('cursor', ''); // Reset cursor
}

// Toolbar button handlers
searchBtn.click(function() {
    searchOverlay.show();
    searchInput.focus();
});

searchCloseBtn.click(function() {
    searchOverlay.hide();
    searchInput.val('');
    searchResults.html('');
});

searchOverlay.click(function(e) {
    if (e.target === this) {
        searchOverlay.hide();
    }
});

searchInput.on('input', function() {
    const query = $(this).val().trim();
    if (query.length >= 2) {
        performSearch(query);
    } else {
        searchResults.html('');
    }
});

function performSearch(query) {
    console.log('performSearch called with:', query);
    console.log('searchData available:', !!searchData);

    if (!searchData) {
        searchResults.html('<p style="color: red;">Vyhledávací data se nenačetla. Zkontrolujte konzoli.</p>');
        return;
    }

    if (!query) {
        searchResults.html('<p>Zadejte hledaný text</p>');
        return;
    }

    console.log('Searching in', Object.keys(searchData.pages).length, 'pages');

    const results = [];
    const lowerQuery = query.toLowerCase();

    // Search through all pages
    Object.entries(searchData.pages).forEach(([pageNum, text]) => {
        const lowerText = text.toLowerCase();
        if (lowerText.includes(lowerQuery)) {
            // Find snippet around the match
            const index = lowerText.indexOf(lowerQuery);
            const start = Math.max(0, index - 50);
            const end = Math.min(text.length, index + query.length + 50);
            let snippet = text.substring(start, end);

            // Add ellipsis
            if (start > 0) snippet = '...' + snippet;
            if (end < text.length) snippet = snippet + '...';

            // Highlight the match
            const regex = new RegExp(`(${query})`, 'gi');
            snippet = snippet.replace(regex, '<span class="search-highlight">$1</span>');

            results.push({
                page: parseInt(pageNum),
                snippet: snippet
            });
        }
    });

    if (results.length === 0) {
        searchResults.html('<p>Nenalezeny žádné výsledky</p>');
    } else {
        searchResults.html(`
            <p>Nalezeno <strong>${results.length}</strong> výsledků:</p>
            ${results.map(r => `
                <div class="search-result-item" onclick="goToPage(${r.page})">
                    <div class="search-result-page">Stránka ${r.page}</div>
                    <div class="search-result-snippet">${r.snippet}</div>
                </div>
            `).join('')}
        `);
    }
}

function goToPage(page) {
    flipbook.turn('page', page);
    searchOverlay.hide();
    searchInput.val('');
    searchResults.html('');
}

// Click on page to zoom or turn pages
flipbook.on('click', '.page', function(e) {
    // Zoom cursor mode - zoom to click position (single click only)
    if (isZoomCursorMode) {
        e.preventDefault();
        e.stopPropagation();

        const viewer = $('#flipbook-viewer');

        // Get click position relative to viewer
        const viewerOffset = viewer.offset();
        const clickX = e.pageX - viewerOffset.left;
        const clickY = e.pageY - viewerOffset.top;

        // Calculate target zoom level (single zoom to 1.5x)
        const targetZoom = 1.5;

        // Apply zoom
        applyZoom(targetZoom, clickX, clickY);

        // Deactivate zoom cursor mode after first click
        isZoomCursorMode = false;
        zoomToggleBtn.removeClass('active');
        viewer.removeClass('zoom-cursor-mode');

        // Show zoom panel and activate pan mode automatically
        zoomPanel.show();
        isPanMode = true;
        panToolBtn.addClass('active');
        viewer.addClass('pan-mode');
        enablePanning();

        return;
    }

    // Don't turn pages if pan mode is active
    if (isPanMode) return;

    const page = $(this);
    const offset = page.offset();
    const width = page.width();
    const x = e.pageX - offset.left;

    // Define click zones (20% on each edge)
    const leftZone = width * 0.2;
    const rightZone = width * 0.8;

    // Click on left edge - go to previous page
    if (x < leftZone) {
        flipbook.turn('previous');
    }
    // Click on right edge - go to next page
    else if (x > rightZone) {
        flipbook.turn('next');
    }
});

prevPageBtn.click(function() {
    flipbook.turn('previous');
});

nextPageBtn.click(function() {
    flipbook.turn('next');
});

firstPageBtn.click(function() {
    flipbook.turn('page', 1);
});

lastPageBtn.click(function() {
    flipbook.turn('page', flipbook.turn('pages'));
});

// Share button - show modal with QR code
let qrCodeInstance = null;

shareBtn.click(function() {
    const currentPage = flipbook.turn('page');
    const shareUrl = window.location.href.split('#')[0] + '#page=' + currentPage;

    // Update URL input
    shareUrlInput.val(shareUrl);

    // Clear previous QR code
    $('#qrcode').empty();

    // Generate new QR code
    qrCodeInstance = new QRCode(document.getElementById("qrcode"), {
        text: shareUrl,
        width: 200,
        height: 200,
        colorDark: "#000000",
        colorLight: "#ffffff",
        correctLevel: QRCode.CorrectLevel.H
    });

    // Show modal
    shareOverlay.show();
});

// Copy URL button
copyUrlBtn.click(function() {
    const url = shareUrlInput.val();
    shareUrlInput.select();

    navigator.clipboard.writeText(url).then(() => {
        // Change button text temporarily
        const originalText = copyUrlBtn.text();
        copyUrlBtn.text('Zkopírováno! ✓');
        setTimeout(() => {
            copyUrlBtn.text(originalText);
        }, 2000);
    }).catch(() => {
        alert('Nepodařilo se zkopírovat odkaz');
    });
});

// Share close button
shareCloseBtn.click(function() {
    shareOverlay.hide();
});

shareOverlay.click(function(e) {
    if (e.target === this) {
        shareOverlay.hide();
    }
});

fullscreenBtn.click(function() {
    const elem = document.documentElement;
    if (!document.fullscreenElement) {
        if (elem.requestFullscreen) {
            elem.requestFullscreen();
        } else if (elem.webkitRequestFullscreen) {
            elem.webkitRequestFullscreen();
        } else if (elem.msRequestFullscreen) {
            elem.msRequestFullscreen();
        }
        $(this).find('i').removeClass('fa-expand').addClass('fa-compress');
    } else {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }
        $(this).find('i').removeClass('fa-compress').addClass('fa-expand');
    }
});

// Download PDF button
downloadPdfBtn.click(function() {
    // Trigger download of original PDF (if available in same directory)
    const pdfFilename = document.title.replace(/[^a-z0-9]/gi, '-').toLowerCase() + '.pdf';

    // Try to download using <a> tag for better download behavior
    const link = document.createElement('a');
    link.href = pdfFilename;
    link.download = pdfFilename;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});

// AI Summary handlers - if button exists
if ($('#ai-summary-btn').length > 0) {
    $('#ai-summary-btn').click(function() {
        aiSummaryOverlay.show();
        generateAISummary();
    });
}

aiSummaryCloseBtn.click(function() {
    aiSummaryOverlay.hide();
});

aiSummaryOverlay.click(function(e) {
    if (e.target === this) {
        aiSummaryOverlay.hide();
    }
});

// Menu button - toggle thumbnail sidebar
menuBtn.click(function() {
    thumbnailSidebar.toggleClass('thumbnail-sidebar-hidden');
});

// Menu button - generates smart index from headings
function generateSmartIndex() {
    if (!searchData) {
        menuContent.html('<p>Obsah není dostupný</p>');
        return;
    }

    const headings = [];

    // Extract headings from each page (lines with ALL CAPS or ending with :)
    Object.entries(searchData.pages).forEach(([pageNum, text]) => {
        const lines = text.split('\\n');
        lines.forEach(line => {
            const trimmed = line.trim();
            // Detect headings: ALL CAPS lines > 5 chars, or lines ending with :
            if ((trimmed === trimmed.toUpperCase() && trimmed.length > 5 && trimmed.length < 100) ||
                (trimmed.endsWith(':') && trimmed.length > 10 && trimmed.length < 100)) {
                headings.push({
                    text: trimmed.replace(':', ''),
                    page: parseInt(pageNum)
                });
            }
        });
    });

    if (headings.length === 0) {
        menuContent.html('<p>Nenalezeny žádné nadpisy</p>');
        return;
    }

    // Remove duplicates
    const unique = headings.filter((h, i, self) =>
        i === self.findIndex((t) => t.text === h.text)
    );

    // Generate HTML
    const html = unique.slice(0, 20).map(h => `
        <div class="menu-item" onclick="goToPageFromMenu(${h.page})">
            <div class="menu-item-text">${h.text}</div>
            <div class="menu-item-page">Strana ${h.page}</div>
        </div>
    `).join('');

    menuContent.html(html);
}

function goToPageFromMenu(page) {
    flipbook.turn('page', page);
    menuOverlay.hide();
}

menuCloseBtn.click(function() {
    menuOverlay.hide();
});

menuOverlay.click(function(e) {
    if (e.target === this) {
        menuOverlay.hide();
    }
});

// Generate AI Summary using Claude/ChatGPT
async function generateAISummary() {
    if (!searchData) {
        aiSummaryContent.html('<p style="color: red;">Text zpravodaje není dostupný</p>');
        return;
    }

    // Collect all text
    let allText = '';
    Object.entries(searchData.pages).forEach(([pageNum, text]) => {
        allText += `\\n\\n=== Stránka ${pageNum} ===\\n${text}`;
    });

    // For now, create a simple summary (you can add API call to ChatGPT/Claude later)
    try {
        // Option 1: Client-side summary (simple)
        const summary = createSimpleSummary(allText);

        aiSummaryContent.html(`
            <div class="ai-summary-result">
                <h3>📝 Shrnutí nejdůležitějších témat:</h3>
                ${summary}
                <hr>
                <p style="font-size: 12px; color: #666; margin-top: 20px;">
                    💡 <strong>Tip:</strong> Pro pokročilé AI shrnutí s ChatGPT/Claude kontaktujte správce.<br>
                    Aktuálně zobrazeno automatické shrnutí založené na OCR textu.
                </p>
            </div>
        `);

        // TODO: Add real AI API call
        // const response = await fetch('YOUR_AI_API_ENDPOINT', {
        //     method: 'POST',
        //     headers: { 'Content-Type': 'application/json' },
        //     body: JSON.stringify({ text: allText })
        // });
        // const aiResult = await response.json();

    } catch (error) {
        aiSummaryContent.html(`<p style="color: red;">Chyba při generování shrnutí: ${error.message}</p>`);
    }
}

function createSimpleSummary(text) {
    // Extract headings and key topics
    const lines = text.split('\\n');
    const topics = [];
    const numbers = [];

    lines.forEach(line => {
        const trimmed = line.trim();

        // Find headings (ALL CAPS)
        if (trimmed === trimmed.toUpperCase() && trimmed.length > 10 && trimmed.length < 100) {
            topics.push(trimmed);
        }

        // Find numbers (statistics)
        const numberMatches = trimmed.match(/\\d+\\s*(tun|mil|Kč|stran|dětí|občan|procent|%)/gi);
        if (numberMatches) {
            numbers.push(trimmed);
        }
    });

    let html = '<ul style="text-align: left;">';

    // Add unique topics
    const uniqueTopics = [...new Set(topics)].slice(0, 8);
    uniqueTopics.forEach(topic => {
        html += `<li><strong>${topic}</strong></li>`;
    });

    html += '</ul>';

    if (numbers.length > 0) {
        html += '<h4>📊 Klíčová čísla:</h4><ul style="text-align: left;">';
        numbers.slice(0, 5).forEach(num => {
            html += `<li>${num}</li>`;
        });
        html += '</ul>';
    }

    return html;
}

// Thumbnail click handlers
thumbnailItems.click(function() {
    const page = $(this).data('page');
    flipbook.turn('page', page);
});

// Keyboard navigation
$(document).keydown(function(e) {
    switch(e.which) {
        case 37: // left arrow
        case 33: // page up
            flipbook.turn('previous');
            e.preventDefault();
            break;
        case 39: // right arrow
        case 34: // page down
        case 32: // space
            flipbook.turn('next');
            e.preventDefault();
            break;
        case 36: // home
            flipbook.turn('page', 1);
            e.preventDefault();
            break;
        case 35: // end
            flipbook.turn('page', flipbook.turn('pages'));
            e.preventDefault();
            break;
    }
});'''
