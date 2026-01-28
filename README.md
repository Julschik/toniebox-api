<div align="center">

# Tonie API

[![Python](https://img.shields.io/badge/Python-3.9+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-79_passed-success?style=flat-square)](tests/)
[![Coverage](https://img.shields.io/badge/Coverage-96%25-brightgreen?style=flat-square)](tests/)

**Python client for the Tonie Cloud API | Python-Client für die Tonie Cloud API**

*Upload audiobooks to your Creative Tonies directly from your computer*<br>
*Lade Hörbücher direkt vom Computer auf deine Creative Tonies*

</div>

> [!WARNING]
> **Unofficial** | This is not associated with tonies® or Boxine in any way.<br>
> **Inoffiziell** | Dies ist kein offizielles Produkt von tonies® oder Boxine.

> [!NOTE]
> **[🔒 Vertrauen & Sicherheit](TRUST.md)** - Lies, wie deine Daten geschützt werden.<br>
> **[🔒 Trust & Security](TRUST.md)** - Read how your data is protected.

---

<details open>
<summary><h2>🇩🇪 Deutsch</h2></summary>

### Über das Projekt

Ein Kommandozeilen-Tool und eine Python-Bibliothek zum Hochladen von Hörbüchern und Musik auf Kreativ-Tonies ohne die offizielle App.

---

### 📦 Installation

<details open>
<summary><strong>macOS</strong></summary>

1. Öffne das Terminal: `Cmd + Leertaste`, tippe "Terminal", drücke Enter
2. Kopiere diesen Befehl und drücke Enter:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Julschik/toniebox-api/main/install.sh)"
```

3. Gib deine Tonie-Zugangsdaten ein (die gleichen wie in der Tonie-App)

</details>

<details>
<summary><strong>Windows</strong></summary>

1. Öffne PowerShell als Administrator
2. Kopiere diesen Befehl und drücke Enter:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/Julschik/toniebox-api/main/install.ps1'))
```

3. Gib deine Tonie-Zugangsdaten ein (die gleichen wie in der Tonie-App)

</details>

---

### 🔧 Verfügbare Befehle

| Befehl | Beschreibung |
|:-------|:-------------|
| `tonie login` | Zugangsdaten einrichten/ändern |
| `tonie logout` | Zugangsdaten löschen |
| `tonie me` | Zeigt deine Benutzerinfo |
| `tonie households` | Listet alle deine Haushalte |
| `tonie tonies` | Zeigt alle Creative Tonies |
| `tonie upload DATEI TONIE-ID` | Lädt eine Audio-Datei auf einen Tonie |
| `tonie shuffle TONIE-ID` | Mischt die Kapitelreihenfolge zufällig |
| `tonie clear TONIE-ID --yes` | Löscht alle Kapitel vom Tonie |
| `tonie config` | Zeigt Backend-Limits (Kapitel, Dauer, Dateigröße) |
| `tonie status` | Prüft API-Erreichbarkeit |

---

### 🚀 Beispiel: Hörbuch hochladen

```bash
# 1. Zeige alle Tonies an und notiere die ID
tonie tonies

# 2. Lade eine Datei hoch (ersetze ID mit deiner Tonie-ID)
tonie upload /Users/ich/Downloads/hoerbuch.mp3 CF12345678901234

# 3. Stelle den Tonie auf die Box um zu synchronisieren
```

---

<details>
<summary><strong>❓ Troubleshooting</strong></summary>

| Problem | Lösung |
|:--------|:-------|
| `tonie: command not found` | Terminal neu starten oder `source ~/.zshrc` |
| `Authentication failed` | Zugangsdaten prüfen mit `tonie login` |
| `No households found` | Account muss mindestens eine Toniebox haben |
| Upload schlägt fehl | Dateiformat prüfen (MP3, M4A, WAV, OGG, FLAC) |
| Tonie synchronisiert nicht | Tonie kurz auf Box stellen / WLAN Verbindung prüfen |

</details>

<details>
<summary><strong>📚 Python-Bibliothek</strong></summary>

#### Installation

```bash
pip install git+https://github.com/Julschik/toniebox-api.git
```

#### Schnellstart

```python
from tonie_api import TonieAPI

# Mit Zugangsdaten initialisieren
api = TonieAPI(username="user@example.com", password="secret")

# Oder aus Umgebungsvariablen laden
api = TonieAPI()  # Nutzt TONIE_USERNAME und TONIE_PASSWORD

# Benutzerinfo abrufen
user = api.get_me()
print(f"Eingeloggt als: {user.email}")

# Haushalte auflisten
households = api.get_households()

# Creative Tonies abrufen
tonies = api.get_creative_tonies(households[0].id)

# Audio hochladen
api.upload_audio_file(
    file_path="geschichte.mp3",
    household_id=households[0].id,
    tonie_id=tonies[0].id,
    title="Meine Geschichte"
)
```

Mehr Details: [docs/LIBRARY.md](docs/LIBRARY.md)

</details>

---

### 📖 Dokumentation

| Dokument | Beschreibung |
|:---------|:-------------|
| [Python Library](docs/LIBRARY.md) | Nutzung als Python-Bibliothek |
| [API Reference](docs/API.md) | Technische API-Dokumentation |
| [Contributing](docs/CONTRIBUTING.md) | Entwickler-Setup und Guidelines |
| [Architecture](docs/ARCHITECTURE.md) | Projektstruktur und Datenfluss |

---

### 🙏 Credit

Dieses Tool wurde von Grund auf neu entwickelt. Die notwendigen API-Informationen stammen von [Wilhelmsson177/tonie-api](https://github.com/Wilhelmsson177/tonie-api). Vielen Dank!

</details>

---

<details>
<summary><h2>🇬🇧 English</h2></summary>

### About

A command-line tool and Python library for uploading audiobooks to Creative Tonies - without the official app.

---

### 📦 Installation

<details open>
<summary><strong>macOS</strong></summary>

1. Open Terminal: Press `Cmd + Space`, type "Terminal", press Enter
2. Copy this command and press Enter:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Julschik/toniebox-api/main/install.sh)"
```

3. Enter your Tonie credentials (same as in the Tonie app)

</details>

<details>
<summary><strong>Windows</strong></summary>

1. Open PowerShell as Administrator
2. Copy this command and press Enter:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/Julschik/toniebox-api/main/install.ps1'))
```

3. Enter your Tonie credentials (same as in the Tonie app)

</details>

---

### 🔧 Available Commands

| Command | Description |
|:--------|:------------|
| `tonie login` | Set up / change credentials |
| `tonie logout` | Remove credentials |
| `tonie me` | Show your user info |
| `tonie households` | List all your households |
| `tonie tonies` | Show all Creative Tonies |
| `tonie upload FILE TONIE-ID` | Upload an audio file to a Tonie |
| `tonie shuffle TONIE-ID` | Randomly shuffle chapter order |
| `tonie clear TONIE-ID --yes` | Delete all chapters from Tonie |
| `tonie config` | Show backend limits (chapters, duration, file size) |
| `tonie status` | Check API availability |

---

### 🚀 Example: Upload an Audiobook

```bash
# 1. List all your Tonies and note the ID
tonie tonies

# 2. Upload a file (replace ID with your Tonie ID)
tonie upload /Users/me/Downloads/audiobook.mp3 CF12345678901234

# 3. Place the Tonie on the box to sync
```

---

<details>
<summary><strong>❓ Troubleshooting</strong></summary>

| Problem | Solution |
|:--------|:---------|
| `tonie: command not found` | Restart terminal or run `source ~/.zshrc` |
| `Authentication failed` | Check credentials with `tonie login` |
| `No households found` | Account needs at least one Toniebox |
| Upload fails | Check file format (MP3, M4A, WAV, OGG, FLAC) |
| Tonie doesn't sync | Place Tonie on box briefly |

</details>

<details>
<summary><strong>📚 Python Library</strong></summary>

#### Installation

```bash
pip install git+https://github.com/Julschik/toniebox-api.git
```

#### Quick Start

```python
from tonie_api import TonieAPI

# Initialize with credentials
api = TonieAPI(username="user@example.com", password="secret")

# Or load from environment variables
api = TonieAPI()  # Uses TONIE_USERNAME and TONIE_PASSWORD

# Get user info
user = api.get_me()
print(f"Logged in as: {user.email}")

# List households
households = api.get_households()

# Get creative tonies
tonies = api.get_creative_tonies(households[0].id)

# Upload audio
api.upload_audio_file(
    file_path="story.mp3",
    household_id=households[0].id,
    tonie_id=tonies[0].id,
    title="My Story"
)
```

More details: [docs/LIBRARY.md](docs/LIBRARY.md)

</details>

---

### 📖 Documentation

| Document | Description |
|:---------|:------------|
| [Python Library](docs/LIBRARY.md) | Library usage guide |
| [API Reference](docs/API.md) | Technical API documentation |
| [Contributing](docs/CONTRIBUTING.md) | Developer setup and guidelines |
| [Architecture](docs/ARCHITECTURE.md) | Project structure and data flow |

---

### 🙏 Credit

This tool was built from scratch. The necessary API information comes from [Wilhelmsson177/tonie-api](https://github.com/Wilhelmsson177/tonie-api). Thank you!

</details>

---

<div align="center">

**[MIT License](LICENSE)** · Made with ❤️ for the Tonie community

</div>
