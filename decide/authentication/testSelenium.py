from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from .models import CustomUser


class TestSignin(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = "localhost"
        cls.port = 8000
        super(TestSignin, cls).setUpClass()

    def setUp(self):
        self.driver = webdriver.Chrome()

        u = CustomUser(username='voter1')
        u.set_password('123')
        u.save()
        u2 = CustomUser(username='admin')
        u2.set_password('admin')
        u2.is_superuser = True
        u2.save()

    def tearDown(self):
        self.driver.close()

    # def test_signin(self):
    #     self.driver.get(
    #         self.live_server_url +
    #         "/authentication/accounts/login/"
    #     )
    #     self.driver.find_element_by_id('id_login').send_keys("voter1")
    #     self.driver.find_element_by_id(
    #         'id_password'
    #     ).send_keys("123" + Keys.ENTER)
    #     self.assertEqual(
    #         self.driver.find_element_by_id('navbarDropdownMenuLink').text,
    #         'voter1'
    #     )

    # TODO: Comentado por imcompatibilidad de versiones con selenium 2.33.0
    # def test_fake_signin(self):
    #     self.driver.get(
    #         self.live_server_url +
    #         "/authentication/accounts/login/"
    #     )
    #     self.driver.find_element_by_id('id_login').send_keys("voter")
    #     self.driver.find_element_by_id(
    #         'id_password'
    #     ).send_keys("123" + Keys.ENTER)
    #     self.assertNotEqual(
    #         self.driver.find_element_by_id('navbarDropdownMenuLink').text,
    #         'voter1'
    #     )

    def test_no_username_signin(self):
        self.driver.get(
            self.live_server_url +
            "/authentication/accounts/login/"
        )
        self.driver.find_element_by_id('id_login').send_keys("")
        self.driver.find_element_by_id(
            'id_password'
        ).send_keys("123" + Keys.ENTER)
        self.assertEqual(
            self.driver.find_element_by_class_name('errorlist').text,
            'This field is required.'
        )

    def test_no_password_signin(self):
        self.driver.get(
            self.live_server_url +
            "/authentication/accounts/login/"
        )
        self.driver.find_element_by_id('id_login').send_keys("voter1")
        self.driver.find_element_by_id(
            'id_password'
        ).send_keys("" + Keys.ENTER)
        self.assertEqual(
            self.driver.find_element_by_class_name('errorlist').text,
            'This field is required.'
        )

    def test_no_password_no_username_signin(self):
        self.driver.get(
            self.live_server_url +
            "/authentication/accounts/login/"
        )
        self.driver.find_element_by_id('id_login').send_keys("")
        self.driver.find_element_by_id(
            'id_password'
        ).send_keys("" + Keys.ENTER)

        errors = self.driver.find_elements_by_class_name('errorlist')
        for error in errors:
            self.assertEqual(
                error.text,
                'This field is required.'
            )
