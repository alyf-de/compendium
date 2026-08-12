---
title: Erste Schritte
translated_from_rev: 82e1353
---

# Erste Schritte


Öffnen Sie **Dokumentation** im Hilfe-Menü des Desk oder rufen Sie `/app/docs` auf.

Jede Seite wird zur Laufzeit aus den installierten Apps ermittelt. Über das Frontmatter lässt sich eine Seite auf bestimmte Rollen einschränken:

```yaml
---
title: Sales Guide
roles:
  - Sales User
---
```

Benutzer benötigen eine der aufgeführten Rollen, um die Seite im Navigationsbaum zu sehen und direkt zu öffnen.
