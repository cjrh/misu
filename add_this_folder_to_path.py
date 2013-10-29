# Actually adds the parent folder, not this one, to the site-packages.
# Basically to get modules working easily.
import os
from distutils.sysconfig import get_python_lib
with open(os.path.join(get_python_lib(), 'library.pth'), 'wb') as f:
    f.write(os.path.abspath('..'))
