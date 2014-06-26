__author__ = 'alan'


from netaddr import *

ip = IPNetwork('10.108.1.0/24')
print list(ip.subnet(27))

for i in ["m", "s"]:
    print i
    print i.index(i)


subnets = list(IPNetwork('10.108.1.0/27'))
print len(subnets)