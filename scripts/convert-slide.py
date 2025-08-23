import os
import sys
from playwright.sync_api import sync_playwright, Playwright

f = sys.argv[1]
if not os.path.exists(f):
    print("File does not exist:", f)
    exit(1)

for filename in sorted([f]):

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

        print(filename)

        html_file = os.getcwd() + "/" + filename.replace('.ipynb', '.slides.html?print-pdf')
        
        if verbose: print("Visiting the page:", html_file)
        
        page.goto(
            f"file://{html_file}",
            wait_until="load"
        )
        
        wait_ms = 1000
        if verbose: print("Waiting for", wait_ms, "ms")

        page.wait_for_timeout(wait_ms);

        page.pdf(
            path=os.getcwd() + "/" + filename.replace('.ipynb', '.pdf'),
            print_background=True,
            margin=[],
            # format="A4",
            height="800",
            width="1024",
        )
        browser.close()

    with sync_playwright() as playwright:
        run(playwright)