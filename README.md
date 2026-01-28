# Tonie API

Python client for the Tonie Cloud API (tonies.de).

> **Note:** This is an unofficial API client, not associated with Boxine.

## Installation

```bash
pip install git+https://github.com/Julschik/toniebox-api.git
```

## Konfiguration

1. Kopiere `.env.example` nach `.env`
2. Trage deine Tonie-Zugangsdaten ein:
   ```
   USERNAME=deine@email.de
   PASSWORD=dein_passwort
   ```

## Quick Start

```python
from tonie_api import TonieAPI

# Lädt automatisch Credentials aus .env
api = TonieAPI()

# Oder explizit:
# api = TonieAPI(username="user@example.com", password="secret")

# Get user info
user = api.get_me()
print(f"Logged in as: {user.email}")

# Get households
households = api.get_households()

# Get creative tonies for a household
tonies = api.get_creative_tonies(households[0].id)

for tonie in tonies:
    print(f"{tonie.name}: {tonie.chapters_present} chapters")

# Upload audio file (handles S3 upload automatically)
api.upload_audio_file(
    file_path="story.mp3",
    household_id=households[0].id,
    tonie_id=tonies[0].id,
    title="My Story"  # optional, defaults to filename
)

# Shuffle chapters
api.shuffle_chapters(households[0].id, tonies[0].id)

# Clear all chapters
api.clear_chapters(households[0].id, tonies[0].id)
```

## Kommandozeilen-Tool (CLI)

Du kannst die Tonie API auch ohne Python-Kenntnisse direkt im Terminal nutzen.

### Terminal öffnen

- **macOS**: Drücke `Cmd + Leertaste`, tippe "Terminal" und drücke Enter
- **Windows**: Drücke die Windows-Taste, tippe "cmd" oder "PowerShell" und drücke Enter

### Voraussetzung: Python installieren

Falls du die Fehlermeldung `command not found: pip` erhältst, musst du zuerst Python installieren.

**macOS:**
1. Öffne das Terminal
2. Gib ein: `brew install python`
3. Falls Homebrew nicht installiert ist, besuche [brew.sh](https://brew.sh) und folge der Anleitung

**Windows:**
1. Lade Python von [python.org/downloads](https://www.python.org/downloads/) herunter
2. Führe den Installer aus
3. **Wichtig:** Setze den Haken bei "Add Python to PATH"
4. Starte das Terminal neu

### Installation

Gib im Terminal folgenden Befehl ein:

```bash
pip install git+https://github.com/Julschik/toniebox-api.git
```

Falls `pip` nicht funktioniert, versuche `pip3`:

```bash
pip3 install git+https://github.com/Julschik/tonie-api.git
```

### Zugangsdaten einrichten

Erstelle eine Datei namens `.env` im Ordner, von dem aus du die Befehle ausführst:

```
USERNAME=deine@email.de
PASSWORD=dein_passwort
```

Ersetze die Werte mit deinen echten Tonie-Zugangsdaten.

### Verfügbare Befehle

| Befehl | Beschreibung |
|--------|--------------|
| `tonie me` | Zeigt deine Benutzerinfo |
| `tonie households` | Listet alle deine Haushalte |
| `tonie tonies` | Zeigt alle Creative Tonies |
| `tonie upload DATEI TONIE-ID` | Lädt eine Audio-Datei auf einen Tonie |
| `tonie shuffle TONIE-ID` | Mischt die Kapitelreihenfolge zufällig |
| `tonie clear TONIE-ID --yes` | Löscht alle Kapitel vom Tonie |

### Praxisbeispiel: Hörbuch hochladen

1. **Tonie-ID herausfinden**
   ```bash
   tonie tonies
   ```
   Notiere dir die ID deines Creative Tonies (z.B. `CF12345678901234`).

2. **Audio-Datei hochladen**
   ```bash
   tonie upload /pfad/zu/hoerbuch.mp3 CF12345678901234
   ```

3. **Kapitel mischen** (optional)
   ```bash
   tonie shuffle CF12345678901234
   ```

Fertig! Stelle den Tonie auf die Box, um die Änderungen zu synchronisieren.

### Hilfe anzeigen

Für weitere Optionen zu jedem Befehl:

```bash
tonie --help
tonie upload --help
```

## Error Handling

```python
from tonie_api import TonieAPI, AuthenticationError, NotFoundError

try:
    api = TonieAPI()
    tonie = api.get_creative_tonie(household_id, tonie_id)
except AuthenticationError:
    print("Invalid credentials")
except NotFoundError:
    print("Tonie not found")
```

For detailed API documentation (endpoints, response models, file upload flow), see [API.md](API.md).

## Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Run linting
pre-commit run -a
```

## License

MIT
