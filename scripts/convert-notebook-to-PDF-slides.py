#!/usr/bin/env python3

import glob
import os
import hashlib
import glob
from playwright.sync_api import sync_playwright, Playwright
import argparse
import signal
import sys
import time
import json
import re
import subprocess
import fitz  # PyMuPDF for PDF manipulation
import threading
import multiprocessing

def file_hash(path):
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def name_hash(path):
    hasher = hashlib.sha256()
    hasher.update(path.encode('utf-8'))
    return hasher.hexdigest()

def check_first_cell_is_slide(notebook_path):
    """Check if the first cell has slide type metadata."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # Get the first cell
        if not notebook.get('cells'):
            return False
            
        first_cell = notebook['cells'][0]
        
        # Check if the cell has slideshow metadata with slide type
        metadata = first_cell.get('metadata', {})
        slideshow = metadata.get('slideshow', {})
        slide_type = slideshow.get('slide_type', '')
        
        return slide_type == 'slide'
        
    except Exception as e:
        print(f"Warning: Could not check slide type from {notebook_path}: {e}")
        return False

def extract_h1_title_from_notebook(notebook_path):
    """Extract the first H1 (#) title from the first cell of the notebook."""
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            notebook = json.load(f)
        
        # Get the first cell
        if not notebook.get('cells'):
            return None
            
        first_cell = notebook['cells'][0]
        
        # Check if it's a markdown cell
        if first_cell.get('cell_type') != 'markdown':
            return None
            
        # Get the source content
        source = first_cell.get('source', [])
        
        # Process line by line to find the first H1
        if isinstance(source, list):
            # Process each line in the list
            for line in source:
                line = line.strip()
                if line.startswith('#') and not line.startswith('##'):
                    # Extract everything after the first #
                    title_text = line[1:].strip()
                    # Remove HTML tags if present
                    title_text = re.sub(r'<[^>]+>', '', title_text)
                    # Remove backticks from title
                    title_text = title_text.replace('`', '')
                    return title_text.strip()
        else:
            # If source is a string, split by lines
            lines = source.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('#') and not line.startswith('##'):
                    # Extract everything after the first #
                    title_text = line[1:].strip()
                    # Remove HTML tags if present
                    title_text = re.sub(r'<[^>]+>', '', title_text)
                    # Remove backticks from title
                    title_text = title_text.replace('`', '')
                    return title_text.strip()
            
        return None
    except Exception as e:
        print(f"Warning: Could not extract title from {notebook_path}: {e}")
        return None

def remove_first_slide(pdf_path, output_path):
    """Remove the first slide from a PDF and save to output_path."""
    try:
        doc = fitz.open(pdf_path)
        if doc.page_count <= 1:
            # If only one page, return None (no slides to keep)
            doc.close()
            return None
        
        # Create new document without first page
        new_doc = fitz.open()
        for page_num in range(1, doc.page_count):  # Start from page 1 (skip page 0)
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        
        new_doc.save(output_path)
        new_doc.close()
        doc.close()
        return output_path
    except Exception as e:
        print(f"Warning: Could not remove first slide: {e}")
        return None

def generate_front_slide(title, slides_pdf_path):
    """Generate a front slide PDF and merge with slides (minus first slide)."""
    try:
        # Remove first slide from the original slides
        slides_without_first = slides_pdf_path.replace('.pdf', '_no_first.pdf')
        if not remove_first_slide(slides_pdf_path, slides_without_first):
            print("Warning: Could not remove first slide, using original PDF")
            slides_without_first = slides_pdf_path
    
        print(f"Generating front slide with title: {title}")
        
        # Use the front template and generate the cover
        cmd = [
            'python3', 'scripts/generate_front.py',
            '--title', title,
            '--title-font', 'src/dist/fonts/LuissSans-Bold.otf',
            'src/front.pdf',
            slides_without_first,
            '--output', slides_pdf_path.replace('.pdf', '_with_front.pdf')
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        # Clean up temporary file
        if os.path.exists(slides_without_first) and slides_without_first != slides_pdf_path:
            os.remove(slides_without_first)
        
        if result.returncode == 0:
            return slides_pdf_path.replace('.pdf', '_with_front.pdf')
        else:
            print(f"Warning: Failed to generate front slide: {result.stderr}")
            return None
    except Exception as e:
        print(f"Warning: Could not generate front slide: {e}")
        return None

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

def convert_to_pdf(filename, force=False, verbose=False, abort_event=None):
    """Converts a single notebook file to PDF, checking cache unless forced."""
    filename = str(filename)
    hash_name = name_hash(filename)
    
    # Define expected output files
    pdf_file = filename.replace(".ipynb", ".pdf")
    html_file = filename.replace(".ipynb", ".slides.html")

    # Check cache - require both PDF and HTML files to exist
    if not force and 'ALL' not in os.environ and os.path.exists(pdf_file) and os.path.exists(html_file) \
        and hash_name in cached_hashes and file_hash(filename) == cached_hashes.get(hash_name):
        print(f"Skipping cached conversion: {filename}")
        return

    print(f"\nConverting to PDF: {filename}")
    
    # Check if first cell is marked as slide type
    is_slide_presentation = check_first_cell_is_slide(filename)
    if verbose:
        print(f"First cell is slide type: {is_slide_presentation}")
    
    # Extract title from notebook for front slide (only if it's a slide presentation)
    title = None
    if is_slide_presentation:
        title = extract_h1_title_from_notebook(filename)
        if verbose and title:
            print(f"Extracted title: {title}")

    # Check for abortion before starting expensive operations
    if abort_event and abort_event.is_set():
        print(f"Conversion aborted for {filename}")
        return

    # Generate the prerequisite HTML slides for PDF conversion (step 1)
    # Use subprocess instead of os.system to avoid signal handling issues in threads
    try:
        if verbose: print("Generating HTML slides for PDF conversion...")
        env = os.environ.copy()
        env['SCROLLABLE'] = 'False'
        env['SUFFIX'] = '.slide.pdf'
        result = subprocess.run([
            'python3', 'scripts/convert-notebook-to-HTML-slides.py', filename
        ], env=env, check=True, capture_output=False, text=True)
        if verbose: print("HTML slides generation completed.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] HTML generation failed: {e}")
        return

    # Check for abortion after HTML generation
    if abort_event and abort_event.is_set():
        print(f"Conversion aborted for {filename}")
        # Clean up the generated slide.pdf.html file
        slide_pdf_html = filename.replace('.ipynb', '.slide.pdf.html')
        if os.path.exists(slide_pdf_html):
            os.remove(slide_pdf_html)
        return

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

        # Use the slide.pdf.html file for PDF conversion
        html_file = f"file://{os.getcwd()}/{filename.replace('.ipynb', '.slide.pdf.html?print-pdf')}"
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

        # Generate main slides PDF (without front slide initially)
        main_pdf_path = f"{os.getcwd()}/{filename.replace('.ipynb', '_slides.pdf')}"
        page.pdf(
            path=main_pdf_path,
            print_background=True, margin=[], height="720px", width="1280px"
        )
        browser.close()
        
        # Clean up the slide.pdf.html file after PDF generation
        slide_pdf_html = filename.replace('.ipynb', '.slide.pdf.html')
        if os.path.exists(slide_pdf_html):
            os.remove(slide_pdf_html)
        
        # Generate final PDF with front slide if title was extracted
        final_pdf_path = f"{os.getcwd()}/{filename.replace('.ipynb', '.pdf')}"
        if title:
            if verbose: print(f"Generating front slide with title: {title}")
            front_pdf = generate_front_slide(title, main_pdf_path)
            if front_pdf and os.path.exists(front_pdf):
                # Move the front slide PDF to final location
                os.rename(front_pdf, final_pdf_path)
                # Clean up temporary main slides PDF
                if os.path.exists(main_pdf_path):
                    os.remove(main_pdf_path)
                print(f"Successfully generated PDF with front slide for {filename}")
            else:
                # Fallback: use main PDF without front slide
                os.rename(main_pdf_path, final_pdf_path)
                print(f"Successfully generated PDF (no front slide) for {filename}")
        else:
            # No title found, use main PDF as final
            os.rename(main_pdf_path, final_pdf_path)
            print(f"Successfully generated PDF (no title found) for {filename}")

        with open(f"{HASHED_DIR}{hash_name}.hash", 'w') as f:
            f.write(file_hash(filename))

    try:
        with sync_playwright() as playwright:
            # Check for abortion before starting playwright
            if abort_event and abort_event.is_set():
                print(f"Conversion aborted for {filename}")
                # Clean up the generated slide.pdf.html file
                slide_pdf_html = filename.replace('.ipynb', '.slide.pdf.html')
                if os.path.exists(slide_pdf_html):
                    os.remove(slide_pdf_html)
                return
            run_playwright(playwright)
    except Exception as e:
        print(f"[ERROR] Failed to convert {filename} to PDF: {e}", file=sys.stderr)

def generate_scrollable_html(filename, verbose=False, force=False):
    """Generate scrollable version for viewing (step 3)."""
    filename = str(filename)
    hash_name = name_hash(filename)
    html_file = filename.replace(".ipynb", ".slides.html")
    
    # Check cache for HTML file
    if not force and os.path.exists(html_file) \
        and hash_name in cached_hashes and file_hash(filename) == cached_hashes.get(hash_name):
        if verbose: print(f"Skipping cached HTML generation: {filename}")
        return
    
    print(f"Generating scrollable HTML: {filename}")
    # Use subprocess instead of os.system to avoid signal handling issues in threads
    try:
        if verbose: print("Starting scrollable HTML generation...")
        env = os.environ.copy()
        env['SCROLLABLE'] = 'True'
        result = subprocess.run([
            'python3', 'scripts/convert-notebook-to-HTML-slides.py', filename
        ], env=env, check=True, capture_output=False, text=True)
        if verbose: print("Scrollable HTML generation completed.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Scrollable HTML generation failed: {e}")
        raise

# --- Main execution ---
if args.watch:
    if not args.input:
        print("[ERROR] --watch requires a single input file.", file=sys.stderr)
        sys.exit(1)
    
    print(f"[INFO] Watching {args.input} for changes...\n")
    last_hash = None
    changed = True
    abort_event = threading.Event()
    pdf_thread = None
    scrollable_thread = None
    
    def run_pdf_conversion():
        try:
            convert_to_pdf(args.input, force=True, verbose=args.verbose, abort_event=abort_event)
        except Exception as e:
            print(f"[ERROR] PDF conversion failed: {e}")
    
    def run_scrollable_generation():
        try:
            generate_scrollable_html(args.input, verbose=args.verbose, force=True)
        except Exception as e:
            print(f"[ERROR] Scrollable HTML generation failed: {e}")
    
    try:
        while True:
            current_hash = file_hash(args.input)
            if current_hash != last_hash:
                if last_hash is not None:
                    print("[INFO] File change detected.")
                    
                    # Signal abortion to ongoing PDF conversion
                    if pdf_thread and pdf_thread.is_alive():
                        print("[INFO] Aborting ongoing PDF conversion...")
                        abort_event.set()
                        pdf_thread.join(timeout=2)  # Wait up to 2 seconds for graceful shutdown
                        if pdf_thread.is_alive():
                            print("[WARNING] PDF conversion did not stop gracefully")
                    
                    # Reset abort event for new conversion
                    abort_event.clear()
                
                # Start PDF conversion (steps 1-2)
                pdf_thread = threading.Thread(target=run_pdf_conversion)
                pdf_thread.start()
                
                # Start scrollable HTML generation in parallel (step 3)
                scrollable_thread = threading.Thread(target=run_scrollable_generation)
                scrollable_thread.start()
                
                last_hash = current_hash
                changed = True
            elif changed:
                print("\n[INFO] Waiting for file changes... Ctrl+C to exit")
                changed = False
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[INFO] Watch mode stopped by user. Stopping ongoing processes...")
        
        # Signal abortion and wait for threads to finish
        abort_event.set()
        if pdf_thread and pdf_thread.is_alive():
            pdf_thread.join(timeout=5)
        if scrollable_thread and scrollable_thread.is_alive():
            scrollable_thread.join(timeout=5)
        
        print("[INFO] Exiting.")
        sys.exit(0)
else:
    for filename in files:
        convert_to_pdf(filename, force=force, verbose=args.verbose)
        generate_scrollable_html(filename, verbose=args.verbose, force=force)