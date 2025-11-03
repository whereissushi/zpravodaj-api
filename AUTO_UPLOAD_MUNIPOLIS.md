# Automatické Nahrávání na Munipolis Server

## Možnosti jak dostat flipbook na zpravodaj.munipolis.cz

### Varianta A: Manuální Upload (Rychlé)

1. Stáhni ZIP z converteru
2. Rozbal lokálně
3. Nahraj přes FTP/FileZilla na server:
   ```
   zpravodaj.munipolis.cz/mesto-nazev/MM-RRRR/
   ```

**Pros:** Jednoduchý, funguje hned
**Cons:** Manuální práce

---

### Varianta B: Automatický Upload z Railway/Lambda

Upravíme backend aby po konverzi automaticky uploadoval na Munipolis server.

#### Co potřebujeme:

1. **SFTP/FTP credentials** pro zpravodaj.munipolis.cz
2. **Cestu** kam ukládat (např. `/var/www/zpravodaj.munipolis.cz/`)
3. **Pravidlo pro složky** (např. `mesto-{slug}/MM-RRRR/`)

#### Implementace:

```python
# app.py - po konverzi uploaduj na server
import paramiko  # SFTP knihovna

def upload_to_munipolis(flipbook_files, mesto_slug, mesic_rok):
    """
    Upload flipbook na Munipolis server

    Args:
        flipbook_files: dict s HTML, CSS, JS, images
        mesto_slug: např. "frydekmistek"
        mesic_rok: např. "09-2025"
    """

    # SFTP connection
    transport = paramiko.Transport((MUNIPOLIS_HOST, 22))
    transport.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)

    # Create directory
    remote_path = f'/var/www/zpravodaj.munipolis.cz/{mesto_slug}/{mesic_rok}/'
    sftp.mkdir(remote_path)

    # Upload files
    sftp.put('index.html', f'{remote_path}/index.html')
    sftp.put('css/style.css', f'{remote_path}/css/style.css')
    # ... atd

    sftp.close()
    transport.close()

    return f'https://zpravodaj.munipolis.cz/{mesto_slug}/{mesic_rok}/'
```

---

### Varianta C: S3 Bucket + CloudFront CDN

Nejmodernější řešení - ukládání do AWS S3, distribuce přes CDN.

#### Výhody:
- ✅ Neomezená kapacita
- ✅ Rychlé načítání (CDN)
- ✅ Automatické zálohování
- ✅ Levné (~pár korun/měsíc)

#### Setup:

1. **Vytvoř S3 bucket**: `munipolis-zpravodaje`
2. **Nahraj flipbooky** do:
   ```
   s3://munipolis-zpravodaje/frydekmistek/09-2025/index.html
   ```
3. **CloudFront distribution** před S3
4. **Custom doména**: `zpravodaj.munipolis.cz` → CloudFront

**URL Result:**
```
https://zpravodaj.munipolis.cz/frydekmistek/09-2025/
```

---

### Varianta D: GitHub Pages (Zdarma!)

Pokud jsou flipbooky veřejné, můžete použít GitHub Pages:

1. Vytvoř repo: `munipolis/zpravodaje`
2. Nahraj flipbooky do složek
3. Zapni GitHub Pages
4. Custom doména: `zpravodaj.munipolis.cz`

**Pros:** Úplně zdarma, neomezené
**Cons:** Veřejné repository

---

## Doporučení

Pro Munipolis bych zvolil **Variantu C (S3 + CloudFront)**:

- Moderní, škálovatelné
- Levné (pár desítek Kč/měsíc)
- Rychlé (CDN)
- Automatizovatelné z Lambda

---

## Quick Start - Manuální Upload

**Potřebuješ od Mariána/IT:**

```
FTP Host: zpravodaj.munipolis.cz
Username: ???
Password: ???
Path: /var/www/zpravodaj.munipolis.cz/
```

**Pak:**
1. FileZilla → připoj se
2. Vytvoř složku `/frydekmistek/09-2025/`
3. Nahraj obsah ZIP
4. Otevři: `https://zpravodaj.munipolis.cz/frydekmistek/09-2025/`

---

**Ptej se Mariána co preferují!** 🙂
