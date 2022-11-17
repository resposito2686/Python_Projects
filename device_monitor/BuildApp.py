"""
========================================================================================================================
AUTHOR        : Robert Esposito
COMPANY       : Positioning Universal Inc.
CREATE DATE   : February 15th, 2022
========================================================================================================================
PURPOSE       : This application is intended to monitor PUI device's voltage, state, and serial data.
              :  
              : Currently supports: FJ2500 and FJ2050 ( GTI / GCF / SKYT ) 
========================================================================================================================
Change History:

    BETA
    --------------------------------------------------------------------------------------------------------------------
    02/15/22 : vBeta1 - Initial beta release.
    02/16/22 : vBeta2 - State colors.
    02/21/22 : vBeta3 - puibtool.exe tool integrated.
    02/28/22 : vBeta4 - Device settings + console font selection.
    03/01/22 : vBeta5 - Function-based implementation -> class-based implementation + Log Parser.
    03/03/22 : vBeta6 - Device Info and right click menu.
    03/09/22 : vBeta7 - Layout overhaul + threading safety.
    03/15/22 : vBeta8 - Settings.ini file + write to log comments.
    03/17/22 : vBeta8b - Line break settings + puibtool fixes.
    03/21/22 : vBeta9 - Threading changes + error log.
    03/22/22 : vBeta9a - Further threading improvements + error log improvements.
    --------------------------------------------------------------------------------------------------------------------
    
    1.0
    --------------------------------------------------------------------------------------------------------------------
    03/24/22 : v1.0.0 - Various application adjustments and clean up for end of beta.
    03/29/22 : v1.0.1 - Logging unhandled exceptions + save logging settings.
    --------------------------------------------------------------------------------------------------------------------
    
    1.1
    --------------------------------------------------------------------------------------------------------------------
    04/06/22 : v1.1.0 - Console highlighting.
    --------------------------------------------------------------------------------------------------------------------
    
    1.2
    --------------------------------------------------------------------------------------------------------------------
    04/07/22 : v1.2.0 - Change window title.
    04/11/22 : v1.2.1 - puibtool bug fix.
    04/13/22 : v1.2.2 - Console highlighting improvements.
    04/18/22 : v1.2.3 - More highlighting improvements.
    --------------------------------------------------------------------------------------------------------------------
    
    1.3
    --------------------------------------------------------------------------------------------------------------------
    04/22/22 : v1.3.0 - Preferences menu + global variables -> class variables
    04/25/22 : v1.3.1 - Preferences log file path
    04/28/22 : v1.3.2 - Add carriage return + puibtool improvements + serial improvements
    05/04/22 : v1.3.3 - Start new log file + puibtool internal + log file formatting.
    --------------------------------------------------------------------------------------------------------------------
    
========================================================================================================================
"""

import os
import shutil
import PyInstaller.__main__

VERSION = 'DeviceMonitor_1.3.3_Debug'
CURRENT_PATH = os.path.join(os.path.dirname(__file__))

#: Builds application using pyInstaller.
PyInstaller.__main__.run([
    'DeviceMonitor.py',
    '--distpath', 
    f'{CURRENT_PATH}\\{VERSION}',
    '--workpath',
    f'{CURRENT_PATH}\\{VERSION}_build',
    '--clean'
])

#: Moves additional files to build folder.
print('Copying \'puilogo.ico\'')
shutil.copy(f'{CURRENT_PATH}\\puilogo.ico', f'{CURRENT_PATH}\\{VERSION}\\DeviceMonitor')
print('Copying \'puibtool.exe\'')
shutil.copy(f'{CURRENT_PATH}\\puibtool.exe', f'{CURRENT_PATH}\\{VERSION}\\DeviceMonitor')

#: ZIPs build folder.
print(f'Zipping {VERSION}...')
shutil.make_archive(f'{VERSION}', 'zip', f'{CURRENT_PATH}\\{VERSION}')

#: Removes temporary work files.
print('Removing build directory...')
shutil.rmtree(f'{CURRENT_PATH}\\{VERSION}_build')
os.remove(f'{CURRENT_PATH}\\DeviceMonitor.spec')
print('Build complete\n\n')