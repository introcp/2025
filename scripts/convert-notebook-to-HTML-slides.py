#!/usr/bin/env python3
import argparse
import hashlib
import os
import re
import signal
import subprocess
import sys
import time
import threading
from pathlib import Path

MATHJAX_CONFIG = r"""<!-- Load mathjax -->
<script>
  window.MathJax = {
    options: {
      renderActions: { addMenu: [] },
      processHtmlClass: 'tex2jax_process', // Only process elements with this class
    },
    tex: {
      processClass: 'tex2jax_process', // Only process elements with this class
      inlineMath: [['$', '$']],
      displayMath: [['$$', '$$']],
      tags: 'ams'
    },
    chtml: {
      linebreaks: { automatic: true }
    }
  };
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml-full.js"></script>
<!-- End of MathJax v3 configuration -->"""

def get_file_hash(path):
    """Compute SHA256 hash of a file."""
    if not os.path.exists(path):
        return None
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def process_slides(notebook_path):
    """Convert a Jupyter notebook to Reveal.js slides and post-process it."""
    print(f"[INFO] Converting {notebook_path}...")
    
    # Check for custom suffix from environment variable
    suffix = os.environ.get('SUFFIX', '.slides')
    slides_html_path = notebook_path.with_suffix(f'{suffix}.html')

    # Run nbconvert
    scrollable = os.environ.get('SCROLLABLE', 'True')

    # For custom suffixes, we need to account for nbconvert appending .slides.html
    if suffix != '.slides':
        # nbconvert will create filename.suffix.slides.html, but we want filename.suffix.html
        # So we use the base name without extension + suffix (without the .html part)
        output_name = notebook_path.stem + suffix.replace('.html', '')
        expected_nbconvert_output = notebook_path.with_suffix(f'{suffix}.slides.html')
    else:
        output_name = None  # Use default naming
        expected_nbconvert_output = slides_html_path

    original_sigint_handler = signal.getsignal(signal.SIGINT)
    try:
        # Only modify signal handling if we're in the main thread
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, signal.SIG_IGN)
        
        cmd = [
            'jupyter-nbconvert', str(notebook_path),
            '--to', 'slides',
            '--SlidesExporter.reveal_url_prefix', '..',
            '--SlidesExporter.reveal_theme', 'luiss',
            '--SlidesExporter.reveal_number', 'c/t',
            '--SlidesExporter.reveal_scroll', scrollable,
            '--SlidesExporter.reveal_height', '700',
            '--SlidesExporter.reveal_transition', 'none'
        ]
        if output_name:
            cmd.extend(['--output', output_name])
        
        subprocess.run(cmd, check=True)
        
        # If we used a custom suffix, rename the file to the expected name
        if suffix != '.slides' and expected_nbconvert_output.exists():
            expected_nbconvert_output.rename(slides_html_path)
            
    finally:
        # Only restore signal handling if we're in the main thread
        if threading.current_thread() is threading.main_thread():
            signal.signal(signal.SIGINT, original_sigint_handler)

    # Post-process the generated HTML
    with open(slides_html_path, 'r+') as f:
        content = f.read()
        
        # 1. Replace MathJax v2 with v3
        mathjax_v2_pattern = re.compile(
            r'<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/[\s\S]*?</script>\s*'
            r'<!-- MathJax configuration -->[\s\S]*?init_mathjax\(\);\s*</script>',
            re.DOTALL
        )
        content = mathjax_v2_pattern.sub(MATHJAX_CONFIG, content)

        # 2. Add RevealZoom plugin
        # 2a. Add zoom plugin to the list of scripts to load
        content = re.sub(
            r'("../plugin/notes/notes.js")',
            r'"../dist/plugin/notes/notes.js",\n      "../dist/plugin/zoom/zoom.js"',
            content
        )

        # 2b. Add RevealZoom to the callback function
        content = re.sub(
            r'(function\(Reveal, RevealNotes\))',
            r'function(Reveal, RevealNotes, RevealZoom)',
            content
        )

        # 2c. Initialize the RevealZoom plugin
        content = content.replace('plugins: [RevealNotes]', 'plugins: [RevealNotes, RevealZoom]')

        # 3. Fix alignment for the first slide
        content = re.sub(r'<div class="jp-InputPrompt jp-InputArea-prompt">\n</div>', '', content, 1)

        # 4. Customize Reveal.js min/max scale
        min_scale = os.environ.get('MIN_SCALE', '1.45')
        max_scale = os.environ.get('MAX_SCALE', '2.0')
        
        # Remove existing scale settings
        content = re.sub(r'minScale: [\d\.]+,', '', content)
        content = re.sub(r'maxScale: [\d\.]+,', '', content)

        # Add new scale settings
        scale_insertion_point = 'slideNumber: "c/t",'
        scale_config = f"""{scale_insertion_point}
      minScale: {min_scale},
      maxScale: {max_scale},"""
        content = content.replace(scale_insertion_point, scale_config)

        # 5. Fix scrolling view, scrollbar, and borders
        content = content.replace('.height() * 0.9', '.height() * 0.99')
        content = content.replace(".css('margin-top', '20px')", ".css('margin-top', '0px').css('scrollbar-width', 'none')")
        content = re.sub(r'(\.jp-MarkdownOutput \{)\n  display: table-cell;', r'\1', content)

        # 6. Reduce height of bottom controls and fix inline code styling
        controls_css = """\
.reveal .controls {\n  height: 20px !important;\n}\n.reveal .controls button {\n  padding: 2px 4px !important;\n  font-size: 8px !important;\n}
/* Fix inline code styling */
.jp-RenderedHTMLCommon :not(pre) > code {
  background-color: transparent !important;
  padding: 0px 2px !important;
}
</style>"""
        content = content.replace('</style>', controls_css)

        f.seek(0)
        f.write(content)
        f.truncate()

    print(f"[INFO] Successfully generated {slides_html_path}")

def main():
    parser = argparse.ArgumentParser(description='Convert Jupyter notebooks to Reveal.js slides.')
    parser.add_argument('notebook', help='Path to the Jupyter notebook file.')
    parser.add_argument('--watch', '-w', action='store_true', help='Watch for file changes and re-run conversion.')
    args = parser.parse_args()

    notebook_path = Path(args.notebook)
    if not notebook_path.exists():
        print(f"[ERROR] File not found: {notebook_path}", file=sys.stderr)
        sys.exit(1)

    if not args.watch:
        process_slides(notebook_path)
        return

    print(f"[INFO] Watching {notebook_path} for changes...")
    last_hash = None
    try:
        while True:
            current_hash = get_file_hash(notebook_path)
            if current_hash != last_hash:
                if last_hash is not None:
                    print("[INFO] File change detected.")
                try:
                    process_slides(notebook_path)
                    last_hash = current_hash
                except subprocess.CalledProcessError as e:
                    print(f"[ERROR] Failed to convert {notebook_path}: {e}", file=sys.stderr)
                except Exception as e:
                    print(f"[ERROR] An unexpected error occurred: {e}", file=sys.stderr)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[INFO] Watch mode stopped by user. Exiting.")
        sys.exit(0)

if __name__ == '__main__':
    main()
