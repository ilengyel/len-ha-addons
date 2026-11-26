# ha-addons

This repository contains Home Assistant add-ons for Git-based installation.

## Included add-ons

### `valetudo_proxy`

Opens an existing robot's Valetudo web interface inside Home Assistant through an ingress-only Nginx proxy. The robot address is configurable, no host port is exposed, and existing vacuum/MQTT integrations are unchanged.

### `task_solver`

Task Solver is a Home Assistant add-on that exposes a touch-first task board for shared household chores and repeatable checklists. It is designed for a wall-mounted tablet workflow, so people can quickly open the board, start a task, work through its checklist, record who completed it, and review recent activity.

It provides:

- A board view for creating, renaming, and removing tasks.
- A completion flow that lets a person pick themselves and tick checklist items.
- Recent completion history and a reports screen.
- An optional, persisted dark theme for low-light tablet use.
- Home Assistant add-on packaging with ingress support and direct access on port `8099` when enabled in the add-on config.

## Local development

Run tests from the repository root (Docker must be running for the proxy tests):

```powershell
python -m pytest -q
```

Valetudo Proxy's container tests require a running Docker engine:

```powershell
python -m pytest valetudo_proxy\tests -q
```

## Publishing note

Before adding this repository to Home Assistant from a Git URL, update the placeholder URLs and maintainer details in `repository.yaml` and `task_solver\config.yaml`.

## Browser compatibility requirement

Support for particularly old browsers is a requirement for this add-on, not a nice-to-have. Because the UI is intended for older wall-mounted tablets and iPads, frontend changes should favor broadly supported HTML, CSS, and JavaScript patterns, and avoid introducing dependencies on modern browser-only features unless they are backed by an explicit compatibility strategy.
