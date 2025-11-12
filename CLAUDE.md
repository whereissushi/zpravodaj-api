# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Zpravodaj API** is a cloud-based PDF to HTML flipbook converter service that transforms newsletter PDFs into interactive, mobile-friendly HTML flipbooks. The service runs on Railway.app (production) with unlimited file upload support.

## Core Architecture

### Dual Deployment Strategy

The project supports two deployment platforms with different request size limits:

1. **Railway (Production)** - Unlimited file upload
   - Flask WSGI app (`app.py` + `wsgi.py`)
   - Deployed via `Procfile` with gunicorn
   - Supports PDFs up to 50+ MB
   - Returns ZIP file with complete flipbook

2. **Vercel (Legacy)** - 4.5 MB request limit
   - Serverless function (`api/index.py`)
   - Configured via `vercel.json`
   - Limited to smaller PDFs only

### Conversion Pipeline

The `PDFToFlipbook` class in `lib/pdf_converter.py` handles the entire conversion:

1. **PDF → Images**: Uses PyMuPDF (fitz) to convert each page to JPEG
   - Full-size: 150 DPI, 85% quality
   - Thumbnails: 200x300px, 75% quality
2. **HTML Generation**: Creates self-contained static flipbook with:
   - `index.html`: Main viewer with turn.js integration
   - `css/style.css`: Complete styling (blue toolbar #2563a6, light background #e8e8e8)
   - `js/flipbook.js`: jQuery + turn.js-based flipbook with drag-to-flip

**Important**: All HTML/CSS/JS is generated as strings in memory. The flipbook uses CDN dependencies (jQuery, turn.js, Font Awesome) for enhanced interactivity.

### Output Format

API returns a ZIP file containing:
```
flipbook.zip
├── index.html          # Main flipbook viewer with turn.js
├── css/style.css       # Styling (blue toolbar, light background)
├── js/flipbook.js      # Flipbook interaction logic (jQuery + turn.js)
└── files/
    ├── pages/          # Full-resolution JPEGs (1.jpg, 2.jpg, ...)
    └── thumb/          # Thumbnail JPEGs (1.jpg, 2.jpg, ...)
```

## Development Commands

### Local Development (Railway Mode)

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask development server
python app.py
# OR with gunicorn (production-like)
gunicorn -w 4 -b 0.0.0.0:8080 wsgi:app --timeout 300
```

### Testing the API

```bash
# Test conversion endpoint
curl -X POST http://localhost:8080/api/convert \
  -F "pdf=@test.pdf" \
  -F "title=Test Newsletter" \
  -F "account=test" \
  -o output.zip

# Verify output
unzip -l output.zip
```

### Deployment

**Railway** (recommended for production):
```bash
# Push to main branch - Railway auto-deploys from GitHub
git push origin main

# Deployment typically takes 8-10 minutes:
# - Nix package installation: 5-6 minutes
# - PyMuPDF wheel compilation: 2-3 minutes
# - Subsequent builds with cache: 2-3 minutes
```

**Important**: Railway auto-deploys from the `main` branch via GitHub integration. Monitor deployment status in Railway dashboard. The project is named "handsome-flexibility" in Railway.

**Vercel** (legacy, 4.5 MB limit):
```bash
vercel --prod
```

## Key Technical Decisions

### PyMuPDF vs pdf2image

The project uses **PyMuPDF (fitz)** instead of pdf2image because:
- No system dependencies (pdf2image requires Poppler)
- Works in serverless environments (Vercel, Railway)
- Faster rendering and better quality
- Pure Python library

### ZIP Response vs S3 Upload

Originally designed for S3 upload (`lib/s3_uploader.py`), but changed to ZIP download because:
- No AWS credentials needed
- User has full control over hosting
- Simpler deployment
- Lower costs

**Note**: S3 upload code remains in `lib/s3_uploader.py` and `lib/db.py` but is not actively used. Can be re-enabled by:
1. Setting environment variables (AWS_S3_BUCKET, DATABASE_URL)
2. Modifying `app.py` to use S3Uploader instead of ZIP response

### Flipbook Design (Generated Output)

The generated flipbook (`index.html` in ZIP) uses:
- **Turn.js library** - Realistic page-flip animations with drag-to-flip
- **Blue toolbar design** - Matches Munipolis style (#2563a6 toolbar, #e8e8e8 background)
- **CDN dependencies** - jQuery 3.6.0, turn.js 3.0, Font Awesome 6.4.0
- **Google Analytics** - Tracks page_turn events (requires GA ID replacement)

### Frontend Upload UI

The web UI (`public/index.html`) uses:
- **Glassmorphism design** - Professional dark theme with blur effects
- **No build step** - Pure HTML/CSS/JS, no framework
- **Drag & drop** - File upload with visual feedback
- **50 MB limit** - Enforced client-side for Railway deployment

## Important Constraints

### Vercel Limitations

Vercel has a **hard 4.5 MB request body limit** that cannot be increased even with Pro plan. This is why Railway is used for production. See `VERCEL_LIMITS.md` for workarounds.

### PyMuPDF Build Time

PyMuPDF is a large library (~200 MB). Railway builds can take 8-10 minutes due to:
1. Nix package installation (5-6 minutes)
2. Docker image export (2-3 minutes)
3. PyMuPDF wheel compilation

This is normal - subsequent builds use cache and are faster (~2-3 minutes).

## File Organization

- `app.py` - Flask application for Railway
- `wsgi.py` - WSGI entry point for gunicorn
- `api/index.py` - Vercel serverless function (legacy)
- `lib/pdf_converter.py` - Core conversion logic (PyMuPDF-based)
- `lib/s3_uploader.py` - S3 upload (unused, kept for reference)
- `lib/db.py` - Neon PostgreSQL logging (unused, kept for reference)
- `public/index.html` - Web UI (glassmorphism design)
- `Procfile` - Railway deployment configuration
- `railway.json` - Railway build settings
- `vercel.json` - Vercel routing (legacy)

## Generated Flipbook Features

The output HTML flipbook includes:
- **Search with highlighting**: Full-text search with OCR, results stay visible, found words highlighted with yellow overlay boxes
- **Click navigation**: Click right half of page to go forward, left half to go back
- **Drag-to-flip**: Realistic page turning by dragging pages (turn.js)
- **Zoom-to-click**: Click magnifying glass icon to enable zoom cursor, then click anywhere to zoom to that exact point
- **Pan tool**: After zooming, use pan tool (hand icon) to drag the zoomed view in any direction
- **Sound effects**: Page flip sound with toggle button (base64 WAV embedded)
- **Share button**: Web Share API with clipboard fallback
- **Navigation**: Arrow buttons, keyboard shortcuts (←/→, PageUp/PageDown, Space, Home/End)
- **Page thumbnails**: Clickable preview bar with auto-scroll to active page
- **Fullscreen mode**: Toggle fullscreen viewing
- **Mobile responsive**: Single page on mobile (<768px), double spread on desktop
- **Google Analytics**: Page turn event tracking (requires GA ID configuration)

**Important**: The flipbook depends on CDN resources (jQuery, turn.js, Font Awesome). Ensure internet connectivity for full functionality.

### Zoom & Pan Architecture

The zoom/pan system uses a **spacer div pattern** to create unlimited scrollable area:

1. **Spacer div** (`#zoom-spacer`): Invisible div with `width: totalWidth` and `height: totalHeight` to establish scrollable area in browser
2. **Flipbook positioning**: Uses `position: absolute` with `top/left` offset by `paddingX/paddingY` (200% of scaled flipbook size)
3. **Transform scaling**: Flipbook uses `transform: scale(zoomLevel)` with `transformOrigin: top left` - this is critical because turn.js requires original dimensions
4. **Scroll calculation**: When user clicks to zoom, calculates exact scroll position to keep clicked point at same viewport location

**Critical constraints**:
- `transform: scale()` does NOT affect browser's `scrollWidth/scrollHeight` calculations
- Spacer div must have actual width/height (not transform) to create scrollable area
- Viewer must have `position: relative` so absolute children are positioned relative to it
- Turn.js manipulates page element dimensions, so cannot resize pages directly - must use transform on container

**Debugging zoom issues**: Check console logs for:
- "Scroll range" should match "Total container size" (if not, spacer isn't working)
- "Actual scroll after set" should match "Calculated scroll" (if not, browser is clamping values)

### Search & Highlighting Architecture

The search feature extracts text from PDFs using **pytesseract OCR** with word-level bounding boxes:

1. **OCR Extraction** (`_extract_text_ocr()` in `lib/pdf_converter.py`):
   - Uses `pytesseract.image_to_data()` to get word positions (not just text)
   - Stores each word's coordinates (x, y, width, height) normalized to original image dimensions
   - Only keeps words with confidence > 30%
   - Data structure: `{boxes: [{word, x, y, w, h}], width, height}` per page

2. **Search Data Embedding**:
   - OCR text and word positions embedded as JSON in `index.html`
   - Format: `{pages: {pageNum: text}, positions: {pageNum: {boxes, width, height}}}`

3. **Highlight Overlay** (`#highlight-overlay`):
   - Positioned absolutely relative to `#flipbook-viewer` (sibling of `#flipbook`)
   - Must use `right: 0; bottom: 0` with `width: auto !important` to prevent turn.js manipulation
   - Turn.js will add `.turn-page` class if overlay is inside flipbook - must be outside!
   - Z-index: 100 to appear above pages

4. **Matching Logic** (`performSearch()` and `highlightSearchOnPage()`):
   - Uses `word.startsWith(query)` to match words beginning with search term
   - Skips single-letter matches unless query itself is single letter
   - Calculates box positions: `getBoundingClientRect()` for page + viewer, then relative offset
   - Scale factors: `displayWidth / originalWidth` and `displayHeight / originalHeight`

**Critical constraints**:
- Overlay must be **sibling** of flipbook, not child (turn.js treats children as pages)
- Use `getBoundingClientRect()` not `offset()` for accurate positioning with transforms
- Clear highlights in `turned` event only if not from search navigation
- Responsive sizing: Calculate height from viewport (90%), then width from aspect ratio

**Debugging search issues**:
- Check "Matching boxes found: X" in console (should be > 0)
- Verify overlay dimensions match viewer: width should be full viewport, not 944px
- Check box positions: should be within viewer bounds (0 to viewerWidth)
- If highlights invisible: check `overflow: visible` on overlay and z-index > turn.js pages

## Modifying Generated Flipbook

All HTML/CSS/JS for the generated flipbook is embedded as Python strings in `lib/pdf_converter.py`:

- **HTML structure**: `_generate_html()` method (lines ~80-150)
- **CSS styling**: `_get_css()` method (lines ~160-360)
- **JavaScript logic**: `_get_js()` method (lines ~960-2200+)
  - Search: `performSearch()` and `highlightSearchOnPage()` functions
  - Click navigation: `flipbook.on('click')` handler
  - Zoom functionality: `applyZoom()` function
  - Pan functionality: `enablePanning()` function

**Critical**: When modifying these strings:
1. Use triple-quoted strings (`'''`) for multiline content
2. Escape curly braces: `{{` and `}}` for literal braces in f-strings
3. Use f-string interpolation for dynamic values (e.g., `{page_count}`)
4. Test output by running a conversion and inspecting the generated `index.html`
5. **Always test zoom/pan after modifications** - use Railway API endpoint to generate a real flipbook and verify in browser

**Testing zoom/pan changes**:
```bash
# Convert PDF via API
curl -X POST https://[your-railway-url]/api/convert \
  -F "pdf=@test.pdf" \
  -F "title=Test" \
  -F "account=test" \
  -o test-flipbook.zip

# Extract and open in browser
unzip test-flipbook.zip -d test-output
# Open test-output/index.html in browser
# Check browser console for debug logs
```

**Google Analytics Setup**: Replace `G-XXXXXXXXXX` in `_generate_html()` with actual GA tracking ID.

**Design Reference**: Current design matches Munipolis flipbook style (blue toolbar #2563a6, light background #e8e8e8).

## Development Workflow for UI Changes

When modifying zoom/pan or other flipbook UI features:

1. **Make changes** to `lib/pdf_converter.py` (JavaScript embedded in `_get_js()` method)
2. **Commit and push** to trigger Railway deployment
3. **Wait for build** (8-10 minutes for first build, 2-3 minutes with cache)
4. **Test via API**:
   ```bash
   curl -X POST https://[railway-url]/api/convert \
     -F "pdf=@Zpravodaje/Beroun - Říjen 2025.pdf" \
     -F "title=Test" \
     -F "account=test" \
     -o test-flipbook.zip
   ```
5. **Extract and test** in browser:
   - Unzip the output
   - Open `index.html` in browser
   - Open DevTools Console to check debug logs
   - Test zoom-to-click: Click zoom icon, then click on page
   - Test pan: After zooming, click pan tool (hand icon) and drag
   - Verify scroll range matches container size in console logs

### Flipbook Responsive Sizing

The flipbook dimensions are calculated to fit viewport while maintaining A4 aspect ratio (1:1.414):

```javascript
// Calculate from HEIGHT first (not width) to avoid white side margins
const availableHeight = viewportHeight * 0.9;  // 90% of viewport
const optimalWidth = 2 * (availableHeight / 1.414);  // For double-page spread

// Then constrain by viewport width
bookWidth = Math.min(optimalWidth, viewportWidth * 0.7);
bookHeight = availableHeight;
```

**Why height-first calculation**:
- Width-first creates letterboxing (white margins on sides)
- Height-first with `object-fit: contain` ensures full page visible without cropping
- Pages fill vertical space completely

**Screen-specific sizing**:
- FullHD (1920x1080): 70% viewport width, max 1400px
- 1440p+ (>1920): 70% viewport width, max 1600px
- Mobile (<768px): Single-page mode, 90% viewport

**Common issues**:
- White side margins: Width calculated incorrectly, use height-based formula above
- Cropped content: Using `object-fit: cover` instead of `contain`
- Can't zoom on FullHD: Flipbook too large (>70% viewport width)
- If zoom doesn't center on click: Check "Scroll range" vs "Total container size" in console
- If pan has boundaries: Check padding calculation (should be 200% of scaled dimensions)
- If turn.js breaks: Make sure you're only using `transform: scale()` on flipbook container, not resizing page elements directly
