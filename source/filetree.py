import logging
log = logging.getLogger(__name__)
from inspect import currentframe
from sys import exit as exits

##
### Data structure #####################################################
##
from datetime import date as date_module
from copy import deepcopy
from pprint import pformat
class CourseFile:
    def __init__(self, *, name_in_fs,
                          size_bytes,
                          download_url,
                          **args):
        self.name_in_fs     = name_in_fs
        self.size_bytes     = size_bytes
        self.download_url   = download_url
        self.iso_date_class = args.pop('iso_date_class', None)
        if not self.iso_date_class:
            self.iso_date_class = self.get_date(args.pop('iso_date_str',
                                                         None))
        assert args == {}, "Unhandled args in {} constructor: {}"\
                                                .format(type(self).__name__,
                                                        args)
    def get_date(self, iso_date_str = None):
        if iso_date_str:
            return date_module.fromisoformat(iso_date_str)
        else:
            return self.iso_date_class

    def get_size(self):
        return self.size_bytes

    def dumpd(self):
        dict_repr = deepcopy(self.__dict__)
        dict_repr["iso_date_str"] = str(dict_repr["iso_date_class"])[0:10]
        dict_repr["iso_date_class"] = None
        del dict_repr["iso_date_class"]
        return dict_repr

    def __repr__(self):
        return pformat(self.dumpd())

    def download(self, driver):
        log.info(currentframe().f_code.co_name)
        log.info("Downloading: {} from {}".format(self.name_in_fs,
                                                  self.download_url))
        driver.delay(1, 4)
        try:
            response = driver.request('GET', self.download_url)
            with open(self.name_in_fs, 'wb+') as out:
                out.write(response.content)
        except Exception as e:
            log.error("Download failed with exception:")
            log.error(e)

    def needs_downloading(self):
        log.info(currentframe().f_code.co_name)
        from os.path import getmtime as last_modified_unix
        from os.path import exists
        from time import mktime
        if not exists(self.name_in_fs):
            log.info("{} does not exist in filesystem".format(self.name_in_fs))
            return True
        filesystem_time = last_modified_unix(self.name_in_fs)
        canvas_time     = mktime(self.iso_date_class.timetuple())
        result = canvas_time > filesystem_time
        log.info("{} has filesystem time: {} and canvas time: {} => {}".format(
            self.name_in_fs, filesystem_time, canvas_time, result))
        return result

    def download_if_needed(self, driver):
        log.info(currentframe().f_code.co_name)
        if self.needs_downloading():
            self.download(driver)

class CourseDir(CourseFile):
    def __init__(self, *, children, **args):
        self.children = []
        for child in children:
            if type(child) == dict:
                if "children" in child:
                    self.children.append(CourseDir(**child))
                else:
                    self.children.append(CourseFile(**child))
            else:
                self.children.append(child)
        size_bytes = args.pop('size_bytes', None)
        if not size_bytes:
            size_bytes = self.get_size()
        super().__init__(size_bytes = size_bytes, **args)

    def get_size(self):
        size = 0
        for child in self.children:
            size += child.get_size()
        return size

    def dumpd(self):
        dict_repr = super().dumpd()
        dict_repr["children"] = [child.dumpd() for child in self.children]
        return dict_repr

    def set_children(self, children):
        self.children       = children
        self.size_bytes     = self.get_size()
        self.iso_date_class = self.get_date()

    download = None

    def needs_downloading(self):
        log.info(currentframe().f_code.co_name)
        result = False
        enter_creating(self.name_in_fs)
        for child in self.children:
            result |= child.needs_downloading()
            if result:
                break
        go_up()
        return result

    def download_if_needed(self, driver):
        log.info(currentframe().f_code.co_name)
        log.info("Downloading: {} if needed".format(self.name_in_fs))
        driver.delay(0.5, 1)
        enter_creating(self.name_in_fs)
        for child in self.children:
            child.download_if_needed(driver)
        go_up()

##
### OS Navigation and Directory Creation Helpers #######################
##
from os import mkdir, getcwd, chdir
from os.path import isdir, isfile

def create_if_needed(file_name_in_fs, content=''):
    log.info(currentframe().f_code.co_name)
    if not isfile(file_name_in_fs):
        with open(file_name_in_fs, 'w+') as f:
            f.write(content)
        return False
    return True

def create(dir):
    if not isdir(dir):
        mkdir(dir)
        
def enter_creating(dir):
    log.info(currentframe().f_code.co_name)
    log.info("Entering "+dir)
    create(dir)
    chdir(dir)
    
def go_up():
    log.info(currentframe().f_code.co_name)
    chdir('..')
