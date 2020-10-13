
import os
import sys
import configparser

import utilitiy
from utilitiy import log

# work direction
work_dir = utilitiy.get_work_dir('INIMerge')
#work_dir = R'D:\Creative\Py\cnc tools' + os.path.sep
input_direction = work_dir + 'input' + os.path.sep
output_direction = work_dir + 'output' + os.path.sep
utilitiy.init_dir([work_dir, input_direction, output_direction])

# ini files to process
ini_files = ['rulesmd.ini', 'artmd.ini', 'aimd.ini']
utilitiy.set_log_file(
    open(output_direction + 'merge.log', 'w', encoding='utf-8'))
# show what section reset
show_details = False


log('author: Xkein')
log('work dir: ' + work_dir)
log('ini files: ' + str(ini_files))
log()


def open_ini(file_name):
    ini = configparser.ConfigParser(delimiters=('='), interpolation=None,
                                    # strict: check error and throw
                                    # allow_no_value: allow option without value
                                    strict=False, allow_no_value=True)
    ini.optionxform = lambda option: option
    path = input_direction + file_name
    try:
        with open(path, encoding='utf-8', errors='ignore') as file:
            ini.read_file(file)
    except configparser.Error as e:
        log('read error: ' + e.message)
        raise e

    log('open file success: ' + file_name)
    return ini


# load sub ini's content to ini
def load_sub_ini(ini: configparser.ConfigParser, sub_file_name):
    sub_ini = open_ini(sub_file_name)

    sections = sub_ini.sections()
    for section in sections:
        if not ini.has_section(section):
            ini.add_section(section)

        options = sub_ini.options(section)
        for option in options:

            value = sub_ini.get(section, option)
            ini.set(section, option, value)

        if show_details:
            log(file_name + ': reset [' + section + ']')

    sub_ini.clear()
    log('close sub ini "' + sub_file_name + '"')


include_section = '#include'


def read_save_ini(file_name):
    ini = open_ini(file_name)
    log()

    sub_file_options = ini.options(include_section)
    for sub_file_option in sub_file_options:
        sub_file_name = ini.get(include_section, sub_file_option)
        # ini.read(sub_file_name)
        try:
            load_sub_ini(ini, sub_file_name)
        except Exception as e:
            log('load sub ini ' + sub_file_name + ' fail: ' + str(e.args))
        else:
            log(file_name + ': ' + sub_file_name + ' applied')
        finally:
            log()

    output_file = open(output_direction + file_name, 'w', encoding='utf-8')
    ini.write(output_file)
    log('write file "' + output_file.name + '"')

    ini.clear()
    log('close file "' + file_name + '"')


for file_name in ini_files:
    try:
        read_save_ini(file_name)
    except Exception as e:
        log('load ' + file_name + ' fail: ' + str(e.args))
    finally:
        log()

log('exit.')
