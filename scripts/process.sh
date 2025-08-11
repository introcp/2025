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
    --SlidesExporter.reveal_height=800  \
    --SlidesExporter.reveal_transition="none" 
    # \
    # --SlidesExporter.reveal_width=1280 \
    # --SlidesExporter.reveal_height=600 

# --no-input # --post serve # ?print-pdf

# fix: top vertical alignment
if [ -z "${SCROLLABLE}" ] || [ "${SCROLLABLE}" = "True" ]; then
    sed -i -e 's/controls: true/controls: true, center: false, margin: 0/g' ${1%%.*}.slides.html
fi

# fix: luiss font
# sed -i -e 's/jp-content-font-family: system-ui/jp-content-font-family: LUISS, system-ui/g' ${1%%.*}.slides.html

# fix: luiss font size
# sed -i -e 's/jp-content-font-size1: 20px/jp-content-font-size1: 28px/g' ${1%%.*}.slides.html

# fix scrolling view
sed -i -e "s/.css('height', 'calc(95vh)')/.css('height', 'calc(90vh)')/g" ${1%%.*}.slides.html
sed -i -e "s/.height() \* 0.9/.height() \* 0.75/g" ${1%%.*}.slides.html

# fix scrollbar visibility
sed -i -e "s/.css('margin-top', '20px')/.css('margin-top', '0px').css('scrollbar-width', 'none')/g" ${1%%.*}.slides.html

# remove right border
perl -0777 -i -pe 's/.jp-MarkdownOutput {\n  display: table-cell;/.jp-MarkdownOutput {\n  /igs' ${1%%.*}.slides.html

# fix alignment first slide
perl -0777 -i -pe 's/<div class="jp-InputPrompt jp-InputArea-prompt">\n<\/div>//' ${1%%.*}.slides.html


echo "Done"
