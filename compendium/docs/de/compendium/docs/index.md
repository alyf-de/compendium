---
title: App-interne Dokumentation
translated_from_rev: f837f9e
---

Mit Compendium können Frappe-Apps ihre Benutzerdokumentation als Markdown-Dateien in einem `docs/`-Ordner im App-Paket ausliefern.

## Funktionsweise

- Compendium liest Markdown aus dem `docs/{language}/`-Baum jeder installierten App
- Der Dokumentationsbrowser liegt im Desk unter `/app/docs` (oder unter `/app/docs/{locale}/...` für eine bestimmte Sprache)
- Ordner- und Dateinamen bestimmen den Navigationsbaum
- `index.md` dient als Startseite eines Verzeichnisses
- Optionale Frontmatter-Schlüssel: `title`, `order`, `roles`
- Ohne `roles` ist eine Seite für alle **Desk User** sichtbar
- Später installierte Apps überschreiben Seiten mit gleichem logischem Pfad

Eine Einführung finden Sie unter [Erste Schritte](/app/docs/compendium/docs/getting-started),
und unter [Suche](/app/docs/compendium/docs/search), wie Sie eine Seite über die
Awesome Bar finden.
