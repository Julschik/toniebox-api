# API Reference

Technical documentation for the Tonie Cloud REST API.

## Base URL

```
https://api.tonie.cloud/v2
```

## Authentication

OAuth2 password grant via OpenID Connect:

```
POST https://login.tonies.com/auth/realms/tonies/protocol/openid-connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=password
&client_id=my-tonies
&scope=openid
&username={email}
&password={password}
```

Response includes `access_token` (Bearer token, ~1 hour validity).

All API requests require:

```
Authorization: Bearer {access_token}
```

## Endpoints

### User & Config

#### GET /me

Get current user information.

**Response:**

```json
{
  "uuid": "12345678-1234-1234-1234-123456789abc",
  "email": "user@example.com"
}
```

#### GET /config

Get backend configuration and limits.

**Response:**

```json
{
  "locales": ["de-DE", "en-US"],
  "unicodeLocales": ["de_DE", "en_US"],
  "maxChapters": 99,
  "maxSeconds": 5400,
  "maxBytes": 524288000,
  "accepts": [
    "audio/mpeg",
    "audio/mp4",
    "audio/x-wav",
    "audio/ogg",
    "audio/flac"
  ],
  "stageWarning": false,
  "paypalClientId": "...",
  "ssoEnabled": true
}
```

### Households

#### GET /households

List all households for the current user.

**Response:**

```json
[
  {
    "id": "household-id-123",
    "name": "My Home",
    "ownerName": "John Doe",
    "access": "owner",
    "canLeave": false
  }
]
```

### Creative Tonies

#### GET /households/{householdId}/creativetonies

List all Creative Tonies in a household.

**Response:**

```json
[
  {
    "id": "CF12345678901234",
    "householdId": "household-id-123",
    "name": "My Creative Tonie",
    "imageUrl": "https://...",
    "secondsRemaining": 4500.0,
    "secondsPresent": 900.0,
    "chaptersRemaining": 95,
    "chaptersPresent": 4,
    "transcoding": false,
    "lastUpdate": "2024-01-15T10:30:00Z",
    "chapters": [
      {
        "id": "chapter-id-1",
        "title": "Story 1",
        "file": "file-id-1",
        "seconds": 300.5,
        "transcoding": false
      }
    ]
  }
]
```

#### GET /households/{householdId}/creativetonies/{tonieId}

Get a specific Creative Tonie.

**Response:** Same as single item in list above.

#### PATCH /households/{householdId}/creativetonies/{tonieId}

Update a Creative Tonie (name, chapters).

**Request:**

```json
{
  "name": "New Name",
  "chapters": [
    { "id": "chapter-id-1", "title": "Story 1", "file": "file-id-1" },
    { "id": "chapter-id-2", "title": "Story 2", "file": "file-id-2" }
  ]
}
```

**Response:** Updated CreativeTonie object.

#### POST /households/{householdId}/creativetonies/{tonieId}/chapters

Add a new chapter to a Creative Tonie.

**Request:**

```json
{
  "title": "My New Chapter",
  "file": "uploaded-file-id"
}
```

**Response:** Updated CreativeTonie object.

### File Upload

#### POST /file

Request a presigned S3 URL for file upload.

**Request:** Empty body.

**Response:**

```json
{
  "fileId": "uploaded-file-id-123",
  "request": {
    "url": "https://s3.eu-central-1.amazonaws.com/bucket-name",
    "fields": {
      "key": "uploads/...",
      "x-amz-algorithm": "AWS4-HMAC-SHA256",
      "x-amz-credential": "...",
      "x-amz-date": "20240115T000000Z",
      "policy": "...",
      "x-amz-signature": "..."
    }
  }
}
```

## File Upload Flow

Uploading audio files is a three-step process:

```
1. POST /file              → Get presigned S3 URL + fileId
2. POST {S3 URL}           → Upload file directly to S3
3. POST .../chapters       → Add chapter with fileId to tonie
```

### Step 1: Request Upload URL

```http
POST /v2/file
Authorization: Bearer {token}
```

### Step 2: Upload to S3

```http
POST {request.url}
Content-Type: multipart/form-data

{request.fields as form fields}
file: {binary file content}
```

### Step 3: Add Chapter

```http
POST /v2/households/{id}/creativetonies/{id}/chapters
Authorization: Bearer {token}
Content-Type: application/json

{"title": "My Chapter", "file": "{fileId}"}
```

## Data Models

### User

| Field | Type   | Description |
| ----- | ------ | ----------- |
| uuid  | string | User UUID   |
| email | string | User email  |

### Config

| Field          | Type     | Description                             |
| -------------- | -------- | --------------------------------------- |
| locales        | string[] | Available locales                       |
| unicodeLocales | string[] | Unicode locale codes                    |
| maxChapters    | int      | Max chapters per tonie (99)             |
| maxSeconds     | int      | Max duration in seconds (5400 = 90 min) |
| maxBytes       | int      | Max file size in bytes (500 MB)         |
| accepts        | string[] | Accepted MIME types                     |
| stageWarning   | bool     | Show staging warning                    |
| paypalClientId | string   | PayPal client ID                        |
| ssoEnabled     | bool     | SSO enabled                             |

### Household

| Field     | Type   | Description                        |
| --------- | ------ | ---------------------------------- |
| id        | string | Household ID                       |
| name      | string | Household name                     |
| ownerName | string | Owner's display name               |
| access    | string | User's access level (owner/member) |
| canLeave  | bool   | Can user leave household           |

### CreativeTonie

| Field             | Type      | Description                 |
| ----------------- | --------- | --------------------------- |
| id                | string    | Tonie ID (starts with CF)   |
| householdId       | string    | Parent household ID         |
| name              | string    | Tonie display name          |
| imageUrl          | string    | Tonie image URL             |
| secondsRemaining  | float     | Remaining duration capacity |
| secondsPresent    | float     | Current content duration    |
| chaptersRemaining | int       | Remaining chapter slots     |
| chaptersPresent   | int       | Current chapter count       |
| transcoding       | bool      | Transcoding in progress     |
| lastUpdate        | datetime  | Last content update         |
| chapters          | Chapter[] | List of chapters            |

### Chapter

| Field       | Type   | Description             |
| ----------- | ------ | ----------------------- |
| id          | string | Chapter ID              |
| title       | string | Chapter title           |
| file        | string | File reference          |
| seconds     | float  | Duration in seconds     |
| transcoding | bool   | Transcoding in progress |

### FileUploadRequest

| Field          | Type   | Description               |
| -------------- | ------ | ------------------------- |
| fileId         | string | ID for the uploaded file  |
| request        | object | S3 presigned POST details |
| request.url    | string | S3 bucket URL             |
| request.fields | object | Form fields for S3 POST   |

## Error Responses

| Status | Exception           | Description              |
| ------ | ------------------- | ------------------------ |
| 400    | ValidationError     | Invalid request data     |
| 401    | AuthenticationError | Invalid or expired token |
| 403    | AuthenticationError | Access denied            |
| 404    | NotFoundError       | Resource not found       |
| 429    | RateLimitError      | Too many requests        |
| 5xx    | ServerError         | Server error             |

Error response format:

```json
{
  "message": "Error description"
}
```

## Supported Audio Formats

- MP3 (`audio/mpeg`)
- M4A/AAC (`audio/mp4`)
- WAV (`audio/x-wav`)
- OGG (`audio/ogg`)
- FLAC (`audio/flac`)

## Rate Limits

The API enforces rate limits. When exceeded, responses include:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
```

The `Retry-After` header indicates seconds to wait before retrying.
