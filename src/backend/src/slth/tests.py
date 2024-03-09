import os
from datetime import date, timedelta
from unittest import skipIf

from django.core.cache import cache
from django.core.management import call_command
from .selenium import SeleniumTestCase


# @skipIf(os.environ.get("FRONTEND_PROJECT_DIR") is None, "FRONTEND_PROJECT_DIR is not set")
class IntegrationTest(SeleniumTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test(self):
        if self.step("1"):
            self.create_superuser("admin@tavos.com", "123")
        if self.step("2"):
            self.open("/admin/")
            self.wait(3)
            self.open('/')
