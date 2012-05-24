

class Environment:
    def __init__(self, name):
        self.name = name
        self.networks = []
        self.nodes = []

class Network:
    def __init__(self, name, kind='hostonly'):
        self.name = name
        self.kind = kind

class Node:
    def __init__(self, name, cpu=1, memory=512, arch='x86_64', vnc=False):
        self.name = name

        self.cpu = cpu
        self.memory = memory
        self.arch = arch
        self.vnc = vnc
        self.interfaces = []
        self.disks = []
        self.boot = []
        self.cdrom = None

class Cdrom:
    def __init__(self, isopath=None, bus='ide'):
        self.isopath = isopath
        self.bus = bus

class Disk:
    def __init__(self, size, format='qcow2', bus='ide'):
        self.size = size
        self.format = format
        self.bus = bus
        self.path = None

class Interface:
    def __init__(self, network):
        self.network = network

