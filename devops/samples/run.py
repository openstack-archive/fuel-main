import time

import devops
from devops.helpers import wait, tcp_ping

import logging

MASTER_AND_SLAVE_CONFIG = """
    name: 'Sample environment'
    networks:
      - network: internal
      - network: external
    nodes:
      - node: master
        disk: '5Gb'
        cdrom: http://mc0n1-srt.srt.mirantis.net/nailgun-ubuntu-12.04-amd64.last.iso
        networks: ['external', 'internal']
        vnc: True
      - node: slave
        networks: ['internal']
        vnc: True
"""


def main():
    logging.basicConfig(level=logging.WARN)
    logger = logging.getLogger('test.integration')
    logger.setLevel(logging.INFO)

    environment = devops.load(MASTER_AND_SLAVE_CONFIG)

    logger.info("Building environment")

    devops.build(environment)

    logger.info("Environment ready")

    try:
        external_network = environment.network['external']

        master_node = environment.node['master']
        slave_node = environment.node['slave']

        logger.info("Starting master node")
        master_node.start()

        logger.info("VNC to master is available on %d" % master_node.vnc_port)

        logger.info("Waiting master node to boot")
        time.sleep(15)

        logger.info("Sending user input")

        ip = external_network.ip_addresses
        host_ip = ip[1]
        master_ip = ip[2]
        netmask = ip.netmask

        master_node.send_keys("""<Esc><Enter>
<Wait>
/install/vmlinuz initrd=/install/initrd.gz
 priority=critical
 locale=en_US
 file=/cdrom/preseed/manual.seed
 vga=788
 netcfg/get_ipaddress=%s
 netcfg/get_netmask=%s
 netcfg/get_gateway=%s
 netcfg/get_nameservers=%s
 netcfg/confirm_static=true
 <Enter>""" % (master_ip, netmask, host_ip, host_ip))
        logger.info("Finished sending user input")

        logger.info("Waiting master node to install")
        wait(lambda: tcp_ping(master_ip, 22))

        logger.info("Starting slave node")

        slave_node.start()

        logger.info("VNC to slave node at port %d" % slave_node.vnc_port)

        logger.info("Waiting slave node to configure network")

        wait(lambda: len(slave_node.ip_addresses) > 0, timeout=120)

        logger.info(
            "Slave node has IP address %s" % slave_node.ip_addresses[0])
    except:
        devops.save(environment)
        logger.warn("Environment has been saved as %s" % environment.id)
        raise


if __name__ == '__main__':
    main()
