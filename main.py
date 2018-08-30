import downloader
import canvas
import filetree

credentials = downloader.get_credentials()
driver = downloader.driver_init()
canvas.login(driver, credentials)
#file_tree = canvas.index_file_tree(driver)
file_tree = filetree.load('tree.json')
filetree.download(driver, file_tree)
