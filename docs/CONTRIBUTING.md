# Contributing

Thank you for your interest in contributing to the Tonie API project!

## Development Setup

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management
- Git

### Installation

```bash
# Install Poetry (macOS)
brew install pipx
pipx install poetry

# Add to PATH (add to ~/.zshrc or ~/.bashrc)
export PATH="$HOME/.local/bin:$PATH"

# Clone the repository
git clone https://github.com/Julschik/toniebox-api.git
cd toniebox-api

# Install dependencies
poetry install

# Install pre-commit hooks
pre-commit install
```

### Environment Variables

| Variable         | Description                          |
| ---------------- | ------------------------------------ |
| `TONIE_USERNAME` | Tonie Cloud email (for tests/CLI)    |
| `TONIE_PASSWORD` | Tonie Cloud password (for tests/CLI) |

Credentials can also be stored in `.env` or `~/.config/tonie-api/credentials`.

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

## Development Commands

```bash
# Run all tests with coverage
poetry run pytest

# Run a single test file
poetry run pytest tests/test_models.py

# Run a specific test
poetry run pytest tests/test_models.py::test_user_model

# Stop at first failure
poetry run pytest -x

# Run linting (all pre-commit hooks)
pre-commit run -a

# Test CLI locally
poetry run tonie --help
```

## Code Style

This project uses strict linting with [ruff](https://github.com/astral-sh/ruff):

- **Line length:** 120 characters
- **Docstrings:** Google-style convention
- **Type hints:** Required (except for `__init__` return types)
- **Rules:** `select = ["ALL"]` (most ruff rules enabled)

Pre-commit hooks will automatically check your code before each commit.

## Terminology

This tool supports **any audio files** (music, audiobooks, podcasts, voice memos, etc.). Always use generic terms in documentation and UI text:

| ❌ Don't use | ✅ Use instead |
|--------------|----------------|
| audiobook(s) | audio file(s) |
| Hörbuch/Hörbücher | Audiodatei(en) |

**Exception:** When explicitly listing multiple types (e.g. "audiobooks and music" / "Hörbücher und Musik"), that's correct.

## Security Rules

**CRITICAL:** These rules must be followed for all code changes. See [TRUST.md](../TRUST.md) for user-facing security documentation.

### Credentials & Tokens

- ✅ Store credentials only in `~/.config/tonie-api/credentials`
- ✅ Use file permissions `0o600` (owner read/write only)
- ✅ Keep OAuth tokens in memory only, **never persist**
- ✅ Environment variables: `TONIE_USERNAME`, `TONIE_PASSWORD` (not `USERNAME`/`PASSWORD` due to system conflicts)
- ❌ Never log credentials, tokens, or email addresses

### Network Communication

- ✅ Use HTTPS only
- ✅ Only communicate with official Tonie endpoints:
  - `login.tonies.com` (OAuth)
  - `api.tonie.cloud` (API)
  - S3 URLs returned by the API (uploads)
- ❌ No third-party services or CDNs
- ❌ No telemetry, analytics, or tracking

### Critical Files

Extra care required when modifying:

| File | Critical Area |
|------|---------------|
| `session.py` | Token handling, OAuth flow |
| `api.py` | S3 upload, API requests |
| `cli/commands.py` | Credential storage (`login`/`logout`) |

### Error Handling

- ❌ Never include sensitive data in error messages or exceptions
- ✅ Use generic messages for auth failures ("Authentication failed")

## Commit Message Format

This project follows [Conventional Commits](https://www.conventionalcommits.org):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type       | Description                |
| ---------- | -------------------------- |
| `feat`     | New feature                |
| `fix`      | Bug fix                    |
| `docs`     | Documentation only         |
| `style`    | Formatting, no code change |
| `refactor` | Code restructuring         |
| `test`     | Adding/updating tests      |
| `chore`    | Maintenance tasks          |

### Examples

```
feat(cli): add upload progress bar
fix(api): handle token expiration correctly
docs(readme): add troubleshooting section
test(models): add edge case tests for Chapter
```

Commitlint validates messages via pre-commit hook.

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Make your changes
4. Run tests: `poetry run pytest`
5. Run linting: `pre-commit run -a`
6. Commit with conventional commit message
7. Push and create a Pull Request

## Project Structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed project structure and data flow.

## Testing

Tests are in `tests/` and use:

- **pytest** as test framework
- **responses** for mocking HTTP requests
- **coverage** for code coverage reporting

Current coverage: 77% with 79 tests.

## Questions?

Open an issue on GitHub if you have questions or need help.
