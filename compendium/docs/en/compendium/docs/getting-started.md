---
title: Getting Started
order: 1
roles:
  - System Manager
---

Open **Compendium** from the Desk Help menu or navigate to `/app/docs`.

Each page is discovered at runtime from installed apps. Restrict a page to specific roles with frontmatter:

```yaml
---
title: Sales Guide
roles:
  - Sales User
---
```

Users need any one of the listed roles to see the page in the tree and open it directly.
