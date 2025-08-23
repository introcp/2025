import glob
import os
import hashlib
import glob
from playwright.sync_api import sync_playwright, Playwright
import argparse

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

for filename in files:
    
    hash_name = name_hash(filename)

    if (not force) and 'ALL' not in os.environ and os.path.exists(filename.replace(".ipynb", ".pdf")) \
        and hash_name in cached_hashes and file_hash(filename) in cached_hashes[hash_name]:
        print("Skipping conversion into slide:", filename)
        continue
    else:
        print("Converting into slide:", filename)

    os.system('SCROLLABLE=False bash scripts/process.sh ' + filename)

    def run(playwright: Playwright, verbose=False):

        if verbose: print("Launching the browser")

        chromium = playwright.chromium # or "firefox" or "webkit".
        browser = chromium.launch(
            headless=True,
            args = [
                "--disable-gpu",
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-zygote',
                '--single-process'
            ]
        )
        context = browser.new_context()

        if verbose: print(browser)
        if verbose: print("Opening a new page")

        page = context.new_page()

        if verbose: print("Setting the viewport")

        page.emulate_media(media="screen")

        html_file = os.getcwd() + "/" + filename.replace('.ipynb', '.slides.html?print-pdf')
        
        if verbose: print("Visiting the page:", html_file)
        
        page.goto(
            f"file://{html_file}",
            wait_until="load"
        )
        # Ensure network is idle (scripts and images fetched)
        page.wait_for_load_state("networkidle")

        # Wait for Reveal to be ready, if available
        try:
            page.wait_for_function("() => window.Reveal && (Reveal.isReady ? Reveal.isReady() : true)", timeout=5000)
        except Exception:
            pass

        # Wait for MathJax to finish rendering all equations.
        # Wait for MathJax to finish rendering, with a timeout.
        try:
            page.wait_for_function("() => window.MathJax && window.MathJax.startup", timeout=5000)
            page.evaluate("async () => { await MathJax.startup.promise; await MathJax.typesetPromise(); }")
        except Exception as e:
            print(f"    - MathJax rendering timed out or failed: {e}")

        page.pdf(
            path=os.getcwd() + "/" + filename.replace('.ipynb', '.pdf'),
            print_background=True,
            margin=[],
            # format="A4",
            height="680",
            width="1024",
        )
        browser.close()

        with open(HASHED_DIR + hash_name + ".hash", 'w') as f:
            f.write(file_hash(filename))

    with sync_playwright() as playwright:
        run(playwright)

    os.system('SCROLLABLE=True bash scripts/process.sh ' + filename)