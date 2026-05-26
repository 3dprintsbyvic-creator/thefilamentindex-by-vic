# The Filament Index by Vic

A community filament library for [HueForge](https://thehueforge.com/) 0.9.4+, published from [The Filament Index](https://3dprintsbyvic.com/filaments) — Vic's growing database of hand-verified Transmission Distance (TD) measurements across the brands HueForge users actually print with.

Every entry in this library is sourced from the live Filament Index on [3dprintsbyvic.com](https://3dprintsbyvic.com/filaments). Subscribers get the same measurements Vic uses in his own prints, refreshed automatically as the Index grows.

## Add this source to HueForge

1. In HueForge, open **Filaments → Manage Community Sources**.
2. Click **+ Add Source**.
3. Paste this manifest URL:
   ```
   https://raw.githubusercontent.com/3dprintsbyvic-creator/thefilamentindex-by-vic/main/manifest.json
   ```
4. Click **OK**. HueForge fetches and verifies the manifest.

Filaments appear in your **Filaments** menu under **Community → The Filament Index by Vic** with a source badge.

**Auto-updates:** HueForge 0.9.4 background-checks registered manifests. Subscribe once and the data stays current as Vic adds + reverifies measurements.

## What's inside

- **Hand-verified TD measurements** for every entry, captured under documented conditions (nozzle temp + size + measurement method recorded against each filament).
- **Coverage today:** Bambu Lab, Polymaker, 3D-Fuel, Overture, Prusa Research, Jessie Premium, Paramount 3D, IIID Max, Numakers, Kexcelled, Sunlu, Protopasta, Copymaster 3D, Fillamentum, eSun, Kingroon, Creality, Hatchbox, JAYO, GEETECH — anything that lands in the Filament Index lands here.
- **Tags for fast filtering** inside HueForge — finish (matte, silk, glossy, translucent), color family, and a `verified-by-3dpbv` marker so you can find Vic's entries quickly.

## Submitting a filament (PR-as-submission lane)

The Filament Index accepts submissions through [the website form](https://3dprintsbyvic.com/filaments) and through pull requests against this repo. PRs work well if you have a batch of carefully-measured filaments — drop them in a `libraries/<your-brand>.json` file and open a PR.

PR review checklist:
- One filament per entry, required fields populated (`Brand`, `Color`, `Name`, `Owned: false`, `Transmissivity`, `Type`, `uuid`).
- Fresh UUIDs — generate with `python -c "import uuid; print('{' + str(uuid.uuid4()) + '}')"`.
- Measurement notes in the PR body (nozzle temp, nozzle size, method — TD1, TD1S, seashell, etc.).
- One PR per brand or batch — easier review.

Vic reviews and merges. Auto-merge isn't on the table — every entry that publishes under this source is something Vic stands behind.

## How the data flows

Base44 Filament Index (data of record) → `scripts/sync_filament_library.py` deterministic export → per-brand JSON files in `libraries/` → pre-commit hook regenerates `manifest.json` → push → HueForge subscribers auto-update.

If a community PR's TD measurement conflicts with the Index, Vic's measurement wins by default (or triggers a re-measurement, his call).

## Conflict priority

When a HueForge user has both this source and HueForge's bundled vendor library registered, the user picks which source wins on overlap. The exact UX is still being characterized — Phase 1a (the first 10–20 filament test slice) is what tells us how it surfaces. README will be updated with the recommendation once we've seen it.

## Repo structure

```
thefilamentindex-by-vic/
├── libraries/                  # Per-brand×material JSON files
├── .githooks/pre-commit        # Auto-regenerates manifest.json on commit
├── generate_manifest.py        # Standalone manifest generator (from template)
├── manifest.json               # Generated index — don't hand-edit
├── .gitattributes              # LF normalization for SHA256 consistency
└── README.md
```

## License

Same license as [HueForge](https://github.com/HueForge/hueforge). License text will be added here before Phase 1b ships the full Index.

## Credits

- **Template:** [thehueforge/hueforge-community-library-example](https://github.com/thehueforge/hueforge-community-library-example) by Steve Hardy (HueForge creator).
- **Filament Index:** [3dprintsbyvic.com/filaments](https://3dprintsbyvic.com/filaments) — Vic's database, free to browse, deep features (Owned / Want / community measurements) live behind the Master Maker tier on [Patreon](https://patreon.com/3DPrintsByVic).
