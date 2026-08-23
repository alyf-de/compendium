---
title: Suche
translated_from_rev: f837f9e
---

Tippen Sie in die Awesome Bar am oberen Rand des Desk, um die Dokumentation zu
durchsuchen. Die Treffer erscheinen zusammen mit den übrigen Ergebnissen der
Awesome Bar. Wählen Sie einen Treffer aus, um die Seite zu öffnen.

## Was Compendium durchsucht

Compendium durchsucht den Titel, den Pfad und den gesamten Text jeder Seite.
Dazu gehören Überschriften, Fließtext, Tabellen, Codeblöcke und der Alternativtext
von Bildern. Linkziele werden nicht durchsucht, denn der Leser sieht sie nicht.

Compendium durchsucht die Seiten so, wie Sie sie lesen. Gibt es eine Seite nicht
in Ihrer Sprache, durchsucht Compendium die Fassung, die Sie stattdessen erhalten.

## Wie eine Suchanfrage trifft

- Ein Wort trifft ab seinem Anfang. `migr` findet eine Seite über Migration.
- Eine Anfrage aus mehreren Wörtern trifft eine Seite, die alle enthält.
- Akzente werden ignoriert. `ubersicht` findet `Übersicht`.
- Die Wortform muss übereinstimmen. `Migrationen` findet keine Seite, die
  `Migration` schreibt.

Angezeigt werden die besten 20 Treffer, der beste zuerst. Ein Treffer im Titel
wird höher bewertet als ein Treffer im Text. Unter jedem Ergebnis zeigt
Compendium die Stelle der Seite, die den Treffer enthält.

## Berechtigungen

Die Ergebnisse enthalten nur Seiten, die Sie öffnen dürfen. Eine über `roles`
eingeschränkte Seite bleibt für alle anderen Benutzer verborgen.

> [!NOTE]
> Der Index erneuert sich, sobald sich eine Markdown-Datei ändert. Suchen Sie
> nach dem Bearbeiten einer Seite erneut, um den neuen Inhalt zu sehen. Ein
> Neustart ist nicht nötig.
