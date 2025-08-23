import sys
import glob
import os

for filename in glob.glob('src/*/*slides.html'):
    print("Processing", filename)
    d = os.path.dirname(filename)
    print("Copying", d)
    os.system('cp -a ' + d + '/* ' + sys.argv[1] + "/" + d + "/")