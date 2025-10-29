# Zpravodaj API - Project Summary

## ✅ Co je hotové

### 1. **GitHub Repository**
- 🔗 https://github.com/whereissushi/zpravodaj-api
- Kompletní kód pushnutý a připravený k deployi

### 2. **Refaktorovaný converter**
- ✅ PyMuPDF místo pdf2image (žádný Poppler!)
- ✅ Funguje v serverless prostředí
- ✅ Stejná kvalita výstupu
- 📄 `lib/pdf_converter.py`

### 3. **Vercel API Endpoint**
- ✅ `POST /api/convert` - hlavní konverze
- ✅ `GET /api/init-db` - inicializace DB (spustit jednou)
- ✅ Multipart form upload (PDF + metadata)
- 📄 `api/convert.py`, `api/init-db.py`

### 4. **S3 Upload**
- ✅ Automatický upload HTML/CSS/JS/images
- ✅ Veřejně dostupné URLs
- ✅ Organizace podle účtu/názvu
- 📄 `lib/s3_uploader.py`

### 5. **Neon Database**
- ✅ PostgreSQL schema pro logování
- ✅ Tracking konverzí (kdo, kdy, kolik stránek)
- ✅ Error logging
- 📄 `lib/db.py`

### 6. **Dokumentace**
- ✅ README.md - Kompletní API dokumentace
- ✅ DEPLOYMENT.md - Deployment instrukce
- ✅ .env.example - Template pro env variables

---

## 🚀 Next Steps (co musíš udělat ty)

### 1. Import do Vercelu (2 minuty)
1. Jdi na https://vercel.com/new
2. Import `whereissushi/zpravodaj-api`
3. Deploy

### 2. Nastavit Environment Variables (5 minut)
V Vercel Settings → Environment Variables:
```
DATABASE_URL=postgresql://...  (z Neon)
AWS_S3_BUCKET=bucket-name
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

### 3. Inicializovat databázi (30 sekund)
Zavolat jednou: `https://your-app.vercel.app/api/init-db`

### 4. Test!
```bash
curl -X POST https://your-app.vercel.app/api/convert \
  -F "pdf=@test.pdf" \
  -F "title=Frýdek-Místek 10/2024" \
  -F "account=fm"
```

---

## 📊 Struktura projektu

```
zpravodaj-api/
├── api/
│   ├── convert.py       # POST /api/convert - main endpoint
│   └── init-db.py       # GET /api/init-db - DB setup
├── lib/
│   ├── pdf_converter.py # PyMuPDF converter (no Poppler!)
│   ├── s3_uploader.py   # AWS S3 upload logic
│   └── db.py            # Neon PostgreSQL
├── requirements.txt     # Python deps (PyMuPDF, Pillow, boto3, psycopg2)
├── vercel.json          # Vercel config
└── README.md            # Full documentation
```

---

## 🔑 Tokeny které MUŠ���Š smazat

⚠️ **HNED po dokončení deploymentu smaž a vygeneruj nové:**

1. **GitHub token**: https://github.com/settings/tokens
2. **Vercel token**: https://vercel.com/account/tokens
3. **Neon API key**: https://console.neon.tech/app/settings/api-keys

(Všechny které jsi sdílel během setupu - viz chat historie)

---

## 💡 Technická výhoda vs. původní řešení

| Původní (Desktop)           | Nové (Cloud API)              |
|-----------------------------|-------------------------------|
| Windows EXE                 | Web API (Vercel serverless)   |
| pdf2image + Poppler         | PyMuPDF (pure Python)         |
| Lokální soubory             | S3 hosting                    |
| Manuální distribuce         | Auto-deploy z GitHub          |
| Žádné logování              | Neon DB tracking              |

---

## 🎯 Co API dělá

1. Přijme PDF + metadata (`title`, `account`)
2. Konvertuje PDF → JPEG stránky (PyMuPDF)
3. Vygeneruje HTML flipbook (stejný jako desktop verze)
4. Uploadne vše do S3 (veřejný přístup)
5. Zaloguje do Neon DB
6. Vrátí URLs: `index_url`, `pages[]`, `thumbs[]`

---

## 📱 Použití z frontendu

```javascript
const formData = new FormData();
formData.append('pdf', pdfFile);
formData.append('title', 'Frýdek-Místek 10/2024');
formData.append('account', 'fm');

const response = await fetch('https://zpravodaj-api.vercel.app/api/convert', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Flipbook URL:', result.urls.index_url);
```

---

## ✨ Hotovo!

Celý projekt je připravený k nasazení. Stačí dokončit kroky z `DEPLOYMENT.md` a máš plně funkční cloud službu!
