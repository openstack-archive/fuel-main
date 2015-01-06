
class BaseTests(object):

    def __init__(self, conn, cluster_id, timeout):
        self.conn = conn
        self.cluster_id = cluster_id
        self.timeout = timeout

    def run_tests(self, tests):
        raise NotImplementedError()

    def get_available_tests(self):
        raise NotImplementedError()
