# ha-addons

This repository is a Home Assistant add-on repository prepared for Git-based installation. The current add-on lives in `task_solver\`.

## Included add-ons

### `task_solver`

Task Solver is a Home Assistant add-on that exposes a touch-first task board for shared household chores and repeatable checklists. It is designed for a wall-mounted tablet workflow, so people can quickly open the board, start a task, work through its checklist, record who completed it, and review recent activity.

It provides:

- A board view for creating, renaming, and removing tasks.
- A completion flow that lets a person pick themselves and tick checklist items.
- Recent completion history and a reports screen.
- Home Assistant add-on packaging with ingress support and direct access on port `8099` when enabled in the add-on config.

## Local development

Run tests from the repository root:

```powershell
python -m pytest -q
```

## Publishing note

Before adding this repository to Home Assistant from a Git URL, update the placeholder URLs and maintainer details in `repository.yaml` and `task_solver\config.yaml`.

## Browser compatibility requirement

Support for particularly old browsers is a requirement for this add-on, not a nice-to-have. Because the UI is intended for older wall-mounted tablets and iPads, frontend changes should favor broadly supported HTML, CSS, and JavaScript patterns, and avoid introducing dependencies on modern browser-only features unless they are backed by an explicit compatibility strategy.
