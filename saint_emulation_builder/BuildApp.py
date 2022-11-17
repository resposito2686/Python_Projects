"""
===============================
AUTHOR        : Robert Esposito
CREATE DATE   : January 27th, 2022
PURPOSE       : This application will generate emulation files for the SAINT Bus Monitor.
===============================
Change History:
    01/27/22 - Version 1.0
    02/02/22 - Version 1.1: Added support for active DTCs.
    02/18/22 - Version 1.2: Added support for PUE Script and PID 1F.
    05/09/22 - Version 2.0: Added GUI to emulation builder.
    08/19/22 - Version 2.1: Changed file format from txt -> json
==================================

"""

import os
import shutil
import PyInstaller.__main__

VERSION = 'SAINT_Emulation_Builder_2.1'
CURRENT_PATH = os.path.join(os.path.dirname(__file__))

#: Builds application using pyInstaller.
PyInstaller.__main__.run([
    'SaintEmulationBuilder.py',
    '--distpath', 
    f'{CURRENT_PATH}\\{VERSION}',
    '--workpath',
    f'{CURRENT_PATH}\\{VERSION}_build',
    '--clean'
])

#: Moves additional files to build folder.
print('Copying \'puilogo.ico\'')
shutil.copy(f'{CURRENT_PATH}\\puilogo.ico', f'{CURRENT_PATH}\\{VERSION}\\SaintEmulationBuilder')
print('Copying \'saved_parameters.json\'')
shutil.copy(f'{CURRENT_PATH}\\saved_parameters.json', f'{CURRENT_PATH}\\{VERSION}\\SaintEmulationBuilder')

#: ZIPs build folder.
print(f'Zipping {VERSION}...')
shutil.make_archive(f'{VERSION}', 'zip', f'{CURRENT_PATH}\\{VERSION}')

#: Removes temporary work files.
print('Removing build directory...')
shutil.rmtree(f'{CURRENT_PATH}\\{VERSION}_build')
os.remove(f'{CURRENT_PATH}\\SaintEmulationBuilder.spec')
print('Build complete\n\n')