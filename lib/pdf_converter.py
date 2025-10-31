#!/usr/bin/env python3
"""
PDF to Flipbook Converter - Cloud API Version
Konvertuje PDF zpravodaj na interaktivní HTML flipbook (PyMuPDF verze)
"""

import io
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image


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

    def convert(self):
        """
        Main conversion function - returns dict with all assets

        Returns:
            dict with keys: 'html', 'css', 'js', 'pages', 'thumbs'
        """
        # Convert PDF to images
        self._convert_pdf_to_images()

        # Generate HTML/CSS/JS
        html = self._generate_html(len(self.pages_images))
        css = self._get_css()
        js = self._get_js()

        return {
            'html': html,
            'css': css,
            'js': js,
            'pages': self.pages_images,  # List of bytes (JPEG)
            'thumbs': self.thumb_images,  # List of bytes (JPEG)
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

    def _generate_html(self, page_count):
        """Generate HTML content"""
        return f'''<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>{self.title}</title>
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <div id="flipbook-container">
        <!-- Modrý toolbar -->
        <div id="flipbook-toolbar">
            <button id="zoom-in-btn" class="toolbar-btn" title="Přiblížit">
                <i class="fas fa-plus"></i>
            </button>
            <button id="zoom-out-btn" class="toolbar-btn" title="Oddálit">
                <i class="fas fa-minus"></i>
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

    <script>
        const totalPages = {page_count};
    </script>
    <script src="js/flipbook.js"></script>
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

.page-right.page-turning-next {
    animation: pageFlipRight 0.7s cubic-bezier(0.645, 0.045, 0.355, 1);
    z-index: 10;
}

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
}'''

    def _get_js(self):
        """Return JavaScript content"""
        return '''let currentSpread = 0;
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
const zoomOutBtn = document.getElementById('zoom-out-btn');
const rotateLeftBtn = document.getElementById('rotate-left-btn');
const rotateRightBtn = document.getElementById('rotate-right-btn');
const fullscreenBtn = document.getElementById('fullscreen-btn');

function loadSpread(spreadNum, direction = 'none') {
    if (isAnimating) return;
    if (spreadNum < 0) spreadNum = 0;

    const maxSpread = Math.ceil(totalPages / 2) - 1;
    if (spreadNum > maxSpread) spreadNum = maxSpread;

    currentSpread = spreadNum;

    const leftPage = currentSpread * 2 + 1;
    const rightPage = currentSpread * 2 + 2;

    pageContainer.innerHTML = '';

    if (leftPage <= totalPages) {
        const leftDiv = document.createElement('div');
        leftDiv.className = 'page-spread page-left';
        if (direction === 'prev') leftDiv.classList.add('page-turning-prev');

        const leftImg = document.createElement('img');
        leftImg.src = `files/pages/${leftPage}.jpg`;
        leftImg.alt = `Page ${leftPage}`;
        leftDiv.appendChild(leftImg);
        pageContainer.appendChild(leftDiv);
    }

    if (!isMobile && rightPage <= totalPages) {
        const rightDiv = document.createElement('div');
        rightDiv.className = 'page-spread page-right';
        if (direction === 'next') rightDiv.classList.add('page-turning-next');

        const rightImg = document.createElement('img');
        rightImg.src = `files/pages/${rightPage}.jpg`;
        rightImg.alt = `Page ${rightPage}`;
        rightDiv.appendChild(rightImg);
        pageContainer.appendChild(rightDiv);
    }

    if (isMobile) {
        currentPageSpan.textContent = leftPage;
    } else {
        const displayPages = rightPage <= totalPages ? `${leftPage}-${rightPage}` : leftPage;
        currentPageSpan.textContent = displayPages;
    }

    prevBtn.disabled = currentSpread === 0;
    nextBtn.disabled = (isMobile ? leftPage >= totalPages : rightPage >= totalPages);

    thumbnails.forEach(thumb => {
        const thumbPage = parseInt(thumb.dataset.page);
        const isActive = (thumbPage === leftPage || (!isMobile && thumbPage === rightPage));
        thumb.classList.toggle('active', isActive);
    });

    const activeThumb = document.querySelector(`.thumbnail[data-page="${leftPage}"]`);
    if (activeThumb) {
        activeThumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }

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

// Event listeners - navigation
prevBtn.addEventListener('click', prevPage);
nextBtn.addEventListener('click', nextPage);
firstPageBtn.addEventListener('click', firstPage);
lastPageBtn.addEventListener('click', lastPage);
prevPageBtn.addEventListener('click', prevPage);
nextPageBtn.addEventListener('click', nextPage);

// Event listeners - toolbar
zoomInBtn.addEventListener('click', zoomIn);
zoomOutBtn.addEventListener('click', zoomOut);
rotateLeftBtn.addEventListener('click', rotateLeft);
rotateRightBtn.addEventListener('click', rotateRight);
fullscreenBtn.addEventListener('click', toggleFullscreen);

thumbnails.forEach(thumb => {
    thumb.addEventListener('click', () => {
        const pageNum = parseInt(thumb.dataset.page);
        const spreadNum = Math.floor((pageNum - 1) / 2);
        if (!isAnimating) {
            loadSpread(spreadNum, 'none');
        }
    });
});

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

loadSpread(0, 'none');'''
