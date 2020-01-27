from django.test import TestCase
'''
import unittest
from selenium import webdriver
import os

class TestSignup(unittest.TestCase):

    def setUp(self):
        locate = os.name
        if locate == 'nt':
            self.path = os.path.realpath("../drivers/phantomjs.exe")
        else:
            self.path = os.path.realpath("../drivers/phantomjs")
        self.driver = webdriver.PhantomJS(executable_path=self.path)
        
    # Alberto
    # Test 1:
    # Hace una captura de pantalla después de hacer click en el botón de 
    # activación del modo oscuro
    def testActivateDarkMode(self):
        self.driver.get("http://localhost:8000/visualizer/2/")
        activeDarkMode = self.driver.find_element_by_id("activeDarkModeButton")
        activeDarkMode.click()
        self.driver.save_screenshot("activateDarkModeScreenshot.jpg")
        self.assertTrue(True)

    # Test 2:
    # Hace una captura de pantalla después de hacer click en el botón de 
    # activación del modo claro
    def testActivateLightMode(self):
        self.driver.get("http://localhost:8000/visualizer/2/")
        activeLightMode = self.driver
                              .find_element_by_id("activeLightModeButton")
        activeLigthMode.click()
        self.driver.save_screenshot("activateLightModeScreenshot.jpg")
        self.assertTrue(True)

    # Test 3:
    # Comprueba que se crea la cookie al activar el modo oscuro
    def testExistsCookie(self):
        self.driver.get("http://localhost:8000/visualizer/2/")
        activeDarkMode = self.driver.find_element_by_id("activeDarkModeButton")
        activeDarkMode.click()
        cookie = driver.manage().getCookieNamed("theme")
        self.assertTrue(cookie == "dark")

    # Test 4:
    # Comprueba que se actualiza la cookie al cambiar al modo claro
     def testUpdateCookie(self):
        self.driver.get("http://localhost:8000/visualizer/2/")
        activeLightMode = self.driver
                              .find_element_by_id("activeLightModeButton")
        activeLightMode.click()
        cookie = driver.manage().getCookieNamed("theme")
        self.assertTrue(cookie == "light")
        
    # Sergio    
    # Testing that the graph is showed to the user on a tallied test
    # Must return true if the canvas is displayer
    def test_exist_canvas_on_tallied_test(self):
        self.driver.get("http://localhost:8000/visualizer/3/")
        canvas = self.driver.find_elements_by_tag_name("canvas")
        self.assertTrue(len(canvas) > 0)

    # Test 2
    # Testing there is a form to change the chartjs type of the representation
    # Must return true if there are 1 select displayed and 5 options
    # inside the select
    def test_form_select_tallied_test(self):
        self.driver.get("http://localhost:8000/visualizer/2/")
        select = self.driver.find_elements_by_tag_name("select")
        options = self.driver.find_elements_by_tag_name("option")
        self.assertTrue(len(select) == 1 and len(options) == 5)

    def tearDown(self):
        self.driver.quit()


if __name__ == '__main__':
    unittest.main()
    
'''
