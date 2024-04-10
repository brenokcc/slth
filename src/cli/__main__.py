import sys
import os
import shutil


def copy_files(src, dest):
    src_files = os.listdir(src)
    for file_name in src_files:
        full_file_name = os.path.join(src, file_name)
        if os.path.isfile(full_file_name):
            shutil.copy(full_file_name, dest)
        if os.path.isdir(full_file_name):
            dirname = os.path.join(dest, file_name)
            os.makedirs(dirname, exist_ok=True)
            copy_files(full_file_name, dirname)

if len(sys.argv) > 1:
    command = sys.argv[1]
    if command == 'startproject':
        src = os.path.join(os.path.dirname(__file__), 'boilerplate')
        dest = os.path.abspath('.')
        copy_files(src, dest)
    else:
        print('Invalid command!')