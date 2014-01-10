import libvirt

def chunk_render(self, fd, size):
    return fd.read(1024)

libvirt.virInitialize()
conn=libvirt.open('qemu:///system')
with open('/home/alan/Downloads/fuel-4.1-21-2014-01-08_01-17-41.iso',"rb") as fd:
    stream = conn.newStream(0)
    conn.storageVolLookupByPath('/var/lib/libvirt/images/fuel_4.1-21_admin-iso').upload(
    stream=stream, offset=0,
    length=1838868480, flags=0)
    stream.sendAll(chunk_render, fd)
