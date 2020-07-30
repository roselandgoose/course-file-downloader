import logging
log = logging.getLogger(__name__)
from inspect import currentframe
from sys import exit as exits

import filetree
from .parse import build_name
from datetime import date as date_module
from copy import deepcopy
class Course(filetree.CourseDir):
    _build_name = build_name

    def __init__(self, *, title, year, quarter, listings, **args):
        self.title              = title
        self.year               = year
        self.quarter            = quarter
        self.course_source_type = args.pop('course_source_type',
                                           'ALL_COURSES_LIST')
        self.canvas_course_id   = args.pop('canvas_course_id', -1)
        settings                = args.pop('settings', {})
        self.listings = []
        for listing in listings:
            if type(listing) == dict:
                listing = CourseListing(**listing)
            self.listings.append(listing)
        name_in_fs = args.pop('name_in_fs', None)
        if not name_in_fs:
            name_in_fs = self._build_name(listing = self.listings[0],
                                          settings = settings,
                                          **self.__dict__)
        args.pop('label', None)
        super().__init__(name_in_fs = name_in_fs, **args)

    def get_date(self, *pos_args):
        latest_iso_date = None
        for child in self.children:
            child_date = child.iso_date_class 
            if not latest_iso_date or child_date > latest_iso_date:
                latest_iso_date = child_date
        if latest_iso_date:
            return latest_iso_date
        else:
            return date_module.today()
        
    def dumpd(self):
        dict_repr = super().dumpd()
        listings = []
        for i in range(len(self.listings)):
            listings.append(deepcopy(self.listings[i].__dict__))
        dict_repr["listings"] = listings
        return dict_repr
        
class CourseListing:
    def __init__(self, **args):
        self.program        = args.pop('program', str())
        self.course_number  = args.pop('course_number', str())
        self.section        = args.pop('section', str())
        assert args == {}, "Unhandled args in {} constructor"\
                                                .format(type(self).__name__)

##
###
##
def update_files(driver, settings):
    # To index the whole tree, we need to:
    #   1. Identify the courses from both the user files page and the
    #      all courses page
    #   2. Visit each course with a files page
    #   3. Click through each directory in the tree recursively
    pass

def index_courses(driver, settings):
    log.info(currentframe().f_code.co_name)
    driver.delay(3, 5)
    courses = []

    from . import scrape
    from .database import get_course, add_course, get_all_courses, \
                          replace_course
    
    ##
    ### 1. Identify Courses in Canvas all courses list #################
    ##
    courses = scrape.find_canvas_course_pages(driver, settings)
    for label, course in courses.items():
        existing_course = get_course(label)
        if existing_course == None:
            add_course(label, course)
        else:
            log.info("Not replacing existing course:\n{}\nwith course:\n{}"\
                     .format(str(existing_course), str(course)))

    ##
    ### 2. Identify Courses in Left Pane of Canvas files tree ##########
    ##
    ## Edge case - probably wont find any courses here which aren't on 
    ## all courses page.
    ##
    courses = scrape.find_canvas_files_page_courses(driver, settings)
    for label, course in courses.items():
        existing_course = get_course(label)
        if existing_course == None:
            add_course(label, course)
        else:
            log.info("Not replacing existing course:\n{}\nwith course:\n{}"\
                     .format(str(existing_course), str(course)))


def index_course_files(driver, settings):
    log.info(currentframe().f_code.co_name)
    driver.delay(3, 5)

    from .scrape import index_right_pane_file_tree
    
    for course in database.get_all_courses():
        driver.delay(2, 6)
        course_url = 'https://canvas.northwestern.edu/courses/{}'\
                    .format(course.canvas_course_id)
        course_files_url = course_url+"/files"
        driver.goto(course_files_url)
        if driver.current_url == course_url:
            log.info("Course {} files inaccessible, though main page is"\
                     .format(course.name_in_fs))
            continue
        children = index_right_pane_file_tree(driver, settings)
        course.set_children(children)
        log.info(str(course))
        database.update_course_files(course)
