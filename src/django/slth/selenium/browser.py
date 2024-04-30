import datetime
import unicodedata
import os
import sys
import time

from django.conf import settings
from selenium import webdriver
from selenium.common.exceptions import (
    ElementNotInteractableException,
    StaleElementReferenceException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select


from selenium.webdriver import Remote, Firefox
from selenium.webdriver.remote.file_detector import LocalFileDetector
from selenium.webdriver.remote.webelement import WebElement

REMOTE = 'SELENIUM_HOST' in os.environ

def to_label_case(text):
    return unicodedata.normalize('NFD', text.replace('-', '').replace('_', '').lower())

def _upload(self, filename):
    return filename

WebElement._upload = _upload

class Browser(Remote if REMOTE else Firefox):
    def __init__(self, server_url, options=None, verbose=True, slowly=False, maximize=True, headless=True):
        if not options:
            options = Options()
        if maximize:
            options.add_argument("--start-maximized")
        else:
            options.add_argument("--window-size=720x800")
        if headless and "-v" not in sys.argv:
            options.add_argument("--headless")
        
        if REMOTE:
            url = 'http://{}:{}'.format(
                os.environ.get('SELENIUM_HOST', '127.0.0.1'),
                os.environ.get('SELENIUM_POST', '4444')
            )
            super().__init__(command_executor=url, options=options)
            self.file_detector = LocalFileDetector()
        else:
             super().__init__(options=options)

        self.cursor = None
        self.verbose = verbose
        self.slowly = slowly
        self.server_url = server_url
        self.headless = headless

        if maximize:
            self.maximize_window()
        else:
            self.set_window_position(700, 0)
            self.set_window_size(720, 800)
        self.switch_to.window(self.current_window_handle)

    def slow(self, slowly=True):
        self.slowly = slowly

    def is_cursor_inside(self, tag_name):
        if self.cursor:
            if self.cursor.tag_name == tag_name:
                self.debug(f"Cursor {self.cursor.tag_name} is inside {tag_name}")
                return True
            elif self.cursor.tag_name == "html":
                self.debug(f"Cursor {self.cursor.tag_name} is NOT inside {tag_name}")
                return False
            else:
                parent = self.cursor.find_element("xpath", "..")
                while True:
                    self.debug(f"Checking {parent.tag_name}")
                    if parent.tag_name == tag_name:
                        self.debug(f"Cursor {self.cursor.tag_name} is inside {tag_name}")
                        return True
                    elif parent.tag_name == "html":
                        return False
                    else:
                        parent = parent.find_element("xpath", "..")
        self.debug(f"Cursor {self.cursor.tag_name} is NOT inside {tag_name}")
        return False

    def initialize_cursor(self):
        try:
            dialogs = super().find_elements(By.TAG_NAME, "dialog")
            if dialogs:
                if self.cursor is None or not self.is_cursor_inside("dialog"):
                    self.cursor = dialogs[0]
            else:
                if self.cursor is None or not self.is_cursor_inside("html"):
                    self.cursor = super().find_element(By.TAG_NAME, "html")
            self.cursor.tag_name
        except StaleElementReferenceException:
            self.cursor = super().find_element(By.TAG_NAME, "html")
        self.debug(f"Cursor is at tag {self.cursor.tag_name}")

    def find_elements(self, by, value):
        self.initialize_cursor()
        while True:
            elements = self.cursor.find_elements(by, value)
            if elements:
                self.debug(f"Element {value} found in {self.cursor.tag_name}.")
                return elements
            elif self.cursor.tag_name == "dialog":
                self.debug("Recursive search stopped inside dialog!")
                break
            if self.cursor.tag_name != "html":
                self.debug(f"Element {value} not found in {self.cursor.tag_name}. Searching in the parent element...")
                self.cursor = self.cursor.find_element("xpath", "..")
            else:
                raise WebDriverException(f"Element {value} NOT FOUND in {self.cursor.tag_name}.")
        return []

    def find_element(self, by, value):
        self.initialize_cursor()
        while True:
            elements = self.cursor.find_elements(by, value)
            if elements:
                self.debug(f"Element {value} found in {self.cursor.tag_name}.")
                return elements[0]
            elif self.cursor.tag_name == "dialog":
                self.debug("Recursive search stopped inside dialog!")
                raise WebDriverException(f"Element {value} not found in the dialog.")
            if self.cursor.tag_name != "html":
                self.debug(f"Element {value} not found in {self.cursor.tag_name}. Searching in the parent element...")
                self.cursor = self.cursor.find_element("xpath", "..")
            else:
                raise WebDriverException(f"Element {value} NOT FOUND in {self.cursor.tag_name}.")

    def wait(self, seconds=2):
        time.sleep(seconds)

    def watch(self, e):
        self.save_screenshot("/tmp/test.png")
        if self.headless:
            raise e
        else:
            breakpoint()
            raise e

    def print(self, message):
        if self.verbose:
            print(message)

    def debug(self, message):
        # print(message)
        pass

    def execute_script(self, script, *args):
        super().execute_script(script, *args)
        if self.slowly:
            self.wait(3)

    def open(self, url):
        if url.startswith("http"):
            self.get(url.replace("http://localhost:8000", self.server_url))
        else:
            self.get(f"{self.server_url}{url}")

    def reload(self):
        self.open(self.current_url)

    def enter(self, name, value, submit=False, count=4):
        if callable(value):
            value = value()
        if type(value) == datetime.date:
            value = value.strftime("%Y-%d-%m")
        self.print('{} "{}" for "{}"'.format("Entering", value, name))
        if value:
            value = str(value)
            if len(value) == 10 and value[2] == "/" and value[5] == "/":
                value = datetime.datetime.strptime(value, "%d/%m/%Y").strftime("%Y-%m-%d")
        try:
            widget = self.find_element("css selector", f'[data-label="{to_label_case(name)}"]')
            if widget.tag_name == "input" and widget.get_property("type") == "color":
                self.execute_script(
                    f'document.querySelector(\'input[data-label="{to_label_case(name)}"]\').value = "{value}";'
                )
            else:
                if widget.tag_name == "input" and widget.get_property("type") == "file":
                    value = os.path.join(settings.BASE_DIR, value)
                widget.clear()
                widget.send_keys(value)
        except WebDriverException as e:
            if count:
                self.wait()
                self.enter(name, value, submit, count - 1)
            else:
                self.watch(e)
        if self.slowly:
            self.wait(2)

    def choose(self, name, value, count=4):
        self.print('{} "{}" for "{}"'.format("Choosing", value, name))
        try:
            widgets = self.find_elements(By.CSS_SELECTOR, f'[data-label="{to_label_case(name)}"]')
            if widgets:
                if widgets[0].tag_name.lower() == "select":
                    select = Select(widgets[0])
                    select.select_by_visible_text(value)
                elif widgets[0].tag_name.lower() == "input":
                    widgets[0].send_keys(value)
                    for i in range(0, 10):
                        print('Trying ({}) click at "{}"...'.format(i, value))
                        self.wait(0.5)
                        try:
                            super().find_element(By.CSS_SELECTOR, f'.autocomplete-item[data-label*="{to_label_case(value)}"]').click()
                            self.wait(0.5)
                            break
                        except WebDriverException:
                            pass
                elif widgets[0].get_dom_attribute("type") == "radio":
                    widgets[0].click()
                elif widgets[0].get_dom_attribute("type") == "checkbox":
                    widgets[0].click()
            else:
                raise WebDriverException()
        except WebDriverException as e:
            if count:
                self.wait()
                self.choose(name, value, count - 1)
            else:
                self.watch(e)
        if self.slowly:
            self.wait(2)

    def see(self, text, flag=True, count=4):
        if flag:
            self.print(f'See "{text}"')
            try:
                assert text in self.find_element(By.TAG_NAME, "body").text
            except AssertionError as e:
                if count:
                    self.wait()
                    self.see(text, flag, count - 1)
                else:
                    self.watch(e)
            if self.slowly:
                self.wait(2)
        else:
            self.print(f'Can\'t see "{text}"')
            try:
                assert text not in self.find_element(By.TAG_NAME, "body").text
            except AssertionError as e:
                if count:
                    self.wait()
                    self.see(text, flag, count - 1)
                else:
                    self.watch(e)
            if self.slowly:
                self.wait(2)

    def look_at(self, text, count=4):
        self.print(f'Loking at "{text}"')
        try:
            self.cursor = self.find_element(By.CSS_SELECTOR, f'[data-label="{to_label_case(text)}"]')
            if self.cursor:
                self.execute_script("arguments[0].scrollIntoView();", self.cursor)
                self.debug(f"Cursor is now at {self.cursor.tag_name}")
        except WebDriverException as e:
            if count:
                self.wait()
                self.look_at(text, count - 1)
            else:
                self.watch(e)
        if self.slowly:
            self.wait(2)

    def click(self, text, count=4):
        self.print(f'Clicking "{text}"')
        try:
            elements = self.find_elements("css selector", f'[data-label="{to_label_case(text)}"]')
            if elements:
                for element in elements:
                    try:
                        element.click()
                        break
                    except ElementNotInteractableException:
                        pass
            else:
                raise WebDriverException()
        except WebDriverException as e:
            if count:
                self.wait()
                self.click(text, count=count - 1)
            else:
                self.watch(e)

    def close(self, seconds=0):
        self.wait(seconds)
        super().close()
