import rpm
import sys
specfile = sys.argv[1]
spec = rpm.spec(specfile)
for pkg in spec.packages:
    print pkg.header.format('%{name}')
