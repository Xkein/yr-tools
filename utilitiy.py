
import os
import sys
import typing

def get_work_dir(tool_name: str):
    return os.path.abspath(sys.path[0]) + os.path.sep + tool_name + os.path.sep

log_file : typing.IO

def set_log_file(file):
    global log_file
    log_file = file
    
def log(message=''):
    print(message)
    global log_file
    if log_file != None:
        log_file.write(message + '\n')

def init_dir(dirs):
    for direction in dirs:
        os.makedirs(direction, exist_ok=True)
