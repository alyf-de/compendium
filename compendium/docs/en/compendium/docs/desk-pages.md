---
title: Writing Pages in Desk
order: 3
roles:
  - System Manager
  - Compendium Contributor
---

Besides the pages that apps ship, you can write your own pages in Desk, saved in the Database of your Site.
You need the **Compendium Contributor** role to see the buttons in the documentation.
A **System Manager** can also add pages in the **Compendium Page** list.

## Add a page

Click **+ Add new Page** at the bottom of the documentation sidebar.

To add a page below a group or a page, move the pointer over it in the sidebar
and click **+**. The path of the new page starts with the path of the group.

## Groups and index pages

A page with pages below it is a group. The page itself is the index page of
the group. To start a new group, add a page below an existing page.

A group without an index page shows a list of its pages. To write the index
page, open the group and click **Edit** at the bottom of the page.

## Path

The path is filled from the title, e.g. `Getting Started` becomes
`getting-started`. Use slashes to place the page in a folder, e.g.
`wiki/onboarding`. Each language can hold only one page per path.

A page at the same path as an app's page replaces it on this site, for example
to correct instructions that do not fit your setup.

To replace an app's page:

1. Open the page and click **Edit** at the bottom of the page.
2. Click **Override with Compendium Page**. A new form opens with the content,
   path and roles of the app's page.
3. Change the content and save.

If the app has a GitHub repository, the same dialog also has **Edit on GitHub**.
Use it to change the page for all sites.

> [!NOTE]
> Images with relative paths in the app's page do not show in your copy.
> Attach the images to your page and change the links.

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
