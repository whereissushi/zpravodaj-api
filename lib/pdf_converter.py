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
            <button id="zoom-in-btn" class="toolbar-btn" title="Přiblížit">
                <i class="fas fa-magnifying-glass-plus"></i>
            </button>
            <button id="zoom-out-btn" class="toolbar-btn" title="Oddálit">
                <i class="fas fa-magnifying-glass-minus"></i>
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
            <button id="ai-summary-btn" class="toolbar-btn" title="AI Shrnutí">
                <i class="fas fa-robot"></i>
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
            <h2>🤖 AI Shrnutí Zpravodaje</h2>
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
            <h2>📑 Obsah</h2>
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

    <!-- Zoom menu overlay -->
    <div id="zoom-menu-overlay" style="display: none;">
        <div class="search-modal zoom-menu-modal">
            <h2>🔍 Přiblížení</h2>
            <div id="zoom-menu-content">
                <p style="text-align: center; margin-bottom: 20px; color: #666;">
                    Aktuální: <strong id="current-zoom-display">100%</strong>
                </p>
                <div class="zoom-options">
                    <button class="zoom-option-btn" data-zoom="0.5">50%</button>
                    <button class="zoom-option-btn" data-zoom="0.75">75%</button>
                    <button class="zoom-option-btn active" data-zoom="1">100%</button>
                    <button class="zoom-option-btn" data-zoom="1.25">125%</button>
                    <button class="zoom-option-btn" data-zoom="1.5">150%</button>
                    <button class="zoom-option-btn" data-zoom="2">200%</button>
                    <button class="zoom-option-btn" data-zoom="2.5">250%</button>
                    <button class="zoom-option-btn" data-zoom="3">300%</button>
                </div>
                <div style="margin-top: 20px;">
                    <label style="display: block; margin-bottom: 10px; font-weight: 500; color: #333;">Vlastní:</label>
                    <input type="range" id="zoom-slider" min="50" max="300" value="100" step="25" style="width: 100%;">
                    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #666; margin-top: 5px;">
                        <span>50%</span>
                        <span>300%</span>
                    </div>
                </div>
            </div>
            <button id="zoom-menu-close-btn">Zavřít</button>
        </div>
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
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    background: #e8e8e8;
    padding: 20px;
}

#flipbook {
    width: 80%;
    height: 85vh;
    margin: 0 auto;
    user-select: none;
}

#flipbook .page {
    width: 50%;
    height: 100%;
    background-color: white;
    background-size: 100% 100%;
}

#flipbook .page img {
    width: 100%;
    height: 100%;
    object-fit: contain;
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

/* All overlays */
#search-overlay,
#zoom-menu-overlay,
#share-overlay,
#ai-summary-overlay,
#menu-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.search-modal {
    background: white;
    padding: 30px;
    border-radius: 8px;
    max-width: 600px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
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

/* Zoom menu styling */
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
const zoomInBtn = $('#zoom-in-btn');
const zoomOutBtn = $('#zoom-out-btn');
const prevPageBtn = $('#prev-page-btn');
const nextPageBtn = $('#next-page-btn');
const firstPageBtn = $('#first-page-btn');
const lastPageBtn = $('#last-page-btn');
const shareBtn = $('#share-btn');
const fullscreenBtn = $('#fullscreen-btn');
const downloadPdfBtn = $('#download-pdf-btn');
const aiSummaryBtn = $('#ai-summary-btn');

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
const zoomMenuOverlay = $('#zoom-menu-overlay');
const zoomMenuCloseBtn = $('#zoom-menu-close-btn');
const zoomSlider = $('#zoom-slider');
const currentZoomDisplay = $('#current-zoom-display');
const zoomOptionBtns = $('.zoom-option-btn');

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
    flipbook.turn({
        width: isMobile ? 400 : 1400,
        height: isMobile ? 600 : 990,
        elevation: 50,
        gradients: true,
        autoCenter: true,
        duration: 600,
        acceleration: true,
        display: isMobile ? 'single' : 'double',
        // Enable drag-to-flip - can grab and drag page corners/edges
        when: {
            turning: function(e, page, view) {
                // Disable turning if zoomed in
                if (zoomActive) {
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
            }
        }
    });

    // Update page display
    currentPageSpan.text(1);
    updateThumbnails(1);

    // Turn.js already has built-in drag-to-flip functionality
    // Just make sure it works on mobile with touch events
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

    // Zoom menu handlers (must be inside ready to ensure elements exist)
    const zoomOptionBtnsReady = $('.zoom-option-btn');

    zoomInBtn.click(function() {
        // Update current zoom display
        currentZoomDisplay.text(Math.round(zoomLevel * 100) + '%');

        // Update slider position
        zoomSlider.val(Math.round(zoomLevel * 100));

        // Update active button
        updateZoomActiveButton(zoomLevel);

        // Show zoom menu
        zoomMenuOverlay.show();
    });

    zoomOutBtn.click(function() {
        applyZoom(zoomLevel - 0.25);
        updateZoomDisplay();
    });

    zoomMenuCloseBtn.click(function() {
        zoomMenuOverlay.hide();
    });

    zoomMenuOverlay.click(function(e) {
        if (e.target === this) {
            zoomMenuOverlay.hide();
        }
    });

    // Preset zoom buttons
    zoomOptionBtnsReady.click(function() {
        const zoom = parseFloat($(this).data('zoom'));
        applyZoom(zoom);
        updateZoomDisplay();

        // Update active state
        zoomOptionBtnsReady.removeClass('active');
        $(this).addClass('active');
    });

    // Zoom slider
    zoomSlider.on('input', function() {
        const zoom = parseInt($(this).val()) / 100;
        applyZoom(zoom);
        updateZoomDisplay();
        updateZoomActiveButton(zoom);
    });

    function updateZoomDisplay() {
        currentZoomDisplay.text(Math.round(zoomLevel * 100) + '%');
        zoomSlider.val(Math.round(zoomLevel * 100));
        updateZoomActiveButton(zoomLevel);
    }

    function updateZoomActiveButton(zoom) {
        zoomOptionBtnsReady.removeClass('active');
        zoomOptionBtnsReady.each(function() {
            if (Math.abs(parseFloat($(this).data('zoom')) - zoom) < 0.01) {
                $(this).addClass('active');
            }
        });
    }
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

function applyZoom(scale) {
    zoomLevel = Math.max(0.5, Math.min(3, scale));
    flipbook.turn('stop').css({
        transform: `scale(${zoomLevel})`,
        transformOrigin: 'center center'
    });

    // Update zoom active flag
    zoomActive = zoomLevel > 1;
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

// Click-to-zoom on pages (only if not dragging)
let clickStartTime = 0;
let clickStartPos = { x: 0, y: 0 };

flipbook.on('mousedown', '.page img', function(e) {
    clickStartTime = Date.now();
    clickStartPos = { x: e.pageX, y: e.pageY };
});

flipbook.on('click', '.page img', function(e) {
    const timeDiff = Date.now() - clickStartTime;
    const distanceMoved = Math.sqrt(
        Math.pow(e.pageX - clickStartPos.x, 2) +
        Math.pow(e.pageY - clickStartPos.y, 2)
    );

    // Only zoom if it's a real click (not a drag)
    // Quick click with minimal movement
    if (timeDiff < 300 && distanceMoved < 10) {
        if (!zoomActive) {
            // Get click position relative to the image
            const offset = $(this).offset();
            const x = e.pageX - offset.left;
            const y = e.pageY - offset.top;
            const width = $(this).width();
            const height = $(this).height();

            // Calculate transform origin as percentage
            const originX = (x / width) * 100;
            const originY = (y / height) * 100;

            // Zoom to 2x at click point
            zoomLevel = 2;
            flipbook.turn('stop').css({
                transform: `scale(2)`,
                transformOrigin: `${originX}% ${originY}%`
            });
            zoomActive = true;
        } else {
            // Reset zoom
            zoomLevel = 1;
            flipbook.turn('stop').css({
                transform: `scale(1)`,
                transformOrigin: 'center center'
            });
            zoomActive = false;
        }
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

// AI Summary button
aiSummaryBtn.click(function() {
    aiSummaryOverlay.show();
    generateAISummary();
});

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
