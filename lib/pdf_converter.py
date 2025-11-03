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
            'page_count': len(self.pages_images)
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
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/turn.js/3/turn.min.js"></script>
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
        </div>

        <div id="flipbook-viewer">
            <div id="flipbook">
                {''.join(f'<div class="page"><img src="files/pages/{i}.jpg" alt="Stránka {i}"></div>' for i in range(1, page_count + 1))}
            </div>
        </div>

        <div id="thumbnail-bar">
            <div id="thumbnail-container">
                {''.join(f'<img src="files/thumb/{i}.jpg" class="thumbnail" data-page="{i}" alt="Stránka {i}">' for i in range(1, page_count + 1))}
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

#thumbnail-bar {
    background: #f5f5f5;
    padding: 10px;
    overflow-x: auto;
    overflow-y: hidden;
    border-top: 1px solid #ddd;
}

#thumbnail-container {
    display: flex;
    gap: 10px;
    width: max-content;
}

.thumbnail {
    height: 100px;
    cursor: pointer;
    border: 3px solid transparent;
    transition: border-color 0.3s, transform 0.3s;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.thumbnail:hover {
    transform: scale(1.05);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.thumbnail.active {
    border-color: #2563a6;
    box-shadow: 0 4px 8px rgba(37, 99, 166, 0.3);
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

    .thumbnail {
        height: 80px;
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

/* Search overlay */
#search-overlay {
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
}'''

    def _get_js(self):
        """Return JavaScript content"""
        return '''// Configuration
let zoomLevel = 1;
const isMobile = window.innerWidth <= 768;

// Elements
const flipbook = $('#flipbook');
const currentPageSpan = $('#current-page');
const thumbnails = $('.thumbnail');

// Toolbar buttons
const searchBtn = $('#search-btn');
const zoomInBtn = $('#zoom-in-btn');
const zoomOutBtn = $('#zoom-out-btn');
const prevPageBtn = $('#prev-page-btn');
const nextPageBtn = $('#next-page-btn');
const firstPageBtn = $('#first-page-btn');
const lastPageBtn = $('#last-page-btn');
const shareBtn = $('#share-btn');
const fullscreenBtn = $('#fullscreen-btn');

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
        when: {
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
});

// Helper functions
function updateThumbnails(page) {
    thumbnails.removeClass('active');
    thumbnails.eq(page - 1).addClass('active');

    // Auto-scroll to active thumbnail
    const activeThumbnail = thumbnails.eq(page - 1)[0];
    if (activeThumbnail) {
        activeThumbnail.scrollIntoView({behavior: 'smooth', block: 'nearest', inline: 'center'});
    }
}

function applyZoom(scale) {
    zoomLevel = Math.max(0.5, Math.min(3, scale));
    flipbook.turn('stop').css({
        transform: `scale(${zoomLevel})`,
        transformOrigin: 'center center'
    });
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

zoomInBtn.click(function() {
    applyZoom(zoomLevel + 0.25);
});

zoomOutBtn.click(function() {
    applyZoom(zoomLevel - 0.25);
});

// Click-to-zoom on pages
flipbook.on('click', '.page img', function(e) {
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

shareBtn.click(function() {
    if (navigator.share) {
        navigator.share({
            title: document.title,
            text: 'Podívejte se na tento flipbook',
            url: window.location.href
        }).catch(() => {});
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('Odkaz zkopírován do schránky!');
        }).catch(() => {
            alert('URL: ' + window.location.href);
        });
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

// Thumbnail click handlers
thumbnails.click(function() {
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
});

// Zoom on click - click on page to zoom to that point
flipbook.on('click', '.page', function(e) {
    if (zoomLevel === 1) {
        // Zoom in to 2x at click position
        const rect = this.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;

        zoomLevel = 2;
        flipbook.turn('stop').css({
            transform: `scale(2)`,
            transformOrigin: `${x}% ${y}%`
        });
    } else {
        // Zoom out to 1x
        applyZoom(1);
    }
});'''
