import sys
import glob
import os

for filename in glob.glob('src/*/*slides.html'):
    print("Processing", filename)
    d = os.path.dirname(filename)
    print("Copying", d)
    os.system('cp -a ' + d + '/* ' + sys.argv[1] + "/" + d + "/")

for filename in glob.glob('docs/_sources/src/*/*.ipynb'):
    print("Processing", filename)
    data = open(filename).read()
    d = os.path.basename(os.path.dirname(filename))
    data = data.replace('(img/', '(https://introcp.github.io/src/' + d + '/img/')
    data = data.replace('"img/', '"https://introcp.github.io/src/' + d + '/img/')
    open(filename, 'w').write(data)

for filename in sorted(glob.glob(sys.argv[1] + '/src/*/*.html')):
    if 'slides' in filename:
        continue
    if not os.path.basename(filename)[1].isdigit():
        continue

    print("add slide button to:", filename)
    
    data = open(filename, 'r').read()

    slide_button = """

    <button onclick="window.open(window.location.pathname.replace('.html', '.slides.html'));"
    class="btn btn-sm btn-fullscreen-button"
    title="Slide"
    data-bs-placement="bottom" data-bs-toggle="tooltip"
    >
    
    <span class="btn__icon-container">
        <i class="fa-brands fa-slideshare"></i>
    </span>

    </button>

    """

    jupyterlite_button = """<span class="btn__text-container">Colab</span>
</a>
</li>

<li><a href="https://ercoppa.github.io/jupyterlite/lab/?fromURL=https://introcp.github.io/_sources/<PATH>" target="_blank"
  class="btn btn-sm dropdown-item"
  title="Launch on JupyterLite"
  data-bs-placement="left" data-bs-toggle="tooltip"
>
 

<span class="btn__icon-container">
 
   <img alt="JupyterLite logo" src="https://avatars.githubusercontent.com/u/81094398?s=200&v=4">
 </span>
<span class="btn__text-container">JupyterLite</span>
</a>
</li>
    """

    pivot2 = """<span class="btn__text-container">Colab</span>
</a>
</li>"""

    pivot = '<button onclick="toggleFullScreen()"'

    if 'fa-slideshare' not in data:
        data = data.replace(pivot, slide_button + pivot)
        data = data.replace(
            "window.print()", 
            "window.open(window.location.pathname.replace('.html', '.pdf'));"
        )
        data = data.replace(
            pivot2,
            jupyterlite_button.replace("<PATH>", filename.replace("docs", "").replace(".html", ".ipynb"))
        )


    a = '<li><a href="../../_sources<PATH>" target="_blank'
    a = a.replace("<PATH>", filename.replace("docs", "").replace(".html", ".ipynb"))
    a_force_download = a.replace('href="../..', 'href="https://introcp.github.io/src/download.html?file=')
    data = data.replace(a, a_force_download)

    open(filename, 'w').write(data)