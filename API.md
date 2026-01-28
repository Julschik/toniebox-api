# API Reference

This document describes the Tonie Cloud REST API.

## Authentication

The Tonie Cloud uses OAuth2 with OpenID Connect for authentication:

- **Token Endpoint:** `https://login.tonies.com/auth/realms/tonies/protocol/openid-connect/token`
- **Grant Type:** Password
- **Client ID:** `my-tonies`
- **Scope:** `openid`

## Base URL

```
https://api.tonie.cloud/v2
```

## Endpoints

| Endpoint                                        | Method    | Description               |
| ----------------------------------------------- | --------- | ------------------------- |
| `/me`                                           | GET       | Current user info         |
| `/config`                                       | GET       | Backend configuration     |
| `/households`                                   | GET       | List all households       |
| `/households/{id}/creativetonies`               | GET       | List creative tonies      |
| `/households/{id}/creativetonies/{id}`          | GET/PATCH | Get/Update creative tonie |
| `/households/{id}/creativetonies/{id}/chapters` | POST      | Add chapter to tonie      |
| `/file`                                         | POST      | Request file upload URL   |

## Response Models

**User**
| Field | Type |
|-------|------|
| `uuid` | `str` |
| `email` | `str` |

**Config**
| Field | Type |
|-------|------|
| `locales` | `list[str]` |
| `unicodeLocales` | `list[str]` |
| `maxChapters` | `int` |
| `maxSeconds` | `int` |
| `maxBytes` | `int` |
| `accepts` | `list[str]` |
| `stageWarning` | `bool` |
| `paypalClientId` | `str` |
| `ssoEnabled` | `bool` |

**Household**
| Field | Type |
|-------|------|
| `id` | `str` |
| `name` | `str` |
| `ownerName` | `str` |
| `access` | `str` |
| `canLeave` | `bool` |

**CreativeTonie**
| Field | Type |
|-------|------|
| `id` | `str` |
| `householdId` | `str` |
| `name` | `str` |
| `imageUrl` | `str` |
| `secondsRemaining` | `float` |
| `secondsPresent` | `float` |
| `chaptersRemaining` | `int` |
| `chaptersPresent` | `int` |
| `transcoding` | `bool` |
| `lastUpdate` | `datetime \| None` |
| `chapters` | `list[Chapter]` |

**Chapter**
| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | |
| `title` | `str` | |
| `file` | `str` | UUID for new uploads, opaque blob for existing, `ContentToken:...` for content tokens |
| `seconds` | `float` | |
| `transcoding` | `bool` | |

**FileUploadRequest**
| Field | Type |
|-------|------|
| `request.url` | `str` |
| `request.fields` | `dict` |
| `fileId` | `str` |

## File Upload Flow

1. **Request upload URL:** POST to `/file` → returns `FileUploadRequest`
2. **Upload to S3:** POST to `request.url` with:
   - `request.fields` as form data
   - File as multipart under key `file` with `request.fields["key"]` as filename
3. **Add chapter:** POST to `/households/{id}/creativetonies/{id}/chapters` with `{title, file: fileId}`

## Additional Operations

- **Sort chapters:** PATCH `/households/{id}/creativetonies/{id}` with `{chapters: [...]}`
- **Delete all chapters:** PATCH `/households/{id}/creativetonies/{id}` with `{chapters: []}`
