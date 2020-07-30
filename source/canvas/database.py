import logging
log = logging.getLogger(__name__)
from inspect import currentframe
from sys import exit as exits

from tinydb import TinyDB, Query

from . import Course

def get_all_courses():
    log.info(currentframe().f_code.co_name)
    course_dicts = course_table().all()
    return [Course(**course_dict) for course_dict in course_dicts]

def get_course(label):
    log.info(currentframe().f_code.co_name)
    course_dicts = course_table().search(Query().label == label)
    if not course_dicts:
        return None
    course_dict = course_dicts[0]
    log.info("Retrieved record {}".format(course_dict))
    return Course(**(course_dict)) 

def add_course(label, course):
    log.info(currentframe().f_code.co_name)
    if get_course(label):
        log.error("Will not replace existing course for label: "+label)
        exits(1)
    ensure_fewer_than(Query().name_in_fs == course.name_in_fs, 1,
                      "Attempting to add another course with name {}"\
                      .format(course.name_in_fs))
    dict_repr = course.dumpd()
    dict_repr["label"] = label
    course_table().insert(dict_repr)

def replace_course(label, new_course):
    log.info(currentframe().f_code.co_name)
    query = Query().label == label
    ensure_fewer_than(query, 2,
                      "Replacing course for label {} but already too many!"\
                      .format(label))
    course_table().remove(query)
    add_course(label, new_course)

def update_course_files(course):
    log.info(currentframe().f_code.co_name)
    query = Query().name_in_fs == course.name_in_fs
    ensure_fewer_than(query, 2, "Name collision found in course table!")
    course_dict = course.dumpd()
    course_table().update(
    	{
    	    'children'      : course_dict["children"],
    	    'iso_date_str'  : course_dict["iso_date_str"],
    	    'size_bytes'    : course_dict["size_bytes"]
    	},
    	query)

##
### Labels to Ignore ###################################################
##
def get_ignore_list():
    log.info(currentframe().f_code.co_name)
    return [entry["label"] for entry in db().table('ignored')]

def ignore(label):
    log.info(currentframe().f_code.co_name)
    db().table('ignored').insert({'label': label})

##
### Wrapping TinyDB ###################################################
##
course_db = None
def db():
    global course_db
    if course_db == None:
        log.info("opening tinydb database")
        course_db = TinyDB('course_db.json', indent=4)
    return course_db

def course_table():
    return db().table('courses')

def ensure_fewer_than(query, count, err_msg=None):
    if course_table().count(query) >= count:
        if err_msg == None:
            err_msg = "Not fewer than {} for {}".format(count, query)
        log.error(err_msg)
        exits(1)

