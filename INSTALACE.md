# Zpravodaj Converter - Návod k instalaci

## 📋 Požadavky

### Windows
- Python 3.8 nebo novější ([stáhnout zde](https://www.python.org/downloads/))
- Poppler (pro konverzi PDF)

## 🚀 Instalace

### Krok 1: Instalace Pythonu
1. Stáhněte Python z https://www.python.org/downloads/
2. Při instalaci **zaškrtněte** "Add Python to PATH"
3. Dokončete instalaci

### Krok 2: Instalace Poppler (nutné pro PDF konverzi)

#### Windows:
1. Stáhněte Poppler pro Windows: https://github.com/oschwartz10612/poppler-windows/releases/
2. Stáhněte `Release-XX.XX.X-X.zip` (nejnovější verzi)
3. Rozbalte do `C:\Program Files\poppler`
4. Přidejte do PATH:
   - Otevřete "Upravit systémové proměnné prostředí"
   - Klikněte na "Proměnné prostředí"
   - V "Systémové proměnné" najděte `Path` a klikněte "Upravit"
   - Přidejte: `C:\Program Files\poppler\Library\bin`
   - Klikněte OK

### Krok 3: Instalace Python knihoven
Otevřete příkazový řádek (cmd) ve složce projektu a spusťte:

```bash
pip install -r requirements.txt
```

## 💻 Použití

### Varianta A: Grafické rozhraní (doporučeno)
Jednoduše dvojklikem spusťte:
```bash
python zpravodaj_gui.py
```

1. Klikněte na "Procházet..." u PDF souboru
2. Vyberte kam se má výstup uložit
3. Zadejte název zpravodaje
4. Klikněte "KONVERTOVAT"
5. Hotovo!

### Varianta B: Příkazová řádka
```bash
python pdf_to_flipbook.py "cesta/k/pdf.pdf" "vystupni-slozka" "Název zpravodaje"
```

Příklad:
```bash
python pdf_to_flipbook.py "Zpravodaje/FM Zari 2025 zdroj.pdf" "FM-zari-2025" "Frýdek-Místek 09/2025"
```

## 📦 Vytvoření .exe souboru (pro distribuci kolegům)

Pokud chcete vytvořit samostatný .exe soubor, který nemusí mít Python nainstalovaný:

### 1. Instalace PyInstaller
```bash
pip install pyinstaller
```

### 2. Vytvoření .exe
```bash
pyinstaller --onefile --windowed --name="ZpravodajConverter" --icon=icon.ico zpravodaj_gui.py
```

Pokud nemáte ikonu, vynechte `--icon=icon.ico`:
```bash
pyinstaller --onefile --windowed --name="ZpravodajConverter" zpravodaj_gui.py
```

### 3. Výsledek
- Najdete v `dist/ZpravodajConverter.exe`
- Tento soubor můžete rozdistribuovat kolegům
- **POZOR:** Stále potřebují mít nainstalovaný Poppler!

## 🔧 Řešení problémů

### Chyba: "pdf2image.exceptions.PDFInfoNotInstalledError"
- Poppler není správně nainstalován nebo není v PATH
- Zkontrolujte instalaci Poppler (Krok 2)
- Restartujte počítač po přidání do PATH

### Chyba: "No module named 'pdf2image'"
- Spusťte: `pip install -r requirements.txt`

### GUI se nespouští
- Zkontrolujte že máte Python 3.8+
- Tkinter by měl být součástí Pythonu, pokud ne:
  ```bash
  pip install tk
  ```

## 📄 Výstup

Konverze vytvoří složku s touto strukturou:
```
vystup-slozka/
├── index.html          (hlavní soubor - tento otevřete v prohlížeči)
├── css/
│   └── style.css
├── js/
│   └── flipbook.js
└── files/
    ├── pages/          (velké obrázky stránek)
    │   ├── 1.jpg
    │   ├── 2.jpg
    │   └── ...
    └── thumb/          (náhledy)
        ├── 1.jpg
        ├── 2.jpg
        └── ...
```

Celou složku nahrajte na váš webový server.

## 🎯 Funkce flipbooku

- ✅ Listování stránkami (šipky, tlačítka)
- ✅ Zoom (přiblížení/oddálení)
- ✅ Náhledy stránek
- ✅ Klávesové zkratky:
  - `←` / `→` - předchozí/další stránka
  - `+` / `-` - zoom
  - `0` - reset zoomu
  - `Home` / `End` - první/poslední stránka
- ✅ Mobilní responzivita
- ✅ Swipe gesta na mobilech

## 📞 Podpora

Při problémech kontaktujte IT oddělení nebo zkontrolujte dokumentaci výše.
