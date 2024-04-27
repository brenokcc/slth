from slth.selenium import SeleniumTestCase
class IntegrationTestCase(SeleniumTestCase):
    
    def test(self):
        self.create_superuser('admin', '123')
        self.login('admin', '123')
        self.wait(3)
        self.logout('admin')
