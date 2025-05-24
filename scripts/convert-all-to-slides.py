import glob
import os

for filename in sorted(glob.glob('src/*/*.ipynb')):

    if 'ALL' not in os.environ and os.path.exists(filename.replace(".ipynb", ".pdf")) \
        and os.path.getmtime(filename) < os.path.getmtime(filename.replace(".ipynb", ".slides.html")) \
        and os.path.getmtime(filename) < os.path.getmtime(filename.replace(".ipynb", ".pdf")):
        continue
    else:
        print("Converting into slide:", filename)

    os.system('SCROLLABLE=False bash scripts/process.sh ' + filename)

    from playwright.sync_api import sync_playwright, Playwright

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

    with sync_playwright() as playwright:
        run(playwright)

    os.system('SCROLLABLE=True bash scripts/process.sh ' + filename)