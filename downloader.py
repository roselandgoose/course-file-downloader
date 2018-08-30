from getpass import getpass

from seleniumrequests import Chrome
from os import path # for specifying path to Chromium
from selenium.webdriver.chrome.options import Options # for specifying headlessness and path

from time import sleep # for adding human delays
from random import random as rand # for randomizing delays

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from selenium.common.exceptions import StaleElementReferenceException as stale


def driver_init(options=None):
    chrome_options = Options()
    chrome_options.binary_location = '/usr/bin/chromium'
    #chrome_options.add_argument('headless')

    if options:
        for option in options:
            chrome_options.add_argument(option)
    
    driver = Chrome(executable_path=path.abspath('chromedriver'), chrome_options=chrome_options)
    driver.implicitly_wait(10) # seconds

    return driver


def get_credentials():
    user = input('Please enter your username: ')
    password = getpass('Please enter your password: ')
    credentials = {'user': user, 'password': password}
    return credentials


# Function for delaying actions of browsing agent to respect server resources
def delay(low, expect):
    if (low < 0.5):
        low = 0.5
    if (expect <= low):
        duration = low
    else:
        duration = (2 * expect - (2 * low)) * rand() + low
    sleep(duration)


# Functions for finding elements with proper wait conditions
def get_element_by_xpath(driver, wait_limit, el_path):
    return WebDriverWait(driver, wait_limit).until(
        expected_conditions.presence_of_element_located((By.XPATH, el_path))
    )

def get_elements_by_xpath(driver, wait_limit, el_path):
    return WebDriverWait(driver, wait_limit).until(
        expected_conditions.presence_of_all_elements_located((By.XPATH, el_path))
    )

def get_element_by_css(driver, wait_limit, el_css):
    return WebDriverWait(driver, wait_limit).until(
        expected_conditions.presence_of_element_located((By.CSS_SELECTOR, el_css))
    )


def anticipate_staleness(func):
    def wrapper():
        n = 3
        while n >= 0:
            try:
                result = func()
                break
            except stale:
                n -= 1
        else:
            raise stale
        return result

    return wrapper

