import time
import glob
import pprint
import os.path
import pkgutil
import smtplib
import inspect
import functools
import contextlib
from email.mime.text import MIMEText

import yaml

from fuelclient import client
from fuelclient.objects import Environment
from fuelclient.objects import Node
from fuelclient.objects import NodeCollection
from tests import base
import type_check

logger = None


def set_logger(log):
    global logger
    logger = log


sections = {
    'sahara': 'additional_components',
    'murano': 'additional_components',
    'ceilometer': 'additional_components',
    'volumes_ceph': 'storage',
    'images_ceph': 'storage',
    'ephemeral_ceph': 'storage',
    'objects_ceph': 'storage',
    'osd_pool_size': 'storage',
    'volumes_lvm': 'storage',
    'volumes_vmdk': 'storage',
    'tenant': 'access',
    'password': 'access',
    'user': 'access',
    'vc_password': 'vcenter',
    'cluster': 'vcenter',
    'host_ip': 'vcenter',
    'vc_user': 'vcenter',
    'use_vcenter': 'vcenter',
}


def find_node_by_requirements(nodes, requirements):
    GB = 1024 * 1024 * 1024
    TOO_LARGE_NUMBER = 1000 ** 3
    
    min_cpu = requirements.get('cpu_count_min', 0)
    max_cpu = requirements.get('cpu_count_max', TOO_LARGE_NUMBER)
    
    min_hd = requirements.get('hd_size_min', 0)
    max_hd = requirements.get('hd_size_max', TOO_LARGE_NUMBER)

    min_mem = requirements.get('mem_count_min', 0)
    max_mem = requirements.get('mem_count_max', TOO_LARGE_NUMBER)

    def hd_valid(hd):
        return max_hd >= hd >= min_hd

    def cpu_valid(cpu):
        return max_cpu >= cpu >= min_cpu

    def mem_valid(mem):
        return max_mem >= mem >= min_mem

    for node in nodes:
        cpu = node.data['meta']['cpu']['total']
        mem = node.data['meta']['memory']['total'] / GB
        hd = sum(disk['size'] for disk in node.data['meta']['disks']) / GB

        if cpu_valid(cpu) and hd_valid(hd) and mem_valid(mem):
            return node
    return None


def match_nodes(nodes_descriptions, timeout):
    required_nodes_count = len(nodes_descriptions)
    msg = "Waiting for nodes {} to be discovered...".\
        format(required_nodes_count)

    logger.debug(msg)
    result = []

    for _ in range(timeout):
        free_nodes = [node for node in NodeCollection.get_all()
                      if not node.env_id]

        if len(free_nodes) >= required_nodes_count:
            node_mac_mapping = dict([(node.data['mac'].upper(), node) for
                                     node in free_nodes])
            for node_description in nodes_descriptions.values():
                found_node = None
                node_mac = node_description.get('mac')
                if node_mac is not None:
                    node_mac = node_mac.upper()
                    if node_mac in node_mac_mapping:
                        found_node = node_mac_mapping[node_mac]
                elif 'requirements' in node_description:
                    found_node = find_node_by_requirements(
                        free_nodes, node_description['requirements'])
                else:
                    found_node = free_nodes[0]

                if found_node is None:
                    if node_mac is not None:
                        msg_templ = "Can't found node for requirements: mac={}, {}"
                        msg = msg_templ.format(node_mac,
                                         node_description.get('requirements'))
                    else:
                        msg_templ = "Can't found node for requirements: {}"
                        msg = msg_templ.format(node_description.get('requirements'))

                    logger.error(msg)
                    break

                free_nodes.remove(found_node)
                result.append((node_description, found_node))
            else:
                return result
        time.sleep(1)

    raise Exception('Timeout exception')


def find_test_classes():
    test_classes = []
    for loader, name, _ in pkgutil.iter_modules(['tests']):
        module = loader.find_module(name).load_module(name)
        test_classes.extend([member for name, member in
                             inspect.getmembers(module)
                             if inspect.isclass(member) and
                             issubclass(member, base.BaseTests)])
    return test_classes


def run_all_tests(cluster_id, timeout, tests_to_run):
    test_classes = find_test_classes()
    print test_classes
    results = []
    for test_class in test_classes:
        test_class_inst = test_class(cluster_id, timeout)
        available_tests = test_class_inst.get_available_tests()
        results.extend(test_class_inst.run_tests(
            set(available_tests) & set(tests_to_run)))
    return results


def send_results(mail_config, tests):
    server = smtplib.SMTP(mail_config['smtp_server'], 587)
    server.starttls()
    server.login(mail_config['login'], mail_config['password'])

    # Form message body
    failed_tests = [test for test in tests if test['status'] == 'failure']
    msg = '\n'.join([test['name'] + '\n        ' + test['message']
                     for test in failed_tests])

    msg = MIMEText(msg)
    msg['Subject'] = 'Test Results'
    msg['To'] = mail_config['mail_to']
    msg['From'] = mail_config['mail_from']

    logger.debug("Sending results by email...")
    server.sendmail(mail_config['mail_from'],
                    [mail_config['mail_to']],
                    msg.as_string())
    server.quit()


def load_all_clusters(path):
    res = {}
    for fname in glob.glob(os.path.join(path, "*.yaml")):
        try:
            cluster = yaml.load(open(fname).read())
            res[cluster['name']] = cluster
        except Exception as exc:
            msg = "Failed to load cluster from file {}: {}".format(
                fname, exc)
            logger.error(msg)
    return res


def deploy_cluster(cluster_desc, additional_cfg=None, debug_mode=False):
    if cluster_desc['settings']['net_provider'] == "nova_network":
        net_provider = "nova"
    else:
        net_provider = cluster_desc['settings']['net_provider']
    cluster = Environment.create(cluster_desc['name'],
                                 cluster_desc['release'],
                                 net_provider,
                                 cluster_desc.get('net_segment_type'))
    mode = cluster_desc.get('deployment_mode')
    if mode:
        cluster.set({'mode': mode})
    attributes = cluster.get_settings_data()
    settings = cluster_desc['settings']
    ed_attrs = attributes['editable']
    for option, value in settings.items():
        if option in sections:
            attr_val_dict = ed_attrs[sections[option]]
            attr_val_dict['value'] = value

    ed_attrs['common']['debug']['value'] = debug_mode
    cluster.set_settings_data(attributes)
    if 'network_configuration' in cluster_desc:
        net_descriptions = cluster_desc['network_configuration']
        configuration = cluster.get_network_data()
        current_networks = configuration['networks']
        parameters = configuration['networking_parameters']

        if net_descriptions.get('networks'):
            # net_mapping = {}
            # for net_description in net_descriptions['networks']:
            #     print net_description + "!!!!!!!!111one"
            #     net_mapping[net_descriptions[net_description["name"]]] = net_descriptions
            net_mapping = net_descriptions['networks']

            for net in current_networks:
                net_desc = net_mapping.get(net['name'])
                if net_desc:
                    net.update(net_desc)

        if net_descriptions.get('networking_parameters'):
            parameters.update(net_descriptions['networking_parameters'])
        cluster.set_network_data(configuration)

    nodes_discover_timeout = cluster_desc.get('nodes_discovery_timeout', 3600)
    deploy_timeout = cluster_desc.get('DEPLOY_TIMEOUT', 36000)
    nodes_info = cluster_desc['nodes']

    for node_desc, node in match_nodes(nodes_info,
                                       nodes_discover_timeout):
        cluster.assign([node], node_desc['roles'])
        if 'interfaces' in node_desc:
            networks = {}
            for iface_name, params in node_desc['interfaces'].items():
                networks[iface_name] = params['networks']
            set_network_assigment(node, networks)

    if additional_cfg is not None:
        # TODO: update network from this call 
        # can be merged with cluster.set_networks above
        update_cluster(cluster, additional_cfg)

    task = cluster.deploy_changes()
    wd = with_timeout(deploy_timeout, "Wait cluster deployed")
    wd(lambda t: t.is_finished)(task)
    return cluster


def with_timeout(tout, message):
    def closure(func):
        @functools.wraps(func)
        def closure2(*dt, **mp):
            ctime = time.time()
            etime = ctime + tout

            while ctime < etime:
                if func(*dt, **mp):
                    return
                sleep_time = ctime + 1 - time.time()
                if sleep_time > 0:
                    time.sleep(sleep_time)
                ctime = time.time()
            raise RuntimeError("Timeout during " + message)
        return closure2
    return closure


def check_exists(cluster):
    try:
        cluster.status()
    except Exception:
        return True


def delete_if_exists(name):
    for cluster_obj in Environment.get_all():
        if cluster_obj.name == name:
            cluster_obj.delete()
            wd = with_timeout(60, "Wait cluster deleted")
            wd(lambda co: not check_exists(co))(cluster_obj)


def delete_all_clusters():
    for cluster_obj in Environment.get_all():
        cluster_obj.delete()
        wd = with_timeout(60, "Wait cluster deleted")
        wd(lambda co: not co.check_exists())(cluster_obj)


@contextlib.contextmanager
def make_cluster(cluster, auto_delete=False, debug=False, delete=True, additional_cfg=None):
    if auto_delete:
        for cluster_obj in Environment.get_all():
            if cluster_obj._data['name'] == cluster['name']:
                cluster_obj.delete()
                wd = with_timeout(60, "Wait cluster deleted")
                wd(lambda co: not check_exists(cluster_obj))(cluster_obj)

    c = deploy_cluster(cluster, additional_cfg)
    try:
        yield c
    except Exception as _:
        if not debug and delete:
            # c.delete()
            pass
    else:
        if delete:
            # c.delete()
            pass


def with_cluster(template_name, tear_down=True, **params):

    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            cluster_desc = args[0].templates.get(template_name)
            cluster_desc.update(params)
            with make_cluster(cluster_desc, delete=tear_down) as cluster:
                arg_spec = inspect.getargspec(f)
                if 'cluster_id' in arg_spec.args:
                    kwargs['cluster_id'] = cluster.id
                elif 'cluster' in arg_spec.args:
                    kwargs['cluster'] = cluster
                return f(*args, **kwargs)
        return wrapper
    return decorator


def to_utf8(val):
    if isinstance(val, basestring):
        return val.encode('utf8')
    return val


def encode_recursivelly(root):
    if isinstance(root, list):
        return map(encode_recursivelly, root)
    elif isinstance(root, dict):
        return {to_utf8(key): encode_recursivelly(val)
                for key, val in root.items()}
    else:
        return to_utf8(root)


def load_config_from_fuel(cluster_id):
    cluster = Environment(cluster_id)
    status = {}
    c = cluster.get_status()

    status['name'] = c['name']
    status['deployment_mode'] = c['mode']
    status['release'] = c['release_id']
    status['settings'] = {}
    status['settings']['net_provider'] = c['net_provider']

    status['nodes'] = {}

    for cnt, node in enumerate(cluster.get_nodes(), 1):
        if node['cluster'] == cluster_id:
            cur_node = 'node{}'.format(cnt)
            cnode = status['nodes'][cur_node] = {}

            #cnode['requirements'] = {}
            #cnode['roles'] = node['roles']
            cnode['network_data'] = node['network_data']
            cnode['main_mac'] = node['mac']

            #if 'controller' in cnode['roles']:
            #    cnode['dns_name'] = 'controller' + str(cnt)

    status['timeout'] = 3600

    net_data = cluster.get_networks(
        net_provider=status['settings']['net_provider'])

    status['network_provider_configuration'] = net_data

    status = encode_recursivelly(status)
    return status


def store_config(config, file_name):
    if not file_name.endswith('.yaml'):
        file_name += '.yaml'

    with open(file_name, 'w') as fd:
        fd.write(yaml.dump(config))


def load_config(file_name):
    with open(file_name) as fd:
        return yaml.load(fd.read())


def set_network_assigment(node, mapping):
    """Assings networks to interfaces
    :param mapping: list (dict) interfaces info
    """

    type_check.check({str: [str]}, mapping)

    curr_interfaces = node.get_attribute('interfaces')

    network_ids = {}
    for interface in curr_interfaces:
        for net in interface['assigned_networks']:
            network_ids[net['name']] = net['id']

    #transform mappings
    new_assigned_networks = {}

    for dev_name, networks in mapping.items():
        new_assigned_networks[dev_name] = []
        for net_name in networks:
            nnet = {'name': net_name, 'id': network_ids[net_name]}
            new_assigned_networks[dev_name].append(nnet)

    # update by ref
    for dev_descr in curr_interfaces:
        if dev_descr['name'] in new_assigned_networks:
            nass = new_assigned_networks[dev_descr['name']]
            dev_descr['assigned_networks'] = nass

    node.upload_node_attribute('interfaces', curr_interfaces)


def update_cluster(cluster, cfg):

    cfg_for_mac = {val['main_mac']: val for name, val in cfg['nodes'].items()}

    for node in cluster.get_nodes():
        if node.data['mac'] in cfg_for_mac:
            node_cfg = cfg_for_mac[node.data['mac']]

            mapping = {}
            for net_descr in node_cfg['network_data']:
                net_name = net_descr['name']
                if net_name == 'admin':
                    net_name = 'fuelweb_admin'
                dev_name = net_descr['dev']
                mapping.setdefault(dev_name, []).append(net_name)

            node.set_network_assigment(mapping)

    net_data = cfg['network_provider_configuration']
    cluster.set_networks(net_data)
