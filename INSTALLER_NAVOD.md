# Jak vytvořit installer pro Zpravodaj Converter

## Krok 1: Nainstaluj Inno Setup

1. Stáhni **Inno Setup 6** z: https://jrsoftware.org/isdl.php
2. Nainstaluj (default nastavení je OK)
3. Restartuj není potřeba

## Krok 2: Připrav Poppler pro zabalení

Musíš mít Poppler v adresáři projektu (ne jen v `C:\poppler`):

```bash
# Zkopíruj celý Poppler do projektu
xcopy /E /I C:\poppler poppler
```

Výsledná struktura:
```
Zpravodaj/
├── dist/
│   └── ZpravodajConverter.exe
├── poppler/                    ← DŮLEŽITÉ!
│   └── Library/
│       └── bin/
│           └── pdftoppm.exe
├── installer.iss
└── CREATE_INSTALLER.bat
```

## Krok 3: Vytvoř installer

```bash
CREATE_INSTALLER.bat
```

Skript:
1. ✓ Zkontroluje Inno Setup
2. ✓ Zkontroluje EXE (případně ho buildne)
3. ✓ Zkontroluje Poppler
4. ✓ Vytvoří installer

## Výsledek

**installer_output/ZpravodajConverter_Setup.exe**

Tento soubor obsahuje:
- ✅ ZpravodajConverter.exe
- ✅ Poppler binárky
- ✅ Automatické přidání do PATH
- ✅ Desktop ikonu (volitelně)
- ✅ Start menu zástupce

## Použití pro koncové uživatele

1. Stáhnou `ZpravodajConverter_Setup.exe`
2. Spustí jako **Administrátor**
3. Kliknou "Next, Next, Install"
4. **HOTOVO** - aplikace funguje okamžitě

Žádná manuální instalace Poppleru, žádné PATH konfigurace!

## Velikost installeru

- EXE: ~50 MB
- Poppler: ~40 MB
- **Celkem: ~90 MB** (jeden soubor)

## Poznámky

- Installer vyžaduje **admin práva** (kvůli PATH a instalaci do Program Files)
- Automaticky přidá Poppler do systémového PATH
- Po instalaci možná bude potřeba restart (ale obvykle ne)
