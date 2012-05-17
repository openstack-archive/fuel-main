

class Environment:
    def __init__(self):
        self.networks = []
        self.nodes = []

class Network:
    def __init__(self, name, kind='hostonly'):
        self.name = name
        self.kind = kind

class Node:
    def __init__(self, name, cpu=1, memory=512):
        self.name = name

        self.cpu = cpu
        self.memory = memory
        self.interfaces = []
        self.disks = []

class Disk:
    def __init__(self, size):
        self.size = size

class Interface:
    def __init__(self, network):
        self.network = network

