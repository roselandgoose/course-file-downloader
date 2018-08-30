* I'm refactoring from this file into
    * downloader : all target-agnostic web-driving code
    * canvas : code specific to interfacing with canvas
    * main : script calling functions from above two files
* I'm flattening the code into a much more functional style, using no classes yet and relying on dictionaries
* I've refactored all of the canvas-agnostic agent class methods
* I've refactored the root node class into a dictionary
* My plan is to use proper wait conditions to prevent the need for retry's


ToDo:
* [x] extract node class attributes into dictionary
* [x] determine distinct functions that will need to act on node object
    * I don't need so many functions if I used proper wait conditions!
* [x] Update existing code to use separate filetree utilities
* [] write out the plan from the above notes into the comments of the three files
* [] note chmod required to run seleniumrequests

Goals
* [] Compare two file trees
* [] Crawl Courses page for every course file
* [] Crawl only 'My Files' on the Files page
* [x] Compute total size of tree
