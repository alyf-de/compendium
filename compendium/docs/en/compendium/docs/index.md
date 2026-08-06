---
title: In-app documentation
order: 0
roles:
  - System Manager
---


# In-app documentation

Compendium lets Frappe apps ship user documentation as Markdown files under a `docs/` folder in the app package.

## How it works

- Compendium discovers Markdown from every installed app's `docs/{language}/` tree
- Open the docs browser at `/app/docs` in Desk (or `/app/docs/{locale}/...` for a specific language)
- Folders and file names define the navigation tree
- Use `index.md` for a directory landing page
- Optional frontmatter keys: `title`, `order`, `roles`
- Omit `roles` to allow all **Desk User** accounts
- Later installed apps override pages at the same logical path

See [Getting Started](/app/docs/en/compendium/docs/getting-started) for a walkthrough.
