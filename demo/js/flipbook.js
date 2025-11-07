// Configuration
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

    // Update active zoom button
    $('.zoom-option-btn').removeClass('active');
    $(`.zoom-option-btn[data-zoom="${zoomLevel}"]`).addClass('active');
    $('#zoom-slider').val(zoomLevel);
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

    // Generate new QR code (using local js/qrcode.min.js)
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
        const lines = text.split('\n');
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
        allText += `\n\n=== Stránka ${pageNum} ===\n${text}`;
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
    const lines = text.split('\n');
    const topics = [];
    const numbers = [];

    lines.forEach(line => {
        const trimmed = line.trim();

        // Find headings (ALL CAPS)
        if (trimmed === trimmed.toUpperCase() && trimmed.length > 10 && trimmed.length < 100) {
            topics.push(trimmed);
        }

        // Find numbers (statistics)
        const numberMatches = trimmed.match(/\d+\s*(tun|mil|Kč|stran|dětí|občan|procent|%)/gi);
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
});

// Zoom on click - click on page to zoom to that point
flipbook.on('click', '.page', function(e) {
    if (zoomLevel === 1) {
        // Zoom in to 2x at click position
        const rect = this.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;

        applyZoom(2);
        flipbook.css('transformOrigin', `${x}% ${y}%`);
    } else {
        // Zoom out to 1x
        applyZoom(1);
    }
});

// Prevent page flip when zoomed (allow normal drag-to-flip when zoom = 1x)
flipbook.bind('start', function(e, pageObj, corner) {
    if (zoomActive) {
        e.preventDefault();
        return false;
    }
});