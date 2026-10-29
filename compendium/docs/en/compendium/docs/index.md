---
title: In-app documentation
order: 0
roles:
  - System Manager
---

Compendium lets Frappe apps ship user documentation as Markdown files under a `docs/` folder in the app package.

## How it works

- Compendium discovers Markdown from every installed app's `docs/{language}/` tree
- Open the docs browser at `/desk/docs` in Desk (or `/desk/docs/{locale}/...` for a specific language)
- Folders and file names define the navigation tree
- Use `index.md` for a directory landing page
- Optional frontmatter keys: `title`, `order`, `roles`
- Omit `roles` to allow all **Desk User** accounts
- Later installed apps override pages at the same logical path
- Pages written in Desk come on top of all apps — see [Writing Pages in Desk](/desk/docs/compendium/docs/desk-pages)

See [Getting Started](/desk/docs/compendium/docs/getting-started) for a walkthrough,
or [Search](/desk/docs/compendium/docs/search) to find a page from the Awesome Bar.
