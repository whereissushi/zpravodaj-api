# Co instalujeme a proč

## Python balíčky (requirements.txt)

### 1. **PyMuPDF==1.23.8**
- **Co to je:** Knihovna pro práci s PDF soubory (PyMuPDF = Python binding pro MuPDF engine)
- **Co dělá:** Konvertuje PDF stránky na JPEG obrázky (150 DPI)
- **Proč to používáme:** Pure Python knihovna, nečekuje systémové závislosti (na rozdíl od pdf2image který potřebuje Poppler)
- **Kde se použije:** `lib/pdf_converter.py` - funkce `_convert_pdf_to_images()`

### 2. **Pillow==10.1.0**
- **Co to je:** Python Imaging Library (PIL fork)
- **Co dělá:** Zpracovává obrázky - resize, crop, format conversion
- **Proč to používáme:** Vytváříme thumbnaily (200x300px) z full-size JPEG
- **Kde se použije:** `lib/pdf_converter.py` - generování miniatur pro thumbnail bar

### 3. **pytesseract==0.3.10**
- **Co to je:** Python wrapper pro Tesseract OCR engine
- **Co dělá:** Extrahuje text z obrázků (Optical Character Recognition)
- **Proč to používáme:** Umožňuje vyhledávání v flipbooku - extrahujeme text z každé stránky PDF
- **⚠️ POZOR:** Potřebuje systémový balíček `tesseract-ocr` nainstalovaný!
- **Kde se použije:** `lib/pdf_converter.py` - funkce `_extract_text_ocr()`

### 4. **Flask==3.0.0**
- **Co to je:** Micro web framework pro Python
- **Co dělá:** Poskytuje HTTP server, routing, request handling
- **Proč to používáme:** Naše API endpoint `/api/convert` (přijímá POST s PDF)
- **Kde se použije:** `app.py` - celá Flask aplikace

### 5. **Flask-CORS==4.0.0**
- **Co to je:** Flask extension pro Cross-Origin Resource Sharing
- **Co dělá:** Umožňuje frontend (jiná doména) volat naše API
- **Proč to používáme:** Web UI (`public/index.html`) může uploadovat PDF z jiné domény
- **Kde se použije:** `app.py` - `CORS(app)`

### 6. **gunicorn==21.2.0**
- **Co to je:** Python WSGI HTTP Server (Green Unicorn)
- **Co dělá:** Production-ready server pro Flask aplikace
- **Proč to používáme:** Flask development server není vhodný pro produkci, gunicorn zvládá multiple workers
- **Kde se použije:** `wsgi.py` + `Procfile` (Railway/EB spouští: `gunicorn wsgi:app`)

### 7. **python-dotenv==1.0.0**
- **Co to je:** Načítá environment variables z `.env` souboru
- **Co dělá:** `load_dotenv()` - načte ENV proměnné pro local development
- **Proč to používáme:** AWS credentials, S3 bucket names (původně, teď nepoužíváme)
- **Kde se použije:** `app.py` (ale teď je to disabled, protože nepoužíváme S3)

---

## Systémové balíčky (OS level)

### 1. **tesseract-ocr**
- **Co to je:** OCR engine (C++ aplikace)
- **Co dělá:** Rozpoznává text z obrázků (main engine)
- **Proč to potřebujeme:** `pytesseract` je jen Python wrapper, potřebuje skutečný Tesseract binary
- **Jak se instaluje:**
  - Railway: automaticky přes Nixpacks
  - EB/ECS: přes `.ebextensions/01_gunicorn.config` → `yum install tesseract`
  - Lambda: musí být v Docker image nebo Lambda Layer

### 2. **tesseract-langpack-ces**
- **Co to je:** Jazykový model pro češtinu
- **Co dělá:** Trained data pro rozpoznávání českých znaků (ě, š, č, ř, ...)
- **Proč to potřebujeme:** Naše zpravodaje jsou v češtině → lepší OCR accuracy
- **Jak se instaluje:** Stejně jako `tesseract-ocr` (balíček navíc)

---

## Workflow: Co se stane při konverzi PDF

```
1. User uploadne PDF (POST /api/convert)
   ↓ Flask přijme request

2. PyMuPDF otevře PDF
   ↓ Konvertuje každou stránku na JPEG (150 DPI)

3. Pillow vezme JPEG
   ↓ Vytvoří thumbnail (200x300px, 75% kvalita)

4. Tesseract (přes pytesseract) zpracuje každý JPEG
   ↓ OCR extrahuje text → uloží do JSON pro search

5. Python generuje HTML/CSS/JS flipbook
   ↓ Zabalí do ZIP (pages/ + thumbs/ + index.html)

6. Flask vrátí ZIP ke stažení
```

---

## Proč máme právě tyto verze?

- **PyMuPDF 1.23.8** - poslední stabilní před breaking changes v 1.24.x
- **Pillow 10.1.0** - kompatibilní s Python 3.11
- **pytesseract 0.3.10** - poslední před změnou API
- **Flask 3.0.0** - nová major version, lepší type hints
- **gunicorn 21.2.0** - async worker support

---

## Co říct na meetingu

**"Používáme 6 Python balíčků:**
- **PyMuPDF** - konverze PDF na obrázky (pure Python, bez systémových závislostí)
- **Pillow** - generování thumbnailů
- **pytesseract** - wrapper pro OCR
- **Flask + Flask-CORS** - API endpoint
- **gunicorn** - production server

**Plus jeden systémový balíček:**
- **Tesseract OCR** - samotný OCR engine (C++ binary)

**Důležité:** Railway instaluje Tesseract automaticky, na AWS musíme přidat do `.ebextensions/01_gunicorn.config`"

---

## Troubleshooting

### "TesseractNotFoundError"
→ Tesseract binary není nainstalovaný v systému
→ Řešení: `apt-get install tesseract-ocr tesseract-ocr-ces` (Debian/Ubuntu)
→ Nebo: `yum install tesseract tesseract-langpack-ces` (Amazon Linux)

### "PyMuPDF import failed"
→ Špatná verze nebo chybí dependencies
→ Řešení: `pip install --upgrade PyMuPDF==1.23.8`

### "Flask CORS errors"
→ Frontend nemůže volat API (různé domény)
→ Řešení: Zkontroluj že máš `Flask-CORS` nainstalované a `CORS(app)` v kódu
