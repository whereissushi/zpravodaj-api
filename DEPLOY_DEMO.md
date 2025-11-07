# 🚀 JAK ZVEŘEJNIT DEMO FLIPBOOK

## NEJRYCHLEJŠÍ MOŽNOST - Netlify Drop (2 minuty, ZDARMA)

### Krok 1: Připravte složku
Máte připravenou složku: `C:\Users\Daniel\Downloads\Beroun - Říjen 2025-flipbook`

### Krok 2: Nahrajte na Netlify
1. Otevřete prohlížeč a jděte na: **https://app.netlify.com/drop**
2. Přetáhněte celou složku `Beroun - Říjen 2025-flipbook` přímo na stránku
3. Počkejte 10 sekund na upload
4. Dostanete okamžitě URL typu: `https://amazing-site-123.netlify.app`

### Krok 3: Sdílejte URL
Hotovo! Máte funkční demo, které můžete sdílet. URL bude fungovat 24 hodin (nebo se můžete zdarma registrovat pro trvalé hostování).

---

## ALTERNATIVA 1 - Surge.sh (3 minuty, ZDARMA)

```bash
# Instalace (jednou)
npm install -g surge

# Deploy
cd "C:\Users\Daniel\Downloads\Beroun - Říjen 2025-flipbook"
surge

# Vyberte název domény např: beroun-zpravodaj.surge.sh
```

---

## ALTERNATIVA 2 - GitHub Pages (5 minut, TRVALÉ)

### Pro vaše repo zpravodaj-api:

1. **Vytvořte větev gh-pages:**
```bash
cd /mnt/c/Users/Daniel/Zpravodaj
git checkout -b gh-pages
cp -r "/mnt/c/Users/Daniel/Downloads/Beroun - Říjen 2025-flipbook"/* .
git add .
git commit -m "Deploy demo flipbook"
git push origin gh-pages
```

2. **Aktivujte GitHub Pages:**
   - Jděte na: https://github.com/whereissushi/zpravodaj-api/settings/pages
   - Source: Deploy from a branch
   - Branch: gh-pages
   - Folder: / (root)
   - Save

3. **Vaše demo bude na:**
   https://whereissushi.github.io/zpravodaj-api/

---

## ALTERNATIVA 3 - Vercel (3 minuty, PROFESIONÁLNÍ)

1. Zaregistrujte se na https://vercel.com (GitHub login)
2. Klikněte "Add New" → "Project"
3. Import from Git → vyberte zpravodaj-api
4. Deploy

---

## CO FUNGUJE V DEMO:

✅ **Listování** - táhněte rohy stránek nebo klikněte na šipky
✅ **Fulltextové vyhledávání** - ikonka lupy, hledá v OCR textu
✅ **Zoom** - klikněte na stránku pro přiblížení
✅ **Menu/Obsah** - automaticky generované z nadpisů
✅ **AI Shrnutí** - rychlý přehled obsahu
✅ **Sdílení** - QR kód a kopírování URL
✅ **Náhledy** - miniatury stránek vlevo
✅ **Stažení PDF** - původní PDF ke stažení
✅ **Mobilní zobrazení** - responzivní design

## POZNÁMKY:

- Demo funguje kompletně offline (všechny JS knihovny jsou lokální)
- OCR text je embedded přímo v HTML pro rychlé vyhledávání
- Zoom menu je pod toolbarem (Munipolis styl)
- Při zoomu je vypnuté listování (musíte odscrollovat nebo kliknout pro reset)

---

**TIP:** Netlify Drop je nejrychlejší - stačí přetáhnout složku na web a máte URL!