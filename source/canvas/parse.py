import logging
log = logging.getLogger(__name__)
from inspect import currentframe
from sys import exit as exits

from utils import input_with_prefill

def identify_course(label, nickname, settings):
    log.info(currentframe().f_code.co_name)

    from . import Course
    from .database import get_course, get_ignore_list, ignore

    def _identify_course(label, nickname, settings):
        course = parse_for_course(label, nickname, settings)
        if course:
            print("Parsed label:\n{}\n into course:\n{}"\
                  .format(label, course))
            while True:
                choice = input_with_prefill("Accept / Edit / Reject: ", "A")\
                                            [0].upper()
                if choice == 'A':
                    return label, course
                elif choice == 'E':
                    course = edit_course(course, settings)
                    return label, course
                elif choice == 'R':
                    ignore(label)
                    return None, None
                else:
                    print("Unrecognized option")
                    continue
                break
        else:
            print("Failed to parse label: \n"+label)
            while True:
                choice = input_with_prefill("Manually Enter / Ignore: ", "I")\
                                            [0].upper()
                if choice == 'M':
                    course = edit_course(Course(), settings)
                    return label, course
                elif choice == 'I':
                    ignore(label)
                    return None, None
                else:
                    print("Unrecognized option")
                    continue
                break
    
    if label in get_ignore_list():
        log.info("Ignoring label "+label)
        return None, None

    if settings.get("reload_all"):
        log.info("Parsing because of 'reload_all' setting")
        return _identify_course(label, nickname, settings)

    existing_course = get_course(label)
    if existing_course != None:
        log.info("Found existing course for label: \n{}\n{}"\
                 .format(label, existing_course))
        return label, existing_course

    log.info("Unrecognized label - Parsing")
    return _identify_course(label, nickname, settings)

def parse_for_course(label, nickname, settings):
    log.info(currentframe().f_code.co_name)

    from . import Course
    
    import re
    term_pattern = re.compile(r"""
        (?:CCS\_)?
        (?P<year>       \d      {4}     )
        (?P<quarter>    [A-Z]   {2,4}   )
        \_
    """, re.VERBOSE)
    if not term_pattern.match(label):
        return None
    year, quarter, rest = term_pattern.split(label)[1:]

    listing_pattern = re.compile(r"""
        (?:\_AND\_)??
        (?:
          (?P<program>        [A-Z]   +
                              (?:\_ [A-Z] +) *
          )
          \_
        )??
        (?P<course_number>    \d      {3}
                              (?: \-
                                \d    {,3}
                              )       ?
        )
        (?:
          \_
          (?P<section>
            (?:
              (?: SEC \d +)
            | ( ALL\_SECTIONS )
            )
          )
        )?
        #(?:\s(?P<title>         [A-Z][a-z].+    ))?
    """, re.VERBOSE\
    )
    end = 0
    listings = []
    for listing_match in listing_pattern.finditer(rest):
        end = listing_match.end()
        listings.append(
            build_listing_from_match(listing_match.group(1),
                                     listing_match.group(2),
                                     listing_match.group(3),
                                     listing_match.group(4)
                                    )
        )
    title = ''
    if end+1 < len(rest):
        title += rest[end+1:]

    if nickname != '' and nickname != title:
        title += " | " + nickname

    return Course(title = title,
                  year = year,
                  quarter = quarter,
                  listings = listings,
                  settings = settings)

def build_listing_from_match(program_match,
                             course_number_match,
                             section_number_match,
                             all_sections_match
                            ):
    from . import CourseListing
    def pick_first_or_unknown(options):
        for option in options:
            if option:
                return option
        return "Unknown"
    return CourseListing(
    	program = pick_first_or_unknown([program_match]),
    	course_number = course_number_match,
  	section = pick_first_or_unknown(
            [section_number_match, all_sections_match]
        )
    )

def edit_course(course, settings):
    log.info(currentframe().f_code.co_name)
    log.info("Editing course: \n"+course.__repr__())
    course.year = int(input_with_prefill("year: ", course.year))
    course.quarter = input_with_prefill("quarter: ", course.quarter)
    course.title = input_with_prefill("title: ", course.title)

    num_listings = len(course.listings)
    for i in range(num_listings):
        program = course.listings[i].program
        program = input_with_prefill("listing {} program: ".format(i+1), program)
        course.listings[i].program = program

        course_number = course.listings[i].course_number
        course_number = input_with_prefill("listing {} course_number: ".format(i+1), course_number)
        course.listings[i].course_number = course_number

        section = course.listings[i].section
        section = input_with_prefill("listing {} section: ".format(i+1), section)
        course.listings[i].section = section
     
    if num_listings > 1:
        primary_listing_i = int(input_with_prefill("primary listing number: ", "1"))-1
        if primary_listing_i != 0:
            set_aside_listings = []
            for i in range(num_listings):
                if i != primary_listing_i:
                    set_aside_listings.append(course.listings[i])
            course.listings[0] = course.listings[primary_listing_i]
            course.listings[1:] = set_aside_listings

    course.name_in_fs = input_with_prefill("name: ",
                                              build_name(course.year,
                                                         course.quarter,
                                                         course.listings[0],
                                                         course.title,
                                                         settings))
    return course

def build_name(*pos_args, year, quarter, listing, title, settings, **args):
    assert len(pos_args) <= 1, "build_name received too many positional args"
    if settings.get("shorten_terms"):
        year_str, quarter_str = shorten_terms(year, quarter)
        term_str = year_str+quarter_str
    else:
        term_str = "{}_{}".format(year, quarter)
    name = "{}.{}: {}".format(term_str,
                              listing.course_number,
                              title)
    program = listing.program
    if program not in ["EECS", "COMP_SCI"]:
        name += " ({})".format(program)
    return name
        
def shorten_terms(year, quarter):
    year = int(year) - 2015
    quarter = {"FA": 1, "WI": 2, "SP": 3, "SU": 4}[quarter.upper()[0:2]]
    if quarter > 1:
        year -= 1
    return str(year), str(quarter)
