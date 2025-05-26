import glob
import os
import hashlib
import glob
from playwright.sync_api import sync_playwright, Playwright

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

for filename in sorted(glob.glob('src/*/*.ipynb')):
    
    hash_name = name_hash(filename)

    if 'ALL' not in os.environ and os.path.exists(filename.replace(".ipynb", ".pdf")) \
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
                "--disable-gpu"
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
        
        if verbose: print("Waiting for 800ms")

        page.wait_for_timeout(1000);

        page.pdf(
            path=os.getcwd() + "/" + filename.replace('.ipynb', '.pdf'),
            print_background=True,
            margin=[],
            format="A4",
            # height="800",
            # width="1200",
        )
        browser.close()

        with open(HASHED_DIR + hash_name + ".hash", 'w') as f:
            f.write(file_hash(filename))

    with sync_playwright() as playwright:
        run(playwright)

    os.system('SCROLLABLE=True bash scripts/process.sh ' + filename)