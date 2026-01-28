# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python library to access the REST API of the Tonie Cloud (tonies.de). This is an unofficial API client, not associated with Boxine.

## Konfiguration

Credentials werden aus `.env` geladen (via `python-dotenv`):

- Kopiere `.env.example` nach `.env`
- Variablen: `USERNAME`, `PASSWORD`

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
poetry run tonie --help
poetry run tonie me
poetry run tonie households
poetry run tonie tonies
poetry run tonie upload /path/to/audio.mp3 TONIE_ID
poetry run tonie shuffle TONIE_ID
poetry run tonie clear TONIE_ID --yes
```

## Architecture

The library is structured in `src/tonie_api/`:

- **api.py** - `TonieAPI`: Haupt-Client-Klasse mit allen API-Methoden und Convenience-Funktionen
- **session.py** - `TonieCloudSession`: OAuth2-Session für API-Authentifizierung. Extends `requests.Session`, handles token acquisition from Tonie's OpenID Connect endpoint
- **models.py** - Pydantic v2 Models: `User`, `Config`, `Household`, `CreativeTonie`, `Chapter`, `FileUploadRequest`, `UploadRequestDetails`
- **exceptions.py** - Custom Exception-Hierarchie: `TonieAPIError`, `AuthenticationError`, `NotFoundError`, `RateLimitError`, `ValidationError`, `ServerError`
- **cli/** - CLI-Package mit Click Framework:
  - `main.py` - Root CLI Group mit globalen Optionen
  - `commands.py` - Alle CLI Commands (me, households, tonies, upload, shuffle, clear)
  - `output.py` - Table/JSON Output Formatter

**Authentication flow**: `TonieCloudSession.acquire_token()` → OAuth2 password grant to `login.tonies.com` → Bearer token stored in session

**File upload flow**: Three-step process - (1) POST to `/file` to get S3 presigned URL, (2) Upload directly to S3, (3) POST to add chapter to tonie. Implementiert in `TonieAPI.upload_audio_file()`

## Code Style

- **Linter**: ruff with `select = ["ALL"]` (most rules enabled)
- **Line length**: 120 characters
- **Docstrings**: Google-style convention
- **Type hints**: Required (except for `__init__` return types)

## Testing

Tests in `tests/`:

- **test_api.py** - Unit-Tests für `TonieAPI` (38 Tests): Initialisierung, Core-Methoden, Error-Handling, Convenience-Methoden
- **test_models.py** - Unit-Tests für alle Pydantic Models (User, Household, CreativeTonie, etc.)
- **test_connectivity.py** - Prüft API-Erreichbarkeit (login.tonies.com, api.tonie.cloud)
- **test_cli.py** - Unit-Tests für CLI Commands (31 Tests)

Tests verwenden `pytest` und mocken HTTP-Requests mit der `responses` Library. Aktuell 79 Tests mit 96% Coverage.

## API Reference

See API.md for full API endpoint documentation, response models, and the file upload flow.

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
- [x] CLI Commands: `me`, `households`, `tonies`, `upload`, `shuffle`, `clear`
- [x] CLI Tests (`test_cli.py`) mit 31 Tests

**Mögliche Erweiterungen:**

- Token-Refresh bei Ablauf
- Retry-Logic mit exponential backoff
- Async-Support (aiohttp)
