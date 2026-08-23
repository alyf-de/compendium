---
title: Search
order: 5
roles:
  - System Manager
---

Type in the Awesome Bar at the top of Desk to search the documentation. Results
appear together with the other Awesome Bar results. Select one to open the page.

## What Compendium searches

Compendium searches the title, the path, and the full text of every page. This
includes headings, body text, tables, code blocks, and the alt text of images.
Link targets are not searched, because the reader does not see them.

Compendium searches the pages as you read them. If a page has no version in your
language, Compendium searches the version you get instead.

## How a query matches

- A word matches at its start. `migr` finds a page about migration.
- A query with several words matches a page that contains all of them.
- Accents are ignored. `ubersicht` finds `Übersicht`.
- A word form must match. `migrating` does not find a page that writes `migrate`.

The best 20 matches are shown, best first. A match in the title ranks above a
match in the body. Under each result Compendium shows the part of the page that
contains the match.

## Permissions

The results only contain pages that you are allowed to open. A page that is
restricted with `roles` stays hidden for all other users.

> [!NOTE]
> The index updates itself when a Markdown file changes. After you edit a page,
> search again to see the new content. A restart is not needed.
