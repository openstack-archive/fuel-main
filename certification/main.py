import sys
import pprint
import os.path
import logging.config
from optparse import OptionParser
import urlparse

import yaml
from fuelclient import client

sys.path.insert(0, '../lib/requests')


DEFAULT_CONFIG_PATH = 'config.yaml'


def parse_config(cfg_path):
    with open(cfg_path) as f:
        return yaml.load(f.read())


def parse_command_line():
    parser = OptionParser("usage: %prog [options]")

    parser.add_option('-p', '--password',
                      help='password for email', default=None)

    parser.add_option('-c', '--config',
                      help='config file path', default=DEFAULT_CONFIG_PATH)

    parser.add_option('-u', '--fuelurl',
                      help='fuel rest url',
                      default="http://172.18.201.17:8000/")

    parser.add_option('-d', '--deploy-only',
                      help='only deploy cluster',
                      metavar="CONFIG_FILE",
                      dest="deploy_only")

    parser.add_option('-s', '--save-config',
                      help='save network configuration',
                      metavar='CLUSTER_NAME',
                      dest="save_config", default=None)

    parser.add_option('-r', '--reuse-config',
                      help='reuse previously stored network configuration',
                      dest="reuse_config", action="store_true",
                      default=False)

    parser.add_option('-a', '--auth',
                      help='keystone credentials in format '
                           'username=admin,tenant_name=admin,password=admin',
                      dest="creds", default=None)

    parser.add_option('-D', '--delete',
                      help='delete list of environments separated by coma e.g'
                           'environment1,environment2. Use ALL to delete all',
                      dest='delete', default=None)

    parser.add_option('-e', '--email',
                      help='email to send results. If not provided the results'
                           'will not be sent',
                      dest='email', default=None)

    options, _ = parser.parse_args()

    return options.__dict__


def merge_config(config, command_line):
    if command_line.get('password') is not None:
        config['report']['mail']['password'] = command_line.get('password')
    config['fuelurl'] = command_line['fuelurl']


def setup_logger(cs, config):
    with open(config['log_settings']) as f:
        cfg = yaml.load(f)

    logging.config.dictConfig(cfg)

    cs.set_logger(logging.getLogger('clogger'))
    # fuel_rest_api.set_logger(logging.getLogger('clogger'))


def deploy_single_cluster(cs, args, clusters, logger, auto_delete=True,
                          additional_cfg=None):
    cluster_name_or_file = args['deploy_only']

    file_exists = os.path.exists(cluster_name_or_file)
    if cluster_name_or_file.endswith('.yaml') and file_exists:
        try:
            cluster = yaml.load(open(cluster_name_or_file).read())
        except Exception:
            print "Failed to load cluster from {}".format(cluster_name_or_file)
            raise
    else:
        try:
            cluster = clusters[cluster_name_or_file]
        except KeyError:
            templ = "Error: No cluster with name {} found"
            logger.fatal(templ.format(cluster_name_or_file))
            return 1

    if auto_delete:
        cs.delete_if_exists(cluster['name'])

    cs.deploy_cluster(cluster, additional_cfg=additional_cfg)
    return 0


def main():
    # prepare and config
    args = parse_command_line()
    config = parse_config(args['config'])
    merge_config(config, args)
    cfg_fname = config["gui_config_file"]
    creds = args.get('creds')
    admin_node_ip = urlparse.urlparse(config['fuelurl']).hostname
    conn_dict = {"SERVER_ADDRESS": admin_node_ip}
    if creds:
        keyst_creds = dict([pair.split("=") for pair in creds.split(",")
                            if pair and "=" in pair])
        required_keys = ['username', 'password']
        if keyst_creds and all([key in keyst_creds for key in required_keys]):
            conn_dict.update({"KEYSTONE_USER": keyst_creds['username'],
                              "KEYSTONE_PASSWORD": keyst_creds['password']})
    client.connect(config=conn_dict)
    import tools as cs
    from fuelclient.objects import Environment
    setup_logger(cs, config)
    logger = logging.getLogger('clogger')

    test_run_timeout = config.get('testrun_timeout', 3600)

    path = os.path.join(os.path.dirname(DEFAULT_CONFIG_PATH),
                        config['tests']['clusters_directory'])

    clusters = cs.load_all_clusters(path)

    clusters_to_delete = args.get('delete')
    if clusters_to_delete:
        if clusters_to_delete == "ALL":
            cs.delete_all_clusters()
        else:
            for cl_name in clusters_to_delete.split(','):
                cs.delete_if_exists(cl_name)
        return

    saved_cfg = None
    if args.get('reuse_config') is True:
        saved_cfg = cs.load_config(cfg_fname)

    if args.get('deploy_only') is not None:
        return deploy_single_cluster(cs, args, clusters, logger,
                                     additional_cfg=saved_cfg)

    save_cluster_name = args.get('save_config')
    if save_cluster_name is not None:
        clusters = list(Environment.get_all())
        if save_cluster_name == "AUTO":
            if len(clusters) > 1:
                print "Can't select cluster - more then one available"
                return 1
            save_cluster_name = clusters[0].name

        for cluster in clusters:
            if cluster.name == save_cluster_name:
                cfg = cs.load_config_from_fuel(cluster.id)
                cs.store_config(cfg, cfg_fname)
        return 0

    tests_cfg = config['tests']['tests']
    for _, test_cfg in tests_cfg.iteritems():
        cluster = clusters[test_cfg['cluster']]

        tests_to_run = test_cfg['suits']
        cont_man = cs.make_cluster(cluster,
                                   auto_delete=True,
                                   additional_cfg=saved_cfg)

        with cont_man as cluster_id:
            results = cs.run_all_tests(cluster_id,
                                       test_run_timeout,
                                       tests_to_run)

            tests = []
            for testset in results:
                tests.extend(testset['tests'])

            failed_tests = [test for test in tests
                            if test['status'] == 'failure']

            for test in failed_tests:
                logger.debug(test['name'])
                logger.debug(" "*10 + 'Failure message: '
                             + test['message'])

            email_for_results = args.get("email")
            if email_for_results:
                cs.send_results(email_for_results, tests)

    return 0


if __name__ == "__main__":
    exit(main())
