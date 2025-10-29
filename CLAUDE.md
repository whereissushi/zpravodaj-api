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
   - `index.html`: Main viewer (inline page count, embedded JS)
   - `css/style.css`: Complete styling (glassmorphism dark theme)
   - `js/flipbook.js`: Vanilla JS flipbook logic (no external dependencies)

**Important**: All HTML/CSS/JS is generated as strings in memory - the flipbook is completely standalone with no external CDN dependencies.

### Output Format

API returns a ZIP file containing:
```
flipbook.zip
├── index.html          # Main flipbook viewer
├── css/style.css       # Styling (glassmorphism design)
├── js/flipbook.js      # Flipbook interaction logic
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
```

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

### Frontend Design

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
- **Navigation**: Arrow buttons, keyboard shortcuts (←/→, PageUp/PageDown, Space, Home/End)
- **Mobile support**: Touch swipe gestures, responsive layout
- **Page thumbnails**: Clickable preview bar with auto-scroll
- **Double-page spread**: Desktop shows two pages side-by-side (book-like)
- **Single-page mode**: Mobile displays one page at a time
- **Page flip animation**: 3D rotation effect when turning pages

All flipbook logic is self-contained with zero external dependencies.
