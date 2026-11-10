#!/usr/bin/env python3
"""
tools/build_fonts.py

Builds the Storefront Fonts catalog:
1. Packages each full font family into packages/<safe_name>.zip with LICENSE.txt / OFL.txt
2. Subsets each font's regular style with fontTools.subset into previews/<safe_name>/<font_file> (~5-12 KB)
3. Bundles all subsetted preview fonts into previews/font_previews.zip (~150-350 KB)
4. Fetches live community ratings and download metrics from Cloudflare D1
5. Generates fonts.json and fonts.lite.json
6. Generates CREDITS.md with license and author attributions
"""

import os
import sys
import json
import zipfile
import urllib.request
from datetime import datetime

try:
    import fontTools.subset
    HAS_FONTTOOLS = True
except ImportError:
    HAS_FONTTOOLS = False

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_FILE = os.path.join(REPO_ROOT, "fonts_manifest.json")
SEED_FONTS_DIR = os.path.join(REPO_ROOT, "seed_fonts")
PACKAGES_DIR = os.path.join(REPO_ROOT, "packages")
PREVIEWS_DIR = os.path.join(REPO_ROOT, "previews")
OUTPUT_JSON = os.path.join(REPO_ROOT, "fonts.json")
OUTPUT_LITE_JSON = os.path.join(REPO_ROOT, "fonts.lite.json")
CREDITS_FILE = os.path.join(REPO_ROOT, "CREDITS.md")

BASE_PAGES_URL = "https://ultimatejimmy.github.io/storefront-fonts"
RATINGS_API_URL = "https://storefront-vote.ultimatejimmy.workers.dev/ratings?fresh=1"

# Standard Unicode ranges for preview specimen:
# ASCII Printable (32-126)
# Latin-1 Supplement (160-255)
# Latin Extended-A (256-383)
# General Punctuation & Quotes (8211: en-dash, 8212: em-dash, 8216: left sq, 8217: right sq, 8220: left dq, 8221: right dq, 8230: ellipsis, 8242: prime, 8243: double prime)
SUBSET_UNICODES = (
    list(range(32, 127)) +
    list(range(160, 256)) +
    list(range(256, 384)) +
    [8211, 8212, 8216, 8217, 8220, 8221, 8230, 8242, 8243]
)

def fetch_live_ratings(timeout=10):
    try:
        req = urllib.request.Request(
            RATINGS_API_URL,
            headers={
                "User-Agent": "Storefront-Fonts-Builder/1.0",
                "Accept": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                if isinstance(data, dict):
                    print(f"Fetched live ratings from worker ({len(data)} entries)")
                    return data
    except Exception as e:
        print(f"Warning: Could not fetch live ratings ({e})", file=sys.stderr)
    return {}

def subset_font(src_path, dst_path):
    if not HAS_FONTTOOLS:
        print("Warning: fonttools not installed; copying source font un-subsetted.")
        with open(src_path, "rb") as sf, open(dst_path, "wb") as df:
            df.write(sf.read())
        return

    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    options = fontTools.subset.Options()
    options.desubroutinize = True
    options.hinting = False

    font = fontTools.subset.load_font(src_path, options)
    subsetter = fontTools.subset.Subsetter(options=options)
    subsetter.populate(unicodes=SUBSET_UNICODES)
    subsetter.subset(font)
    fontTools.subset.save_font(font, dst_path, options)

def main():
    print("=== KOReader Storefront Fonts Builder ===")
    if not os.path.exists(MANIFEST_FILE):
        print(f"Error: Manifest not found at {MANIFEST_FILE}", file=sys.stderr)
        sys.exit(1)

    with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    os.makedirs(PACKAGES_DIR, exist_ok=True)
    os.makedirs(PREVIEWS_DIR, exist_ok=True)

    ratings_map = fetch_live_ratings()

    full_catalog = []
    lite_catalog = []
    credits_entries = []

    preview_files_to_bundle = []

    total_orig_size = 0
    total_subset_size = 0

    for entry in manifest:
        font_id = entry["id"]
        name = entry["name"]
        font_family = entry.get("font_family", name)
        font_file = entry.get("font_file", f"{name}-Regular.ttf")
        safe_name = name.replace(" ", "-")

        print(f"Processing: {name} (ID: {font_id})...")

        seed_dir_name = entry.get("seed_dir", name)
        src_dir = os.path.join(SEED_FONTS_DIR, seed_dir_name)
        if not os.path.exists(src_dir):
            print(f"  Warning: seed directory {src_dir} not found, skipping packaging", file=sys.stderr)
            continue

        # 1. Package into packages/<safe_name>.zip
        pkg_zip_name = f"{safe_name}.zip"
        pkg_zip_path = os.path.join(PACKAGES_DIR, pkg_zip_name)
        with zipfile.ZipFile(pkg_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            has_license = False
            for root, _, files in os.walk(src_dir):
                for file in files:
                    if file.lower().endswith(".png") and "preview" in file.lower():
                        continue
                    file_p = os.path.join(root, file)
                    arcname = os.path.relpath(file_p, src_dir)
                    zipf.write(file_p, arcname)
                    if file.lower().startswith("license") or file.lower().startswith("ofl"):
                        has_license = True
            
            # If font directory lacks explicit license file, embed standard OFL / Open License note
            if not has_license:
                lic_text = f"{name} Font Family\nLicense: {entry.get('license', 'SIL Open Font License 1.1')}\nAuthor: {entry.get('author', 'Open Source Community')}\nSource: {entry.get('source_url', '')}\n"
                zipf.writestr("LICENSE.txt", lic_text)

        download_url = f"{BASE_PAGES_URL}/packages/{pkg_zip_name}"

        # 2. Subset Regular font file into previews/<safe_name>/<font_file>
        src_font_file = os.path.join(src_dir, font_file)
        if not os.path.exists(src_font_file):
            for f in os.listdir(src_dir):
                if (f.lower().endswith(".ttf") or f.lower().endswith(".otf")) and "regular" in f.lower():
                    src_font_file = os.path.join(src_dir, f)
                    font_file = f
                    break

        if os.path.exists(src_font_file):
            preview_font_dir = os.path.join(PREVIEWS_DIR, safe_name)
            os.makedirs(preview_font_dir, exist_ok=True)
            preview_dst_file = os.path.join(preview_font_dir, font_file)
            subset_font(src_font_file, preview_dst_file)

            orig_sz = os.path.getsize(src_font_file)
            sub_sz = os.path.getsize(preview_dst_file)
            total_orig_size += orig_sz
            total_subset_size += sub_sz
            print(f"  Subsetted {font_file}: {orig_sz // 1024} KB -> {sub_sz // 1024} KB")

            preview_files_to_bundle.append((preview_dst_file, f"{safe_name}/{font_file}"))
            preview_font_url = f"{BASE_PAGES_URL}/previews/{safe_name}/{font_file}"
        else:
            print(f"  Warning: regular font file not found for {name} ({src_font_file})", file=sys.stderr)
            preview_font_url = ""

        # Live ratings
        r = ratings_map.get(str(font_id)) or ratings_map.get(font_id) or ratings_map.get(name.lower()) or {}
        up = int(r.get("up", 0))
        down = int(r.get("down", 0))
        wilson = float(r.get("wilson", 0.0))
        downloads = int(r.get("downloads", 0))

        full_item = {
            "id": font_id,
            "repo_id": font_id,
            "name": name,
            "font_family": font_family,
            "font_file": font_file,
            "author": entry.get("author", ""),
            "owner": entry.get("owner", ""),
            "description": entry.get("description", ""),
            "category": entry.get("category", "Serif"),
            "license": entry.get("license", "SIL Open Font License 1.1"),
            "license_url": entry.get("license_url", ""),
            "source_url": entry.get("source_url", ""),
            "download_url": download_url,
            "preview_font_url": preview_font_url,
            "stars": entry.get("stars", 100),
            "stargazers_count": entry.get("stars", 100),
            "user_thumbs_up": up,
            "user_thumbs_down": down,
            "wilson_score": wilson,
            "downloads": downloads,
        }
        full_catalog.append(full_item)

        lite_item = {
            "id": font_id,
            "repo_id": font_id,
            "name": name,
            "font_family": font_family,
            "font_file": font_file,
            "author": entry.get("author", ""),
            "owner": entry.get("owner", ""),
            "description": entry.get("description", ""),
            "category": entry.get("category", "Serif"),
            "license": entry.get("license", "SIL Open Font License 1.1"),
            "download_url": download_url,
            "preview_font_url": preview_font_url,
            "stars": entry.get("stars", 100),
            "user_thumbs_up": up,
            "user_thumbs_down": down,
            "wilson_score": wilson,
            "downloads": downloads,
        }
        lite_catalog.append(lite_item)

        credits_entries.append({
            "name": name,
            "author": entry.get("author", "Community"),
            "category": entry.get("category", "Serif"),
            "license": entry.get("license", "SIL Open Font License 1.1"),
            "source_url": entry.get("source_url", ""),
        })

    # 3. Create font_previews.zip bundle
    bundle_zip_path = os.path.join(PREVIEWS_DIR, "font_previews.zip")
    with zipfile.ZipFile(bundle_zip_path, "w", zipfile.ZIP_DEFLATED) as bzf:
        for fpath, arcname in preview_files_to_bundle:
            bzf.write(fpath, arcname)

    bundle_sz = os.path.getsize(bundle_zip_path)
    print(f"\nCreated previews/font_previews.zip: {bundle_sz // 1024} KB ({len(preview_files_to_bundle)} fonts)")
    print(f"Total un-subsetted regular fonts: {total_orig_size // 1024} KB")
    print(f"Total subsetted preview fonts: {total_subset_size // 1024} KB ({(1 - total_subset_size / max(1, total_orig_size)) * 100:.1f}% reduction)")

    # 4. Save fonts.json & fonts.lite.json
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    catalog_envelope = {
        "version": 1,
        "previews_version": int(datetime.utcnow().timestamp()),
        "previews_bundle_url": f"{BASE_PAGES_URL}/previews/font_previews.zip",
        "previews_bundle_size": bundle_sz,
        "generated_at": now_iso,
        "total_fonts": len(full_catalog),
        "fonts": full_catalog,
    }
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(catalog_envelope, f, indent=2, ensure_ascii=False)

    lite_envelope = {
        "version": 1,
        "previews_version": int(datetime.utcnow().timestamp()),
        "previews_bundle_url": f"{BASE_PAGES_URL}/previews/font_previews.zip",
        "previews_bundle_size": bundle_sz,
        "generated_at": now_iso,
        "total_fonts": len(lite_catalog),
        "fonts": lite_catalog,
    }
    with open(OUTPUT_LITE_JSON, "w", encoding="utf-8") as f:
        json.dump(lite_envelope, f, separators=(",", ":"), ensure_ascii=False)

    # 5. Generate CREDITS.md
    with open(CREDITS_FILE, "w", encoding="utf-8") as f:
        f.write("# Storefront Fonts — Credits & Licensing\n\n")
        f.write("All fonts distributed in this catalog are licensed under approved open licenses (SIL Open Font License, Apache 2.0, MIT, or Public Domain).\n\n")
        f.write("| Font Name | Designer / Foundry | Category | License | Source / Repository |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for c in credits_entries:
            src_link = f"[{c['source_url']}]({c['source_url']})" if c['source_url'] else "N/A"
            f.write(f"| **{c['name']}** | {c['author']} | {c['category']} | {c['license']} | {src_link} |\n")

    print(f"Successfully generated {OUTPUT_JSON}, {OUTPUT_LITE_JSON}, and {CREDITS_FILE}")

if __name__ == "__main__":
    main()
