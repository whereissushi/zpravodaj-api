# AWS Deployment Guide - Zpravodaj API

## JAK JSI TO DĚLAL PŮVODNĚ

1. **Flask API** (`app.py`) - základní POST endpoint `/api/convert`
2. **PyMuPDF converter** (`lib/pdf_converter.py`) - konverze PDF→JPEG→HTML
3. **Původně S3 upload** - kód v `lib/s3_uploader.py` + `lib/db.py` (Neon Postgres)
4. **Změna na ZIP** - místo S3 se vrací ZIP přímo (jednodušší, bez AWS credentials)
5. **Vercel pokus** - narazil jsi na 4.5 MB limit
6. **Railway** - finální řešení pro production (neomezený upload)

**TVŮJ SOUČASNÝ STAV:**
- Flask app funguje na Railway s gunicorn
- Žádné AWS credentials v kódu
- ZIP download místo S3 upload
- PyMuPDF bez systémových závislostí

---

## VARIANTA 1: Elastic Beanstalk (⭐ NEJJEDNODUŠŠÍ)

### Proč Elastic Beanstalk?
- ✅ **Zero změn kódu** - tvůj Flask funguje BEZ úprav
- ✅ **Žádný upload limit** - jako Railway
- ✅ **Auto-scaling** - zvládne více konverzí najednou
- ✅ **Load balancer** - included
- 💰 **Cena**: ~$50/měsíc (24/7) nebo ~$0.50 pro 2h test

### Co potřebuješ (setup jednou)

1. **AWS účet** s admin přístupem
2. **AWS EB CLI**: `pip install awsebcli`

```bash
# Konfigurace AWS credentials
aws configure
# Zadej:
# - AWS Access Key ID (z AWS Console → IAM)
# - AWS Secret Access Key
# - Default region: eu-central-1
# - Default output: json
```

### Deployment (RYCHLÝ START)

```bash
# 1. Inicializace EB projektu (jednou)
eb init -p python-3.11 zpravodaj-api --region eu-central-1

# 2. Vytvoření prostředí (jednou)
eb create zpravodaj-test \
  --instance-type t3.medium \
  --envvars "MAX_CONTENT_LENGTH=52428800" \
  --timeout 10

# 3. Deploy nové verze (při každé změně)
eb deploy

# 4. Otevřít v prohlížeči
eb open

# 5. Sledovat logy
eb logs --stream

# 6. UKLIDIT po testu
eb terminate zpravodaj-test
```

### Co se děje při deploy

1. EB zkomprimuje kód (použije `.ebignore`)
2. Nahraje na S3
3. Vytvoří EC2 instanci s Python 3.11
4. Nainstaluje `requirements.txt`
5. Spustí `wsgi.py` s gunicorn
6. Vytvoří load balancer

**Konfigurace**:
- Instance: t3.medium (2 vCPU, 4GB RAM - potřebné pro PyMuPDF)
- Timeout: 600s (10 minut)
- Max upload: 50MB
- Auto-scaling: 1-4 instance

**Cena**: ~$50/měsíc (24/7) nebo ~$0.50 pro 2h test

---

## VARIANTA 2: AWS Lambda (💰 NEJLEVNĚJŠÍ)

### Proč Lambda?
- ✅ **Pay-per-use** - platíš jen za konverze ($0.20/1000)
- ✅ **Auto-scaling** - zvládne tisíce requestů
- ✅ **15 min timeout** - stačí i na velké PDF
- ⚠️ **6 MB upload limit** - musíš použít S3 presigned upload

### Problémy s Lambda
Lambda má **hard 6 MB synchronní limit** → musíš předělat API workflow:

**SOUČASNÝ WORKFLOW (Railway/EB):**
```
User → Upload PDF (POST) → API → Vrátí ZIP
```

**LAMBDA WORKFLOW (povinný):**
```
User → Request presigned URL (GET) → Upload PDF do S3 →
Trigger Lambda → Lambda stáhne z S3 → Konverze → Upload ZIP do S3 → Vrátí URL
```

### Co musíš změnit v kódu

**1. Nový handler pro Lambda:**

```python
# api/lambda_handler.py (NOVÝ SOUBOR)
import json
import boto3
from lib.pdf_converter import PDFToFlipbook

def handler(event, context):
    # Parse request
    body = json.loads(event['body'])
    s3_key = body['s3_key']  # PDF už je v S3

    # Stáhnout PDF z S3
    s3 = boto3.client('s3')
    pdf_bytes = s3.get_object(Bucket='zpravodaj-pdfs', Key=s3_key)['Body'].read()

    # Konverze (tento kód už máš)
    converter = PDFToFlipbook(pdf_bytes)
    zip_bytes = converter.convert()

    # Upload ZIP do S3
    zip_key = f"flipbooks/{s3_key.replace('.pdf', '.zip')}"
    s3.put_object(Bucket='zpravodaj-flipbooks', Key=zip_key, Body=zip_bytes)

    # Vygeneruj presigned URL (platnost 7 dní)
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': 'zpravodaj-flipbooks', 'Key': zip_key},
        ExpiresIn=604800
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'download_url': url})
    }
```

**2. Upravit frontend (`public/index.html`):**

```javascript
// Nový upload workflow
async function uploadPDF(file) {
  // 1. Získat presigned URL
  const presignedResponse = await fetch('/api/get-upload-url', {
    method: 'POST',
    body: JSON.stringify({ filename: file.name })
  });
  const { uploadUrl, s3Key } = await presignedResponse.json();

  // 2. Upload PDF přímo do S3
  await fetch(uploadUrl, {
    method: 'PUT',
    body: file,
    headers: { 'Content-Type': 'application/pdf' }
  });

  // 3. Trigger konverze
  const convertResponse = await fetch('/api/convert', {
    method: 'POST',
    body: JSON.stringify({ s3_key: s3Key })
  });
  const { download_url } = await convertResponse.json();

  // 4. Stáhnout ZIP
  window.location.href = download_url;
}
```

### Deployment Lambda

**1. Dockerfile s PyMuPDF:**

```dockerfile
# Dockerfile.lambda (NOVÝ SOUBOR)
FROM public.ecr.aws/lambda/python:3.11

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy code
COPY lib/ ${LAMBDA_TASK_ROOT}/lib/
COPY api/lambda_handler.py ${LAMBDA_TASK_ROOT}/

CMD ["lambda_handler.handler"]
```

**2. Build & deploy:**

```bash
# Login do ECR
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin \
  <ACCOUNT-ID>.dkr.ecr.eu-central-1.amazonaws.com

# Build & push
docker build -f Dockerfile.lambda -t zpravodaj-lambda .
docker tag zpravodaj-lambda:latest <ACCOUNT-ID>.dkr.ecr.eu-central-1.amazonaws.com/zpravodaj-lambda:latest
docker push <ACCOUNT-ID>.dkr.ecr.eu-central-1.amazonaws.com/zpravodaj-lambda:latest

# Deploy Lambda
aws lambda create-function \
  --function-name zpravodaj-converter \
  --package-type Image \
  --code ImageUri=<ACCOUNT-ID>.dkr.ecr.eu-central-1.amazonaws.com/zpravodaj-lambda:latest \
  --role arn:aws:iam::<ACCOUNT-ID>:role/lambda-execution-role \
  --timeout 900 \
  --memory-size 3008
```

**Cena**: ~$0.20 za 1000 konverzí

---

## VARIANTA 3: ECS Fargate (🚀 PRODUKČNÍ)

### Proč ECS Fargate?
- ✅ **Žádné změny kódu** - tvůj Flask funguje
- ✅ **Docker based** - podobné Railway
- ✅ **Auto-scaling** - jako EB, ale víc kontroly
- 💰 **Cena**: ~$35/měsíc (levnější než EB)

### Deployment ECS Fargate

**1. Vytvoř Dockerfile:**

```dockerfile
# Dockerfile (NOVÝ SOUBOR)
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Expose port
EXPOSE 8080

# Run with gunicorn (stejné jako Railway)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8080", "wsgi:app", "--timeout", "300"]
```

**2. Build & push do ECR:**

```bash
# Vytvoř ECR repository
aws ecr create-repository --repository-name zpravodaj-api --region eu-central-1

# Login
aws ecr get-login-password --region eu-central-1 | \
  docker login --username AWS --password-stdin \
  <ACCOUNT-ID>.dkr.ecr.eu-central-1.amazonaws.com

# Build & push
docker build -t zpravodaj-api .
docker tag zpravodaj-api:latest <ACCOUNT-ID>.dkr.ecr.eu-central-1.amazonaws.com/zpravodaj-api:latest
docker push <ACCOUNT-ID>.dkr.ecr.eu-central-1.amazonaws.com/zpravodaj-api:latest
```

**3. Deploy ECS:**

```bash
# Vytvoř cluster
aws ecs create-cluster --cluster-name zpravodaj-cluster

# Vytvoř task definition (viz task-definition.json níže)
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Vytvoř service s load balancerem
aws ecs create-service \
  --cluster zpravodaj-cluster \
  --service-name zpravodaj-api \
  --task-definition zpravodaj-api \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

**task-definition.json:**

```json
{
  "family": "zpravodaj-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "zpravodaj-api",
      "image": "<ACCOUNT-ID>.dkr.ecr.eu-central-1.amazonaws.com/zpravodaj-api:latest",
      "portMappings": [{"containerPort": 8080, "protocol": "tcp"}],
      "environment": [
        {"name": "MAX_CONTENT_LENGTH", "value": "52428800"}
      ]
    }
  ]
}
```

**Cena**: ~$35/měsíc (1 vCPU, 2GB RAM, 24/7)

---

## SROVNÁNÍ VŠECH VARIANT

| Řešení | Cena (měsíc) | Složitost | Upload limit | Změny kódu |
|--------|--------------|-----------|--------------|------------|
| **Elastic Beanstalk** | $50 | ⭐ Snadné | Žádný | **0 změn** |
| **Lambda** | $0.20/1000 | ⭐⭐⭐ Složité | 6 MB → S3 | Přepsat API |
| **ECS Fargate** | $35 | ⭐⭐ Střední | Žádný | Jen Dockerfile |
| **Railway (teď)** | $5-20 | ⭐ Snadné | Žádný | 0 změn |

---

## CO SE ZEPTAT NA IT MEETINGU

### 1. Budget
- **Kolik můžeme dát měsíčně?** ($5 Railway vs. $35-50 AWS)
- **Platíme teď nebo test zdarma?** (AWS Free Tier)

### 2. Traffic odhad
- **Kolik konverzí denně?**
  - Málo (< 10/den) → Lambda ($0.20/měsíc)
  - Hodně (> 100/den) → EB/ECS ($35-50/měsíc)

### 3. AWS setup
- **Už máte AWS účet?** Jaký region? (doporučuji eu-central-1 = Frankfurt)
- **Kdo bude mít admin přístup?**

### 4. Storage strategie
- **Chcete ukládat flipbooky do S3?** (trvalé storage)
- **Nebo jen ZIP download?** (jako teď)

### 5. Deployment workflow
- **GitHub Actions → AWS?** (automatický deploy při push)
- **Ruční deploy?** (`eb deploy` nebo `docker push`)

### 6. Monitoring
- **CloudWatch logs stačí?**
- **Potřebujeme custom metriky?** (počet konverzí, velikost PDF, ...)

---

## DOPORUČENÍ PRO TEST TENTO TÝDEN

### Nejrychlejší: Elastic Beanstalk (30 minut setup)

```bash
# 1. Install AWS EB CLI
pip install awsebcli

# 2. Konfigurovat AWS credentials
aws configure
# (Access Key z AWS Console → IAM)

# 3. Deploy!
eb init -p python-3.11 zpravodaj-api --region eu-central-1
eb create zpravodaj-test --instance-type t3.medium

# 4. Test
eb open  # Otevře URL
curl -X POST https://zpravodaj-test.eu-central-1.elasticbeanstalk.com/api/convert \
  -F "pdf=@test.pdf" \
  -F "title=Test" \
  -o output.zip

# 5. Uklidit
eb terminate zpravodaj-test
```

**Cena testu**: ~$0.50 (2 hodiny běhu)

---

## DLOUHODOBĚ: Co použít?

### Pro produkci (příští měsíc):
**→ ECS Fargate** ($35/měsíc)
- Lepší kontrola než EB
- CI/CD s GitHub Actions
- Docker-based (jako Railway)

### Pro pay-per-use (nízký traffic):
**→ Lambda** ($0.20/1000 konverzí)
- Musíš předělat na S3 workflow
- Složitější, ale nejlevnější

### Pro rychlý start (tento týden):
**→ Elastic Beanstalk** ($50/měsíc)
- Zero změn kódu
- Funguje hned

---

## SOUBORY CO JSI UŽ VYTVOŘIL

- `.ebextensions/01_gunicorn.config` - EB konfigurace (timeout, WSGI)
- `.ebignore` - Co neposílat do AWS (jako .gitignore)

**Co ještě chybí:**
- `Dockerfile` (pro ECS Fargate variantu)
- `Dockerfile.lambda` (pro Lambda variantu)
- `api/lambda_handler.py` (pro Lambda variantu)
- `task-definition.json` (pro ECS Fargate variantu)
