# Offene Aufgaben

## 🖥️ CLI Tool verbessern

- [ ] Optisch verschönern
- [ ] Alles konsequent auf Deutsch (später Sprachauswahl für Englisch)
- [ ] Komplette Navigation im CLI
  - Menü mit Pfeiltasten statt manuelle Eingabe
  - User muss sich keine IDs oder Namen merken
  - Direkt in der CLI die Dateien für den Upload bequem über Finder/Explorer auswählen anstatt kompliziert mit Pfaden hantieren zu müssen.
  - Beispiel: "Tonies anzeigen" → Liste erscheint → Navigation mit Pfeiltasten → Enter → Optionen
- [ ] Debug-Modus (`--debug` Flag)
- [ ] Upload-Fortschritt mit Progress-Bar (tqdm)
- [ ] Langfristig eventuell die CLI Oberfläche durch eine ordentliche Desktop App/local Browser App mit richtiger UI ablösen

## ⚙️ Technische Verbesserungen

- [ ] Token-Refresh bei Ablauf (KRITISCH - Token läuft nach ~1h ab)
- [ ] Retry-Logic mit exponential backoff
- [ ] Rate-Limit Handling mit `Retry-After` Header
- [ ] Async-Support (aiohttp/httpx für parallele Uploads)
- [ ] Timeout-Handling verbessern

## 🔄 Workflows einrichten

- [ ] Terminierte Workflows
  - Muss das Terminal dafür dauerhaft offen sein?
  - Docker für Homelabber anbieten?
- [ ] Manuell ausführbare Workflows
  - Einmal einrichten: Tonie A bekommt Shuffle, Tonie B lädt neue Geschichte aus Ordner X
  - Dann einfacher Befehl im CLI und alles wird ausgeführt

## 🧪 Tests erweitern

- [ ] Test-Fix für macOS `$USERNAME` Konflikt
- [ ] Token-Ablauf Tests
- [ ] File-Upload Edge Cases (große Dateien, leere Dateien)
- [ ] Integration Tests mit echten API-Responses
- [ ] Network-Error Tests (Timeout, DNS, SSL)
