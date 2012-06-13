from django.test import TestCase


class TestSampleEnvironmentFixtureLoad(TestCase):

    fixtures = ['sample_environment']

    def test(self):
        pass
