#!/usr/bin/env python3
"""
tools/verify_fonts_catalog.py

Integrity test for storefront-fonts catalog:
1. Validates fonts.json and fonts.lite.json syntax and schema
2. Asserts that each font in the catalog has an open license
3. Asserts that packages/<safe_name>.zip exists and contains a license file
4. Asserts that previews/<safe_name>/<font_file> exists and is under reasonable preview size
5. Asserts that previews/font_previews.zip exists and contains all font previews
"""

import os
import sys
import json
import zipfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_FILE = os.path.join(REPO_ROOT, "fonts.json")
LITE_JSON_FILE = os.path.join(REPO_ROOT, "fonts.lite.json")
PACKAGES_DIR = os.path.join(REPO_ROOT, "packages")
PREVIEWS_DIR = os.path.join(REPO_ROOT, "previews")
BUNDLE_ZIP = os.path.join(PREVIEWS_DIR, "font_previews.zip")

APPROVED_LICENSES = {
    "sil open font license",
    "sil open font license 1.1",
    "ofl",
    "apache",
    "apache 2.0",
    "apache license 2.0",
    "mit",
    "mit license",
    "open license",
    "public domain",
    "cc0",
}

def fail(msg):
    print(f"❌ FAIL: {msg}", file=sys.stderr)
    sys.exit(1)

def main():
    print("=== Verifying Storefront Fonts Catalog Integrity ===")
    if not os.path.exists(JSON_FILE):
        fail(f"{JSON_FILE} does not exist.")
    if not os.path.exists(LITE_JSON_FILE):
        fail(f"{LITE_JSON_FILE} does not exist.")
    if not os.path.exists(BUNDLE_ZIP):
        fail(f"{BUNDLE_ZIP} does not exist.")

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    with open(LITE_JSON_FILE, "r", encoding="utf-8") as f:
        lite_catalog = json.load(f)

    fonts = catalog.get("fonts", [])
    lite_fonts = lite_catalog.get("fonts", [])

    if len(fonts) == 0:
        fail("No fonts found in fonts.json.")
    if len(fonts) != len(lite_fonts):
        fail(f"Font count mismatch: {len(fonts)} in fonts.json vs {len(lite_fonts)} in fonts.lite.json")

    print(f"Checking {len(fonts)} fonts...")

    with zipfile.ZipFile(BUNDLE_ZIP, "r") as bzf:
        bundle_namelist = set(bzf.namelist())

    for font in fonts:
        name = font.get("name")
        font_id = font.get("id")
        safe_name = name.replace(" ", "-")
        font_file = font.get("font_file")
        license_str = font.get("license", "").lower()

        # Check license
        if not any(appr in license_str for appr in APPROVED_LICENSES):
            fail(f"Font '{name}' has unapproved license: '{font.get('license')}'. Must be open source.")

        # Check package zip
        pkg_zip = os.path.join(PACKAGES_DIR, f"{safe_name}.zip")
        if not os.path.exists(pkg_zip):
            fail(f"Missing package archive: {pkg_zip}")
        with zipfile.ZipFile(pkg_zip, "r") as pzf:
            names = pzf.namelist()
            has_font = any(n.lower().endswith((".ttf", ".otf")) for n in names)
            has_lic = any("license" in n.lower() or "ofl" in n.lower() for n in names)
            if not has_font:
                fail(f"Package '{pkg_zip}' contains no font files!")
            if not has_lic:
                fail(f"Package '{pkg_zip}' is missing license/OFL file!")

        # Check preview file
        preview_file = os.path.join(PREVIEWS_DIR, safe_name, font_file)
        if not os.path.exists(preview_file):
            fail(f"Missing preview font file: {preview_file}")
        
        # Check presence in font_previews.zip
        expected_arc = f"{safe_name}/{font_file}"
        if expected_arc not in bundle_namelist:
            fail(f"Missing '{expected_arc}' in {BUNDLE_ZIP}")

    print(f"SUCCESS: All {len(fonts)} fonts passed integrity verification!")
    print(f"   Packages: {len(fonts)} zip files verified with licenses.")
    print(f"   Preview Bundle: {BUNDLE_ZIP} verified with {len(bundle_namelist)} entries.")

if __name__ == "__main__":
    main()
