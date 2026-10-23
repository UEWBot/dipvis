from django.conf import settings
from django_slowtests.testrunner import DiscoverSlowestTestsRunner


class TestRunner(DiscoverSlowestTestsRunner):
    """Test runner that keeps the game seeder from logging its state"""

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        settings.GAME_SEEDER_LOG_STATE = False
