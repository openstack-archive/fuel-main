import os
here = lambda * x: os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

REPOSITORY_ROOT = here('..')

root = lambda * x: os.path.join(os.path.abspath(REPOSITORY_ROOT), *x)