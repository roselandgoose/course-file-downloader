from selenium import webdriver
from os import path # for specifying path to Chromium
from selenium.webdriver.chrome.options import Options # for specifying headlessness and path

from selenium.common.exceptions import StaleElementReferenceException as stale, NoSuchElementException as no_such # for cleaner exception handling
from retrying import retry # for cleaner exception handling

from re import search # for parsing course titles and folder links
from re import compile as comp # for parsing course titles

from time import sleep # for adding human delays
from random import random as rand # for randomizing delays

user = ""
password = ""

# 0: no debugging --> 1: print delays and error catches --> 2: print function calls --> 3: print try attempts and exits
verbose_level = 3

def vprint(string, activation):
    if verbose_level >= activation:
        print(string)


'''
    Process for downloading files from Canvas:
        1. navigate to canvas files site and login
        2. locate list of canvas courses
        3. scan folder hierarchy by clicking through folder links
        4. download desired files by making http requests with AWS
'''

# Function for extracting semantic data from canvas course label
def parse_title(reg_ex_str, label):
    vprint("canvas_course.parse_title", 2)

    pattern = comp(reg_ex_str)
    result = pattern.search(label)
    if not result:
        return "unknown"
    else:
        return result.group(0)


# Class for containing canvas course label information
class canvas_course:
    def __init__(self, label):
        vprint("canvas_course.__init__", 2)
        
        self.label = label

        self.year = parse_title("^\d{4}", label)
        self.quarter = parse_title("(?<=^\d{4})[A-Z]{2}(?=\_)", label)
        self.subject = parse_title("(?<=^\d{4}[A-Z]{2}\_)[A-Z,\_]{4,}(?=\_)", label)
        self.course_number = parse_title("(?<=[A-Z,\_]{3}\_)[\d,\-]{3,}(?=\_)", label)
        self.section_number = parse_title("(?<=\d\_SEC)\d+(?=[\_, ])", label)
        self.title = parse_title("(?<=\d[\_, ])[A-Z][a-z].+$", label)


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

# Functions for conditional retrying
def retry_stale(exception):
    vprint(exception, 3)
    return isinstance(exception, stale)

def retry_no_such(exception):
    vprint(exception, 3)
    return isinstance(exception, no_such)

def retry_stale_or_no_such(exception):
    vprint(exception, 3)
    return isinstance(exception, stale) or isinstance(exception, no_such)


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


    # Find list of canvas courses and file categories and builds file tree
    def build_canvas_file_tree(self):
        vprint("agent.build_canvas_file_tree", 2)

        delay(0.5, 2)

        # Files page features:
        #   * a left pane listing courses and groups in a filesystem tree
        #   * a right file panel listing the files and folders in the current folder

        # Pane has class 'ef-folder-content'
        left_pane = self.driver.find_element_by_class_name('ef-folder-content')

        # Categories in the left pane are li elements with attribute 'data-id'
        #   div - ef-folder-content
        #       div - ef-folder-list
        #           ul - tree
        #               li - data-id
        
        left_pane_elements = left_pane.find_elements_by_xpath("./div/div/ul/li[@data-id]")

        # Some items in left pane are hidden elements, used only by the scripts on the page. These need to be filtered out.
        # It is also wise to only hold onto element references for as long as necessary, so I only store the ids and labels within my canvas_root class. 

        for element in left_pane_elements:

            # The text label displayed for each valid element is stored in the 'aria-label' attribute.
            label = element.get_attribute("aria-label")
            
            # Valid courses and categories have labels like "2018SP_EECS_349-0_SEC20 Machine Learning"
            if bool(search("\d{4}[A-Z]{2}\_[A-Z]", label)):
                
                self.file_tree.append(canvas_root(element, label))

        for node in self.file_tree:
            element = self.driver.find_element_by_css_selector("li[data-id='" + node.data_id + "']")
            
            # click on the left-pane element to display course tree
            element.click()
            node.children = self.build_canvas_subtree()


    @retry(retry_on_exception=retry_no_such, wait_random_min=1000, wait_random_max=2000)
    def build_canvas_subtree(self):
        vprint("agent.build_canvas_subtree", 2)
        children = []

        delay(1.5, 2.5)
        right_pane_ids = self.find_right_pane_elements()

        for element_id in right_pane_ids:
            children.append(canvas_node(element_id, self))

        # Go back up to previous tree depth after recurring down
        delay(1.5, 2.5)
        self.driver.back()
        delay(1.5, 2.5)
        
        return children


    # Locates elements in right pane and returns list of their react_ids
    @retry(retry_on_exception=retry_stale_or_no_such, wait_random_min=1000, wait_random_max=2000)
    def find_right_pane_elements(self):
        vprint("agent.find_right_pane_elements", 2)

        right_pane_directory = self.find_right_pane()

        # Files and folders in the right pane are divs with class 'ef-item-row'
        #   div - ef-directory
        #       div - grid
        #           div - ef-item-row

        vprint("looking for right pane elements", 3)

        # Elements in current directory
        elements = right_pane_directory.find_elements_by_xpath("./div/div[@class='ef-item-row']")

        vprint("looking for right pane element ids", 3)

        # Extract ids to drop element references
        return [element.get_attribute("data-reactid") for element in elements]


    # Locates right pane with proper exception handling and cleaner retries
    @retry(retry_on_exception=retry_no_such, wait_random_min=1000, wait_random_max=2000)
    def find_right_pane(self):
        vprint("agent.find_right_pane", 2)
        return self.driver.find_element_by_class_name('ef-directory')

class canvas_root:
    def __init__(self, element, label):
        vprint("canvas_root.__init__", 2)

        self.label = label
        self.data_id = element.get_attribute("data-id")

        self.children = []


class canvas_node:
    @retry(retry_on_exception=retry_stale, wait_random_min=1000, wait_random_max=2000)
    def __init__(self, element_react_id, agent):
        vprint("canvas_node.__init__", 2)

        # Each item is a row containing data in different elements
        #   div - ef-item-row
        #       div - ef-name-col
        #           a - ef-name-col__link
        #               span - ef-name-col__text
        #       div - ef-date-created-col
        #           time - datetime
        #       div - ef-date-modified-col
        #           time - datetime
        #       div - ef-modified-by-col ellipsis
        #           a - ef-plain-link

        element = agent.driver.find_element_by_css_selector("div[data-reactid='" + element_react_id  + "']")

        vprint("looking for element a_name", 3)
        a_name = element.find_element_by_xpath("./div/a[@class='ef-name-col__link']")

        vprint("looking for element link", 3)
        link = a_name.get_attribute("href")

        # File links are "https://canvas.nor..." links whereas folder links are relative
        is_folder = bool(search("/files/folder", link))
        if is_folder:
            self.name = a_name.find_element_by_xpath("./span/span[@class='ef-name-col__text']").text
        else:
            self.name = a_name.find_element_by_xpath("./span[@class='ef-name-col__text']").text

        #self.date_created

        #self.date_modified

        #self.modified_by

        self.link = link

        if is_folder:
            delay(1.5, 2)
            a_name.click()

            self.children = agent.build_canvas_subtree()
        else:
            self.children = False


    def download(self):
        vprint("canvas_file.download", 2)

        # HTTPS? Plan:
            # Send GET request using download link that I've found
            # Receive a 302 FOUUND and redirect to a more precise download link
            # Send GET request with that link
            # Receive a 302 FOUUND and redirect to AWS download link

        # Now here I'm not suer how to branch. My first thought is:
            # Parse final link for preferential filename
            # Modify link to append unique id to requested filename
            # Send final GET request
            # Monitor download directory for download of requested filename
            # Import downloaded file into store/library

        # But there may be a more direct way to download it once I've got the AWS link. I'll need the AWS alg/creds for sure, but I might be able to change the content disposition or use something like wget

        # And before I can do any of this, I need to know how to get my agent header/cookies from Selenium out into the conn library, or how to send requests through Selenium.


def print_tree(tree):
    vprint("print_tree", 2)

    def p_tree_h(n):
        print(n.name)
        if not (n.children == False):
            for child in n.children:
                p_tree_h(child)

    for root in tree:
        print(root.label)
        for child in root.children:
            p_tree_h(child)



if __name__ == "__main__":
    agent0 = agent()
    agent0.login_canvas()
    agent0.build_canvas_file_tree()

    print_tree(agent0.file_tree)


