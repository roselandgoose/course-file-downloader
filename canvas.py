import downloader
from downloader import delay

import filetree

from re import search # for parsing course titles and folder links
from re import compile as comp # for parsing course titles


def login(driver, credentials):
    driver.get("https://canvas.northwestern.edu/files")

    user_form = driver.find_element_by_id('IDToken1')
    psswd_form = driver.find_element_by_id('IDToken2')

    user_form.send_keys(credentials['user'])
    delay(0.5, 1)
    psswd_form.send_keys(credentials['password'])
    delay(0.5, 1)
    psswd_form.submit()


def parse_title(string):
    def apply_regex(regex_str):
        pattern = comp(regex_str)
        result = pattern.search(string)
        if not result:
            return "unknown"
        else:
            return result.group(0)

    result = {}

    result['year'] = apply_regex("^\d{4}")
    result['quarter'] = apply_regex("(?<=^\d{4})[A-Z]{2}(?=\_)")
    result['subject'] = apply_regex("(?<=^\d{4}[A-Z]{2}\_)[A-Z,\_]{4,}(?=\_)")
    result['course_number'] = apply_regex("(?<=[A-Z,\_]{3}\_)[\d,\-]{3,}(?=\_)")
    result['section_number'] = apply_regex("(?<=\d\_SEC)\d+(?=[\_, ])")
    result['title'] = apply_regex("(?<=\d[\_, ])[A-Z][a-z].+$")

    return result


def index_file_tree(driver):
    delay(0.5, 2)

    file_tree = {
        "name": 'canvas',
        "type": 'root',
        "size": False,
        "_num_bytes": False,
        "children": []
    }

    # Files page features:
    #   * a left pane listing courses and groups in a filesystem tree
    #   * a right file panel listing the files and folders in the current folder

    #
    # To index the whole tree, we need to:
    #   1. Identify the courses in the left pane
    #   2. Click on each to view its sub tree
    #   3. Click through each directory in the sub tree to recursively index it
    #

    ##
    ### 3. Index Sub Tree ################################################################
    #
    # ~~ Skip to the end of these helper functions to see #1 ~~
    ##

    def index_sub_tree():
        delay(1.5, 2)

        # Find elements in right pane by xpath
        @downloader.anticipate_staleness
        def find_right_pane_elements():
            right_pane_elements = downloader.get_elements_by_xpath(driver, 4,
                "//body/div/div/div[@id='main']/div/div/div[@id='content']/div/div[@class='ef-main']/div[@class='ef-directory']/div/div[@role='grid']/div[@class='ef-item-row']"
            ) # Absolute path with markers for efficiency

            return [element.get_attribute("data-reactid") for element in right_pane_elements]

        right_pane_ids = find_right_pane_elements()

        def make_node(el_react_id):
            node = {
                'name': False,
                'link': False,
                'type': False,
                #TODO created
                #TODO modified
                #TODO modifier
                'size': False,
                '_num_bytes': False,
                'children': False
            }

            # Files and folders in the right pane are divs with class 'ef-item-row'
            #   div - ef-directory
            #       div - grid
            #           div - ef-item-row

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
            #       div - ef-size-col

            a_name = downloader.get_element_by_xpath(driver, 3,
                "//body/div/div/div[@id='main']/div/div/div[@id='content']/div/div[@class='ef-main']/div[@class='ef-directory']/div/div[@role='grid']/div[@data-reactid='" + el_react_id + "']/div/a[@class='ef-name-col__link']"
            )

            link = a_name.get_attribute("href")

            # File links are "https://canvas.nor..." links whereas folder links are relative
            is_folder = bool(search("/files/folder", link))

            @downloader.anticipate_staleness
            def get_name():
                if is_folder:
                    return downloader.get_element_by_xpath(driver, 3,
                        "//body/div/div/div[@id='main']/div/div/div[@id='content']/div/div[@class='ef-main']/div[@class='ef-directory']/div/div[@role='grid']/div[@data-reactid='" + el_react_id + "']/div/a[@class='ef-name-col__link']/span/span[@class='ef-name-col__text']"
                    ).text
                else:
                    return downloader.get_element_by_xpath(driver, 3,
                        "//body/div/div/div[@id='main']/div/div/div[@id='content']/div/div[@class='ef-main']/div[@class='ef-directory']/div/div[@role='grid']/div[@data-reactid='" + el_react_id + "']/div/a[@class='ef-name-col__link']/span[@class='ef-name-col__text']"
                    ).text

            name = get_name()

            @downloader.anticipate_staleness
            def get_size():
                if is_folder:
                    return False
                else:
                    return downloader.get_element_by_xpath(driver, 3,
                        "//body/div/div/div[@id='main']/div/div/div[@id='content']/div/div[@class='ef-main']/div[@class='ef-directory']/div/div[@role='grid']/div[@data-reactid='" + el_react_id + "']/div[@class='ef-size-col']"
                    ).text

            size = get_size()

            node['name'] = name
            node['link'] = link
            node['size'] = size
            print(name)
            print(link)
            print(size)
            print('is_folder: ' + str(is_folder) + '\n')
            node['type'] = 'folder' if is_folder else 'file'

            if is_folder:
                delay(1.5, 2)
                downloader.get_element_by_xpath(driver, 3,
                    "//body/div/div/div[@id='main']/div/div/div[@id='content']/div/div[@class='ef-main']/div[@class='ef-directory']/div/div[@role='grid']/div[@data-reactid='" + el_react_id + "']/div/a[@class='ef-name-col__link']"
                ).click()
                delay(1.5, 2)

                node['children'] = index_sub_tree()
        
            return node

        nodes = [make_node(element_id) for element_id in right_pane_ids]

        # Go back up to previous tree depth after recurring down
        delay(1.5, 2.5)
        driver.back()
        delay(1.5, 2.5)

        return nodes
            

    ##
    ### 1. Identify Courses in Left Pane #################################################
    ##

    # Courses in the left pane are li elements with attribute 'data-id.'
    
    left_pane_elements = downloader.get_elements_by_xpath(driver, 4,
        "//body/div/div/div[@id='main']/div/div/div[@id='content']/div/div[@class='ef-main']/aside/div/div/ul/li[@data-id]"
    ) # Absolute path with markers for efficiency

    # It is wise to only hold onto element references for as long as necessary, so I only store the ids and labels 

    roots = []
    for element in left_pane_elements:

        # The text label displayed for each valid element is stored in the 'aria-label' attribute.
        label = element.get_attribute("aria-label")

        # Valid courses and categories have labels like "2018SP_EECS_349-0_SEC20 Machine Learning"
        if bool(search("\d{4}[A-Z]{2}\_[A-Z]", label)):
            
           roots.append({
                'label' : label,
                'data-id' : element.get_attribute("data-id"),
            })

    ##
    ### 2. Click on Each Course in Left Pane #############################################
    ##

    for root in roots:
        element = downloader.get_element_by_css(driver, 4, "li[data-id='" + root['data-id'] + "']")
        
        # click on the left-pane element to display course tree
        element.click()
        file_tree['children'].append({
            'name': root['label'], #TODO Replace with parsed title
            'link': False, #TODO Is this a wise and cosnsitent way to handle?
            'type': 'folder',
            'created': False,
            'modified': False,
            'modifier': False,
            'size': False,
            'children': index_sub_tree() # 3. See above helper functions
        })
        delay(1.5, 2)

    total_size = filetree.compute_sizes(driver, file_tree)
    print(total_size)

    return file_tree


