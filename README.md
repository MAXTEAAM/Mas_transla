# MaxiMots — Translation Studio

> Gestionnaire de traductions pour IBM Maximo MAS 9 · **by maxTeam**

MaxiMots pilote le processus de traduction client pour Maximo MAS 9 : extraction SQL des 6 tables de traduction système (SYNONYMDOMAIN, MAXLABELS, MAXMESSAGES, MAXATTRIBUTE, APPLICATION, LONGDESCRIPTION), proposition IBM/Maximo par défaut, arbitrage client (conserver IBM / Google / manuelle / non obligatoire), contrôle des contraintes DB (longueur max, variables `{0}`, HTML), puis export d'un classeur de suivi au format client avec onglet MxLoader prêt à importer.

---

## Démarrage rapide

### Prérequis

- Python 3.10+
- Un navigateur moderne (Chrome, Edge, Firefox)
- Accès internet pour l'auto-traduction (Google Translate via `deep-translator`, sans clé API)

### Installation

```bash
cd backend
pip install -r requirements.txt
```

> Sous Windows, si la commande échoue :
> `pip install fastapi uvicorn python-multipart openpyxl deep-translator`

### Lancement (version complète)

```bash
cd backend
python app.py
```

Puis ouvrir **http://localhost:8000**

En développement (rechargement automatique) :

```bash
cd backend
uvicorn app:app --reload --port 8000
```

### Version autonome (sans backend)

Ouvrez simplement `standalone/maximots.html` dans un navigateur. Tout fonctionne sauf l'auto-traduction réelle (remplacée par une simulation `[FR] ...`) et l'upload de fichiers MXLoader.

---

## Utilisation

L'interface suit trois étapes, une par colonne :

### 01 — Sélection
Choisissez une structure objet Maximo dans l'arborescence par module (Gestion des actifs, Gestion du travail, Inventaire & articles, Achats, Personnes & organisation). Les champs de l'objet et de ses relations (ASSETSPEC, WPLABOR, POLINE...) se chargent dans la colonne centrale.

### 02 — Traduction
Cochez les champs à traduire et les langues cibles (la source est toujours EN). Chaque champ affiche son statut par langue :

| Badge | Signification |
|---|---|
| 🟢 **Maximo natif** | Géré par les tables `L_` (DESCRIPTION, LONGDESCRIPTION, valeurs de domaine) — rien à faire |
| 🟠 **Traduction requise** | Maximo ne sait pas le traduire — à traiter via MaxiMots/MXLoader |
| 🟣 **Auto / Personnalisé** | Suggestion automatique ou saisie manuelle |

Actions disponibles : tout sélectionner/désélectionner, **Auto-traduire les manquants**, saisie manuelle inline (cliquez « Traduire manuellement »), filtres (tout / natifs / manquants).

### 03 — Export
Statistiques, barres de progression par langue, aperçu du fichier, options (auto-remplissage, inclusion des traductions natives, style), puis **Générer l'Excel MaxiMots**.

Fichier produit : `MaxiMots_[OBJET]_[LANGUES]_[AAAA-MM-JJ].xlsx`

| Feuille | Contenu |
|---|---|
| **Traductions** | OBJECTNAME · ATTRIBUTENAME · TYPE · EN (source) · une colonne par langue · STATUS. Cellules vertes = natif, ambre = à remplir, violettes = auto/manuel. En-tête figé, filtre automatique. |
| **Instructions** | Légende des couleurs, procédure de réimport MXLoader, référence des types |
| **Domaines** | Valeurs des domaines référencés par l'objet (DOMAINID, MAXVALUE, DESCRIPTION) |

### Source de données

L'icône ⚙ de la barre supérieure permet de choisir la source :

- **Démo** — métadonnées embarquées, hors-ligne (par défaut)
- **API REST / OSLC** — source officielle MAS 9, cloud et on-premise
- **SQL direct** — lecture en masse, nécessite un accès base de données

---

## Flux MXLoader (backend)

Le backend permet aussi le chemin inverse : enrichir un export MXLoader existant.

1. **Upload** d'un fichier Excel MXLoader → détection automatique des colonnes de langues (`EN`, `FR`, `DESCRIPTION_FR`, `LDTEXT_EN`...) et des identifiants (OBJECTNAME, ATTRIBUTENAME, DOMAINID, MAXVALUE...)
2. **Détection** des traductions manquantes par langue
3. **Auto-traduction** des manquants et/ou corrections manuelles
4. **Export** au format MXLoader d'origine, prêt à réimporter dans Maximo

## API

| Méthode | Endpoint | Description |
|---|---|---|
| GET | `/` | Interface MaxiMots |
| POST | `/upload` | Upload d'un Excel MXLoader, parsing, création de session |
| GET | `/session/{id}/rows` | Lignes de traduction (filtrables : `sheet`, `filter=missing\|translated`, `target_lang`) |
| POST | `/session/{id}/auto-translate` | Auto-traduction des entrées manquantes |
| POST | `/session/{id}/manual-update` | Mise à jour manuelle d'une traduction |
| POST | `/session/{id}/export` | Export Excel compatible MXLoader |
| POST | `/translate` | Traduction directe par lot (utilisée par le frontend) |
| GET | `/supported-languages` | Langues supportées |

Documentation interactive : **http://localhost:8000/docs** (Swagger généré par FastAPI).

---

## Structure du projet

```
.
├── README.md
├── standalone/
│   └── maximots.html          # Version autonome — à ouvrir directement dans un navigateur
├── backend/
│   ├── app.py                 # Backend FastAPI (version complète)
│   ├── translator.py          # Moteur de traduction (Google Translate / deep-translator)
│   ├── mxloader_parser.py     # Parseur / exporteur de fichiers MXLoader
│   ├── requirements.txt       # Dépendances Python
│   ├── templates/
│   │   └── index.html         # Frontend servi par le backend
│   ├── samples/
│   │   └── test_mxloader.xlsx # Exemple de fichier MXLoader pour tester l'upload
│   ├── uploads/               # Créé automatiquement — fichiers uploadés (sessions)
│   └── exports/               # Créé automatiquement — fichiers Excel exportés
└── docs/
    └── MaxiMots_Project_Brief.md  # Cahier des charges du projet
```

> Les deux versions du frontend divergent volontairement : `standalone/maximots.html` (démo hors-ligne) et `backend/templates/index.html` (servie par FastAPI). Si vous modifiez l'interface, pensez à reporter les changements dans l'autre version si nécessaire.

## Logique de traduction

**Natif Maximo (tables `L_`)** — géré par le système, marqué vert :
- `DESCRIPTION` et `LONGDESCRIPTION` sur tout objet
- Descriptions des valeurs de domaine (ALNDOMAIN, SYNONYMDOMAIN, NUMERICDOMAIN)
- `TITLE` sur MAXATTRIBUTE

**Non natif (nécessite MXLoader / MaxiMots)** — marqué ambre :
- Libellés d'attributs personnalisés, descriptions de classifications, compteurs, valeurs ASSETSPEC/WORKORDERSPEC, descriptions de tâches, champs ALN personnalisés, libellés de rapports, modèles de communication...

**Langues** : source EN ; cibles FR, DE, ES, AR, ZH, JA, PT, IT, NL, KO, TR (multi-sélection).

## Stack technique

- **Backend** : Python · FastAPI · uvicorn · openpyxl · deep-translator
- **Frontend** : HTML/CSS/JS en fichier unique · ExcelJS (CDN) pour la génération Excel côté client
- **Design** : système MXFORGE (Inter + IBM Plex Mono, palette navy/ambre maxTeam)

---

*MaxiMots v2.0.0 — maxTeam*
