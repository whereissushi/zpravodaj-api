#!/usr/bin/env python3
"""
PDF to Flipbook Converter
Konvertuje PDF zpravodaj na interaktivní HTML flipbook
"""

import os
import sys
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
import shutil
import json
import pytesseract


class PDFToFlipbook:
    def __init__(self, pdf_path, output_dir, title="Zpravodaj"):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.title = title
        self.page_texts = {}  # Store OCR text for each page

    def convert(self):
        """Hlavní konverzní funkce"""
        print(f"Konvertuji PDF: {self.pdf_path}")

        # Vytvoř výstupní strukturu
        self._create_directory_structure()

        # Konvertuj PDF na obrázky
        print("Generuji obrázky stránek...")
        pages = self._convert_pdf_to_images()

        # OCR extraction
        print("Extrahuji text pro vyhledávání (OCR)...")
        self._extract_text_ocr(pages)

        # Vytvoř HTML soubory
        print("Generuji HTML...")
        self._generate_html(len(pages))

        # Zkopíruj CSS a JS
        print("Vytvářím styly a skripty...")
        self._create_assets()

        # Ulož search data
        if self.page_texts:
            self._save_search_data()

        # Zkopíruj původní PDF pro download
        print("Kopíruji původní PDF...")
        self._copy_original_pdf()

        print(f"\nHotovo! Vystup je v: {self.output_dir}")
        print(f"  Otevrte soubor: {self.output_dir / 'index.html'}")

    def _create_directory_structure(self):
        """Vytvoř adresářovou strukturu"""
        (self.output_dir / "files" / "pages").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "files" / "thumb").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "css").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "js").mkdir(parents=True, exist_ok=True)

    def _convert_pdf_to_images(self):
        """Konvertuj PDF stránky na obrázky"""
        # Konverze s vysokým DPI pro kvalitu
        pages = convert_from_path(
            self.pdf_path,
            dpi=150,
            fmt='jpeg'
        )

        for i, page in enumerate(pages, start=1):
            # Velký obrázek pro zobrazení
            page_path = self.output_dir / "files" / "pages" / f"{i}.jpg"
            page.save(page_path, 'JPEG', quality=85, optimize=True)

            # Thumbnail
            thumb = page.copy()
            thumb.thumbnail((200, 300), Image.Resampling.LANCZOS)
            thumb_path = self.output_dir / "files" / "thumb" / f"{i}.jpg"
            thumb.save(thumb_path, 'JPEG', quality=75)

            print(f"  Stránka {i}/{len(pages)}")

        return pages

    def _extract_text_ocr(self, pages):
        """Extrahuj text z obrázků pomocí OCR"""
        for i, page in enumerate(pages, start=1):
            try:
                text = pytesseract.image_to_string(page, lang='ces')
                self.page_texts[i] = text.strip()
                print(f"  OCR stránka {i}/{len(pages)}")
            except Exception as e:
                print(f"  Varování: OCR selhalo na stránce {i}: {e}")
                self.page_texts[i] = ""

    def _save_search_data(self):
        """Ulož vyhledávací data do JSON"""
        search_data = {
            "pages": self.page_texts
        }
        search_file = self.output_dir / "search_data.json"
        with open(search_file, 'w', encoding='utf-8') as f:
            json.dump(search_data, f, ensure_ascii=False, indent=2)

    def _copy_original_pdf(self):
        """Zkopíruj původní PDF do výstupní složky pro download"""
        dest_pdf = self.output_dir / self.pdf_path.name
        shutil.copy2(self.pdf_path, dest_pdf)

    def _generate_html(self, page_count):
        """Vygeneruj HTML soubory"""
        # Hlavní index.html
        html_content = f'''<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>{self.title}</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="icon" href="files/thumb/1.jpg" type="image/jpeg">
    <!-- Font Awesome pro ikony -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <div id="flipbook-container">
        <!-- Modrý toolbar -->
        <div id="flipbook-toolbar">
            <button id="zoom-in-btn" class="toolbar-btn" title="Přiblížit">
                <i class="fas fa-plus"></i>
            </button>
            <button id="search-btn" class="toolbar-btn" title="Vyhledávání">
                <i class="fas fa-search"></i>
            </button>
            <button id="menu-btn" class="toolbar-btn" title="Menu">
                <i class="fas fa-bars"></i>
            </button>
            <button id="rotate-left-btn" class="toolbar-btn" title="Otočit doleva">
                <i class="fas fa-rotate-left"></i>
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
            <button id="rotate-right-btn" class="toolbar-btn" title="Otočit doprava">
                <i class="fas fa-rotate-right"></i>
            </button>
            <button id="fullscreen-btn" class="toolbar-btn" title="Celá obrazovka">
                <i class="fas fa-expand"></i>
            </button>
            <button id="download-btn" class="toolbar-btn" title="Stáhnout PDF">
                <i class="fas fa-download"></i>
            </button>
            <button id="text-mode-btn" class="toolbar-btn" title="Textový režim">
                <i class="fas fa-align-left"></i>
            </button>
        </div>

        <div id="flipbook-viewer">
            <button id="prev-btn" class="nav-btn" aria-label="Předchozí stránka">‹</button>

            <div id="page-container">
                <!-- Pages loaded dynamically by JavaScript -->
            </div>

            <button id="next-btn" class="nav-btn" aria-label="Další stránka">›</button>
        </div>

        <div id="thumbnail-bar">
            <div id="thumbnail-container">
                {''.join(f'<img src="files/thumb/{i}.jpg" class="thumbnail" data-page="{i}" alt="Stránka {i}">' for i in range(1, page_count + 1))}
            </div>
        </div>
    </div>

    <!-- Search overlay -->
    <div id="search-overlay" class="overlay" style="display: none;">
        <div class="overlay-content">
            <h2>Vyhledávání</h2>
            <input type="text" id="search-input" placeholder="Zadejte hledaný text...">
            <div id="search-results"></div>
            <button id="search-close-btn">Zavřít</button>
        </div>
    </div>

    <!-- Menu overlay -->
    <div id="menu-overlay" class="overlay" style="display: none;">
        <div class="overlay-content">
            <h2>Menu</h2>
            <ul id="menu-list">
                <li><a href="#" data-page="1">Stránka 1</a></li>
            </ul>
            <button id="menu-close-btn">Zavřít</button>
        </div>
    </div>

    <script>
        const totalPages = {page_count};
        const pdfFileName = "{self.pdf_path.name}";
    </script>
    <script src="js/flipbook.js"></script>
</body>
</html>'''

        (self.output_dir / "index.html").write_text(html_content, encoding='utf-8')

    def _create_assets(self):
        """Vytvoř CSS a JavaScript soubory"""

        # CSS
        css_content = '''* {
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
    overflow: auto;
    background: #e8e8e8;
    perspective: 1500px;
    padding: 20px;
}

#page-container {
    max-width: 1400px;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2px;
    transform-style: preserve-3d;
    position: relative;
    background: white;
    box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    padding: 0;
}

.page-spread {
    position: relative;
    width: 50%;
    height: auto;
    background: white;
}

.page-spread img {
    width: 100%;
    height: auto;
    display: block;
    object-fit: contain;
}

.page-left {
    transform-origin: right center;
    border-right: 1px solid #ddd;
}

.page-right {
    transform-origin: left center;
    border-left: 1px solid #ddd;
}

/* Otáčení kolem středu knihy - vnější okraj jde NAHORU */

/* Pravá stránka - otáčí se kolem LEVÉHO okraje (střed knihy) */
.page-right.page-turning-next {
    animation: pageFlipRight 0.7s cubic-bezier(0.645, 0.045, 0.355, 1);
    z-index: 10;
}

/* Levá stránka - otáčí se kolem PRAVÉHO okraje (střed knihy) */
.page-left.page-turning-prev {
    animation: pageFlipLeft 0.7s cubic-bezier(0.645, 0.045, 0.355, 1);
    z-index: 10;
}

@keyframes pageFlipRight {
    0% {
        transform: rotateY(0deg);
        transform-origin: left center;
        filter: brightness(1);
        box-shadow: 0 5px 30px rgba(0,0,0,0.8);
    }
    25% {
        transform: rotateY(-30deg);
        filter: brightness(0.9);
        box-shadow: -5px 5px 35px rgba(0,0,0,0.7);
    }
    50% {
        transform: rotateY(-90deg);
        filter: brightness(0.6);
        box-shadow: -10px 5px 40px rgba(0,0,0,0.5);
    }
    75% {
        transform: rotateY(-150deg);
        filter: brightness(0.7);
        box-shadow: -5px 5px 35px rgba(0,0,0,0.7);
    }
    100% {
        transform: rotateY(-180deg);
        filter: brightness(0.85);
        box-shadow: 0 5px 30px rgba(0,0,0,0.8);
        opacity: 0;
    }
}

@keyframes pageFlipLeft {
    0% {
        transform: rotateY(0deg);
        transform-origin: right center;
        filter: brightness(1);
        box-shadow: 0 5px 30px rgba(0,0,0,0.8);
    }
    25% {
        transform: rotateY(30deg);
        filter: brightness(0.9);
        box-shadow: 5px 5px 35px rgba(0,0,0,0.7);
    }
    50% {
        transform: rotateY(90deg);
        filter: brightness(0.6);
        box-shadow: 10px 5px 40px rgba(0,0,0,0.5);
    }
    75% {
        transform: rotateY(150deg);
        filter: brightness(0.7);
        box-shadow: 5px 5px 35px rgba(0,0,0,0.7);
    }
    100% {
        transform: rotateY(180deg);
        filter: brightness(0.85);
        box-shadow: 0 5px 30px rgba(0,0,0,0.8);
        opacity: 0;
    }
}

/* Single page mode (first/last page, mobile) */
.page-single {
    width: 100%;
    height: auto;
}

.page-single img {
    width: 100%;
    height: auto;
}

#current-page-img {
    display: none;
}

/* Overlay styles */
.overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.7);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.overlay-content {
    background: white;
    padding: 30px;
    border-radius: 8px;
    max-width: 500px;
    width: 90%;
}

.overlay-content h2 {
    margin-bottom: 20px;
    color: #333;
}

.overlay-content input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 16px;
    margin-bottom: 15px;
}

.overlay-content button {
    background: #2563a6;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
}

.overlay-content ul {
    list-style: none;
    max-height: 300px;
    overflow-y: auto;
}

.overlay-content li {
    padding: 8px 0;
    border-bottom: 1px solid #eee;
}

.overlay-content a {
    color: #2563a6;
    text-decoration: none;
}

.overlay-content a:hover {
    text-decoration: underline;
}

#search-results {
    max-height: 400px;
    overflow-y: auto;
    margin: 15px 0;
}

.search-result-item {
    padding: 10px;
    margin: 5px 0;
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

/* Text mode overlay */
#text-mode-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: white;
    z-index: 999;
    overflow-y: auto;
    padding: 20px;
    display: none;
}

#text-mode-content {
    max-width: 800px;
    margin: 0 auto;
    font-size: 16px;
    line-height: 1.6;
    color: #333;
}

.text-mode-page {
    margin-bottom: 40px;
    padding-bottom: 20px;
    border-bottom: 2px solid #ddd;
}

.text-mode-page-num {
    font-size: 20px;
    font-weight: bold;
    color: #2563a6;
    margin-bottom: 15px;
}

#text-mode-close {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #2563a6;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    cursor: pointer;
    z-index: 1000;
}

.nav-btn {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(37, 99, 166, 0.7);
    color: white;
    border: none;
    font-size: 48px;
    padding: 20px 15px;
    cursor: pointer;
    z-index: 10;
    transition: background 0.3s;
    line-height: 1;
    border-radius: 4px;
}

.nav-btn:hover {
    background: rgba(37, 99, 166, 0.9);
}

.nav-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
}

#prev-btn {
    left: 10px;
}

#next-btn {
    right: 10px;
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

/* Mobile responsivity - single page view */
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

/* Scrollbar styling */
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
}'''

        (self.output_dir / "css" / "style.css").write_text(css_content, encoding='utf-8')

        # JavaScript
        js_content = '''let currentSpread = 0; // 0 = pages 1-2, 1 = pages 3-4, etc.
let isAnimating = false;
const isMobile = window.innerWidth <= 768;
let zoomLevel = 1;
let rotationAngle = 0;

const pageContainer = document.getElementById('page-container');
const currentPageSpan = document.getElementById('current-page');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const firstPageBtn = document.getElementById('first-page-btn');
const lastPageBtn = document.getElementById('last-page-btn');
const prevPageBtn = document.getElementById('prev-page-btn');
const nextPageBtn = document.getElementById('next-page-btn');
const thumbnails = document.querySelectorAll('.thumbnail');

// Toolbar buttons
const zoomInBtn = document.getElementById('zoom-in-btn');
const searchBtn = document.getElementById('search-btn');
const menuBtn = document.getElementById('menu-btn');
const rotateLeftBtn = document.getElementById('rotate-left-btn');
const rotateRightBtn = document.getElementById('rotate-right-btn');
const fullscreenBtn = document.getElementById('fullscreen-btn');
const downloadBtn = document.getElementById('download-btn');
const textModeBtn = document.getElementById('text-mode-btn');

// Overlays
const searchOverlay = document.getElementById('search-overlay');
const menuOverlay = document.getElementById('menu-overlay');
const searchCloseBtn = document.getElementById('search-close-btn');
const menuCloseBtn = document.getElementById('menu-close-btn');
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');

// Search data
let searchData = null;

// Load search data
fetch('search_data.json')
    .then(response => response.json())
    .then(data => {
        searchData = data;
        console.log('Search data loaded');
    })
    .catch(error => {
        console.warn('Search data not available:', error);
    });

function loadSpread(spreadNum, direction = 'none') {
    if (isAnimating) return;
    if (spreadNum < 0) spreadNum = 0;

    const maxSpread = Math.ceil(totalPages / 2) - 1;
    if (spreadNum > maxSpread) spreadNum = maxSpread;

    currentSpread = spreadNum;

    const leftPage = currentSpread * 2 + 1;
    const rightPage = currentSpread * 2 + 2;

    // Clear container
    pageContainer.innerHTML = '';

    // Left page
    if (leftPage <= totalPages) {
        const leftDiv = document.createElement('div');
        leftDiv.className = 'page-spread page-left';
        // Animace jen při listování ZPĚT (levá stránka se otáčí)
        if (direction === 'prev') leftDiv.classList.add('page-turning-prev');

        const leftImg = document.createElement('img');
        leftImg.src = `files/pages/${leftPage}.jpg`;
        leftImg.alt = `Page ${leftPage}`;
        leftDiv.appendChild(leftImg);
        pageContainer.appendChild(leftDiv);
    }

    // Right page (unless mobile or last page is odd)
    if (!isMobile && rightPage <= totalPages) {
        const rightDiv = document.createElement('div');
        rightDiv.className = 'page-spread page-right';
        // Animace jen při listování DOPŘEDU (pravá stránka se otáčí)
        if (direction === 'next') rightDiv.classList.add('page-turning-next');

        const rightImg = document.createElement('img');
        rightImg.src = `files/pages/${rightPage}.jpg`;
        rightImg.alt = `Page ${rightPage}`;
        rightDiv.appendChild(rightImg);
        pageContainer.appendChild(rightDiv);
    }

    // Update page info
    if (isMobile) {
        currentPageSpan.textContent = leftPage;
    } else {
        const displayPages = rightPage <= totalPages ? `${leftPage}-${rightPage}` : leftPage;
        currentPageSpan.textContent = displayPages;
    }

    // Update navigation buttons
    prevBtn.disabled = currentSpread === 0;
    nextBtn.disabled = (isMobile ? leftPage >= totalPages : rightPage >= totalPages);

    // Update thumbnails
    thumbnails.forEach(thumb => {
        const thumbPage = parseInt(thumb.dataset.page);
        const isActive = (thumbPage === leftPage || (!isMobile && thumbPage === rightPage));
        thumb.classList.toggle('active', isActive);
    });

    // Scroll thumbnail into view
    const activeThumb = document.querySelector(`.thumbnail[data-page="${leftPage}"]`);
    if (activeThumb) {
        activeThumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }

    // Animation lock
    if (direction !== 'none') {
        isAnimating = true;
        setTimeout(() => { isAnimating = false; }, 700);
    }
}

function nextPage() {
    if (!isAnimating) {
        loadSpread(currentSpread + 1, 'next');
    }
}

function prevPage() {
    if (!isAnimating) {
        loadSpread(currentSpread - 1, 'prev');
    }
}

function firstPage() {
    if (!isAnimating) {
        loadSpread(0, 'prev');
    }
}

function lastPage() {
    if (!isAnimating) {
        const maxSpread = Math.ceil(totalPages / 2) - 1;
        loadSpread(maxSpread, 'next');
    }
}

// Zoom functions
function zoomIn() {
    zoomLevel = Math.min(zoomLevel + 0.25, 3);
    pageContainer.style.transform = `scale(${zoomLevel}) rotate(${rotationAngle}deg)`;
}

function zoomOut() {
    zoomLevel = Math.max(zoomLevel - 0.25, 0.5);
    pageContainer.style.transform = `scale(${zoomLevel}) rotate(${rotationAngle}deg)`;
}

// Rotation functions
function rotateLeft() {
    rotationAngle -= 90;
    pageContainer.style.transform = `scale(${zoomLevel}) rotate(${rotationAngle}deg)`;
}

function rotateRight() {
    rotationAngle += 90;
    pageContainer.style.transform = `scale(${zoomLevel}) rotate(${rotationAngle}deg)`;
}

// Fullscreen toggle
function toggleFullscreen() {
    if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen();
        fullscreenBtn.querySelector('i').className = 'fas fa-compress';
    } else {
        document.exitFullscreen();
        fullscreenBtn.querySelector('i').className = 'fas fa-expand';
    }
}

// Download PDF
function downloadPDF() {
    // Create a link to download the original PDF
    const link = document.createElement('a');
    link.href = pdfFileName;
    link.download = pdfFileName;
    link.click();
}

// Search overlay
function toggleSearch() {
    const isVisible = searchOverlay.style.display === 'none';
    searchOverlay.style.display = isVisible ? 'flex' : 'none';
    if (isVisible) {
        searchInput.focus();
    } else {
        searchResults.innerHTML = '';
        searchInput.value = '';
    }
}

// Search functionality
function performSearch(query) {
    if (!searchData || !query) {
        searchResults.innerHTML = '<p>Zadejte hledaný text</p>';
        return;
    }

    const results = [];
    const lowerQuery = query.toLowerCase();

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
        searchResults.innerHTML = '<p>Nenalezeny žádné výsledky</p>';
    } else {
        searchResults.innerHTML = results.map(r => `
            <div class="search-result-item" onclick="goToPage(${r.page})">
                <div class="search-result-page">Stránka ${r.page}</div>
                <div class="search-result-snippet">${r.snippet}</div>
            </div>
        `).join('');
    }
}

function goToPage(pageNum) {
    const spreadNum = Math.floor((pageNum - 1) / 2);
    loadSpread(spreadNum, 'none');
    toggleSearch();
}

// Menu overlay
function toggleMenu() {
    menuOverlay.style.display = menuOverlay.style.display === 'none' ? 'flex' : 'none';
}

// Text mode
function toggleTextMode() {
    if (!searchData) {
        alert('Textová data nejsou k dispozici');
        return;
    }

    // Create text mode overlay if it doesn't exist
    let textOverlay = document.getElementById('text-mode-overlay');
    if (!textOverlay) {
        textOverlay = document.createElement('div');
        textOverlay.id = 'text-mode-overlay';

        let content = '<button id="text-mode-close" onclick="closeTextMode()">Zavřít</button>';
        content += '<div id="text-mode-content">';

        Object.entries(searchData.pages).forEach(([pageNum, text]) => {
            content += `
                <div class="text-mode-page">
                    <div class="text-mode-page-num">Stránka ${pageNum}</div>
                    <div>${text.replace(/\\n/g, '<br>')}</div>
                </div>
            `;
        });

        content += '</div>';
        textOverlay.innerHTML = content;
        document.body.appendChild(textOverlay);
    }

    textOverlay.style.display = 'block';
}

function closeTextMode() {
    const textOverlay = document.getElementById('text-mode-overlay');
    if (textOverlay) {
        textOverlay.style.display = 'none';
    }
}

// Event listeners - navigation
prevBtn.addEventListener('click', prevPage);
nextBtn.addEventListener('click', nextPage);
firstPageBtn.addEventListener('click', firstPage);
lastPageBtn.addEventListener('click', lastPage);
prevPageBtn.addEventListener('click', prevPage);
nextPageBtn.addEventListener('click', nextPage);

// Event listeners - toolbar
zoomInBtn.addEventListener('click', zoomIn);
searchBtn.addEventListener('click', toggleSearch);
menuBtn.addEventListener('click', toggleMenu);
rotateLeftBtn.addEventListener('click', rotateLeft);
rotateRightBtn.addEventListener('click', rotateRight);
fullscreenBtn.addEventListener('click', toggleFullscreen);
downloadBtn.addEventListener('click', downloadPDF);
textModeBtn.addEventListener('click', toggleTextMode);

// Event listeners - overlays
searchCloseBtn.addEventListener('click', toggleSearch);
menuCloseBtn.addEventListener('click', toggleMenu);
searchOverlay.addEventListener('click', (e) => {
    if (e.target === searchOverlay) toggleSearch();
});
menuOverlay.addEventListener('click', (e) => {
    if (e.target === menuOverlay) toggleMenu();
});

// Search input listener
searchInput.addEventListener('input', (e) => {
    const query = e.target.value.trim();
    if (query.length >= 2) {
        performSearch(query);
    } else {
        searchResults.innerHTML = '';
    }
});

// Thumbnail clicks - convert page number to spread
thumbnails.forEach(thumb => {
    thumb.addEventListener('click', () => {
        const pageNum = parseInt(thumb.dataset.page);
        const spreadNum = Math.floor((pageNum - 1) / 2);
        if (!isAnimating) {
            loadSpread(spreadNum, 'none');
        }
    });
});

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    switch(e.key) {
        case 'ArrowLeft':
        case 'PageUp':
            prevPage();
            break;
        case 'ArrowRight':
        case 'PageDown':
        case ' ':
            e.preventDefault();
            nextPage();
            break;
        case 'Home':
            firstPage();
            break;
        case 'End':
            lastPage();
            break;
    }
});

// Touch support for mobile swipe
let touchStartX = 0;
let touchEndX = 0;

pageContainer.addEventListener('touchstart', (e) => {
    touchStartX = e.changedTouches[0].screenX;
}, false);

pageContainer.addEventListener('touchend', (e) => {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
}, false);

function handleSwipe() {
    const swipeThreshold = 50;
    if (touchEndX < touchStartX - swipeThreshold) {
        nextPage();
    }
    if (touchEndX > touchStartX + swipeThreshold) {
        prevPage();
    }
}

// Initialize - load first spread
loadSpread(0, 'none');'''

        (self.output_dir / "js" / "flipbook.js").write_text(js_content, encoding='utf-8')


def main():
    """CLI rozhraní"""
    if len(sys.argv) < 2:
        print("Použití: python pdf_to_flipbook.py <cesta_k_pdf> [výstupní_složka] [název]")
        print("\nPříklad:")
        print('  python pdf_to_flipbook.py "zpravodaj.pdf"')
        print('  python pdf_to_flipbook.py "zpravodaj.pdf" "output" "Frýdek-Místek 09/2025"')
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    title = sys.argv[3] if len(sys.argv) > 3 else "Zpravodaj"

    if not output_dir:
        # Automaticky vytvoř název výstupní složky z PDF
        pdf_name = Path(pdf_path).stem
        output_dir = f"{pdf_name}-flipbook"

    if not os.path.exists(pdf_path):
        print(f"Chyba: PDF soubor nenalezen: {pdf_path}")
        sys.exit(1)

    try:
        converter = PDFToFlipbook(pdf_path, output_dir, title)
        converter.convert()
    except Exception as e:
        print(f"\nChyba při konverzi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
