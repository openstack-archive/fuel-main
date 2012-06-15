from django_nose import NoseTestSuiteRunner
from djcelery.contrib.test_runner import CeleryTestSuiteRunner
from django.conf import settings


class MyRunner(NoseTestSuiteRunner, CeleryTestSuiteRunner):

    def setup_test_environment(self, **kwargs):
        super(MyRunner, self).setup_test_environment(**kwargs)
        # As we don't have it in production, it should not be used in tests
        settings.CELERY_EAGER_PROPAGATES_EXCEPTIONS = False
