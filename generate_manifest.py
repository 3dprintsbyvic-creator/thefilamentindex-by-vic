#!/usr/bin/env python3
"""
generate_manifest.py

Scans libraries/ and writes manifest.json. Run from the repo root:

    python generate_manifest.py --source-name "My PLA Collection" \
                                --base-url https://raw.githubusercontent.com/you/repo/main/libraries
"""

import argparse, hashlib, json, pathlib, sys, urllib.parse

def sha256_of_file(path):
    h = hashlib.sha256()
    h.update(path.read_bytes().replace(b'\r\n', b'\n'))
    return h.hexdigest()

def filament_count(path):
    try:
        return len(json.loads(path.read_bytes()).get("Filaments", []))
    except Exception:
        return 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--base-url",    required=True)
    parser.add_argument("--dir",  default="libraries")
    parser.add_argument("--out",  default="manifest.json")
    args = parser.parse_args()

    libs_dir = pathlib.Path(args.dir)
    if not libs_dir.is_dir():
        print(f"ERROR: directory not found: {libs_dir}", file=sys.stderr)
        sys.exit(1)

    base_url = args.base_url.rstrip("/")
    libraries = []
    for f in sorted(libs_dir.glob("*.json")):
        count = filament_count(f)
        libraries.append({
            "name":           f.stem,
            "filename":       f.name,
            "category":       "community",
            "url":            f"{base_url}/{urllib.parse.quote(f.name)}",
            "sha256":         sha256_of_file(f),
            "filament_count": count,
        })
        print(f"  {f.name:50s}  {count:4d} filaments")

    if not libraries:
        print(f"No .json files in {libs_dir}/", file=sys.stderr)
        sys.exit(1)

    # version=1 matches the schema used by HueForge's own vendor manifest at
    # thehueforge/hueforge-version/filament_libraries.json. Without it, the 0.9.4
    # client may route the manifest through a legacy/no-override code path.
    manifest = {"version": 1, "source_name": args.source_name, "libraries": libraries}
    out_path = pathlib.Path(args.out)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {len(libraries)} entries to {out_path}")

if __name__ == "__main__":
    main()
