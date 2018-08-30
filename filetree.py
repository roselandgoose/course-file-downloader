from sh import cd, mkdir
from json import load as jload, dump
from humanfriendly import parse_size, format_size # file size conversions
from os.path import isdir

from downloader import delay

##
### Data structure specification ##################################################
##
# A File Tree is a dictionary/json object with the following attributes:
#   
#   * source : string
#   * node_type : 'root'
#   * size : integer
#   * children : list of File Tree Nodes
#
# A File Tree Node is a dictionary/json object with the following attributes:
#
#   * name : string
#   * link : string
#   * type : 'folder' or 'file'
#   * created : string
#   * modified : string
#   * modifier : string
#   * size : string
#   " _num_bytes: integer
#   * children : if node_type is 'file':
#                   False
#              : if node_type is 'folder':
#                   list of File Tree Nodes
#
#
##

def load(json_file):
    with open(json_file, 'rb') as f:
        file_tree = jload(f)
    return file_tree


def save(file_tree, name):
    with open(name, 'w+') as f:
        dump(file_tree, f, indent=4)


def compute_sizes(file_tree):
    def helper(node):
        if node['type'] == 'file':
            size = parse_size(node['size'])
            node['_num_bytes'] = size
            return size
        else:
            size = 0
            for child in node['children']:
                size += helper(child)
            node['_num_bytes'] = size
            node['size'] = format_size(size)
            return size

    size = 0
    for child in file_tree['children']:
        size =+ helper(child)
    file_tree['_num_bytes'] = size
    human_size = format_size(size)
    file_tree['size'] = human_size
    return human_size
    

def download(driver, file_node):
    print(file_node['name'])
    print(file_node['size'])

    if file_node['type'] == 'file':
        delay(0.5, 1)
        response = driver.request('GET', file_node['link'])

        with open(file_node['name'], 'wb+') as out:
            out.write(response.content)
    else:
        dir_name = file_node['name']
        if not isdir(dir_name):
            mkdir(dir_name)
        cd(dir_name)
        for child in file_node['children']:
            download(driver, child)
        cd('..')



