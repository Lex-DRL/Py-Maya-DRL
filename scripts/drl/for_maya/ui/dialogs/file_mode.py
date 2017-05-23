"""
Possible values for <mode> argument in <file_chooser> function.

Indicate what the dialog is to return.

* FILE_ANY=0 - Any file, whether it exists or not.
* FILE_EXISTING=1 - A single existing file.
* DIR_DISPLAY_FILES=2 - The name of a directory. Both directories and files are displayed in the dialog.
* DIR_HIDE_FILES=3 - The name of a directory. Only directories are displayed in the dialog.
* FILES_MULTIPLE=4 - Then names of one or more existing files.
"""
__author__ = 'DRL'

FILE_ANY = 0
FILE_EXISTING = 1
DIR_DISPLAY_FILES = 2
DIR_HIDE_FILES = 3
FILES_MULTIPLE = 4