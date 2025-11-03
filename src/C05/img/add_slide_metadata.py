#!/usr/bin/env python3
"""
Add slide metadata to all cells in the notebook
"""
import json
import sys

notebook_path = '/home/ercoppa/Desktop/code/introcp/src/C05/C05-Computer-Network.ipynb'

# Read notebook
with open(notebook_path, 'r') as f:
    nb = json.load(f)

# Add slide metadata to all cells
for i, cell in enumerate(nb['cells']):
    if 'metadata' not in cell:
        cell['metadata'] = {}
    
    if 'slideshow' not in cell['metadata']:
        cell['metadata']['slideshow'] = {}
    
    # Set slide type
    if 'slide_type' not in cell['metadata']['slideshow']:
        cell['metadata']['slideshow']['slide_type'] = 'slide'

# Write back
with open(notebook_path, 'w') as f:
    json.dump(nb, f, indent=2)

print(f"Added slide metadata to all {len(nb['cells'])} cells")
