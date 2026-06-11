# MaxiMots — Project Brief
## Maximo MAS 9 Translation Manager by maxTeam

---

## 1. App Identity

- **Name:** MaxiMots ("Maxi" from Maximo + "Mots" = words in French)
- **Subtitle:** Translation Studio
- **Byline:** by maxTeam
- **Naming convention:** follows maxTeam product family (maxForge, maxTeamplate, MaxiMots)
- **UI language:** French (same as MXFORGE)

---

## 2. Purpose

MaxiMots is a web app that manages translations for IBM Maximo MAS 9 objects. It:

1. **Identifies** which translations Maximo handles natively (via L_ tables) vs. which it cannot
2. **Proposes** system translations for native fields and auto-translates the rest
3. **Lets users choose** exactly what to translate, which fields, which languages, and how
4. **Exports** MXLoader-compatible Excel files with attractive formatting, ready to re-import

### The problem it solves
Maximo MAS 9 natively translates only certain fields (DESCRIPTION, LONGDESCRIPTION, domain values) via L_ tables. Everything else (custom attributes, classifications, meter descriptions, spec values, task labels, etc.) requires manual work via MXLoader or XLIFF. MaxiMots bridges this gap.

---

## 3. Architecture Decisions

### Data Source: API-first with SQL fallback
- **Primary:** REST/OSLC API — officially supported by MAS 9, handles auth, works cloud + on-prem
- **Fallback:** SQL queries — faster for bulk reads, requires direct DB access
- **Demo mode:** Embedded metadata (same as MXFORGE) for offline/prototype use
- The app should support all three sources, configurable via a settings modal

### App Type: Python + FastAPI backend with rich HTML frontend
- **Backend:** FastAPI (Python) — handles file upload/download, translation API calls, session management
- **Frontend:** Single-file HTML/CSS/JS — interactive, generates Excel client-side via ExcelJS
- **Translation engine:** Google Translate via `deep-translator` library (free, no API key) with manual override option
- **Excel generation:** ExcelJS (CDN) for client-side styled .xlsx output

### Module Structure
The app is organized by Maximo modules, NOT flat lists:
- **Gestion des actifs** (Assets): MXASSET, MXOPERLOC
- **Gestion du travail** (Work): MXWO, MXSR
- **Inventaire & articles** (Inventory): MXINVENTORY, MXITEM
- **Achats** (Purchasing): MXPO, MXPR
- **Personnes & organisation** (People): MXPERSON, MXLABOR, MXVENDOR

---

## 4. Design System — MUST match MXFORGE exactly

### CSS Theme Variables
```css
:root {
  --navy:#1C477A; --navy-d:#122E4F; --navy-d2:#0D2037;
  --tint:#E4E9EF; --tint2:#F1F4F7; --mid:#829AB6;
  --paper:#FFFFFF;
  --bg:#F1F4F7; --bg2:#FFFFFF;
  --panel:#FFFFFF; --panel2:#F7F9FC;
  --line:#CDD7E2; --line2:#B7C5D6;
  --ink:#0D2037; --mut:#5B7392; --mut2:#829AB6;
  --brand:#1C477A; --brand-l:#2E6BB0; --brand-d:#122E4F;
  --brand-glow:rgba(28,71,122,.18);
  --amber:#E0A030; --amber-d:#C4861B;
  --teal:#2E6BB0; --blue:#1C477A; --violet:#7C4DBC;
  --green:#1F9D5F; --red:#D14343;
  --shadow:0 10px 30px rgba(13,32,55,.10);
  --shadow-sm:0 4px 14px rgba(13,32,55,.08);
  --mono:'IBM Plex Mono',ui-monospace,Menlo,Consolas,monospace;
  --sans:'Inter','IBM Plex Sans',system-ui,-apple-system,sans-serif;
}
```

### Fonts
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

### Background
Dotted grid pattern: `background-image:radial-gradient(var(--line) 1px,transparent 1px); background-size:26px 26px;`

### Top Bar
- Navy gradient: `linear-gradient(135deg, var(--navy), var(--navy-d))`
- Height: 68px, sticky top
- Amber radial glow in top-right corner (decorative)
- Logo: white box 46x46px, border-radius 10px, contains maxTeam logo
- Title: `Maxi` in white + `Mots` in amber (`var(--amber)`)
- Subtitle: `TRANSLATION STUDIO` — mono font, 9.5px, uppercase, letter-spacing .22em, rgba(255,255,255,.7)
- Byline: `by maxTeam` — mono font, 8.5px, amber color, uppercase

### Layout
3-column grid: `grid-template-columns: 262px minmax(360px,1fr) 400px; gap:18px; padding:18px;`

### Component Styles (copy from MXFORGE)
- **Buttons:** `.btn` with border, shadow, hover lift; `.btn.primary` with amber gradient
- **Cards/Panels:** `.col` with border-radius 14px, white bg, shadow
- **Column headers:** `.col-head` with gradient bg, mono label + large title
- **Search inputs:** Rounded, icon left, focus glow
- **Badges:** Mono font, colored bg (TEXT=blue, INT=violet, DEC=green, DATE=amber, BOOL=navy, DOM=red)
- **Toggles:** Switch style with `.sw` slider
- **Toasts:** Fixed bottom center, navy bg, slide-up animation
- **Modals:** Backdrop blur, white card, rounded 16px, header with gradient

### maxTeam Logo (base64)
The logo is embedded as base64 in the MXFORGE HTML file. Extract the `<img src="data:image/png;base64,...">` from inside the `.logo` div in the top bar. It's the cloud icon with antenna/tower. Use this exact same image.

---

## 5. UI Layout — Three Columns

### Column 1: "Modules & Objets" (Étape 01 — Sélection)
- Header: `01 — Sélection` / `Modules & Objets`
- Search bar: "Rechercher un module ou objet..."
- Grouped list by module category (5 groups)
- Each object structure shows: name (mono bold), title, object name, field count
- Click to select → loads fields in column 2
- Active state: navy gradient background, white text (same as MXFORGE `.os.active`)

### Column 2: "Champs traduisibles" (Étape 02 — Traduction)
- Header: `02 — Traduction` / `[OBJECT_NAME] · [Title]`
- **Language selector at top:** Row of language chips with flag emojis — user checks which target languages they want (FR, DE, ES, AR, ZH, JA, PT, IT, NL, KO, TR)
- **Source language:** EN (shown as label, not selectable)
- **Field list with translation status:**
  - Each field card shows:
    - Checkbox (to include in export)
    - Field name (mono font) + description
    - Type badge
    - Source text (English value)
    - Translation status per selected target language:
      - 🟢 **"Maximo natif"** (green badge) — Maximo handles via L_ tables (DESCRIPTION, LONGDESCRIPTION, domain descriptions)
      - 🟠 **"Traduction requise"** (amber badge) — Maximo can't translate, needs MXLoader
      - 🟣 **"Personnalisé"** (violet badge) — user provides manual translation
  - Click a field to expand inline editor for manual translation input per language
- **Action buttons:** "Tout sélectionner", "Tout désélectionner", "Auto-traduire les manquants"
- **Filter toggles:** Show native only / Show missing only / Show all

### Column 3: "Aperçu & Export" (Étape 03 — Export)
- Header: `03 — Export` / `Aperçu & Génération`
- **Stats bar** (same card style as MXFORGE):
  - Champs (total selected fields)
  - Langues (target language count)
  - Natif (native translation count) — green
  - Custom (non-native count) — amber
- **Per-language progress bars:** Each target language shows completion % with colored bar
- **Preview table:** Mini table showing how the Excel will look (color-coded cells)
- **Toggle options:**
  - "Auto-traduire les manquants" (on/off)
  - "Inclure traductions natives" (include Maximo-native ones in export)
  - "Excel stylisé" (styled output vs plain)
- **Generate button:** Amber gradient, full width: "Générer l'Excel MaxiMots"
- **Reset button:** Ghost style: "Réinitialiser"

---

## 6. Translation Logic

### Natively translatable by Maximo (L_ tables)
These fields exist in Maximo's L_ translation tables and are handled by the system:
- `DESCRIPTION` on any object
- `LONGDESCRIPTION` on any object
- Domain value `DESCRIPTION` fields (ALNDOMAIN, SYNONYMDOMAIN, NUMERICDOMAIN)
- `TITLE` on MAXATTRIBUTE

Mark these with green "Maximo natif" badge.

### NOT natively translatable (need MXLoader / MaxiMots)
- Custom attribute labels
- Classification descriptions (CLASSIFICATIONID tree)
- Meter descriptions
- ASSETSPEC / WORKORDERSPEC text values
- Task descriptions in job plans
- Any custom ALN field without L_ table counterpart
- Status descriptions (MAXVALUE descriptions in custom domains)
- Report labels, menu items
- Communication template text

Mark these with amber "Traduction requise" badge.

### Translation methods available to user
1. **Auto-translate:** App calls Google Translate API via `deep-translator` and fills in suggestions. Marked with violet badge "Auto". User can accept or edit.
2. **Manual input:** User clicks the field and types translation directly in the UI.
3. **Skip:** Leave blank — will appear as empty in Excel for later filling.

---

## 7. Supported Languages

```javascript
const LANGUAGES = {
  EN: { name: 'English',    flag: '🇬🇧', code: 'en' },
  FR: { name: 'Français',   flag: '🇫🇷', code: 'fr' },
  DE: { name: 'Deutsch',    flag: '🇩🇪', code: 'de' },
  ES: { name: 'Español',    flag: '🇪🇸', code: 'es' },
  AR: { name: 'العربية',    flag: '🇸🇦', code: 'ar' },
  ZH: { name: '中文',       flag: '🇨🇳', code: 'zh-CN' },
  JA: { name: '日本語',     flag: '🇯🇵', code: 'ja' },
  PT: { name: 'Português',  flag: '🇵🇹', code: 'pt' },
  IT: { name: 'Italiano',   flag: '🇮🇹', code: 'it' },
  NL: { name: 'Nederlands', flag: '🇳🇱', code: 'nl' },
  KO: { name: '한국어',     flag: '🇰🇷', code: 'ko' },
  TR: { name: 'Türkçe',     flag: '🇹🇷', code: 'tr' },
};
```

Source language is always EN. Multiple target languages can be selected simultaneously.

---

## 8. Excel Output Specification

### Library
ExcelJS from CDN: `<script src="https://cdnjs.cloudflare.com/ajax/libs/exceljs/4.4.0/exceljs.min.js"></script>`

### Filename format
`MaxiMots_[OBJECT]_[LANGS]_[YYYY-MM-DD].xlsx`
Example: `MaxiMots_MXASSET_FR-DE-ES_2026-06-10.xlsx`

### Sheet 1: "Traductions" (main data)
| Column | Content |
|--------|---------|
| A | OBJECTNAME |
| B | ATTRIBUTENAME (mono) |
| C | TYPE |
| D | EN (Source) — light blue bg (#E3EDF8) |
| E+ | One column per target language (FR, DE, ES...) |
| Last | STATUS (Natif / Requis / Auto / Manuel) |

**Styling:**
- **Header row:** Navy bg (#1C477A), white bold text, frozen (row 1)
- **Row 1 height:** 28px
- **Alternating rows:** White / #F7F9FC
- **Green cells (#DBF1E5):** Native Maximo translations (pre-filled)
- **Amber cells (#FBEDD3):** Empty, needs translation (user fills in)
- **Violet cells (#EDE6F8):** Auto-translated suggestions
- **Borders:** Thin #CDD7E2 on all cells
- **Font:** Calibri 11, attribute names in Consolas 10
- **Column widths:** A=18, B=22, C=10, D+=30, Status=14
- **Auto-filter** on header row

### Sheet 2: "Instructions"
Formatted guide explaining:
- How to fill in amber cells with translations
- How to import back into Maximo via MXLoader
- Color legend
- Field type reference
- Contact: maxTeam

### Sheet 3 (optional): "Domaines"
If the object has domain fields, list all domain values with their current descriptions for reference.

---

## 9. Maximo Object Data Model

Use the EXACT same data from MXFORGE, which includes these objects with full attribute definitions:

- **MXASSET** — Assets (19 attrs + 2 relations: ASSETSPEC, ASSETMETER)
- **MXOPERLOC** — Locations (9 attrs)
- **MXWO** — Work Orders (17 attrs + 2 relations: WPLABOR, WPMATERIAL)
- **MXSR** — Service Requests (11 attrs)
- **MXINVENTORY** — Inventory (13 attrs + 1 relation: INVBALANCES)
- **MXITEM** — Items catalog (9 attrs)
- **MXPO** — Purchase Orders (11 attrs + 1 relation: POLINE)
- **MXPR** — Purchase Requisitions (8 attrs + 1 relation: PRLINE)
- **MXPERSON** — Persons (11 attrs)
- **MXLABOR** — Labor (7 attrs)
- **MXVENDOR** — Companies/Vendors (8 attrs)

Each attribute has: name, title, type, length, required, domain, sample value, technical flag.

Domains included: ASSETSTATUS, LOCASSETSTATUS, WOSTATUS, SRSTATUS, POSTATUS, PRSTATUS, ITEMSTATUS, PERSONSTATUS, YORN, WORKTYPE, ABCTYPE, COMPANYTYPE, ASSETTYPE, UNITOFMEASURE, COMMODITYGROUP, ORDERTYPE, PRIORITYDOM.

**COPY THE FULL DATA MODEL FROM THE MXFORGE HTML FILE** — it's all in the `<script>` section under `DOMAINS`, `GROUPS`, and `OS` objects (lines 730–957 of the MXFORGE source).

---

## 10. Backend (Python + FastAPI)

### Files
- `app.py` — FastAPI routes
- `mxloader_parser.py` — Parse/export MXLoader Excel sheets
- `translator.py` — Translation engine (Google Translate wrapper)
- `templates/index.html` — The full MaxiMots frontend (single HTML file)
- `requirements.txt` — Dependencies

### Requirements
```
fastapi==0.115.0
uvicorn==0.30.6
python-multipart==0.0.9
openpyxl==3.1.5
deep-translator==1.11.4
```

### API Endpoints
```
GET  /                          → Serve frontend HTML
POST /upload                    → Upload MXLoader Excel, parse, return session
GET  /session/{id}/rows         → Get translation rows (filterable)
POST /session/{id}/auto-translate → Auto-translate missing via Google
POST /session/{id}/manual-update  → Manually set a translation
POST /session/{id}/export       → Export to styled MXLoader Excel
GET  /supported-languages       → List supported language codes
```

### MXLoader Parser Features
- Auto-detects language columns: `EN`, `FR`, `DESCRIPTION_EN`, `DESCRIPTION_FR`, `LDTEXT_EN`, etc.
- Auto-detects identifier columns: OBJECTNAME, ATTRIBUTENAME, DOMAINID, MAXVALUE, etc.
- Preserves original file formatting on export
- Supports multiple sheets per workbook

---

## 11. Key UX Requirements

1. **User chooses everything:** No auto-decisions. User picks objects, fields, languages, translation method.
2. **Visual feedback:** Color-coded badges, progress bars, animated toasts.
3. **Inline editing:** Click any field to type a translation directly, no modal needed.
4. **Bulk actions:** "Select all", "Auto-translate all missing", "Clear all".
5. **Excel must be attractive:** Not a raw data dump — styled, colored, with instructions sheet.
6. **Responsive-ish:** At minimum collapse to single column on narrow screens (same as MXFORGE).

---

## 12. File to Reference

The MXFORGE source HTML file contains the complete design system, component styles, data model, and domain definitions. It should be attached to the next conversation as reference. The file is: `mxforge (2).html`

---

## 13. Summary of What to Build

Build a **single HTML file** (`maximots.html`) that:
- Matches the MXFORGE design system pixel-for-pixel
- Uses the maxTeam logo and branding
- Has a 3-column layout: Modules → Fields/Translations → Preview/Export
- Lets users interactively select objects, fields, and languages
- Shows translation status (native vs. needs-translation)
- Supports manual input + auto-translate (simulated in static HTML, real via backend)
- Generates a beautifully styled .xlsx file via ExcelJS
- Is production-quality, not a prototype

Plus a **Python backend** (FastAPI) that:
- Serves the frontend
- Parses uploaded MXLoader Excel files
- Calls Google Translate for auto-translation
- Exports updated translations back to MXLoader format
