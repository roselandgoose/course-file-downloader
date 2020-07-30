import logging
log = logging.getLogger(__name__)

# Webdriver module
#from seleniumrequests import Chrome
from seleniumrequests import Firefox

# Specify browser executable path
from os import path

# Specify headlessness and path
#from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from selenium.common.exceptions import StaleElementReferenceException as stale

class PatientWebdriver(Firefox):
    def __init__(self, options=None):
        browser_options = Options()
        #browser_options.binary_location = which('firefox')
        #browser_options.add_argument('headless')
        if options:
            for option in options:
                browser_options.add_argument(option)
        super().__init__(executable_path=path.abspath('source/webdriver/geckodriver'),
                         firefox_options=browser_options)
    def goto(self, url):
        if self.current_url != url:
            self.get(url)
            self.delay(3,5)

    # Functions for finding elements with proper wait conditions
    def get_el_by_xpath(self, wait_limit, el_path):
        return WebDriverWait(self, wait_limit).until(
            expected_conditions.presence_of_element_located((By.XPATH, el_path))
        )

    def get_el_by_rel_xpath(self, wait_limit, base_el, el_path):
        return WebDriverWait(base_el, wait_limit).until(
            expected_conditions.presence_of_element_located((By.XPATH, el_path))
        )

    def get_els_by_rel_xpath(self, wait_limit, base_el, el_path):
        return WebDriverWait(base_el, wait_limit).until(
            expected_conditions.presence_of_all_elements_located((By.XPATH, el_path))
        )
        
    def get_els_by_xpath(self, wait_limit, el_path):
        return WebDriverWait(self, wait_limit).until(
            expected_conditions.presence_of_all_elements_located((By.XPATH, el_path))
        )

    def get_el_by_css(self, wait_limit, el_css):
        return WebDriverWait(self, wait_limit).until(
            expected_conditions.presence_of_element_located((By.CSS_SELECTOR, el_css))
        )

    # Function for delaying actions of browsing agent to respect server resources
    def delay(self, low, expect):
        from time import sleep # for adding human delays
        from random import random as rand # for randomizing delays
        if (low < 0.5):
            low = 0.5
        if (expect <= low):
            duration = low
        else:
            duration = (2 * expect - (2 * low)) * rand() + low
        sleep(duration)


def retry_thrice(func):
    def wrapper(*pargs, **kwargs):
        n = 1
        while n <= 3:
            try:
                result = func(*pargs, **kwargs)
                break
            except stale:
                log.info("Error #{} occured in staleness anticipation wrapper"\
                    .format(n))
                n += 1
        else:
            raise stale
        return result

    return wrapper

