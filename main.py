from selenium import webdriver
from os import path # for specifying path to Chromium
from selenium.webdriver.chrome.options import Options # for specifying headlessness and path

from time import sleep # for adding human delays
from random import random as rand # for randomizing delays

user = ""
password = ""

# 0: no debugging --> 1: print delays and error catches --> 2: print function calls --> 3: print try attempts and exits
verbose_level = 3

def vprint(string, activation):
    if verbose_level >= activation:
        print(string)


# Function for delaying actions of browsing agent to respect server resources
def delay(low, expect):
    vprint("delay", 2)
    if (low < 0.5):
        low = 0.5
    if (expect <= low):
        duration = low
    else:
        duration = (2 * expect - (2 * low)) * rand() + low
    vprint("Sleeping for {} seconds".format(duration), 1)
    sleep(duration)


# Class for defining browsing agent to perform file downloading
class agent:
    def __init__(self, options=None):
        vprint("agent.__init__", 2)
        chrome_options = Options()
        chrome_options.binary_location = '/usr/bin/chromium'

        if options:
            for option in options:
                chrome_options.add_argument(option)
        
        self.driver = webdriver.Chrome(executable_path=path.abspath('chromedriver'), chrome_options=chrome_options)
        self.driver.implicitly_wait(10) # seconds

        self.file_tree = []


    def login_canvas(self):
        vprint("agent.login_canvas", 2)
        self.driver.get("https://canvas.northwestern.edu/files")

        user_form = self.driver.find_element_by_id('IDToken1')
        psswd_form = self.driver.find_element_by_id('IDToken2')

        user_form.send_keys(user)
        delay(0.5, 1)
        psswd_form.send_keys(password)
        delay(0.5, 1)
        psswd_form.submit()


if __name__ == "__main__":
    agent0 = agent()
    agent0.login_canvas()


