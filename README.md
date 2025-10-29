# Zpravodaj API

Cloud-based PDF to HTML flipbook converter API. Converts newsletter PDFs into interactive HTML flipbooks and uploads them to AWS S3.

## Features

- 🚀 **Serverless**: Runs on Vercel (Python)
- 📄 **PDF Conversion**: PyMuPDF-based (no Poppler dependency)
- ☁️ **S3 Upload**: Automatic upload to AWS S3
- 🗄️ **Database**: Neon PostgreSQL for conversion logging
- 📱 **Mobile-friendly**: Generated flipbooks work on all devices

## API Endpoint

### `POST /api/convert`

Convert PDF to flipbook and upload to S3.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`

**Parameters:**
- `pdf` (file, required): PDF file to convert
- `title` (string, optional): Title for the flipbook (default: "Zpravodaj")
- `account` (string, optional): Account identifier (default: "default")
- `upload_to_s3` (boolean, optional): Whether to upload to S3 (default: true)

**Response (S3 upload):**
```json
{
  "success": true,
  "urls": {
    "index_url": "https://bucket.s3.region.amazonaws.com/account/title-timestamp/index.html",
    "base_url": "https://bucket.s3.region.amazonaws.com/account/title-timestamp",
    "pages": ["..."],
    "thumbs": ["..."]
  },
  "page_count": 24
}
```

**Response (no S3 upload):**
```json
{
  "success": true,
  "html": "...",
  "css": "...",
  "js": "...",
  "pages": ["base64..."],
  "thumbs": ["base64..."],
  "page_count": 24
}
```

## Setup & Deployment

### 1. Environment Variables

Create `.env` file (or set in Vercel dashboard):

```bash
# Neon PostgreSQL
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require

# AWS S3
AWS_S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### 2. Initialize Database

Run once to create schema:

```bash
python -c "from lib.db import init_db; init_db()"
```

### 3. Deploy to Vercel

#### Option A: GitHub Integration (recommended)

1. Push to GitHub
2. Import project in Vercel dashboard
3. Add environment variables
4. Deploy

#### Option B: Vercel CLI

```bash
npm i -g vercel
vercel login
vercel --prod
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your credentials

# Initialize database
python -c "from lib.db import init_db; init_db()"

# Run locally with Vercel CLI
vercel dev
```

## Testing

```bash
# Test conversion locally
curl -X POST http://localhost:3000/api/convert \
  -F "pdf=@test.pdf" \
  -F "title=Test Zpravodaj" \
  -F "account=test-account"
```

## Project Structure

```
zpravodaj-api/
├── api/
│   └── convert.py          # Vercel API endpoint
├── lib/
│   ├── pdf_converter.py    # PDF → Flipbook converter (PyMuPDF)
│   ├── s3_uploader.py      # S3 upload logic
│   └── db.py               # Neon DB connection & logging
├── tests/
│   └── (test files)
├── requirements.txt         # Python dependencies
├── vercel.json             # Vercel configuration
├── .env.example            # Environment variables template
└── README.md
```

## Architecture

1. **Client** uploads PDF → `/api/convert`
2. **API** converts PDF using PyMuPDF (no system dependencies)
3. **Converter** generates HTML/CSS/JS + images (JPEG)
4. **Uploader** pushes to S3
5. **Logger** saves conversion record to Neon
6. **API** returns S3 URLs

## Dependencies

- **PyMuPDF** (fitz): PDF rendering (no Poppler needed!)
- **Pillow**: Image manipulation
- **boto3**: AWS S3 client
- **psycopg2**: PostgreSQL driver

## Database Schema

```sql
CREATE TABLE conversions (
    id SERIAL PRIMARY KEY,
    account VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    page_count INTEGER NOT NULL,
    s3_url TEXT,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Troubleshooting

### "PyMuPDF not found"
Make sure `requirements.txt` is deployed and Vercel installed dependencies.

### "S3 upload failed"
Check AWS credentials and bucket permissions (needs `PutObject` and `PutObjectAcl`).

### "Database connection failed"
Verify `DATABASE_URL` in environment variables and Neon connection string.

## License

MIT
