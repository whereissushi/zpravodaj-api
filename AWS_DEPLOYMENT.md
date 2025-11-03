# AWS Lambda Deployment Guide

Tento návod popisuje deployment Zpravodaj Converteru na AWS Lambda.

## Proč AWS Lambda?

- ✅ **Žádná údržba serveru** - AWS se stará o vše
- ✅ **Platíte jen za použití** - když nikdo nekonvertuje, platíte €0
- ✅ **Automatické škálování** - zvládne více konverzí najednou
- ✅ **15 minut timeout** - stačí i na 100+ stránkové PDF
- 💰 **Levné** - první 1 milion requestů zdarma měsíčně

## Prerekvizity

1. **AWS účet** s přístupem k Lambda, API Gateway
2. **AWS CLI** nainstalované a nakonfigurované
3. **Python 3.11** nainstalovaný lokálně
4. **Credentials** - Access Key ID + Secret Access Key

## Instalace AWS CLI

```bash
# Windows (PowerShell)
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Konfigurace
aws configure
# Zadejte:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region: eu-central-1
# - Default output: json
```

## Deployment - Krok za Krokem

### 1. Vytvoření IAM Role pro Lambda

```bash
# Vytvoř IAM roli
aws iam create-role \
  --role-name lambda-zpravodaj-role \
  --assume-role-policy-document file://lambda-trust-policy.json

# Přidej základní Lambda permissions
aws iam attach-role-policy \
  --role-name lambda-zpravodaj-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

**Poznamenejte si ARN role**, vypadá takto:
```
arn:aws:iam::123456789012:role/lambda-zpravodaj-role
```

### 2. Vytvoření Lambda funkce (poprvé)

```bash
# Spusť deployment script
chmod +x deploy-lambda.sh
./deploy-lambda.sh

# NEBO manuálně:
aws lambda create-function \
  --function-name zpravodaj-converter \
  --runtime python3.11 \
  --role arn:aws:iam::VASE-ACCOUNT-ID:role/lambda-zpravodaj-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://lambda-deployment.zip \
  --timeout 600 \
  --memory-size 3008 \
  --region eu-central-1
```

### 3. Přidání Tesseract Layer

Tesseract OCR potřebuje nativní knihovny. Použijeme předkompilovaný Layer:

```bash
aws lambda update-function-configuration \
  --function-name zpravodaj-converter \
  --layers arn:aws:lambda:eu-central-1:770693421928:layer:Klayers-p311-tesseract:1 \
  --region eu-central-1
```

**Poznámka**: Layer obsahuje Tesseract + českou jazykovou podporu.

### 4. Vytvoření API Gateway

```bash
# Vytvoř REST API
aws apigatewayv2 create-api \
  --name zpravodaj-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:eu-central-1:ACCOUNT-ID:function:zpravodaj-converter

# Nebo použij AWS Console:
# 1. Jdi na API Gateway → Create API → HTTP API
# 2. Add Integration → Lambda → zpravodaj-converter
# 3. Configure Routes → POST /convert
# 4. Deploy
```

Získáte URL endpoint:
```
https://abc123xyz.execute-api.eu-central-1.amazonaws.com/convert
```

## Update kódu (při změnách)

```bash
# Prostě znovu spusť deployment script
./deploy-lambda.sh
```

## Testování

### Test z příkazové řádky

```bash
# Vytvoř test payload
echo '{"body":"base64-encoded-pdf-here","isBase64Encoded":true}' > test-payload.json

# Invoke Lambda
aws lambda invoke \
  --function-name zpravodaj-converter \
  --payload file://test-payload.json \
  --region eu-central-1 \
  output.json

# Zkontroluj output
cat output.json
```

### Test přes API Gateway

```bash
curl -X POST https://YOUR-API-URL/convert \
  -H "Content-Type: application/pdf" \
  --data-binary @zpravodaj.pdf \
  -o flipbook.zip
```

## Web Upload Formulář

Aktualizujte `public/index.html` - změňte API endpoint:

```javascript
const API_URL = 'https://YOUR-API-URL.execute-api.eu-central-1.amazonaws.com/convert';
```

## Monitoring & Logs

CloudWatch Logs:
```bash
# Sleduj logy v reálném čase
aws logs tail /aws/lambda/zpravodaj-converter --follow --region eu-central-1
```

Nebo v AWS Console:
```
CloudWatch → Log groups → /aws/lambda/zpravodaj-converter
```

## Náklady (odhad)

**FREE Tier** (první rok):
- 1 milion requestů zdarma/měsíc
- 400,000 GB-sekund compute time zdarma/měsíc

**Po FREE Tier** (při 100 konverzích/měsíc):
- Requests: 100 × $0.0000002 = $0.00002
- Compute: 100 × 5min × 3GB × $0.0000166667 = $0.25
- **Celkem: ~$0.25/měsíc** (7 Kč)

Srovnejte s Railway: **$5/měsíc** (140 Kč) i když nic neběží!

## Troubleshooting

### Lambda timeout
- Aktuální timeout: 600s (10 minut)
- Pokud potřebujete více, zvyšte v `deploy-lambda.sh`

### Out of memory
- Aktuální paměť: 3008 MB (maximum)
- OCR potřebuje hodně RAM

### Tesseract not found
- Zkontrolujte že máte přidaný Tesseract Layer
- Layer ARN musí odpovídat vaší region

### CORS errors
- API Gateway musí mít CORS povolený
- Zkontrolujte hlavičky v `lambda_handler.py`

## Bezpečnost

### Doporučené nastavení:

1. **API Key** v API Gateway (zamezí zneužití)
2. **Rate limiting** (max 10 requestů/minuta)
3. **Velikost PDF** - limit na 50 MB

## Další kroky (volitelné)

### S3 Storage pro flipbooky

Pokud chcete ukládat vygenerované flipbooky do S3:

1. Vytvořte S3 bucket
2. Přidejte S3 permissions do IAM role
3. Upravte `lambda_handler.py` - uploadujte ZIP do S3
4. Vraťte URL místo base64

### CloudFront CDN

Pro rychlejší distribuce flipbooků:
1. Vytvořte CloudFront distribution
2. Origin = váš S3 bucket
3. Flipbooky budou servírované z CDN

---

**Potřebujete pomoct?** Napište issue na GitHub nebo kontaktujte správce.
