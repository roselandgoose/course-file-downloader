import logging
log = logging.getLogger(__name__)
from inspect import currentframe
from sys import exit as exits

from . import parse


long_wait = 20
normal_wait = 10
short_wait = 5


def find_canvas_files_page_courses(driver, settings):
    log.info(currentframe().f_code.co_name)
    driver.goto('https://canvas.northwestern.edu/files/')

    # Courses in the left pane are li elements with attribute 'data-id.'
    # Absolute path with markers for efficiency
    course_item_xpath = "//body/div/div/div[@id='main']/div/div/div"+\
                        "[@id='content']/div/div[@class='ef-main']/"+\
                        "aside/div/div/ul/li"
    left_pane_elements = driver.get_els_by_xpath(long_wait,
        course_item_xpath + "[@data-id]"
    ) 
    courses = {}
    data_ids = {}
    for el in left_pane_elements:
        # The text label displayed for each valid element is stored in the 'aria-label' attribute.
        label = el.get_attribute("aria-label")
        label, course = parse.identify_course(label, '', settings)
        if not course:
            continue
        course.course_source_type = "USER_FILES_TREE"
        courses[label] = course
        data_ids[label] = int(el.get_attribute("data-id"))
    for label in courses:
        data_id = data_ids[label]
        driver.delay(0.5, 1)
        driver.get_el_by_xpath(long_wait, course_item_xpath +\
                                    "[@data-id={}]".format(data_id)\
                              ).click()
        courses[label].canvas_course_id = driver.current_url\
                                           .split('courses_')\
                                           [-1].strip('/')
    return courses

def find_canvas_course_pages(driver, settings):
    log.info(currentframe().f_code.co_name)
    driver.goto('https://canvas.northwestern.edu/courses')
    courses = {}

    course_row_els = driver.get_els_by_xpath(short_wait, "/html/body/div[2]/"+
                                                "div[2]/div/div[2]/"+
                                                "div[1]/div/table[1]/"+
                                                "tbody/tr[td[2]/a]")
    course_row_els += driver.get_els_by_xpath(short_wait, "/html/body/div[2]/"+
                                                 "div[2]/div/div[2]/"+
                                                 "div[1]/div/table[2]/"+
                                                 "tbody/tr[td[2]/a]")
    for course_row_el in course_row_els:
        course_el = driver.get_el_by_rel_xpath(short_wait,
                                               course_row_el,
                                               ".//td[2]/a")
        label = course_el.get_attribute('title')
        nickname = driver.get_el_by_rel_xpath(short_wait,
                                         course_row_el,
                                         ".//td[3]").text
        label, course = parse.identify_course(label, nickname, settings)
        if not course:
            continue
        course.canvas_course_id = course_el.get_attribute('href')\
                                              .split("courses/")[-1]
        course.course_source_type = "ALL_COURSES_LIST"
        courses[label] = course
    return courses

def raw_string_to_date(string):
    import datetime
    import time
    if '\n' in string:
        string = string.split('\n')[0]
    # should use python 3.8 datetime.strptime()
    return datetime.datetime(*(time.strptime(string, "%b %d, %Y")[0:6]))

def raw_file_size_to_bytes(string):
    if string == '--':
        return -1
    number, unit = string.split(' ')
    return float(number) * {'bytes': 1,
                       'KB': pow(10,3),
                       'MB': pow(10,6),
                       'GB': pow(10,9),
                       'TB': pow(10,12)
                      }[unit]

def index_right_pane_file_tree(driver, settings):
    log.info(currentframe().f_code.co_name)
    from filetree import CourseFile, CourseDir
    import webdriver
    files = []
    @webdriver.retry_thrice
    def find_table():
        return driver.get_el_by_xpath(normal_wait, "html/body/"+\
                                         "div[@id='application']/"+\
                                         "div[2]/div[@id='main']/"+\
                                         "/div[3]/div[1]/"+\
                                         "div[@id='content']/"+\
                                         "div/div[2]/"+\
                                         "div[@class='ef-directory']/"+\
                                         "div/div")

    divs_in_table = driver.get_els_by_rel_xpath(normal_wait, find_table(), "./div")
    div_one_indices = []
    for div_index, div in enumerate(divs_in_table):
        div_class = div.get_attribute('class')
        if div_class == "ef-item-row":
            div_one_indices.append(div_index+1)

    @webdriver.retry_thrice
    def find_table_text_by_rel(xpath, div_one_index):
        el = driver.get_el_by_rel_xpath(long_wait, find_table(),
                        "./div[{}]/{}".format(div_one_index, xpath))
        # Will only work as long as there are no '/'s in classname
        if xpath.split('/')[-1][0] == 'a':
            return el.get_attribute('href')
        else:
            return el.text

    @webdriver.retry_thrice
    def scrape_table_row(div_one_index):
        file_name_path = "div[@class='ef-name-col']"
        file_link_path = "/a[@class='ef-name-col__link']"
        log.info("  Find file name")
        file_name = find_table_text_by_rel(file_name_path, div_one_index)
        log.info("  Find file link")
        file_link = find_table_text_by_rel(file_name_path+file_link_path,
                        div_one_index)
        log.info("  Find file creation date")
        file_date_created = find_table_text_by_rel(
                                "div[@class='ef-date-created-col']",
                                div_one_index)
        log.info("  Find file modification date")
        file_date_modified = find_table_text_by_rel(
                            "div[@class='ef-date-modified-col']",
                            div_one_index)
        log.info("  Find file size")
        file_size_str = find_table_text_by_rel("div[@class='ef-size-col']",
                            div_one_index)
        file_date = raw_string_to_date(file_date_created) 
        try:
            file_date_modified = raw_string_to_date(file_date_modified) 
            if file_date_modified > file_date:
                file_date = file_date_modified
        except ValueError as e:
            log.info("No file modification date")
        
        if '/files/folder/' in file_link:
            log.info("Its a dir, entering: {}".format(file_name))
            url = driver.current_url
            driver.goto(file_link)
            children = index_right_pane_file_tree(driver, settings)
            log.info("Returning from dir")
            driver.goto(url)
            folder_size = 0
            for child in children:
                folder_size += child.size_bytes
            return CourseDir(name_in_fs=file_name,
                                   size_bytes=folder_size,
                                   iso_date_class=file_date,
                                   download_url=file_link,
                                   children=children)
        else:
            log.info("Its a file: {}".format(file_name))
            file_size = raw_file_size_to_bytes(file_size_str)
            if file_size == -1:
                log.error("file without size?")
                exits(1)
            return CourseFile(name_in_fs=file_name,
                                    size_bytes=file_size,
                                    iso_date_class=file_date,
                                    download_url=file_link)

    log.info("Found {} possible file/folders".format(len(div_one_indices)))
    for i, div_one_index in enumerate(div_one_indices):
        log.info("Visbile row #{}".format(i+1))
        try:
            files.append(scrape_table_row(div_one_index))
        except Exception as e:
            log.error("Exception occured:")
            log.error(e)
            continue
    
    return files
