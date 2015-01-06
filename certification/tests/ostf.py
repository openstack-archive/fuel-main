import base
from certification.tools import with_timeout


class OSTFTests(base.BaseTests):

    def run_test(self, test_name):
        data = {'testset': test_name,
                'tests': [],
                'metadata': {'cluster_id': self.cluster_id}}

        return self.conn.post('ostf/testruns', [data])

    def run_tests(self, tests):
        for test_name in tests:
            print test_name

            run_id = self.run_test(test_name)[0]['id']

            def check_ready(self, run_id):
                status = self.conn.get('/ostf/testruns/{}'.format(run_id))
                return status['status'] == 'finished'

            wt = with_timeout(self.timeout, "run test " + test_name)
            wt(check_ready)(self, run_id)

            yield self.conn.get('/ostf/testruns/{}'.format(run_id))

    def get_available_tests(self):
        testsets = self.conn.get('/ostf/testsets/{}'.format(self.cluster_id))
        return [testset['id'] for testset in testsets]
