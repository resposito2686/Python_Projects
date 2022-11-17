"""
===============================
AUTHOR        : Robert Esposito
CREATE DATE   : February 17th, 2022
PURPOSE       : This will change RPM and Engine Run Time values every x seconds.
===============================
Change History:
    02/17/22 - Version 1.0
==================================
"""
import BuildEmulationFiles as bef
import os
import random
import time


"""MUST RUN SaintEmulationBuilder.py FIRST!!!"""
emu_filename = ''

#: Locates .emu file.
try:
    for root, dirs, items in os.walk(bef.PATH):
        for name in items:
            if '.emu' in name:
                emu_filename = name
                break
except OSError:
    print(f'{bef.PATH} does not exist.')
    exit(1)

if not emu_filename:
    print(f'There was no emulation file found.')
    exit(1)

else:
    can_id = int(emu_filename[3:5])
    tes = 1
    count = 0

    try:
        #: Opens .emu file and checks if the RPM and TES group files have been added.
        f = open(f'{bef.PATH}\\{emu_filename[:5]}\\{emu_filename}', 'r+')
        file_list = f.readlines()

    except FileNotFoundError:
        print(f'Error loading emulation file contents.')
        exit(1)

    #: Adds RPM and TES group files.
    if file_list[0] != '=== PUE RPM & TES ===,Transmit,=== DO NOT DISABLE ===,False\n':
        file_list.insert(0, bef.build_string(parameter='TES', value=tes, can_id=can_id, pue=True) + '\n')
        file_list.insert(0, bef.build_string(parameter='RPM', value=random.randint(1000, 4000),
                                             can_id=can_id, pue=True) + '\n')
        file_list.insert(0, '=== PUE RPM & TES ===,Transmit,=== DO NOT DISABLE ===,False\n')
        f.seek(0, 0)
        f.writelines(file_list)
        f.close()

    print('Starting PUE script...\n\n')

    while True:
        bef.build_string(parameter='RPM', value=random.randint(1000, 4000), can_id=can_id, pue=True)
        bef.build_string(parameter='TES', value=tes, can_id=can_id, pue=True)

        count += 1
        tes += 3

        #: Print update every 30 seconds.
        if (count % 10) == 0:
            print(f'Script has been running for {count * 3} seconds...\n')

        time.sleep(3)
