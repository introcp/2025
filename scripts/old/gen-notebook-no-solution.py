import nbformat as nbf
from glob import glob
import os

# Collect a list of all notebooks in the content folder
notebooks = glob("./**/*-Solutions*.ipynb", recursive=True)

# Search through each notebook and look for the text, add a tag if necessary
for ipath in notebooks:

    if 'docs' in ipath or '_build' in ipath:
        continue

    opath = ipath.replace("-Solutions", "-AUTOGEN")

    if 'ALL' not in os.environ and os.path.exists(opath) \
        and os.path.getmtime(ipath) < os.path.getmtime(opath):
        continue

    print("Processing", ipath)

    ntbk = nbf.read(ipath, nbf.NO_CONVERT)

    to_remove = []
    for cell in ntbk.cells:
        cell_tags = cell.get('metadata', {}).get('tags', [])
        if " [solutions]" in cell['source']:
            cell['source'] = cell['source'].replace(" [solutions]", "")
        if 'solution' in cell_tags:
            to_remove.append(cell)

    for cell in to_remove:
        ntbk.cells.remove(cell)

    nbf.write(ntbk, opath)