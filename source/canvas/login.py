import logging
log = logging.getLogger(__name__)
from sys import exit as exits

from inspect import currentframe

from getpass import getpass
from os import environ

def get_credentials():
    log.info(currentframe().f_code.co_name)
    print("Credentials may be supplied manually or via CANVAS_USERNAME" +
          " and CANVAS_PASSWORD environment variables.")
    user = environ.get('CANVAS_USERNAME')
    if user:
        print("Canvas username found in environment")
    else:
        user = input('Please enter your Canvas username: ')
    password = environ.get('CANVAS_PASSWORD')
    if password:
        print("Canvas password found in environment")
    else:
        password = getpass('Please enter your Canvas password: ')
    return (user, password)

def open_dashboard(driver, user, password):
    log.info(currentframe().f_code.co_name)
    driver.get("https://canvas.northwestern.edu/")

    user_form = driver.get_el_by_xpath(2, "//*[@id='idToken1']")
    psswd_form = driver.get_el_by_xpath(2, "//*[@id='idToken2']")
    log.info("Located forms")

    user_form.send_keys(user)
    driver.delay(0.5, 1)
    psswd_form.send_keys(password)
    driver.delay(0.5, 1)

    from selenium.webdriver.common.keys import Keys
    driver.get_el_by_xpath(2, "//*[@id='loginButton_0']").send_keys(Keys.ENTER)

