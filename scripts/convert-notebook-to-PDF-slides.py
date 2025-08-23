#!/usr/bin/env python3

import glob
import os
import hashlib
import glob
from playwright.sync_api import sync_playwright, Playwright
import argparse
import sys
import time

def file_hash(path):
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def name_hash(path):
    hasher = hashlib.sha256()
    hasher.update(path.encode('utf-8'))
    return hasher.hexdigest()

HASHED_DIR = "docs/.hashes/"

if not os.path.exists(HASHED_DIR):
    os.makedirs(HASHED_DIR)

cached_hashes = {}
for hash in glob.glob(HASHED_DIR + "/*.hash"):
    hf = os.path.basename(hash).replace(".hash", "")
    h = open(hash, 'r').read().strip()
    cached_hashes[hf] = h

parser = argparse.ArgumentParser(description="Convert notebooks to slides PDFs")
parser.add_argument("input", nargs="?", help="Path to a single .ipynb to convert (ignores cache)")
parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output for debugging.")
parser.add_argument("--watch", "-w", action="store_true", help="Watch for file changes and re-run conversion.")
parser.add_argument("--force", action="store_true", help="Force regeneration ignoring cache for all inputs")
args = parser.parse_args()

# Determine files to process
if args.input:
    # Normalize and validate single input
    in_path = args.input
    if not in_path.endswith('.ipynb'):
        print(f"Error: input must be a .ipynb file: {in_path}")
        raise SystemExit(2)
    if not os.path.exists(in_path):
        print(f"Error: file does not exist: {in_path}")
        raise SystemExit(2)
    files = [in_path]
    # When targeting a single file, ignore cache by default
    force = True
else:
    files = sorted(glob.glob('src/*/*.ipynb'))
    force = bool(args.force)

def convert_to_pdf(filename, force=False, verbose=False):
    """Converts a single notebook file to PDF, checking cache unless forced."""
    filename = str(filename)
    hash_name = name_hash(filename)

    # Check cache
    if not force and 'ALL' not in os.environ and os.path.exists(filename.replace(".ipynb", ".pdf")) \
        and hash_name in cached_hashes and file_hash(filename) == cached_hashes.get(hash_name):
        print(f"Skipping cached PDF: {filename}")
        return

    print(f"Converting to PDF: {filename}")

    # Generate the prerequisite HTML slides
    os.system(f'SCROLLABLE=False python3 scripts/convert-notebook-to-HTML-slides.py "{filename}"')

    def run_playwright(playwright: Playwright):
        if verbose: print("Launching browser...")
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-gpu", '--no-sandbox', '--disable-setuid-sandbox',
                '--disable-dev-shm-usage', '--disable-accelerated-2d-canvas',
                '--no-zygote', '--single-process'
            ]
        )
        page = browser.new_page()
        page.emulate_media(media="screen")

        html_file = f"file://{os.getcwd()}/{filename.replace('.ipynb', '.slides.html?print-pdf')}"
        if verbose: print(f"Visiting {html_file}")
        
        page.goto(html_file, wait_until="load")
        page.wait_for_load_state("networkidle")

        try:
            page.wait_for_function("() => window.Reveal && (Reveal.isReady ? Reveal.isReady() : true)", timeout=5000)
        except Exception:
            pass # Ignore if Reveal is not ready

        try:
            page.wait_for_function("() => window.MathJax && window.MathJax.startup", timeout=5000)
            page.evaluate("async () => { await MathJax.startup.promise; await MathJax.typesetPromise(); }")
        except Exception as e:
            print(f"    - MathJax rendering timed out or failed: {e}")

        page.pdf(
            path=f"{os.getcwd()}/{filename.replace('.ipynb', '.pdf')}",
            print_background=True, margin=[], height="680px", width="1024px"
        )
        browser.close()

        with open(f"{HASHED_DIR}{hash_name}.hash", 'w') as f:
            f.write(file_hash(filename))
        print(f"Successfully generated PDF for {filename}")

    try:
        with sync_playwright() as playwright:
            run_playwright(playwright)
        # Generate scrollable version for viewing
        os.system(f'SCROLLABLE=True python3 scripts/convert-notebook-to-HTML-slides.py "{filename}"')
    except Exception as e:
        print(f"[ERROR] Failed to convert {filename} to PDF: {e}", file=sys.stderr)

# --- Main execution ---
if args.watch:
    if not args.input:
        print("[ERROR] --watch requires a single input file.", file=sys.stderr)
        sys.exit(1)
    
    print(f"[INFO] Watching {args.input} for changes...\n")
    last_hash = None
    changed = True
    while True:
        current_hash = file_hash(args.input)
        if current_hash != last_hash:
            if last_hash is not None:
                print("[INFO] File change detected.")
            convert_to_pdf(args.input, force=True)
            last_hash = current_hash
            changed = True
        elif changed:
            print("\n[INFO] Waiting for file changes... Crtl+C to exit")
            changed = False
        time.sleep(0.5)
else:
    for filename in files:
        convert_to_pdf(filename, force=force)