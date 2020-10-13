
import os
import sys
import shutil

import utilitiy
from utilitiy import log

# work direction
work_dir = utilitiy.get_work_dir('Rename')
input_direction = work_dir + 'input' + os.path.sep
output_direction = work_dir + 'output' + os.path.sep
utilitiy.init_dir([work_dir, input_direction, output_direction])

utilitiy.set_log_file(
    open(output_direction + 'rename.log', 'w', encoding='utf-8'))

exts = ['tem', 'sno', 'ubn', 'urb', 'lun', 'des']

log('author: Xkein')
log('work dir: ' + work_dir)
log('exts: ' + str(exts))
log()

for root, dirs, files in os.walk(input_direction):
    for file in files:

        if file.lower().endswith('shp'):
            log('copying: ' + file)
            
            for ext in exts:
                src = os.path.join(input_direction, file)
                dst = os.path.join(output_direction, file.split('.', 1)[0] + '.' + ext)
                shutil.copyfile(src, dst)
                log('copy to: ' + dst)
                
            log()
