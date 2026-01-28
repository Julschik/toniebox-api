# Vertrauen & Sicherheit | Trust & Security

<details open>
<summary><h2>🇩🇪 Deutsch</h2></summary>

### Wie funktioniert dieses Tool?

Dieses Tool ist eine Einbahnstraße:

```
GitHub → Dein PC → Tonie Cloud API
```

- ✅ Keine Telemetrie
- ✅ Keine Tracking-Dienste
- ✅ Keine Drittanbieter-Verbindungen
- ✅ Open Source (MIT Lizenz)

### Wo werden deine Daten gespeichert?

| Daten | Speicherort | Zugriff |
|:------|:------------|:--------|
| E-Mail & Passwort | `~/.config/tonie-api/credentials` | Nur du (0o600) |
| OAuth-Token | Nur im Arbeitsspeicher | Temporär |
| Audiodateien | Tonie Cloud (tonies.de) | Dein Account |

### Kritische Code-Stellen zur Prüfung

| Datei | Funktion |
|:------|:---------|
| `src/tonie_api/session.py` | Token-Anfrage an login.tonies.com |
| `src/tonie_api/api.py` | Datei-Upload zu S3 |
| `src/tonie_api/cli/commands.py` | Credential-Speicherung |

### Haftungsausschluss

> ⚠️ **Inoffizieller Client** - Keine Verbindung zu tonies® oder Boxine GmbH.

Nutzung auf eigene Gefahr. Der Autor übernimmt keine Haftung für:
- Datenverlust
- Account-Sperrungen
- Schäden an Tonies oder Tonieboxen
- Sonstige Schäden durch Nutzung dieser Software

**Lies den Quellcode, bevor du diesem Tool deine Zugangsdaten anvertraust.**

</details>

---

<details>
<summary><h2>🇬🇧 English</h2></summary>

### How does this tool work?

This tool is a one-way street:

```
GitHub → Your PC → Tonie Cloud API
```

- ✅ No telemetry
- ✅ No tracking services
- ✅ No third-party connections
- ✅ Open Source (MIT License)

### Where is your data stored?

| Data | Location | Access |
|:-----|:---------|:-------|
| Email & Password | `~/.config/tonie-api/credentials` | You only (0o600) |
| OAuth Token | Memory only | Temporary |
| Audiofiles | Tonie Cloud (tonies.de) | Your account |

### Critical Code Sections for Review

| File | Function |
|:-----|:---------|
| `src/tonie_api/session.py` | Token request to login.tonies.com |
| `src/tonie_api/api.py` | File upload to S3 |
| `src/tonie_api/cli/commands.py` | Credential storage |

### Disclaimer

> ⚠️ **Unofficial client** - No affiliation with tonies® or Boxine GmbH.

Use at your own risk. The author assumes no liability for:
- Data loss
- Account suspensions
- Damage to Tonies or Tonieboxes
- Any other damages from using this software

**Read the source code before trusting this tool with your credentials.**

</details>
