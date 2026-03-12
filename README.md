# Home Assistant — Educational Smart Room

This repository contains the Simulation Manager integration, Lovelace custom card, and supporting scripts used to run an educational Smart Room on Home Assistant OS (HAOS). It is designed for scalability, maintainability, and safe deployment on HA Green.

**Core ideas:** zero hardcoding, HA-first configuration, and clear separation between integrations, UI, and deploy scripts.

## Features

- Simulation Manager custom integration (`custom_components/simulation_manager`) — handles periods, measurements and services.
- Lovelace custom card `simulation-period-card` (JS + CSS) under `www/simulation-period-card` for teachers to view and add measurements.
- Deployment helpers and CLI scripts in `scripts/` to push resources to Home Assistant.

## Quick install (for Home Assistant users)

1. Copy repository files to your HA config folder (or use the Studio Code Server / Samba add-on). Ensure these paths exist:
   - [www/simulation-period-card/simulation-period-card.js](www/simulation-period-card/simulation-period-card.js)
   - [www/simulation-period-card/simulation-period-card.css](www/simulation-period-card/simulation-period-card.css)
   - [custom_components/simulation_manager](custom_components/simulation_manager)
2. In Lovelace resources add the card JS resource (only the JS is required as a resource):

```yaml
resources:
  - url: /local/simulation-period-card/simulation-period-card.js
    type: module
```

3. Clear browser cache (or add a `?v=` query to the resource URL) and add the card to a dashboard using `type: custom:simulation-period-card`.

## Development notes

- Developer integration code: [custom_components/simulation_manager](custom_components/simulation_manager)
- Lovelace sources and static assets: [www/simulation-period-card](www/simulation-period-card)
- Utility scripts for deployment and scanning: [`scripts/`](scripts)
- Docs for audiences: [docs/README_DEVELOPERS.md](docs/README_DEVELOPERS.md), [docs/README_ADMINS.md](docs/README_ADMINS.md), [docs/README_TEACHERS.md](docs/README_TEACHERS.md)

## Deploying changes to Home Assistant

- Use the provided deployment scripts in `scripts/` (for example `deploy_simulation_manager.py` or `push_dashboard.py`) or copy files to HA `www/` and `custom_components/` using your preferred approved method (Studio Code Server, Samba, or the File Editor add-on).
- After updating `custom_components`, restart the Home Assistant Core integration or reboot the host if required by the integration.

## Contributing

- Follow the project's coding standards: use dynamic configuration (no hardcoded secrets), Jinja2 templates for HA YAML, and PEP 8 for Python in `custom_components`.
- Open an issue or PR with clear description, reproduction steps, and tests where possible.

## Useful links

- Dynamic entity scanner: [docs/dynamic_entity_scanner.md](docs/dynamic_entity_scanner.md)

## License

This repository does not include a license file. Add a LICENSE if you want to publish under an open-source license.

---

If you'd like, I can add a short `README_ADMINS.md` deploy checklist, a `Makefile` or a small `deploy` script to copy the card assets to Home Assistant automatically. Want me to add one now?
