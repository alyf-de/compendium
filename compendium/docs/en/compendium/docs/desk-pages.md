---
title: Writing Pages in Desk
order: 3
roles:
  - System Manager
  - Compendium Contributor
---

Besides the pages that apps ship, you can write your own pages in Desk, saved in the Database of your Site. Click **New Page** at the bottom of the documentation sidebar.
You need the **Compendium Contributor** or **System Manager** role.

## Path

The path is filled from the title, e.g. `Getting Started` becomes
`getting-started`. Use slashes to place the page in a folder, e.g.
`wiki/onboarding`. Each language can hold only one page per path.

A page at the same path as an app's page replaces it on this site, for example
to correct instructions that do not fit your setup.

> [!WARNING]
> While your page replaces it, later updates of the app's page are not shown.
> Delete your page or clear **Published** to show the app's page again.

## Translations

A page with the same path in another language is a translation. It takes
**Sort Order** and **Roles** from the page in the main language — English
wherever one exists — and ignores its own. Set them on the main page.

## Images

You can embed attachments in your own page if they are public or attached to the **Compendium Page**. Other private files are not rendered in Compendium to avoid Permission Bypassing.

Dragging an image into the editor inserts the Markdown for you. For any other
file, attach it with **Attachments** in the form sidebar and link to its URL:

```md
![Warehouse layout](/private/files/warehouse-layout.png)

[Price list (PDF)](/private/files/price-list.pdf)

![Company logo](/files/logo.png)
```
