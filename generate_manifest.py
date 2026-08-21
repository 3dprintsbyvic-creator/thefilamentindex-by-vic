#!/usr/bin/env python3
"""
generate_manifest.py

Scans libraries/ and writes manifest.json. Run from the repo root:

    python generate_manifest.py --source-name "My PLA Collection" \
                                --base-url https://raw.githubusercontent.com/you/repo/main/libraries

Validation gate — the build FAILS (exit 1, propagated by .githooks/pre-commit)
if any library file:
  - is unparseable JSON
  - has a missing or empty "Filaments" array
  - contains an entry with a missing/malformed uuid (8-4-4-4-12 hex, braces optional)
  - repeats a uuid already used in any library
  - has a non-numeric Transmissivity

Zero library files is NOT an error: an empty manifest is written (the honest
pre-launch state).

Self-test the gate (no files written outside a temp dir):

    python generate_manifest.py --check
"""

import argparse, hashlib, json, pathlib, re, sys, urllib.parse

UUID_HEX = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
UUID_RE = re.compile(r"^(\{" + UUID_HEX + r"\}|" + UUID_HEX + r")$")


def sha256_of_file(path):
    h = hashlib.sha256()
    h.update(path.read_bytes().replace(b'\r\n', b'\n'))
    return h.hexdigest()


def validate_library(path):
    """Validate one library file. Returns (filament_count, valid_uuids, errors)."""
    try:
        data = json.loads(path.read_bytes())
    except Exception as e:
        return 0, [], [f"{path.name}: unparseable JSON ({e})"]

    filaments = data.get("Filaments") if isinstance(data, dict) else None
    if not isinstance(filaments, list) or not filaments:
        return 0, [], [f"{path.name}: missing or empty Filaments array"]

    errors, uuids = [], []
    for i, fil in enumerate(filaments):
        label = f"{path.name} entry {i}"
        if not isinstance(fil, dict):
            errors.append(f"{label}: not a JSON object")
            continue
        uuid_val = fil.get("uuid")
        if not isinstance(uuid_val, str) or not UUID_RE.match(uuid_val):
            errors.append(f"{label}: missing or malformed uuid: {uuid_val!r}")
        else:
            uuids.append(uuid_val)
        td = fil.get("Transmissivity")
        if isinstance(td, bool) or not isinstance(td, (int, float)):
            errors.append(f"{label}: non-numeric Transmissivity: {td!r}")
    return len(filaments), uuids, errors


def scan_libraries(libs_dir, base_url):
    """Scan + validate every *.json in libs_dir. Returns (manifest_libraries, errors)."""
    base_url = base_url.rstrip("/")
    libraries, errors, seen_uuids = [], [], {}
    for f in sorted(libs_dir.glob("*.json")):
        count, uuids, file_errors = validate_library(f)
        errors.extend(file_errors)
        for u in uuids:
            key = u.strip("{}").lower()
            if key in seen_uuids:
                errors.append(f"{f.name}: duplicate uuid {u} (already used in {seen_uuids[key]})")
            else:
                seen_uuids[key] = f.name
        libraries.append({
            "name":           f.stem,
            "filename":       f.name,
            "category":       "community",
            "url":            f"{base_url}/{urllib.parse.quote(f.name)}",
            "sha256":         sha256_of_file(f),
            "filament_count": count,
        })
    return libraries, errors


def self_test():
    """Prove each validation failure class trips the gate. Exit 0 only if all pass."""
    import tempfile, uuid as uuid_mod

    def entry(**overrides):
        e = {
            "Brand": "TestBrand", "Color": "#000000", "Name": "Test",
            "Owned": False, "Transmissivity": 4.0, "Type": "PLA",
            "uuid": "{" + str(uuid_mod.uuid4()) + "}",
        }
        e.update(overrides)
        return e

    shared = "{" + str(uuid_mod.uuid4()) + "}"
    cases = [
        # (name, {filename: raw file content}, expect_errors)
        ("unparseable-json",           {"a.json": '{"Filaments": ['},                                   True),
        ("empty-filaments-array",      {"a.json": '{"Filaments": []}'},                                 True),
        ("missing-filaments-key",      {"a.json": '{}'},                                                True),
        ("malformed-uuid",             {"a.json": json.dumps({"Filaments": [entry(uuid="not-a-uuid")]})}, True),
        ("missing-uuid",               {"a.json": json.dumps({"Filaments": [{k: v for k, v in entry().items() if k != "uuid"}]})}, True),
        ("duplicate-uuids-across-libs", {"a.json": json.dumps({"Filaments": [entry(uuid=shared)]}),
                                        "b.json": json.dumps({"Filaments": [entry(uuid=shared)]})},     True),
        ("non-numeric-transmissivity", {"a.json": json.dumps({"Filaments": [entry(Transmissivity="4.8")]})}, True),
        ("valid-library",              {"a.json": json.dumps({"Filaments": [entry()]})},                False),
        ("zero-libraries",             {},                                                              False),
    ]

    failed = 0
    for name, files, expect_errors in cases:
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            for fname, content in files.items():
                (d / fname).write_text(content, encoding="utf-8")
            _, errors = scan_libraries(d, "https://example.com/libraries")
            tripped = bool(errors)
            ok = tripped == expect_errors
            verdict = "PASS" if ok else "FAIL"
            expectation = "gate trips" if expect_errors else "gate clean"
            print(f"  [{verdict}] {name:30s} expected {expectation}, errors: {errors or 'none'}")
            if not ok:
                failed += 1

    if failed:
        print(f"\nSELF-TEST FAILED: {failed} case(s) did not behave as expected.", file=sys.stderr)
        sys.exit(1)
    print(f"\nSelf-test passed: all {len(cases)} cases behaved as expected.")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-name")
    parser.add_argument("--base-url")
    parser.add_argument("--dir",  default="libraries")
    parser.add_argument("--out",  default="manifest.json")
    parser.add_argument("--check", action="store_true",
                        help="run the validation-gate self-test and exit (writes nothing)")
    args = parser.parse_args()

    if args.check:
        self_test()

    if not args.source_name or not args.base_url:
        parser.error("--source-name and --base-url are required (unless running --check)")

    libs_dir = pathlib.Path(args.dir)
    if not libs_dir.is_dir():
        print(f"ERROR: directory not found: {libs_dir}", file=sys.stderr)
        sys.exit(1)

    libraries, errors = scan_libraries(libs_dir, args.base_url)

    if errors:
        print("VALIDATION FAILED — manifest NOT written:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    for lib in libraries:
        print(f"  {lib['filename']:50s}  {lib['filament_count']:4d} filaments")
    if not libraries:
        print(f"NOTE: no .json files in {libs_dir}/ — writing an empty manifest (pre-launch state).")

    # version=1 matches the schema used by HueForge's own vendor manifest at
    # thehueforge/hueforge-version/filament_libraries.json. Without it, the 0.9.4
    # client may route the manifest through a legacy/no-override code path.
    manifest = {"version": 1, "source_name": args.source_name, "libraries": libraries}
    out_path = pathlib.Path(args.out)
    out_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {len(libraries)} entries to {out_path}")

if __name__ == "__main__":
    main()
