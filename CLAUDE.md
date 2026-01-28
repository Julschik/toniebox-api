# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python library to access the REST API of the Tonie Cloud (tonies.de). This is an unofficial API client, not associated with Tonies SE.

## Konfiguration

Credentials werden aus `.env` geladen (via `python-dotenv`):

- Kopiere `.env.example` nach `.env`
- Variablen: `TONIE_USERNAME`, `TONIE_PASSWORD`

Die `TonieAPI` Klasse lädt automatisch aus `.env`, wenn keine Credentials übergeben werden.

## Common Commands

```bash
# Install dependencies
poetry install

# Run all tests with coverage
poetry run pytest

# Run a single test file
poetry run pytest tests/test_models.py

# Run a specific test
poetry run pytest tests/test_models.py::test_user_model

# Run linting (all pre-commit hooks)
pre-commit run -a

# Install pre-commit hooks (run once)
pre-commit install

# Run CLI
poetry run toniebox --help
poetry run toniebox me
poetry run toniebox households
poetry run toniebox tonies
poetry run toniebox upload /path/to/audio.mp3 TONIE_ID
poetry run toniebox shuffle TONIE_ID
poetry run toniebox clear TONIE_ID --yes
poetry run toniebox config
poetry run toniebox status
poetry run toniebox login
poetry run toniebox logout
poetry run toniebox update
```

## Architecture

The library is structured in `src/tonie_api/`:

- **api.py** - `TonieAPI`: Haupt-Client-Klasse mit allen API-Methoden und Convenience-Funktionen
- **session.py** - `TonieCloudSession`: OAuth2-Session für API-Authentifizierung. Extends `requests.Session`, handles token acquisition from Tonie's OpenID Connect endpoint
- **models.py** - Pydantic v2 Models: `User`, `Config`, `Household`, `CreativeTonie`, `Chapter`, `FileUploadRequest`, `UploadRequestDetails`
- **exceptions.py** - Custom Exception-Hierarchie: `TonieAPIError`, `AuthenticationError`, `NotFoundError`, `RateLimitError`, `ValidationError`, `ServerError`
- **cli/** - CLI-Package mit Click Framework:
  - `main.py` - Root CLI Group mit globalen Optionen
  - `commands.py` - Alle CLI Commands (me, households, tonies, upload, shuffle, clear, config, status, login, logout)
  - `output.py` - Table/JSON Output Formatter

**Authentication flow**: `TonieCloudSession.acquire_token()` → OAuth2 password grant to `login.tonies.com` → Bearer token stored in session

**File upload flow**: Three-step process - (1) POST to `/file` to get S3 presigned URL, (2) Upload directly to S3, (3) POST to add chapter to tonie. Implementiert in `TonieAPI.upload_audio_file()`

## Code Style

- **Linter**: ruff with `select = ["ALL"]` (most rules enabled)
- **Line length**: 120 characters
- **Docstrings**: Google-style convention
- **Type hints**: Required (except for `__init__` return types)

## Terminologie / Terminology

**WICHTIG:** Das Tool unterstützt beliebige Audiodateien (Musik, Hörbücher, Podcasts, Sprachmemos, etc.). Verwende daher immer die generischen Begriffe:

| ❌ Nicht verwenden | ✅ Stattdessen |
|--------------------|----------------|
| Hörbuch, Hörbücher | Audiodatei, Audiodateien |
| audiobook, audiobooks | audio file, audio files |

**Ausnahme:** Wenn explizit mehrere Typen aufgezählt werden (z.B. "Hörbücher und Musik"), ist das korrekt.

**IMPORTANT:** This tool supports any audio files (music, audiobooks, podcasts, voice memos, etc.). Always use generic terms:

| ❌ Don't use | ✅ Use instead |
|--------------|----------------|
| audiobook, audiobooks | audio file, audio files |

**Exception:** When explicitly listing multiple types (e.g. "audiobooks and music"), that's correct.

## Security Rules (aus Security Audit)

**KRITISCH:** Diese Regeln müssen bei allen Code-Änderungen eingehalten werden.

### Credentials & Tokens

- ✅ Credentials nur in `~/.config/tonie-api/credentials` speichern
- ✅ Dateiberechtigungen `0o600` (nur Owner lesen/schreiben)
- ✅ OAuth-Tokens nur im Arbeitsspeicher halten, **nie persistieren**
- ✅ Umgebungsvariablen: `TONIE_USERNAME`, `TONIE_PASSWORD` (nicht `USERNAME`/`PASSWORD` wegen System-Konflikten)
- ❌ Keine Credentials in Logs, Fehlermeldungen oder Exceptions

### Netzwerk-Kommunikation

- ✅ Nur HTTPS verwenden
- ✅ Nur mit offiziellen Tonie-Endpoints kommunizieren:
  - `login.tonies.com` (OAuth)
  - `api.tonie.cloud` (API)
  - S3-URLs von der API (Upload)
- ❌ Keine Drittanbieter-Services oder CDNs
- ❌ Keine Telemetrie, Analytics oder Tracking

### Code-Änderungen in kritischen Dateien

Bei Änderungen an diesen Dateien besondere Vorsicht:

| Datei | Kritischer Bereich |
|-------|-------------------|
| `session.py` | Token-Handling, OAuth-Flow |
| `api.py` | S3-Upload, API-Requests |
| `cli/commands.py` | Credential-Speicherung (`login`/`logout`) |

### Logging & Error Handling

- ❌ Keine sensiblen Daten (Passwörter, Tokens, E-Mails) in Logs
- ❌ Keine Credentials in Exception-Messages
- ✅ Bei Auth-Fehlern nur generische Meldung ("Authentication failed")

## Testing

Tests in `tests/`:

- **test_api.py** - Unit-Tests für `TonieAPI` (38 Tests): Initialisierung, Core-Methoden, Error-Handling, Convenience-Methoden
- **test_models.py** - Unit-Tests für alle Pydantic Models (User, Household, CreativeTonie, etc.)
- **test_connectivity.py** - Prüft API-Erreichbarkeit (login.tonies.com, api.tonie.cloud)
- **test_cli.py** - Unit-Tests für CLI Commands (31 Tests)

Tests verwenden `pytest` und mocken HTTP-Requests mit der `responses` Library. Aktuell 79 Tests mit 77% Coverage.

## Documentation

| Document | Description |
|----------|-------------|
| [docs/API.md](docs/API.md) | REST API endpoints and response schemas |
| [docs/LIBRARY.md](docs/LIBRARY.md) | Python library usage guide |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Project structure and data flow |
| [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) | Development setup and guidelines |

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org) format:

```
feat(something): add new feature
fix(api): resolve authentication issue
```

Commitlint validates on CI and via pre-commit hook.

## Session Handover

**Letzter Stand:** TonieAPI vollständig implementiert

**Erledigt:**

- [x] `session.py` mit OAuth2-Authentifizierung
- [x] `models.py` mit allen API-Response-Models
- [x] Field Aliases für camelCase → snake_case Mapping
- [x] Unit-Tests für alle Models (`test_models.py`)
- [x] Exports in `__init__.py`
- [x] `exceptions.py` mit Exception-Hierarchie (TonieAPIError, AuthenticationError, etc.)
- [x] `api.py` mit `TonieAPI` Klasse
- [x] Core API-Methoden: `get_me()`, `get_config()`, `get_households()`, `get_creative_tonies()`, `get_creative_tonie()`, `update_creative_tonie()`, `add_chapter()`, `request_file_upload()`
- [x] Convenience-Methoden: `upload_to_s3()`, `upload_audio_file()`, `shuffle_chapters()`, `clear_chapters()`, `set_chapters()`
- [x] Umfassende Tests (`test_api.py`) mit 100% Coverage
- [x] CLI-Tool mit Click Framework (`cli/`)
- [x] CLI Commands: `me`, `households`, `tonies`, `upload`, `shuffle`, `clear`, `config`, `status`, `login`, `logout`
- [x] CLI Tests (`test_cli.py`) mit 31 Tests
- [x] Quick Wins implementiert:
  - [x] `toniebox config` Command (zeigt API-Limits)
  - [x] `toniebox status` Command (API Health-Check)
  - [x] Input-Validierung in `upload_to_s3()` (Datei-Existenz prüfen)
  - [x] `requests-oauthlib` Dependency entfernt
  - [x] `RateLimitError` mit `retry_after` Property erweitert
  - [x] Umgebungsvariablen-Dokumentation vereinheitlicht (`TONIE_USERNAME`/`TONIE_PASSWORD`)

**Mögliche Erweiterungen:**

- Token-Refresh bei Ablauf (KRITISCH - Token läuft nach ~1h ab)
- Retry-Logic mit exponential backoff
- Async-Support (aiohttp/httpx)
- Rate-Limit Handling mit `Retry-After` Header (Basis bereits implementiert)
