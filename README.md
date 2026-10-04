# Lernraum · Lern-AI-Tutor-Agent

Lokaler SQL-Tutor mit React-PWA, FastAPI, Oracle und SQLite. Der deterministische Prüfer bewertet die SQL-Ergebnisse; die Modell-API unterstützt Erklärungen und Aufgabenentwürfe.

## Start unter Windows

Voraussetzungen: Python 3.11 oder neuer, Node.js 20.19 oder neuer, erreichbare Oracle-Datenbank. Alle Befehle in PowerShell ausführen.

```powershell
# Im Projektordner:
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock
Copy-Item backend\.env.example backend\.env
cd frontend
npm ci
npm run build
cd ..\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Vor dem Backend-Start `backend/.env` bearbeiten. Falls `python` nicht im PATH liegt, den absoluten Pfad zur Python-Installation verwenden. Im Codex-Arbeitsplatz wurde die mitgelieferte Python-Laufzeit verwendet und `.venv` bereits eingerichtet.

Nach dem Build liefert das Backend auch die PWA aus: **http://127.0.0.1:8000**. API-Dokumentation: **http://127.0.0.1:8000/docs**. Backend immer aus `backend` starten, damit `.env` und das Datenverzeichnis richtig aufgelöst werden. Nur einen Uvicorn-Worker verwenden. Nicht auf `0.0.0.0` binden.

Für Frontend-Entwicklung zusätzlich in einem zweiten Terminal:

```powershell
cd frontend
npm run dev
```

Entwicklungsoberfläche: http://127.0.0.1:5173. Der Vite-Proxy leitet `/api` an Port 8000 weiter. PWA/Service-Worker sind nur im Produktionsbuild aktiv.

## Oracle vorbereiten

Ein Administrator stellt eine bereinigte Übungskopie bereit. Der Verbindungsbenutzer benötigt `CREATE SESSION` und **ausschließlich SELECT auf die ausgewählten Tabellen**, keine Schreib-, DDL-, DBA- oder allgemeinen Objekt-/Paketrechte. Die Anwendung legt keine Benutzer oder Tabellen an. Vor dem Pilot müssen tatsächliche Rechte, gegebenenfalls vererbte Rollen und fehlgeschlagene Schreibversuche durch den Administrator geprüft werden.

`ORACLE_DSN` ist zum Beispiel `localhost:1521/FREEPDB1`. Benutzer und Passwort separat setzen. Bei erforderlichem Thick-Modus `ORACLE_CLIENT_DIR` auf einen vorhandenen Oracle Instant Client setzen und das Backend neu starten. Kein automatisches Umschalten nach fehlgeschlagenen Verbindungen. Der Leser kann Tabellen anderer Schemas verwenden; Aufgaben benutzen vollständig qualifizierte Namen, etwa `TRAINING.EMPLOYEES`.

Für JOIN-Aufgaben zwei fachlich passende Tabellen wählen. Die bereinigten Daten sollen NULL-Werte, gleiche Gehälter, Grenzwerte, leere Abteilungen und Eins-zu-viele-Beziehungen enthalten. Der Tutor prüft Ergebnisgleichheit auf den aktuellen Daten innerhalb einer Oracle-Read-only-Transaktion. Das beweist keine allgemeine SQL-Äquivalenz auf beliebigen Daten: Aufgaben zusätzlich auf fachlich vorbereiteten Datenvarianten prüfen.

## Materialien und Aufgaben

1. In **Materialien & Aufgaben** das Oracle-Schema laden, benötigte Tabellen markieren und Freigabe speichern.
2. Textbasierte PDF-, DOCX- oder UTF-8-Markdown-Dateien hochladen. Dateigrenze 20 MB, PDF maximal 500 Seiten; Scans, Verschlüsselung und unlesbare Dateien werden abgelehnt. DOCX-Tabellen werden mit eingelesen.
3. Materialien auswählen, Lernziel und maximal zwei Tabellen zuordnen. Quellen bleiben mit Seiten-/Dokumentangaben gespeichert. Ein Material darf mehrere Lernziele enthalten; zur gezielten Anzeige separate Dokumente pro Lernziel verwenden.
4. Mit konfigurierter Modell-API **20 Entwürfe erzeugen** (zwölf Auswahl/Filter, vier INNER JOIN, vier LEFT JOIN). Ohne API Aufgaben über **Neue Aufgabe** manuell erfassen. Eigene Aufgaben sind erst nach Bereitstellung deiner Materialien und Tabellen möglich; es werden keine erfundenen Aufgaben als dein Lehrstoff vorinstalliert.
5. Jeden Entwurf fachlich prüfen: Aufgabenstellung, Referenz-SQL, drei Hinweise, Quellen und Tabellen. Sortierspalten explizit in der SELECT-Liste aufnehmen. Sortierung/Spaltenaliases nur aktivieren, wenn die Aufgabe sie verlangt.
6. Speichern, Referenz prüfen und veröffentlichen. Veröffentlichung führt die Referenz erneut aus. Änderungen an veröffentlichten Aufgaben erstellen eine neue Entwurfsversion. Bestehende Sitzungen behalten ihre Aufgabenversion.

Das Kapitel unterstützt SELECT, Spaltenaliases, WHERE-Vergleiche, AND/OR, IS NULL/IS NOT NULL, IN-Literale, BETWEEN, LIKE, DISTINCT, ORDER BY sowie INNER/LEFT JOIN mit Gleichheitsbedingungen. Funktionen, Aggregationen, CTEs, Unterabfragen, UNION, Cross-Joins, Datenbanklinks und Schreibbefehle werden abgelehnt. Ungewöhnliche quoted identifiers mit Leerzeichen werden nicht unterstützt.

## Modell-API und Lernablauf

`LLM_BASE_URL`, `LLM_API_KEY` und `LLM_MODEL` konfigurieren einen Chat-Completions-kompatiblen Dienst. Aufgabenentwürfe setzen JSON-Objekt-Ausgabe voraus. Ohne Modell funktionieren SQL-Prüfung, feste Hinweise, Rückblick und Fortschritt weiter. Für Modellaufrufe werden nur ausgewählte Materialauszüge (maximal 14.000 Zeichen), die Aufgabe und benötigte Versuchsinformationen übertragen. Vor Upload eigener Materialien deren externe Verarbeitung freigeben. Zugangsdaten werden nicht im Modellkontext verwendet.

Hinweise müssen explizit angefordert werden. Die Musterlösung wird erst nach **Musterlösung ausdrücklich öffnen** ausgeliefert. Ab diesem Zeitpunkt gelten weitere Versuche der Sitzung als unterstützt. Zwei unterschiedliche Aufgabenlinien ohne Hilfe festigen ein Lernziel; zwei Versionen derselben Aufgabe zählen nicht doppelt. Die generative Tutorantwort ist durch Prompt und SQL-Ausgabefilter eingeschränkt, dennoch müssen fachliche Qualität und mögliche Lösungslecks mit deinem Modell geprüft werden. Sie kann nie den gespeicherten Bewertungsentscheid ändern.

SQL-Anweisungen und persönliche Lerninformationen liegen lokal in `backend/data/tutor.sqlite`; Uploads in `backend/data/uploads`. Für Sicherungen das Backend stoppen und das gesamte Datenverzeichnis kopieren. Neue Uploads sind unveränderliche Materialversionen mit eigener ID; bestehende Materialien werden nicht überschrieben. Für eine geänderte Quelle neu hochladen und neue Aufgabenversionen zuordnen.

Der SQL-Prüfer vergleicht typisierte Multimengen einschließlich Duplikaten. Sortieraufgaben verlangen ORDER BY und die richtige Folge der Referenz-Sortierschlüssel; beliebige Reihenfolge innerhalb gleicher Schlüssel bleibt erlaubt. Jede Query hat zehn Sekunden Laufzeit und maximal 1.000 Zeilen. Fehler und Überschreitungen sind **nicht bewertbar**, niemals korrekt. Maximal eine Ausführung gleichzeitig. Decimal-Werte bleiben während der Bewertung präzise; API-Ergebnisse dienen der Anzeige.

## PWA und Betrieb

Die PWA ist über die Installationsfunktion eines unterstützten Browsers auf localhost installierbar. Sie cached nur Anwendung, Icons und statische Assets. Keine API-Antworten, Uploads, SQL, Chats oder Lernstände im Service-Worker-Cache. Bei Backend-Ausfall bleiben bereits geladene Inhalte und Editorentwurf im laufenden Fenster erhalten; nach vollständigem Offline-Neustart sind dynamische Lerninhalte nicht verfügbar. Kein automatisches Nachsenden. Ein verfügbarer App-Update wird beim nächsten vollständigen Schließen/Öffnen übernommen.

Der Prototyp hat keine Anmeldung. Die Verwaltungsansicht ist lokal zugänglich. Host-/Origin-Prüfung ergänzt die Loopback-Bindung. Schulnetzbetrieb erfordert vorab Authentifizierung, Rollen, TLS und Betriebs-/Datenschutzkonzept. Modelllogs enthalten ausschließlich Laufzeit, Tokenzahl und Fehlertyp, keine Schlüssel, Prompts oder Verbindungsstrings.

## Prüfen

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm run build
npx playwright install chromium
npm run test:e2e
```

Browser-Tests starten einen **isolierten Testserver** mit synthetischen SQLite-Daten und der produktiven SQL-Validierungs-/Vergleichslogik. Das ist kein Oracle-Ersatz im normalen Betrieb. Tests umfassen 20 Aufgaben mit richtigen/falschen Lösungen auf zwei Datenvarianten, SQL-Schutzgrenzen, Uploads, Versionierung, Fortschritt, Modellrückfall, Desktop-/Mobilansicht und Verbindungsabbruch. Falls Chromium vorhanden ist, kann `PLAYWRIGHT_CHROMIUM_EXECUTABLE` auf dessen ausführbare Datei gesetzt werden.

Vor Browser-Tests laufende Entwicklungsserver auf Ports 8000 und 5173 beenden. Die Testdaten werden in einem eigenen temporären Verzeichnis erstellt, nicht im produktiven Datenverzeichnis. `requirements.lock` und `frontend/package-lock.json` halten die geprüften Abhängigkeitsversionen fest.

Vor echtem Einsatz offen: Verbindung zu deiner Oracle-Instanz, Prüfung der tatsächlichen Leserrechte, deine 20 fachlich freigegebenen Aufgaben, Modellqualität/-kosten sowie PWA-Installation in deinem Browser. Ein automatisierter Produktions-PWA-Test prüft zusätzlich Manifest, Service-Worker und Offline-App-Shell; eine echte Browserinstallation bleibt ein manueller Abnahmeschritt.

Technische Referenzen: [python-oracledb](https://python-oracledb.readthedocs.io/en/latest/api_manual/connection.html), [SQLGlot](https://sqlglot.com/sqlglot.html), [Vite PWA](https://vite-pwa-org.netlify.app/guide/).
