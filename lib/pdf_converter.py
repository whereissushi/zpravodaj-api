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
</head>
<body>
    <div id="flipbook-container">
        <div id="flipbook-header">
            <h1>{self.title}</h1>
            <div id="page-info">
                <span id="current-page">1</span> / <span id="total-pages">{page_count}</span>
            </div>
        </div>

        <div id="flipbook-viewer">
            <button id="prev-btn" class="nav-btn" aria-label="Předchozí stránka">‹</button>

            <div id="page-container">
                <!-- Pages loaded dynamically by JavaScript -->
            </div>

            <button id="next-btn" class="nav-btn" aria-label="Další stránka">›</button>
        </div>

        <div id="flipbook-controls">
            <button id="first-page-btn" title="První stránka">⏮</button>
            <button id="last-page-btn" title="Poslední stránka">⏭</button>
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
    background: #2a2a2a;
    color: #fff;
    overflow: hidden;
    height: 100vh;
}

#flipbook-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
}

#flipbook-header {
    background: #1a1a1a;
    padding: 15px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid #3a3a3a;
}

#flipbook-header h1 {
    font-size: 20px;
    font-weight: 500;
}

#page-info {
    font-size: 16px;
    color: #888;
}

#current-page {
    color: #fff;
    font-weight: 600;
}

#flipbook-viewer {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    background: #2a2a2a;
    perspective: 1500px;
}

#page-container {
    max-width: 95%;
    max-height: 90%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    transform-style: preserve-3d;
    position: relative;
}

.page-spread {
    position: relative;
    width: auto;
    height: 100%;
    max-height: 100%;
    box-shadow: 0 5px 30px rgba(0,0,0,0.8);
}

.page-spread img {
    width: auto;
    height: 100%;
    max-height: calc(100vh - 250px);
    display: block;
    object-fit: contain;
}

.page-left {
    transform-origin: right center;
    border-right: 1px solid #1a1a1a;
}

.page-right {
    transform-origin: left center;
    border-left: 1px solid #1a1a1a;
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
    width: auto;
    height: 100%;
}

.page-single img {
    max-height: calc(100vh - 200px);
}

#current-page-img {
    display: none;
}

.nav-btn {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(0, 0, 0, 0.5);
    color: white;
    border: none;
    font-size: 48px;
    padding: 20px 15px;
    cursor: pointer;
    z-index: 10;
    transition: background 0.3s;
    line-height: 1;
}

.nav-btn:hover {
    background: rgba(0, 0, 0, 0.8);
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

#flipbook-controls {
    background: #1a1a1a;
    padding: 10px;
    display: flex;
    justify-content: center;
    gap: 10px;
    border-top: 1px solid #3a3a3a;
}

#flipbook-controls button {
    background: #3a3a3a;
    color: white;
    border: none;
    padding: 10px 20px;
    cursor: pointer;
    border-radius: 4px;
    font-size: 16px;
    transition: background 0.3s;
}

#flipbook-controls button:hover {
    background: #4a4a4a;
}

#thumbnail-bar {
    background: #1a1a1a;
    padding: 10px;
    overflow-x: auto;
    overflow-y: hidden;
    border-top: 2px solid #3a3a3a;
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
}

.thumbnail:hover {
    transform: scale(1.05);
}

.thumbnail.active {
    border-color: #0066cc;
}

@media (max-width: 768px) {
    #flipbook-header h1 {
        font-size: 16px;
    }

    #page-info {
        font-size: 14px;
    }

    .nav-btn {
        font-size: 32px;
        padding: 15px 10px;
    }

    #flipbook-controls button {
        padding: 8px 12px;
        font-size: 14px;
    }

    .thumbnail {
        height: 80px;
    }

    #page-container {
        gap: 0;
    }

    .page-spread {
        width: 90%;
        height: auto;
    }

    .page-spread img {
        width: 100%;
        height: auto;
        max-height: calc(100vh - 220px);
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

const pageContainer = document.getElementById('page-container');
const currentPageSpan = document.getElementById('current-page');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const firstPageBtn = document.getElementById('first-page-btn');
const lastPageBtn = document.getElementById('last-page-btn');
const thumbnails = document.querySelectorAll('.thumbnail');

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

prevBtn.addEventListener('click', prevPage);
nextBtn.addEventListener('click', nextPage);
firstPageBtn.addEventListener('click', firstPage);
lastPageBtn.addEventListener('click', lastPage);

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
