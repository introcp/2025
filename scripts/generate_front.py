#!/usr/bin/env python3
"""
Advanced PDF Cover Generator with better font handling
Requires: pip install PyMuPDF Pillow
"""

import fitz
import sys
import argparse
from pathlib import Path

class PDFCoverGenerator:
    def __init__(self):
        self.font_cache = {}
        self.registered_fonts = {}  # Track registered custom fonts per document
    
    def analyze_text_properties(self, page, search_text):
        """
        Analyze text properties more thoroughly
        """
        text_instances = page.search_for(search_text)
        properties = []
        
        for rect in text_instances:
            # Get detailed text information
            blocks = page.get_text("dict", clip=rect)
            for block in blocks.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            if search_text.lower() in span.get("text", "").lower():
                                properties.append({
                                    'rect': rect,
                                    'font': span.get("font", "helv"),
                                    'size': span.get("size", 12),
                                    'flags': span.get("flags", 0),
                                    'color': span.get("color", 0),
                                    'bbox': span.get("bbox"),
                                    'text': span.get("text", "")
                                })
        return properties
    
    def get_or_create_font(self, doc, font_name, flags=0):
        """
        Get font from document or create if not available
        """
        font_key = f"{font_name}_{flags}"
        
        if font_key in self.font_cache:
            return self.font_cache[font_key]
        
        # Try to find the font in the document
        font_list = doc.get_page_fonts(0)  # Get fonts from first page
        
        matching_font = None
        for font_info in font_list:
            if font_name in font_info[3]:  # font_info[3] is the font name
                matching_font = font_info[3]
                break
        
        if matching_font and '+' not in matching_font:
            self.font_cache[font_key] = matching_font
            return matching_font
        
        # Fallback fonts based on characteristics
        if flags & 2**4:  # Bold flag
            if "serif" in font_name.lower():
                fallback = "Times-Bold"
            else:
                fallback = "Helvetica-Bold"
        elif flags & 2**6:  # Italic flag
            if "serif" in font_name.lower():
                fallback = "Times-Italic"
            else:
                fallback = "Helvetica-Oblique"
        else:
            if "serif" in font_name.lower():
                fallback = "Times-Roman"
            else:
                fallback = "Helvetica"
        
        self.font_cache[font_key] = fallback
        return fallback
    
    def wrap_text(self, text, font_name, font_size, max_width, font_object=None):
        """
        Keep text on a single line - no wrapping
        """
        # Return the entire text as a single line
        return [text]
    
    def calculate_optimal_font_size(self, text, font_name, max_width, max_height, original_size, font_object=None):
        """
        Calculate optimal font size for text to fit in given dimensions
        """
        font_size = original_size
        
        while font_size > 6:  # Minimum readable size
            lines = self.wrap_text(text, font_name, font_size, max_width, font_object=font_object)
            
            # Calculate total height needed
            line_height = font_size * 1.2  # Standard line spacing
            total_height = len(lines) * line_height
            
            if total_height <= max_height:
                return font_size, lines
            
            font_size -= 0.5
        
        # If still too big, return minimum size
        lines = self.wrap_text(text, font_name, 6, max_width, font_object=font_object)
        return 6, lines
    
    def replace_text_advanced(self, input_pdf, output_pdf, replacements, title_font=None):
        """
        Advanced text replacement with multi-line support and better font handling
        """
        doc = fitz.open(input_pdf)
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            
            for placeholder, replacement in replacements.items():
                # Find all instances of placeholder text
                properties_list = self.analyze_text_properties(page, placeholder)
                
                for prop in properties_list:
                    rect = prop['rect']
                    
                    font_object = None
                    font_name = self.get_or_create_font(doc, prop['font'], prop['flags'])

                    # If a custom title font is provided and we're replacing the title, use it
                    if placeholder == 'TITLE' and title_font:
                        try:
                            # Check if font file exists
                            if not Path(title_font).exists():
                                raise FileNotFoundError(f"Font file not found: {title_font}")
                            
                            # Load font file as binary data for font object creation
                            with open(title_font, 'rb') as f:
                                font_buffer = f.read()
                            
                            # Create font object for accurate text measurements
                            font_object = fitz.Font(fontbuffer=font_buffer)
                            
                            # Use font object directly - don't pre-register
                            font_name = None  # Will use font_object instead
                            print(f"Using custom font {title_font} for title.")
                        except Exception as e:
                            print(f"Warning: Could not load custom title font: {e}. Falling back to default font.")
                            font_object = None
                            font_name = self.get_or_create_font(doc, prop['font'], prop['flags'])
                    
                    # Clear the old text area with some padding
                    clear_rect = fitz.Rect(rect.x0 - 5, rect.y0 - 5, rect.x1 + 5, rect.y1 + 20)
                    page.add_redact_annot(clear_rect, fill=(1, 1, 1))
                    page.apply_redactions()
                    
                    # Calculate available space
                    available_width = rect.width
                    available_height = rect.height + 15  # Add some extra height for multi-line
                    
                    # Get optimal font size and wrapped lines
                    font_size, lines = self.calculate_optimal_font_size(
                        replacement, font_name, available_width, available_height, prop['size'], font_object=font_object
                    )
                    
                    # Insert multi-line text
                    line_height = font_size * 1.2
                    
                    # Use the original text baseline position for vertical alignment
                    # This aligns with the existing "Introduction to computer programming" text
                    start_y = prop['bbox'][3]  # Use the bottom of the original text bounding box as baseline
                    
                    # Convert integer color to a tuple of floats (0-1)
                    raw_color = prop['color']
                    if isinstance(raw_color, int):
                        b = (raw_color & 0xff) / 255.0
                        g = ((raw_color >> 8) & 0xff) / 255.0
                        r = ((raw_color >> 16) & 0xff) / 255.0
                        color_tuple = (r, g, b)
                    else:
                        color_tuple = raw_color  # Assume it's already a valid format

                    # Handle custom font with TextWriter (better alignment control)
                    if font_object and font_name is None:
                        tw = fitz.TextWriter(page.rect, color=color_tuple)
                        
                        for i, line in enumerate(lines):
                            line_width = font_object.text_length(line, fontsize=font_size)
                            # Left align with the original text position
                            x_left_aligned = rect.x0
                            y_pos = start_y + i * line_height
                            insert_point = fitz.Point(x_left_aligned, y_pos)
                            # Ensure text case is preserved
                            tw.append(insert_point, str(line), font=font_object, fontsize=font_size)
                        
                        tw.write_text(page)
                    else:
                        # Use regular insert_text for built-in fonts
                        for i, line in enumerate(lines):
                            try:
                                line_width = fitz.get_text_length(line, fontname=font_name, fontsize=font_size)
                            except:
                                line_width = len(line) * font_size * 0.6  # Fallback approximation
                            
                            # Center horizontally within the rect
                            x_centered = rect.x0 + (rect.width - line_width) / 2
                            y_pos = start_y + i * line_height
                            insert_point = fitz.Point(x_centered, y_pos)
                            
                            page.insert_text(
                                insert_point,
                                line,
                                fontname=font_name,
                                fontsize=font_size,
                                color=color_tuple
                            )
                    
                    print(f"Replaced '{placeholder}' with '{replacement}' ({len(lines)} lines) using font {font_name}, size {font_size}")
        
        doc.save(output_pdf)
        doc.close()
        return output_pdf
    
    def merge_with_presentation(self, cover_pdf, presentation_pdf, output_pdf):
        """
        Merge cover with presentation
        """
        final_doc = fitz.open()
        
        # Add cover
        cover_doc = fitz.open(cover_pdf)
        final_doc.insert_pdf(cover_doc)
        cover_doc.close()
        
        # Add presentation
        pres_doc = fitz.open(presentation_pdf)
        final_doc.insert_pdf(pres_doc)
        pres_doc.close()
        
        final_doc.save(output_pdf)
        final_doc.close()
        
        return output_pdf
    
    def generate_cover(self, template_pdf, presentation_pdf, replacements, output_pdf, title_font=None):
        """
        Main method to generate the complete presentation with cover
        """
        temp_cover = "temp_cover.pdf"
        
        # Generate cover
        self.replace_text_advanced(template_pdf, temp_cover, replacements, title_font=title_font)
        
        # Merge with presentation
        final_pdf = self.merge_with_presentation(temp_cover, presentation_pdf, output_pdf)
        
        # Clean up
        Path(temp_cover).unlink()
        
        return final_pdf

def main():
    parser = argparse.ArgumentParser(description='Advanced PDF Cover Generator')
    parser.add_argument('template', help='Cover template PDF')
    parser.add_argument('presentation', help='Main presentation PDF')
    parser.add_argument('--title', required=True, help='Title text')
    parser.add_argument('--subtitle', help='Subtitle text')
    parser.add_argument('--author', help='Author text')
    parser.add_argument('--date', help='Date text')
    parser.add_argument('--title-font', help='Path to the .ttf font file for the title')
    parser.add_argument('--output', '-o', default='final_presentation.pdf', help='Output file')
    
    args = parser.parse_args()
    
    # Prepare replacements
    replacements = {'TITLE': args.title}
    if args.subtitle:
        replacements['SUBTITLE'] = args.subtitle
    if args.author:
        replacements['AUTHOR'] = args.author
    if args.date:
        replacements['DATE'] = args.date
    
    # Generate cover
    generator = PDFCoverGenerator()
    result = generator.generate_cover(
        args.template,
        args.presentation,
        replacements,
        args.output,
        title_font=args.title_font
    )
    
    print(f"✅ Generated presentation: {result}")

if __name__ == "__main__":
    main()