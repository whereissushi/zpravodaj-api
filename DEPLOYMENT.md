# Deployment Instructions

## ✅ Co je hotové

- ✅ GitHub repo vytvořeno: https://github.com/whereissushi/zpravodaj-api
- ✅ Kód pushnutý na `main` branch
- ✅ Kompletní API implementace (PyMuPDF, S3, Neon DB)

## 🚀 Dokončení deploymentu

### 1. Import do Vercelu

Jdi na: https://vercel.com/new

1. Klikni **"Import Git Repository"**
2. Vyber **whereissushi/zpravodaj-api**
3. Framework Preset: **Other**
4. Klikni **Deploy**

### 2. Nastavení Environment Variables

Po vytvoření projektu jdi do **Settings → Environment Variables** a přidej:

#### Neon Database
```
DATABASE_URL = postgresql://user:password@host.neon.tech/dbname?sslmode=require
```
(Zkopíruj z Neon dashboard: https://console.neon.tech/)

#### AWS S3 (pokud máš bucket)
```
AWS_S3_BUCKET = your-bucket-name
AWS_REGION = us-east-1
AWS_ACCESS_KEY_ID = your-access-key-id
AWS_SECRET_ACCESS_KEY = your-secret-access-key
```

### 3. Inicializace Databáze

Po deploymentu spusť jednou (lokálně s .env nebo přes Vercel CLI):

```bash
# Lokálně (s .env)
python -c "from lib.db import init_db; init_db()"

# Nebo přes Vercel serverless function (vytvoř api/init-db.py)
```

**Jednodušší způsob:** Připojit se k Neon přes jejich SQL Editor a spustit:

```sql
CREATE TABLE IF NOT EXISTS conversions (
    id SERIAL PRIMARY KEY,
    account VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    page_count INTEGER NOT NULL,
    s3_url TEXT,
    status VARCHAR(50) NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversions_account ON conversions(account);
CREATE INDEX IF NOT EXISTS idx_conversions_created_at ON conversions(created_at DESC);
```

### 4. Test API

Po deployu test:

```bash
# Get your deployment URL (např. zpravodaj-api.vercel.app)
curl -X POST https://zpravodaj-api.vercel.app/api/convert \
  -F "pdf=@test.pdf" \
  -F "title=Test Zpravodaj" \
  -F "account=test-account"
```

## 📝 Neon API Key

Tvůj Neon API key: `napi_x6l86i0zc1o5vcs8jrc33gx05mpi4etwp6wt6tqodwo2ufgrvijt50f2p3jmic0e`

Connection string získej tady:
https://console.neon.tech/app/projects → Select project → Connection Details

## 🔐 AWS S3 Setup (pokud nemáš bucket)

1. Jdi na AWS Console: https://console.aws.amazon.com/s3/
2. Create bucket (např. `zpravodaj-flipbooks`)
3. Region: `us-east-1` (nebo jiný)
4. **Block all public access**: OFF (nebo nastav bucket policy)
5. Vytvoř IAM user s permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:PutObjectAcl"
         ],
         "Resource": "arn:aws:s3:::zpravodaj-flipbooks/*"
       }
     ]
   }
   ```
6. Vygeneruj Access Key → přidej do Vercel env variables

## 🎉 Hotovo!

Po dokončení těchto kroků budeš mít:
- ✅ Funkční API endpoint na `https://zpravodaj-api.vercel.app/api/convert`
- ✅ Automatický upload do S3
- ✅ Logování do Neon DB
- ✅ Auto-deploy při každém push do GitHub

## ⚠️ NEZAPOMEŇ

**Smazat tokeny** které jsi mi poslal:
- GitHub token: https://github.com/settings/tokens
- Vercel token: https://vercel.com/account/tokens
- Neon API key: https://console.neon.tech/app/settings/api-keys

A vytvoř nové!
