# Vercel Limity

## ⚠️ Problém: Request Size Limit

Vercel má **hard limit 4.5 MB** pro HTTP request body (včetně Pro plánu).

Tvůj PDF má **10.4 MB** → nelze nahrát přes web UI.

## 🔧 Řešení

### Varianta 1: Zmenši PDF (RYCHLÉ)
```bash
# macOS
brew install ghostscript
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=output.pdf input.pdf

# Online nástroj
https://www.ilovepdf.com/compress_pdf
```

### Varianta 2: Použij jiný hosting (DOPORUČUJI)

**Cloudflare Workers** má limit **100 MB**:

1. Deploy na Cloudflare místo Vercel
2. Stejný Python kód funguje
3. Free tier: 100,000 requests/den

```bash
# Přesuň projekt na Cloudflare
npm install -g wrangler
wrangler login
wrangler init zpravodaj-api
# ... zkopíruj kód
wrangler deploy
```

### Varianta 3: Self-hosted (FULL CONTROL)

Deploy na vlastní server:
- Railway.app (doporučuji)
- Render.com
- DigitalOcean App Platform
- AWS EC2 / Lambda (container)

Railway má **neomezený** upload:
```bash
# Install Railway CLI
npm i -g @railway/cli
railway login
railway init
railway up
```

### Varianta 4: Chunked Upload (KOMPLEXNÍ)

Implementovat multi-part upload:
- Frontend rozdělí PDF na kousky po 4 MB
- Backend je složí dohromady
- Složitější, ale funguje na Vercelu

## 💡 Doporučení

Pro produkci:
1. **Railway.app** - $5/měsíc, unlimited upload, jednoduchý deploy
2. **Cloudflare Workers** - free, 100 MB limit, nejrychlejší

Pro test s malými PDF (< 4 MB):
- Současný Vercel deployment funguje perfektně

## 🚀 Rychlý fix

Pokud nemůžeš změnit hosting, **zkomprimuj PDF**:
- Cílová velikost: **< 4 MB**
- Online nástroj: https://www.ilovepdf.com/compress_pdf
- Kvalita zůstane dobrá pro flipbook
