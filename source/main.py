#!/usr/bin/python3

#
# Read commandline arguments
# 
from argparse import ArgumentParser
parser = ArgumentParser(description='Download course files from CANVAS')
parser.add_argument('--log', type=str, nargs=1, dest='logLevel',
                    help='log level to output')
args = parser.parse_args()
if not args.logLevel:
    args.logLevel = "ERROR"
else:
    args.logLevel = args.logLevel[0]
    from importlib import reload

#
# Configure root logger
# 
import logging
# Convert to upper case to allow the user to specify
# --log=DEBUG or --log=debug
numeric_level = getattr(logging, args.logLevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % args.logLevel)
logging.basicConfig(level=numeric_level)

log = logging.getLogger(__name__)
from sys import exit as exits

#
# Login to canvas
#
log.info("Acquiring canvas credentials")
from canvas import login
user, password = login.get_credentials()

log.info("Activating webdriver")
from webdriver import PatientWebdriver
driver = PatientWebdriver()
login.open_dashboard(driver, user, password)

#
# Locate course files
#
import filetree
from canvas import database
filetree.enter_creating('downloads')
filetree.enter_creating("CanvasCourses"+user.upper())

settings = {'shorten_terms': True}

'''
from canvas import index_courses
index_courses(driver, settings)

for course in database.get_all_courses():
    filetree.create(course.name_in_fs)
'''
from canvas import index_course_files
#index_course_files(driver, settings)

#
# Download files
#
##database.update_course_files(courses[0], None)
for course in database.get_all_courses():
    course.download_if_needed(driver)
