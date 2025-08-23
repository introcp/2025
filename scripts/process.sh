#!/bin/bash

#killall jupyter

# see: 
# https://nbconvert.readthedocs.io/en/latest/config_options.html

if [ -n "${SCROLLABLE}" ]; then
    echo "" #SCROLLABLE: ${SCROLLABLE}"
else
    SCROLLABLE="True"
fi

# echo ${SCROLLABLE}

jupyter nbconvert ${1} --to slides \
    --SlidesExporter.reveal_url_prefix=".." \
    --SlidesExporter.reveal_theme="luiss" \
    --SlidesExporter.reveal_number="c/t" \
    --SlidesExporter.reveal_scroll=${SCROLLABLE} \
    --SlidesExporter.reveal_height=700  \
    --SlidesExporter.reveal_transition="none" 
    # \
    # --SlidesExporter.reveal_width=1280 \
    # --SlidesExporter.reveal_height=600 

# --no-input # --post serve # ?print-pdf

# fix: top vertical alignment
# if [ -z "${SCROLLABLE}" ] || [ "${SCROLLABLE}" = "True" ]; then
#    sed -i -e 's/controls: true/controls: true, center: false, margin: 0/g' ${1%%.*}.slides.html
# fi

# fix: luiss font
# sed -i -e 's/jp-content-font-family: system-ui/jp-content-font-family: LUISS, system-ui/g' ${1%%.*}.slides.html

# fix: luiss font size
# sed -i -e 's/jp-content-font-size1: 20px/jp-content-font-size1: 28px/g' ${1%%.*}.slides.html

# fix scrolling view
sed -i -e "s/.css('height', 'calc(95vh)')/.css('height', 'calc(95vh)')/g" ${1%%.*}.slides.html
sed -i -e "s/.height() \* 0.9/.height() \* 0.99/g" ${1%%.*}.slides.html

# fix scrollbar visibility
sed -i -e "s/.css('margin-top', '20px')/.css('margin-top', '0px').css('scrollbar-width', 'none')/g" ${1%%.*}.slides.html

# remove right border
perl -0777 -i -pe 's/.jp-MarkdownOutput {\n  display: table-cell;/.jp-MarkdownOutput {\n  /igs' ${1%%.*}.slides.html

# Reduce height of bottom controls
sed -i -e '/<\/style>/i \
.reveal .controls {\n  height: 20px !important;\n}\n.reveal .controls button {\n  padding: 2px 4px !important;\n  font-size: 8px !important;\n}' ${1%%.*}.slides.html

# Load and initialize revealjs zoom plugin
sed -i -e 's#"../plugin/notes/notes.js"#"../dist/plugin/notes/notes.js",\n      "../dist/plugin/zoom/zoom.js"#' ${1%%.*}.slides.html
sed -i -e 's/function(Reveal, RevealNotes)/function(Reveal, RevealNotes, RevealZoom)/' ${1%%.*}.slides.html
sed -i -e 's/plugins: \[RevealNotes\]/plugins: [RevealNotes, RevealZoom]/' ${1%%.*}.slides.html

# fix alignment first slide
perl -0777 -i -pe 's/<div class="jp-InputPrompt jp-InputArea-prompt">\n<\/div>//' ${1%%.*}.slides.html

# Customize Reveal.js minScale/maxScale (environment overridable)
MIN_SCALE="${MIN_SCALE:-1.45}"
MAX_SCALE="${MAX_SCALE:-2.0}"

# Remove any existing minScale/maxScale within the Reveal.initialize block
sed -i -E '/Reveal\.initialize\(/,/^\s*\}\);\s*$/ { /minScale:/d; /maxScale:/d }' ${1%%.*}.slides.html

# Insert desired minScale/maxScale right after the slideNumber line
sed -i -e "/slideNumber: \\\"c\\/t\\\",/a \\
            minScale: ${MIN_SCALE},\\
            maxScale: ${MAX_SCALE}," ${1%%.*}.slides.html

echo "Done"
