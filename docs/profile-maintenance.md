# Profile Maintenance

This document explains how the public profile repository is maintained.

## What Lives Here

- `README.md` drives the profile landing page
- `assets/hero/` holds three hero options (`hero-facade.svg` is the one in use); `assets/stack.svg` is the tech-stack image
- `assets/src/` holds the generators for those images and the Simple Icons paths they use
- `site/` is the static project site (see `site/README.md`) and `.github/workflows/pages.yml` builds it
- `docs/mcp-audit.md` records the AEC Model Bridge metadata audit
- `assets/bim-hero.svg`, `assets/bim-automation.svg` and `assets/tech-stack.svg` are older images that are no longer used

## Update Workflow

1. Edit the generator in `assets/src/` and run it to change an image: `python3 assets/src/make_hero.py` or `make_stack.py`. Do not edit the SVG output by hand.
2. Keep essential text (name, role, links) in `README.md`, not inside images.
3. Check that every image path and link in the README resolves before merging.
4. Project facts such as version, tool count and Revit versions come from the bridge repository. Update them there, then rebuild the site; do not retype them here. The README shows version 1.3.3 and "Revit 2024-2027" as static text, so recheck both after a release.

## Content Principles

- Prefer clear, durable wording over trend-driven copy.
- State maturity honestly: say beta, in progress or planned where that is true.
- Add a technology to the stack only when your work or a repository shows it.
- Avoid decorative assets unless they support the profile narrative.
