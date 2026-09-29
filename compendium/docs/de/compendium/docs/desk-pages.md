---
title: Seiten in Desk schreiben
translated_from_rev: 282363b
---

Neben den Seiten, die Apps mitbringen, können Sie eigene Seiten in Desk
schreiben, die in der Datenbank Ihrer Site gespeichert werden.
Die Schaltflächen in der Dokumentation sehen Sie mit der Rolle
**Compendium Contributor**. Ein **System Manager** kann Seiten auch in der Liste
**Compendium Page** anlegen.

## Seite hinzufügen

Klicken Sie unten in der Seitenleiste der Dokumentation auf
**+ Neue Seite hinzufügen**.

Um eine Seite unter einer Gruppe oder einer Seite anzulegen, zeigen Sie in der
Seitenleiste mit der Maus darauf und klicken Sie auf **+**. Der Pfad der neuen
Seite beginnt mit dem Pfad der Gruppe.

## Gruppen und Indexseiten

Eine Seite mit Unterseiten ist eine Gruppe. Die Seite selbst ist die Indexseite
der Gruppe. Um eine neue Gruppe anzulegen, fügen Sie unter einer bestehenden
Seite eine Seite hinzu.

Eine Gruppe ohne Indexseite zeigt eine Liste ihrer Seiten. Um die Indexseite zu
schreiben, öffnen Sie die Gruppe und klicken Sie unten auf der Seite auf
**Bearbeiten**.

## Pfad

Der Pfad wird aus der Bezeichnung gefüllt, z. B. wird `Erste Schritte` zu
`erste-schritte`. Mit Schrägstrichen legen Sie die Seite in einen Ordner, z. B.
`wiki/einarbeitung`. Pro Sprache gibt es nur eine Seite je Pfad.

Eine Seite mit demselben Pfad wie die Seite einer App ersetzt diese auf dieser
Site, zum Beispiel um eine Anleitung zu korrigieren, die nicht zu Ihrer
Einrichtung passt.

So ersetzen Sie die Seite einer App:

1. Öffnen Sie die Seite und klicken Sie unten auf der Seite auf **Bearbeiten**.
2. Klicken Sie auf **Mit Compendium Page überschreiben**. Ein neues Formular
   öffnet sich mit Inhalt, Pfad und Rollen der App-Seite.
3. Ändern Sie den Inhalt und speichern Sie.

Hat die App ein GitHub-Repository, bietet derselbe Dialog auch
**Auf GitHub bearbeiten**. Damit ändern Sie die Seite für alle Sites.

> [!NOTE]
> Bilder mit relativen Pfaden in der App-Seite werden in Ihrer Kopie nicht
> angezeigt. Hängen Sie die Bilder an Ihre Seite an und ändern Sie die Links.

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
