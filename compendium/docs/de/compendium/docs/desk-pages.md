---
title: Seiten in Desk schreiben
translated_from_rev: 282363b
---

Neben den Seiten, die Apps mitbringen, können Sie eigene Seiten in Desk
schreiben, die in der Datenbank Ihrer Site gespeichert werden. Klicken Sie unten
in der Seitenleiste der Dokumentation auf **Neue Seite**.
Sie benötigen die Rolle **Compendium Contributor** oder **System Manager**.

## Pfad

Der Pfad wird aus der Bezeichnung gefüllt, z. B. wird `Erste Schritte` zu
`erste-schritte`. Mit Schrägstrichen legen Sie die Seite in einen Ordner, z. B.
`wiki/einarbeitung`. Pro Sprache gibt es nur eine Seite je Pfad.

Eine Seite mit demselben Pfad wie die Seite einer App ersetzt diese auf dieser
Site, zum Beispiel um eine Anleitung zu korrigieren, die nicht zu Ihrer
Einrichtung passt.

> [!WARNING]
> Solange Ihre Seite sie ersetzt, werden spätere Updates der App-Seite nicht
> angezeigt. Löschen Sie Ihre Seite oder entfernen Sie den Haken bei
> **Veröffentlicht**, um wieder die Seite der App zu zeigen.

## Übersetzungen

Eine Seite mit demselben Pfad in einer anderen Sprache ist eine Übersetzung.
Sie übernimmt **Sortierung** und **Rollen** von der Seite in der Hauptsprache –
Englisch, wo es sie gibt – und ignoriert ihre eigenen. Legen Sie diese auf der
Hauptseite fest.

## Bilder

Sie können Anhänge in Ihre Seite einbetten, wenn sie öffentlich sind oder an der
**Compendium Page** hängen. Andere private Dateien zeigt Compendium nicht an,
damit Berechtigungen nicht umgangen werden.

Wenn Sie ein Bild in den Editor ziehen, wird das Markdown automatisch eingefügt.
Jede andere Datei hängen Sie über **Anhänge** in der Seitenleiste des Formulars
an und verlinken ihre URL:

```md
![Lagerplan](/private/files/lagerplan.png)

[Preisliste (PDF)](/private/files/preisliste.pdf)

![Firmenlogo](/files/logo.png)
```
