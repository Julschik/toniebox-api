# Python Library Usage

This document covers using tonie-api as a Python library in your own projects.

## Installation

```bash
pip install git+https://github.com/Julschik/toniebox-api.git
```

## Quick Start

```python
from tonie_api import TonieAPI

# Initialize with credentials
api = TonieAPI(username="user@example.com", password="secret")

# Or load from environment variables / .env file
api = TonieAPI()  # Uses TONIE_USERNAME and TONIE_PASSWORD

# Get user info
user = api.get_me()
print(f"Logged in as: {user.email}")

# List households
households = api.get_households()
for household in households:
    print(f"Household: {household.name} ({household.id})")

# Get creative tonies
tonies = api.get_creative_tonies(households[0].id)
for tonie in tonies:
    print(f"Tonie: {tonie.name} ({tonie.id})")
```

## Uploading Audio

```python
# Upload an audio file to a tonie
api.upload_audio_file(
    file_path="story.mp3",
    household_id=households[0].id,
    tonie_id=tonies[0].id,
    title="My Story"
)

# Supported formats: MP3, M4A, WAV, OGG, FLAC
```

## Managing Chapters

```python
# Shuffle chapter order randomly
api.shuffle_chapters(household_id, tonie_id)

# Clear all chapters
api.clear_chapters(household_id, tonie_id)

# Set specific chapters (replaces existing)
api.set_chapters(household_id, tonie_id, chapter_ids=["chapter-1", "chapter-2"])
```

## Error Handling

The library provides specific exception types for different error scenarios:

```python
from tonie_api import (
    TonieAPI,
    TonieAPIError,      # Base exception
    AuthenticationError, # Invalid credentials
    NotFoundError,       # Resource not found
    RateLimitError,      # Too many requests
    ValidationError,     # Invalid input
    ServerError,         # Server-side error
)

try:
    api = TonieAPI()
    tonie = api.get_creative_tonie(household_id, tonie_id)
except AuthenticationError:
    print("Invalid credentials - check username/password")
except NotFoundError:
    print("Tonie not found - check the ID")
except RateLimitError as e:
    print(f"Rate limited - retry after {e.retry_after} seconds")
except TonieAPIError as e:
    print(f"API error: {e}")
```

## API Methods Reference

### User & Config

| Method         | Description                        |
| -------------- | ---------------------------------- |
| `get_me()`     | Get current user info              |
| `get_config()` | Get backend configuration (limits) |

### Households & Tonies

| Method                                                    | Description                       |
| --------------------------------------------------------- | --------------------------------- |
| `get_households()`                                        | List all households               |
| `get_creative_tonies(household_id)`                       | List creative tonies in household |
| `get_creative_tonie(household_id, tonie_id)`              | Get single tonie details          |
| `update_creative_tonie(household_id, tonie_id, **kwargs)` | Update tonie properties           |

### Content Management

| Method                                                        | Description                  |
| ------------------------------------------------------------- | ---------------------------- |
| `upload_audio_file(file_path, household_id, tonie_id, title)` | Upload audio file            |
| `add_chapter(household_id, tonie_id, file_id, title)`         | Add uploaded file as chapter |
| `shuffle_chapters(household_id, tonie_id)`                    | Randomize chapter order      |
| `clear_chapters(household_id, tonie_id)`                      | Remove all chapters          |
| `set_chapters(household_id, tonie_id, chapter_ids)`           | Set specific chapters        |

### Low-Level Methods

| Method                                      | Description          |
| ------------------------------------------- | -------------------- |
| `request_file_upload(file_name, file_size)` | Get S3 presigned URL |
| `upload_to_s3(file_path, upload_details)`   | Upload file to S3    |

## Data Models

All API responses are parsed into Pydantic models:

- `User` - User account information
- `Config` - Backend configuration and limits
- `Household` - Household with members and permissions
- `CreativeTonie` - Creative tonie with chapters
- `Chapter` - Audio chapter on a tonie

See [API.md](API.md) for detailed endpoint documentation and response schemas.

## Authentication Flow

The library handles OAuth2 authentication automatically:

1. On first API call, credentials are sent to `login.tonies.com`
2. Bearer token is stored in the session
3. Token is included in all subsequent requests

Note: Tokens expire after ~1 hour. Currently, you need to create a new `TonieAPI` instance to refresh.

## Environment Variables

| Variable         | Description          |
| ---------------- | -------------------- |
| `TONIE_USERNAME` | Tonie Cloud email    |
| `TONIE_PASSWORD` | Tonie Cloud password |

The library also loads from `.env` files via `python-dotenv`.
