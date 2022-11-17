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
    
    CURRENT CHANGES:
        ID added to settings in Device Settings.
        PUIBtool image command fix.
        Sleep state will stop from serial data.
========================================================================================================================
"""
import tkinter as tk
import DeviceMonitorFunctions as dmf
import logging
import os
import random
import shutil
import string
import subprocess
import sys
import threading
import time

from tkinter import Toplevel, Frame, Menu, Label, Button, Entry, Text, Scrollbar, OptionMenu, Radiobutton
from tkinter import StringVar, IntVar, filedialog
from tkinter.messagebox import askyesno
from datetime import datetime
from configparser import ConfigParser, NoOptionError, NoSectionError

#: Error logger
ERR_LOGGER = logging.getLogger(__name__)
ERR_LOGGER.setLevel(logging.DEBUG)
ERR_HANDLER = logging.FileHandler(filename=os.path.join(os.path.dirname(__file__),'ErrorLog.log'), encoding='latin-1')
ERR_HANDLER.setLevel(logging.DEBUG)
ERR_HANDLER.setFormatter(logging.Formatter('%(asctime)s - %(name)-s:%(threadName)s:%(funcName)s - %(levelname)s - '
                                           '%(message)s'))
ERR_LOGGER.addHandler(ERR_HANDLER)

#: Start time used for any timer.
T_START = time.time()

class SettingsWindow(Toplevel):
    '''
    Device Settings window.
    '''
    #: Variables used by multiple class methods.
    settings_list = []
    sett_update_thread = None

    def __init__(self, *args, **kwargs):
        '''
        Creates a Device Settings window.
        '''
        super().__init__(*args, **kwargs)
        ERR_LOGGER.info('Creating settings window.')

         #: Device settings window
        self.title('Device Settings')
        self.iconbitmap('puilogo.ico')
        self.resizable(0,0)
        self.lift()

        #: List of StringVar objects to populate entry widgets.
        for _ in range(len(dmf.current_settings)):
            self.settings_list.append(StringVar())

        #: None is inserted at index 0 to align the indices of device settings with the settings_list
        ERR_LOGGER.debug('None inserted at settings[0]')
        self.settings_list.insert(0, None)

        #: Widget row.
        row = 0

        #: Device settings label
        sett_label = Label(self, text='Device Settings', font=('Times', 16))
        sett_label.grid(row=row, column=0, padx=5)

        row +=1

        #: Settings update label.
        self.sett_update_label = Label(self, font=('Times', 10), width=25)
        self.sett_update_label.grid(row=row, column=1)

        #: Get current settings button.
        sett_get_button = Button(self, text='Get Current Settings', command=self.start_update_settings_thread)
        sett_get_button.grid(row=row, column=2, pady=5, padx=5, sticky='e')

        row += 1

        #: Setting 62 Widget.
        sett_report_server_label = Label(self, text='Report Server Address [62]') # setting 62
        sett_report_server_label.grid(row=row, column=0)
        sett_report_server_entry = Entry(self, textvariable=self.settings_list[62], width=50)
        sett_report_server_entry.grid(row=row, column=1, columnspan=2)

        row += 1

        #: Setting 63 Widget.
        sett_report_port_label = Label(self, text='Report Server Port [63]') # setting 63
        sett_report_port_label.grid(row=row, column=0)
        sett_report_port_entry = Entry(self, textvariable=self.settings_list[63], width=50)
        sett_report_port_entry.grid(row=row, column=1, columnspan=2)

        row += 1

        #: Setting 65 Widget.
        sett_dman_server_label = Label(self, text='DMAN Server Address [65]') # setting 65
        sett_dman_server_label.grid(row=row, column=0)
        sett_dman_server_entry = Entry(self, textvariable=self.settings_list[65], width=50)
        sett_dman_server_entry.grid(row=row, column=1, columnspan=2)

        row += 1

        #: Setting 66 Widget.
        sett_dman_port_label = Label(self, text='DMAN Server Port [66]') # setting 66
        sett_dman_port_label.grid(row=row, column=0)
        sett_dman_port_entry = Entry(self, textvariable=self.settings_list[66], width=50)
        sett_dman_port_entry.grid(row=row, column=1, columnspan=2)

        row += 1

        #: Setting 64 Widget.
        sett_cell_init_label = Label(self, text='Cell Init String [64]') # setting 64
        sett_cell_init_label.grid(row=row, column=0)
        sett_cell_init_entry = Entry(self, textvariable=self.settings_list[64], width=50)
        sett_cell_init_entry.grid(row=row, column=1, columnspan=2)

        row += 1

        #: Setting 68 Widget.
        sett_apn_label = Label(self, text='APN [68]') # setting 68
        sett_apn_label.grid(row=row, column=0)
        sett_apn_entry = Entry(self, textvariable=self.settings_list[68], width=50)
        sett_apn_entry.grid(row=row, column=1, columnspan=2)

        row +=1

        #: Apply settings changes button.
        sett_apply_change_button = Button(self, text='Apply Settings Changes', 
                                          command=(lambda : self.start_update_settings_thread(True)))
        sett_apply_change_button.grid(row=row, column=2, pady=5, padx=5, sticky='e')

        #: Exit Settings window when closed.
        self.protocol('WM_DELETE_WINDOW', lambda: self.exit_settings())
        
    def start_update_settings_thread(self, apply_changes=False):
        '''
        Starts thread to read/write device settings when either the 'Get Current Settings' or 
        'Apply Settings Changes' buttons are pressed.

        @param apply_changes: If True, write changes. If False, read current settings. False by default.
        '''
        if self.sett_update_thread:
            ERR_LOGGER.warning(f'Attempting to close previous thread \'{self.sett_update_thread.name}\'.')
            self.sett_update_thread.join()
        self.sett_update_thread = threading.Thread(target=self.update_settings, args=(apply_changes,), 
                                                   name='settings', daemon=True)
        ERR_LOGGER.info('Starting \'settings\' thread.')
        self.sett_update_thread.start()

    def update_settings(self, apply_changes):
        '''
        Reads/writes the device settings.

        @param apply_changes: If True, write any settings changes to the device. If False, read current device settings.
        '''
        #: Checks that a serial connection is open
        if dmf.serial_connection:
            ERR_LOGGER.info(f'Serial connection open on {dmf.working_com_port}.')

            #: Read mode.
            if not apply_changes:
                ERR_LOGGER.info('Fetching device settings.')
                self.sett_update_label.config(fg='green', text='Fetching device settings...')
                dmf.parse_serial_data('Settings')

            #: Write mode.
            else:
                ERR_LOGGER.info('Applying settings changes.')
                self.sett_update_label.config(fg='green', text='Applying settings changes...')

            #: Cannot read or write settings if device is asleep.
            if dmf.current_status["state"] == 'Sleeping':
                ERR_LOGGER.warning('Settings cannot be changed while device is sleeping.')
                self.sett_update_label.config(fg='red', text='ERROR: device is asleep.')
                
            else:
                for i, var in enumerate(self.settings_list):

                    #: Index 0 is of type None.
                    if i == 0:
                        pass

                    #: Prevent IndexError exception
                    elif i == len(dmf.current_settings):
                        ERR_LOGGER.debug('End of settings list reached.')
                        break

                    else:
                        i_str = str(i).zfill(2)

                        #: Write changes to device settings.
                        if apply_changes:
                            if var.get() != dmf.current_settings[f'settings[{i_str}]']:
                                ERR_LOGGER.debug(f'Sending command: set,{i_str},{var.get()}')
                                if root.send_console_command(command=f'set,{i_str},{var.get()}'):
                                    self.sett_update_label.config(fg='green', text=f'Changing settings[{i_str}]...')
                                    ERR_LOGGER.info(f'Changing settings[{i_str}].')
                                    time.sleep(45)
                                else:
                                    ERR_LOGGER.warning(f'settings[{i_str}] could not be changed.')
                                    self.sett_update_label.config(fg='red', text=f'ERROR: settings[{i_str}]')

                        #: Read device settings.    
                        else:
                            var.set(dmf.current_settings[f'settings[{i_str}]'])

                try:
                    if apply_changes:
                        self.sett_update_label.config(fg='black', text='Settings change complete.')
                        ERR_LOGGER.info('Settings change complete.')
                        ERR_LOGGER.debug('Settings list after change:')
                        for key in dmf.current_settings:
                            ERR_LOGGER.debug(f'{key}:{dmf.current_settings[key]}')
                    else:
                        self.sett_update_label.config(fg='black', text='Settings retrieved.')
                        ERR_LOGGER.info('Settings retrieved.')
                        for key in dmf.current_settings:
                            ERR_LOGGER.debug(f'{key}:{dmf.current_settings[key]}')
                
                except tk.TclError as e:
                    ERR_LOGGER.error(e)
                    self.sett_update_label.config(fg='red', text='ERROR: Unexpected error.')
                    return
        
        #: No open connection.
        else:
            ERR_LOGGER.warning('There is no connection open.')
            self.sett_update_label.config(fg='red', text='ERROR: No connection open.')

    def exit_settings(self):
        '''
        Clears all saved settings then destroy the Settings window.
        '''
        self.settings_list.clear()
        ERR_LOGGER.info('Clearing settings list.')
        dmf.clear_settings()
        ERR_LOGGER.debug('Settings list after clear:')
        for key in dmf.current_settings:
            ERR_LOGGER.debug(f'{key}:{dmf.current_settings[key]}')
        destroy_window(self)
        
        
class PUIbtoolWindow(Toplevel):
    '''
    PUIbtool window
    '''
    #: PUIb thread
    puib_thread = None
    
    #: Flag and name for current working port.
    port_closed = False
    port_name = None

    def __init__(self, *args, **kwargs):
        '''
        Creates a PUIbtool window
        '''
        super().__init__(*args, **kwargs)
        ERR_LOGGER.info('Creating puibtool window.')
        
        #: PUIbtool window
        self.title('Run PUIbtool')
        self.iconbitmap('puilogo.ico')
        self.resizable(0,0)
        self.lift()

        #: COM port widget
        puib_com_port_title = Label(self, text='COM Port')
        puib_com_port_title.grid(row=0, column=0)

        self.puib_com_port = StringVar()

        puib_com_port_menu = OptionMenu(self, self.puib_com_port, *dmf.SERIAL_PORTS)
        puib_com_port_menu.grid(row=0, column=1)
        
        #: Firmware image widget
        puib_fw_label = Label(self, text='Firmware')
        puib_fw_label.grid(row=1, column=0)

        self.puib_fw = StringVar()
        puib_fw_entry = Entry(self, width=80, textvariable=self.puib_fw)
        puib_fw_entry.grid(row=1, column=1)

        puib_fw_button = Button(self, text='Image Path', width=10, command=self.get_file_path)
        puib_fw_button.grid(row=1, column=2, sticky='W')
        
        #: Text box widget.
        self.puib_text = Text(self, font=('Times', 16))
        self.puib_text.grid(row=2, column=0, columnspan=3, padx=5, pady=5)
        self.puib_text.insert('end', f'WARNINGS:\n\n'
                              f'* DO NOT power down the device or close this window when the tool is running.\n'
                              f'* This process may take several minutes.\n\n'
                              f'INSTRUCTIONS\n\n'
                              f'Flashing Firmware:\n'
                              f'1. Select the COM port and firmware image for the device above.\n'
                              f'2. Power off the device.\n'
                              f'3. Within 3 seconds of powering on the device, press the \'RUN PUIbtool\' button.\n'
                              f'4. Once the firmware has been flashed, this window may be closed.\n\n'
                              f'Creating Firmware Image:\n'
                              f'1. Select the firmware .bin file above.\n'
                              f'2. Select \'Create Image File\' at the bottom of this page.\n'
                              f'3. Press the \'RUN PUIbtool\' button.\n\n\n')
        self.puib_text.config(state='disabled')
        
        puib_start_button = Button(self, text='Run PUIbtool', command=self.start_puib_thread, 
                                bg="#A8C5A7", fg='black', padx=5, pady=5, width=25, height=3)
        puib_start_button.grid(row=3, rowspan=2, column=1)
        
        #: Flash selection widget.
        self.puib_flash_iv = IntVar()
        puib_ex_flash_button = Radiobutton(self, text='Flash Firmware', variable=self.puib_flash_iv, 
                                          value=0)
        puib_in_flash_button = Radiobutton(self, text='Create Image File', variable=self.puib_flash_iv, 
                                          value=1)
        puib_ex_flash_button.grid(row=3, column=2, padx=5, pady=1)
        puib_in_flash_button.grid(row=4, column=2, padx=5, pady=1)
        
        #: Closes the current port and halts threads so puibtool can be ran.
        if dmf.serial_connection:
            ERR_LOGGER.info(f'Serial connection open on {dmf.working_com_port}.')
            
            #: Wait for connection to close.
            root.run_puibtool_flag = True
            self.port_closed = True
            self.port_name = dmf.working_com_port
            ERR_LOGGER.info(f'Closing {self.port_name}.')
            if not dmf.close_port():
                ERR_LOGGER.error('Could not close serial connection.')
                self.exit_puib()
        
        #: Exit PUIbtool window when closed.
        self.protocol('WM_DELETE_WINDOW', lambda: self.exit_puib())

    def get_file_path(self):
        '''
        Inserts the selected file path into puib_fw_entry.
        If entry already has a value, it is deleted and replaced.
        '''
        ERR_LOGGER.debug('Getting firmware image file path from user.')
        fp = filedialog.askopenfilename(filetypes=[('PUI firmware', '.img .dmi .bin'), ('All Files','.*')])
        ERR_LOGGER.info(f'Firmware file path: {fp}')
        self.puib_fw.set(fp)
        self.lift()
        
    def start_puib_thread(self):
        '''
        Starts puib_tread. A new thread is needed to print the current output of the command line to the
        text window.
        '''
        if self.puib_thread:
            ERR_LOGGER.warning(f'Attempting to close previous thread {self.puib_thread.name}.')
            self.puib_thread.join()
        self.puib_thread = threading.Thread(target=self.run_puibtool, name='puibtool', daemon=True)
        ERR_LOGGER.info('Starting \'puibtool\' thread.')
        self.puib_thread.start()

    def run_puibtool(self):
        '''
        Executes the PUIbtool.exe from the command line.
        '''
        #: Copy the firmware image to the same directory as puibtool.exe
        try:
            ERR_LOGGER.debug(f'Copying firmware from {self.puib_fw.get()} -> {os.path.dirname(__file__)}')
            shutil.copy(self.puib_fw.get(), os.path.dirname(__file__))
            
        #: No firmware image was selected.
        except FileNotFoundError as e:
            ERR_LOGGER.error(e)
            self.puib_text.config(state='normal')
            self.puib_text.insert('end', 'Please select a firmware image.\n')
            self.puib_text.config(state='disabled')
            
            #: Re-open port and return
            if self.port_closed:
                ERR_LOGGER.info(f'Reconnecting to {self.port_name}')
                root.start_console_thread(self.port_name)
                root.run_puibtool_flag = False
            return
        
        #: Parse firmware image filename.
        fw_name = self.puib_fw.get().split('/')[-1]
        ERR_LOGGER.debug(f'Firmware image={fw_name}')
        
        #: Command for internal or external flash memory.
        if self.puib_flash_iv.get() == 0:
            puib_cmd = f'puibtool.exe flash --port \\\\.\\{self.puib_com_port.get()} --img \"{fw_name}\"'
        else:
            puib_cmd = f'puibtool.exe image --bin {fw_name}'
        
        self.puib_text.config(state='normal')
        self.puib_text.insert('end', 'Running puibtool.exe...\n')
        self.puib_text.insert('end', puib_cmd)
        self.puib_text.config(state='disabled')
        
        #: Runs the tool and prints the command line output to the text window.
        try:
            ERR_LOGGER.info(f'Running puibtool: {puib_cmd}')
            with subprocess.Popen(puib_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, 
                                universal_newlines=True) as puib_output:
                for line in puib_output.stdout:
                    ERR_LOGGER.debug(f'Popen output: {line}')
                    self.puib_text.config(state='normal')
                    self.puib_text.insert('end', line)
                    self.puib_text.config(state='disabled')
                    self.puib_text.see('end')
        
        #: Catch any unexpected exceptions generated by subprocess library.
        except Exception as e:
            ERR_LOGGER.error(e)
            self.puib_text.config(state='normal')
            self.puib_text.insert('end', 'An unexpected error has occurred. Please close this window and try again.\n')
            self.puib_text.config(state='disabled')
            
            #: Re-open port and return
            if self.port_closed:
                ERR_LOGGER.info(f'Reconnecting to {self.port_name}')
                root.start_console_thread(self.port_name)
                root.run_puibtool_flag = False
            return
        
        #: Remove firmware image copy from current directory.
        os.remove(fw_name)
        ERR_LOGGER.info(f'Removed {fw_name} from current directory.')
        self.puib_text.config(state='normal')
        self.puib_text.insert('end', 'This window may now be closed.\n')
        self.puib_text.config(state='disabled')
        
    def exit_puib(self):
        '''
        Destroy the PUIbtool window.
        '''
        #: Reconnect the current working port.
        if self.port_closed:
            ERR_LOGGER.info(f'Reconnecting to {self.port_name}')
            root.start_console_thread(self.port_name)
            root.run_puibtool_flag = False
        else:
            self.puib_text.config(state='normal')
            self.puib_text.insert('end', f'Could not re-open connection on {self.port_name}.'
                                  f'Please open the connection again from the File\\COM Port menu.\n')
            self.puib_text.config(state='disabled')
            ERR_LOGGER.warning(f'Could not re-open connection on {self.port_name}.\n')
            time.sleep(5)
        
        ERR_LOGGER.debug('Waiting for \'puibtool\' thread to join')
        if self.puib_thread: self.puib_thread.join()
        destroy_window(self)


class LogParserWindow(Toplevel):
    '''
    Log Parser window
    '''
    def __init__(self, *args, **kwargs):
        '''
        Create a Log Parser window
        '''
        super().__init__(*args, **kwargs)
        ERR_LOGGER.info('Creating log parser window.')

        #: Log Parser window
        self.title('Log Parser')
        self.iconbitmap('puilogo.ico')
        self.resizable(0,0)
        self.lift()

        #: Instructions label
        lp_instruct = Label(self, text='Separate each term with two commas (,,)', font=('Times New Roman', 12))
        lp_instruct.grid(row=0, column=0, columnspan=4, padx=20)

        #: File path widget
        lp_file_path_label = Label(self, text='Log File Path')
        lp_file_path_label.grid(row=1, column=0, padx=20, sticky='e')

        self.lp_file_path = StringVar()
        lp_file_path_entry = Entry(self, bd=3, width=80, textvariable=self.lp_file_path)
        lp_file_path_entry.grid(row=1, column=1, columnspan=2)

        lp_file_path_button = Button(self, text='Open File', command=self.get_file_path)
        lp_file_path_button.grid(row=1, column=3, padx=20)

        #: Targets widget
        lp_targets_label = Label(self, text='Targets')
        lp_targets_label.grid(row=2, column=0, padx=20, sticky='e')

        self.lp_targets = StringVar()
        lp_targets_entry = Entry(self, bd=3, width=80, textvariable=self.lp_targets)
        lp_targets_entry.grid(row=2, column=1, columnspan=2)

        #: Exclude widget
        lp_exclude_label = Label(self, text='Exclude')
        lp_exclude_label.grid(row=3, column=0, padx=20, sticky='e')

        self.lp_exclude = StringVar()
        lp_exclude_entry = Entry(self, bd=3, width=80, textvariable=self.lp_exclude)
        lp_exclude_entry.grid(row=3, column=1, columnspan=2)

        #: Extra lines widget
        lp_extra_lines_label = Label(self, text='Include Extra Lines')
        lp_extra_lines_label.grid(row=4, column=0, padx=20, sticky='e')

        #: Lines before widget
        lp_xlb_label = Label(self, text='Lines Before')
        lp_xlb_label.grid(row=4, column=1, sticky='w')

        self.lp_xlb = StringVar()
        self.lp_xlb.set('0')
        lp_xlb_entry = Entry(self, bd=3, width=5, textvariable=self.lp_xlb)
        lp_xlb_entry.grid(row=4, column=1)

        #: Lines after widget
        lp_xla_label = Label(self, text='Lines After')
        lp_xla_label.grid(row=4, column=2, sticky='w')

        self.lp_xla = StringVar()
        self.lp_xla.set('0')
        lp_xla_entry = Entry(self, bd=3, width=5, textvariable=self.lp_xla)
        lp_xla_entry.grid(row=4, column=2)

        #: Parse button
        lp_parse_button = Button(self, width=25, font='-weight bold', bg='#D0E7E8', text='Parse', 
                                 command=self.parse_terms)
        lp_parse_button.grid(row=5, column=0, columnspan=4, pady=10)

        #: Text box frame
        lp_text_frame = Frame(self, width=125, height=45)
        lp_text_frame.grid(row=6, column=0, columnspan=4, padx=10, pady=5)

        #: Text box widget
        lp_scrollbar = Scrollbar(lp_text_frame, orient='vertical')
        lp_scrollbar.pack(side='right', fill='y')

        self.lp_text_box = Text(lp_text_frame, height=45, width=125, state='disabled')
        self.lp_text_box.pack(side='bottom', fill='both', expand=True)

        self.lp_text_box.config(yscrollcommand=lp_scrollbar.set)
        lp_scrollbar.config(command=self.lp_text_box.yview)
        
        #: Exit Log Parser window when closed.
        self.protocol('WM_DELETE_WINDOW', lambda: destroy_window(self))

    def get_file_path(self):
        '''
        Location of log file that will be parsed.
        '''
        ERR_LOGGER.debug('Getting log file path from user.')
        fp = filedialog.askopenfilename(filetypes=[('Log files', '.txt .log'), ('All Files','.*')])
        ERR_LOGGER.info(f'Log file path: {fp}')
        self.lp_file_path.set(fp)
        self.lift()

    def parse_terms(self):
        '''
        Parses the log file based on targets, excludes, and extra lines.
        Prints the result to the text box window.
        '''
        target_list = self.lp_targets.get().split(',,')
        ERR_LOGGER.debug(f'target list: {target_list}')
        exclude_list = self.lp_exclude.get().split(',,')
        ERR_LOGGER.debug(f'exclude list: {exclude_list}')
        temp_parse_list = []
        parse_list = []

        #: Reads log file.
        if self.lp_file_path.get():
            ERR_LOGGER.info(f'Reading {self.lp_file_path.get()}')
            with open(self.lp_file_path.get(), 'r') as f:
                file_content = f.read().splitlines()

            #: Tries to convert StrinVar() -> int
            try:
                xlb = int(self.lp_xlb.get())
                ERR_LOGGER.debug(f'Lines before: {xlb}')
                xla = int(self.lp_xla.get())
                ERR_LOGGER.debug(f'Lines after: {xla}')
            except ValueError as e:
                ERR_LOGGER.error(e)
                self.lp_text_box.config(state='normal')
                self.lp_text_box.delete(1.0, 'end')
                self.lp_text_box.insert('end', 'Lines before or after must be a number!')
                self.lp_text_box.config(state='disabled')
                return

            ERR_LOGGER.info('Parsing file.')
            
            #: Excludes lines that contain the exclude items.
            if exclude_list[0] != '':
                for line in file_content:
                    if not any(exclude in line for exclude in exclude_list):
                        temp_parse_list.append(line)
            else:
                temp_parse_list = file_content.copy()

            #: Creates a list of all lines containing the targets.
            for i, line in enumerate(temp_parse_list):
                if any(target in line for target in target_list):
                    
                    #: Adds the number of lines before each target.
                    if xlb > 0:
                        for j in range(xlb):
                            try:
                                #: Break loop if line contains a different target.
                                if any(target in temp_parse_list[i - (xlb - j)] for target in target_list):
                                    ERR_LOGGER.debug(f'Line before contains another target: {line}')
                                    break

                                #: Add the jth line before target to parse_list.
                                parse_list.append(temp_parse_list[i - (xlb - j)])

                            #: Break loop if start of temp_parse_list is reached.
                            except IndexError:
                                ERR_LOGGER.info(f'Start of parse list reached.')
                                break
                    
                    #: Add line containing target to parse_list.
                    parse_list.append(line)

                    #: Adds the number of lines after each target.
                    if xla > 0:
                        for j in range(xla):
                            try:
                                
                                #: Break loop if current line contains a different target.
                                if any(target in temp_parse_list[i + (j + 1)] for target in target_list):
                                    ERR_LOGGER.debug(f'Line after contains another target: {line}')
                                    break

                                #: Add the jth line after target to parse_list.
                                parse_list.append(temp_parse_list[i + (j + 1)])

                            #: Break loop if end of temp_parse_list is reached.
                            except IndexError:
                                ERR_LOGGER.info(f'End of parse list reached.')
                                break
                    
                    #: Add a blank space between each target.
                    if xlb + xla > 0:
                        parse_list.append(' ')

            #: Write new parsed file to text box window.
            ERR_LOGGER.info('Parsing complete.')
            self.lp_text_box.config(state='normal')
            self.lp_text_box.delete(1.0, 'end')
            for line in parse_list:
                self.lp_text_box.insert('end', line + '\n')
            self.lp_text_box.config(state='disabled')
            
        #: No log file was selected.
        else:
            ERR_LOGGER.warning('No log file was selected.')
            self.lp_text_box.config(state='normal')
            self.lp_text_box.delete(1.0, 'end')
            self.lp_text_box.insert('end', 'Please select a log file to parse.')
            self.lp_text_box.config(state='disabled')
            
    
class PreferencesWindow(Toplevel):
    '''
    Preferences window.
    '''
    #: Serial console font style, font size, and line break.
    font_styles = ('Arial', 'Courier', 'Impact', 'Lucida Console', 'MS Serif', 'Terminal', 'Times New Roman', 'Verdana')
    font_sizes = ('6', '7', '8', '9', '10', '11', '12', '13', '14')
    line_breaks = ('<LF>', '<CR>', '<CRLF>')
    
    def __init__(self, *args, **kwargs):
        '''
        Create a preferences window.
        '''
        super().__init__(*args, **kwargs)
        ERR_LOGGER.info('Creating preferences window.')
        
        #: Preferences window.
        self.title('Preferences')
        self.iconbitmap('puilogo.ico')
        self.lift()
        
        row = 0
        self.pref_title = Label(self, text='Preferences', font=('Times New Roman', '14', 'bold'), width=27)
        self.pref_title.grid(row=row, column=1, padx=10, pady=5)
        
        row += 1
        self.pref_newline_sv = StringVar()
        self.pref_newline_sv.set(root.nl_break_sv.get())
        self.perf_newline_label = Label(self, text='Line Break', width=9)
        self.pref_newline_options = OptionMenu(self, self.pref_newline_sv, *self.line_breaks)
        
        self.perf_newline_label.grid(row=row, column=0, sticky='w', padx=5, pady=2)
        self.pref_newline_options.grid(row=row, column=2, padx=5, pady=2)
        
        row += 1
        self.pref_font_style_sv = StringVar()
        self.pref_font_style_sv.set(root.console_font_sv.get())
        self.pref_font_style_label = Label(self, text='Font Style', width=9)
        self.pref_font_style_options = OptionMenu(self, self.pref_font_style_sv, *self.font_styles)
        
        self.pref_font_style_label.grid(row=row, column=0, sticky='w', padx=5, pady=2)
        self.pref_font_style_options.grid(row=row, column=2, padx=5, pady=2)
        
        row += 1
        self.pref_font_size_sv = StringVar()
        self.pref_font_size_sv.set(root.console_size_sv.get())
        self.pref_font_size_label = Label(self, text='Font Size', width=9)
        self.pref_font_size_options = OptionMenu(self, self.pref_font_size_sv, *self.font_sizes)
        
        self.pref_font_size_label.grid(row=row, column=0, sticky='w', padx=5, pady=2)
        self.pref_font_size_options.grid(row=row, column=2, padx=5, pady=2)
        
        row += 1
        self.pref_break_label = Label(self, text='')
        self.pref_break_label.grid(row=row, column=0, columnspan=2, pady=5)
        
        row += 1
        self.pref_log_path_sv = StringVar()
        self.pref_log_path_sv.set(root.log_file_path)
        self.pref_log_path_label = Label(self, text='Log File Path')
        self.pref_log_path_entry = Entry(self, bd=3, width=75, textvariable=self.pref_log_path_sv)
        self.pref_log_path_button = Button(self, text='Select Path', command=self.get_log_path)
        
        self.pref_log_path_label.grid(row=row, column=0, padx=3, pady=5)
        self.pref_log_path_entry.grid(row=row, column=1, padx=3, pady=5)
        self.pref_log_path_button.grid(row=row, column=2, padx=3, pady=5)
        
        row += 1
        self.pref_apply_button = Button(self, text='Apply Preferences', font='bold', bg='#D1E8D0', 
                                        command=self.apply_preferences)
        self.pref_apply_button.grid(row=row, column=1, padx=5, pady=10)
        
        #: Exit Preferences window when closed.
        self.protocol('WM_DELETE_WINDOW', lambda: destroy_window(self))
        
    def apply_preferences(self):
        '''
        Apply any preferences changes.
        '''
        ERR_LOGGER.info('Applying preferences changes.')
        ERR_LOGGER.debug(f'line break={self.pref_newline_sv.get()}\nfont style={self.pref_font_style_sv.get()}\n'
                         f'font size={self.pref_font_size_sv.get()}\nlog path={self.pref_log_path_sv.get()}')
        root.change_newline_break(self.pref_newline_sv.get())
        root.change_font(self.pref_font_style_sv.get(), self.pref_font_size_sv.get())
        if self.pref_log_path_sv.get() != root.log_file_path:
            root.change_log_file_path(self.pref_log_path_sv.get())
        destroy_window(self)
        
    def get_log_path(self):
        '''
        Location of where log files will be saved.
        '''
        ERR_LOGGER.debug('Getting log file path from user.')
        fp = filedialog.askdirectory(initialdir=root.log_file_path)
        ERR_LOGGER.info(f'Log file path: {fp}')
        self.pref_log_path_sv.set(fp)
        self.lift()
        
    
class HighlightConsoleWindow(Toplevel):
    '''
    Highlight Console window.
    '''
    def __init__(self, *args, **kwargs):
        '''
        Create a highlight console window.
        '''
        super().__init__(*args, **kwargs)
        ERR_LOGGER.info('Creating highlight console window.')
        
        #: Highlight Console window.
        self.title('Highlight Console')
        self.iconbitmap('puilogo.ico')
        self.lift()
        
        #: Entry widget.
        self.hc_sv = StringVar()
        self.hc_entry = Entry(self, textvariable=self.hc_sv, width=75)
        self.hc_button = Button(self, text='Add', width=10, command=self.highlight_targets)
        
        self.hc_entry.grid(row=0, column=0, padx=1, pady=2)
        self.hc_button.grid(row=0, column=1, padx=1, pady=2)
        self.bind("<Return>", (lambda event: self.highlight_targets()))
        
        self.hc_label_list = []
        self.hc_button_list = []
        
        if root.highlight_target_list:
            ERR_LOGGER.debug('Previous highlight targets present.')
            for item in root.highlight_target_list:
                ERR_LOGGER.debug(f'Previous target: {item}')
                self.hc_label_list.append(Label (self, text=item) )
                self.hc_button_list.append(Button (self, text='X', bg='black', fg='red', 
                                                   command=( lambda: self.delete_target(item) ) ))
            
            for i in range(len(root.highlight_target_list)):
                ERR_LOGGER.debug('Rendering previous highlight targets')
                row = i+1
                self.hc_label_list[i].grid(row=row, column=0, padx=1, pady=2)
                self.hc_button_list[i].grid(row=row, column=1, padx=1, pady=2)
        
        #: Exit Highlight Console window when closed.
        self.protocol('WM_DELETE_WINDOW', lambda: destroy_window(self))
    
    def highlight_targets(self):
        '''
        List of targets that will be highlighted in the serial console, along with their
        associated widgets.
        '''
        #: Checks if target is already in list or if entry is empty.
        if not (self.hc_sv.get() in root.highlight_target_list or self.hc_sv.get() == ''):
            ERR_LOGGER.debug(f'Valid highlight target: \'{self.hc_sv.get()}\'.')
            
            #: Adds new target to the highlight list.
            current_target = self.hc_sv.get()
            root.highlight_target_list.append(current_target)
            self.hc_label_list.append(Label (self, text=current_target) )
            self.hc_button_list.append(Button (self, text='X', bg='black', fg='red', 
                                               command=( lambda: self.delete_target(current_target) ) ))
            
            #: Adjust window geometry length.
            ERR_LOGGER.debug('Adjusting window geometry.')
            current_geometry = str(self.geometry()).replace('+', 'x').split('x')   
            self.geometry(f'{current_geometry[0]}x{str(int(current_geometry[1]) + 30)}+'
                          f'{current_geometry[2]}+{current_geometry[3]}')
        
        #: Renders the widgets.
        if root.highlight_target_list:
            for i, item in enumerate(root.highlight_target_list):
                row = i+1
                self.hc_label_list[i].grid(row=row, column=0, padx=1, pady=2)
                self.hc_button_list[i].grid(row=row, column=1, padx=1, pady=2)
                ERR_LOGGER.info(f'New highlight target: \'{item}\'')
            
        self.hc_sv.set('')
        root.highlight_change_flag = True
    
    def delete_target(self, target):
        '''
        Deletes the target from the list of items to be highlighted and destroys its
        associated widgets.
        
        @param target: The target that will be removed.
        '''
        try:
            #: Get index of target
            ERR_LOGGER.info(f'Attempting to remove highlight target: \'{target}\'')
            index = root.highlight_target_list.index(target)
            ERR_LOGGER.debug(f'Index of target: {index}.')
            root.highlight_target_list.pop(index)
            
            #: Remove associated widgets from list and destroy them.
            ERR_LOGGER.debug(f'Destroying \'{target}\' label and button.')
            self.hc_label_list[index].destroy()
            self.hc_label_list.pop(index)
            self.hc_button_list[index].destroy()
            self.hc_button_list.pop(index)
            
            #: Adjust window geometry length.
            ERR_LOGGER.debug('Adjusting window geometry.')
            current_geometry = str(self.geometry()).replace('+', 'x').split('x')   
            self.geometry(f'{current_geometry[0]}x{str(int(current_geometry[1]) - 30)}+'
                          f'{current_geometry[2]}+{current_geometry[3]}')

        except IndexError as e:
            ERR_LOGGER.error(e)
        
        #: Call highlight_targets again so widgets can be re-rendered.
        ERR_LOGGER.debug('Calling highlight_targets() after deletion.')
        self.highlight_targets()
         

class WriteToLogWindow(Toplevel):
    '''
    Write To Log window.
    '''
    def __init__(self, *args, **kwargs):
        '''
        Create a Write To Log window.
        '''
        super().__init__(*args, **kwargs)
        ERR_LOGGER.info('Creating write to log window.')
        
        #: Write To Log window.
        self.title('Write To Log')
        self.iconbitmap('puilogo.ico')
        self.lift()
        
        #: Entry widget.
        self.wtl_sv = StringVar()
        self.wtl_entry = Entry(self, textvariable=self.wtl_sv, width=75)
        self.wtl_button = Button(self, text='OK', width=10, command=self.add_to_log)
        
        self.wtl_entry.grid(row=0, column=0, padx=1, pady=2)
        self.wtl_button.grid(row=0, column=1, padx=1, pady=2)
        self.bind("<Return>", (lambda event: self.add_to_log()))
        
        #: Exit Write To Log window when closed.
        self.protocol('WM_DELETE_WINDOW', lambda: destroy_window(self))
    
    def add_to_log(self):
        '''
        Sets the root.write_log_flag and root.write_log_text variables to enter
        the log comment.
        '''
        root.write_log_text = f':::: {self.wtl_sv.get()} ::::\n'
        ERR_LOGGER.info(f'\'{self.wtl_sv.get()}\' will be written to log.')
        root.write_log_flag = True
        destroy_window(self)
    

class ChangeWindowTitle(Toplevel):
    '''
    Change Window Title window.
    '''
    def __init__(self, *args, **kwargs):
        '''
        Create a Change Window Title window.
        '''
        super().__init__(*args, **kwargs)
        ERR_LOGGER.info('Creating change window title window.')
        
        #: Write To Log window.
        self.title('Change Window Title')
        self.iconbitmap('puilogo.ico')
        self.lift()
        
        #: Entry widget.
        self.cwt_sv = StringVar()
        self.cwt_entry = Entry(self, textvariable=self.cwt_sv, width=75)
        self.cwt_button = Button(self, text='OK', width=10, command=self.change_title)
        
        self.cwt_entry.grid(row=0, column=0, padx=1, pady=2)
        self.cwt_button.grid(row=0, column=1, padx=1, pady=2)
        self.bind("<Return>", (lambda event: self.change_title()))
        
        #: Exit Write To Log window when closed.
        self.protocol('WM_DELETE_WINDOW', lambda: destroy_window(self))
    
    def change_title(self):
        '''
        Sets the title of Device Monitor window.
        '''
        if self.cwt_sv.get().strip() != '':
            root.title(self.cwt_sv.get())
            ERR_LOGGER.info(f'Window Title changed to \'{self.cwt_sv.get()}\'.')
        destroy_window(self)
    

class AddCarriageReturnWindow(Toplevel):
    '''
    Add Carriage Return window.
    '''
    def __init__(self, *args, **kwargs):
        '''
        Create an Add Carriage Return window.
        '''
        super().__init__(*args, **kwargs)
        ERR_LOGGER.info('Creating add carriage return window.')
        
        #: Write To Log window.
        self.title('Add Carriage Return')
        self.iconbitmap('puilogo.ico')
        self.lift()
        
        #: Entry widget.
        self.acr_sv = StringVar()
        self.acr_entry = Entry(self, textvariable=self.acr_sv, width=75)
        self.acr_button = Button(self, text='OK', width=10, command=self.send_command)
        
        self.acr_entry.grid(row=0, column=0, padx=1, pady=2)
        self.acr_button.grid(row=0, column=1, padx=1, pady=2)
        self.bind("<Return>", (lambda event: self.send_command()))
        
        #: Exit Write To Log window when closed.
        self.protocol('WM_DELETE_WINDOW', lambda: destroy_window(self))
    
    def send_command(self):
        '''
        Send a command with a <CR> at the end.
        '''
        root.send_console_command(self.acr_sv.get(), force_cr=True)
        ERR_LOGGER.info(f'Added <CR> to command: \'{self.acr_sv.get()}\'')
        destroy_window(self)
        
        
class MainWindow(tk.Tk):
    '''
    Device Monitor window
    '''
    #: Log file path.
    log_file_path = None
    
    #: Flags a change in the log file path.   
    log_file_change_flag = False
    
    #: Flag to start a new log file.
    new_log_flag = False
    
    #: Semaphore for threads.
    halt_threads_flag = False
    
    #: Flags a previous connection still trying to open if another is requested.
    cancel_connect_flag = False
    
    #: Flags when PUIBtool is running.
    run_puibtool_flag = False
    
    #: Triggers device info check.
    get_device_info_flag = False
    
    #: Flag and text content for writing to log.
    write_log_flag = False
    write_log_text = None

    #: Flag and content for highlighting console. 
    highlight_change_flag = False
    highlight_target_list = []
    
    #: Position and cutoff for auto scrolling.
    auto_scroll = 0
    auto_scroll_cutoff = 0.998

    #: Flag for spawning extended window.
    extend_window_flag = False
    
    #: Settings.ini file manager and variables.
    config_manager = ConfigParser()
    last_port = None

    #: Console and Status threads.
    console_thread = None
    status_thread = None
    
    #: Child windows created by the Main window.
    sett = None
    puib = None
    lp = None
    pref = None
    hc = None
    wtl = None
    cwt = None
    acr = None
    
    def __init__(self, *args, **kwargs):
        '''
        Create a Device Monitor window.
        '''
        super().__init__(*args, **kwargs)
        ERR_LOGGER.info('Creating main window.')
        
        #: Device monitor window.
        self.title('PUI Device Monitor')
        self.iconbitmap('puilogo.ico')
        self.geometry('800x800')

        #: Menu widget
        self.menubar = Menu(self, tearoff=0)

        #: File menu
        self.file_menu = Menu(self, tearoff=0)
        self.com_menu = Menu(self, tearoff=0)
        
        #: Menu StringVars
        self.com_port_sv = StringVar()
        self.nl_break_sv = StringVar()
        self.console_font_sv = StringVar()
        self.console_size_sv = StringVar()

        #: Settings.ini file check.
        if os.path.exists('settings.ini'):
            ERR_LOGGER.info('Reading settings.ini')
            self.config_manager.read('settings.ini')
            self.console_font_sv.set(self.config_manager.get('console', 'style'))
            self.console_size_sv.set(self.config_manager.get('console', 'size'))
            self.nl_break_sv.set(self.config_manager.get('console', 'line_break'))
            self.change_error_log_level(self.config_manager.get('error_logging', 'level'))
            self.change_log_file_path(self.config_manager.get('log', 'path'))
            
            #: Check if a previous COM port was saved to settings.ini file.
            try:
                self.last_port = self.config_manager.get('com_port', 'port')
                ERR_LOGGER.debug(f'Last port: {self.last_port}')
        
            #: Previous COM port wasn't in settings file.
            #: It will be added once a connection is made.
            except NoSectionError as e:
                ERR_LOGGER.error(e)
                pass
            except NoOptionError as e:
                ERR_LOGGER.error(e)
                pass
        
        #: Set default values for style, size, and line_break if no settings.ini file exists.                
        else:
            ERR_LOGGER.info('No settings.ini file found.')
            self.config_manager['console'] = {}
            with open('settings.ini', 'w') as f:
                self.config_manager.write(f)
            
            self.nl_break_sv.set('<LF>')
            self.console_font_sv.set('Veranda')
            self.console_size_sv.set('9')
            self.change_error_log_level('DEBUG')
            self.change_log_file_path(os.path.join(os.path.dirname(__file__), 'Log_Files'))

        #: Add all available ports to COM port menu.
        ERR_LOGGER.debug(f'Available COM ports: {dmf.SERIAL_PORTS}')
        for item in dmf.SERIAL_PORTS:
            self.com_menu.add_radiobutton(label=item, variable=self.com_port_sv, 
                                          command=(lambda : self.start_console_thread(self.com_port_sv.get())))
        
        #: File menu entries    
        self.menubar.add_cascade(label='File', menu=self.file_menu)
        self.file_menu.add_cascade(label='COM Port', menu=self.com_menu)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Device Settings', command=self.settings_window)
        self.file_menu.add_command(label='PUIbtool', command=self.puibtool_window)
        self.file_menu.add_command(label='Log Parser', command=self.log_parser_window)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Change Window Title', command=self.change_window_title_window)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Exit', command=self.exit_main)

        #: Console menu
        self.console_menu = Menu(self, tearoff=0)

        #: Console Menu entries    
        self.menubar.add_cascade(label='Console', menu=self.console_menu)
        self.console_menu.add_command(label='Highlight Console', command=self.highlight_console_window)
        self.console_menu.add_command(label='Clear Console', command=self.clear_console)
        self.console_menu.add_command(label='Add Carriage Return', command=self.add_carriage_return)
        self.console_menu.add_separator()
        self.console_menu.add_command(label='Write to Log', command=self.write_to_log_window)
        self.console_menu.add_command(label='Start New Log', command=self.start_new_log)
        self.console_menu.add_separator()
        self.console_menu.add_command(label='Preferences', command=self.preferences_window)

        #: Right click menu
        self.right_click_menu = Menu(self, tearoff=0)
        self.right_click_menu.add_command(label='Copy')
        self.right_click_menu.add_command(label='Paste')

        #: Add menus
        self.config(menu=self.menubar)
        self.bind("<Button-3>", self.right_click_event)
        
        #: Console frame
        self.console_window_frame = Frame(self, padx=10, pady=10)
        
        #: Serial Console widget
        self.console_text_frame = Frame(self.console_window_frame)
        
        self.console_scrollbar = Scrollbar(self.console_text_frame, orient='vertical')
        self.console_window = Text(self.console_text_frame, bg='black', fg='white', state='disabled',
                                   font=(self.console_font_sv.get(), int(self.console_size_sv.get())))
        self.console_window.config(yscrollcommand=self.console_scrollbar.set)
        self.console_scrollbar.config(command=self.console_window.yview)
        self.extend_button = Button(self.console_text_frame, text='\u00BB', borderwidth=2, relief='groove', 
                                    font=('Times New Roman', 12), command=self.extend_window)
        
        self.console_window.tag_configure('highlight', background='yellow', foreground='black')
        
        self.console_window.pack(side='left', fill='both', expand=True)
        self.console_scrollbar.pack(side='left', fill='y')
        self.extend_button.pack(side='left', ipady=10)
        
        #: Command Entry widget
        self.command_frame = Frame(self.console_window_frame)
        
        self.command_var = StringVar()
        self.command_entry = Entry(self.command_frame, textvariable=self.command_var, borderwidth=2, relief='groove')
        self.command_button = Button(self.command_frame, text='Send', borderwidth=2, relief='groove',
                                     command=(lambda: self.send_console_command(self.command_var.get())))
        self.bind("<Return>", (lambda event: self.send_console_command(self.command_var.get())))
        
        self.command_entry.pack(side='left', fill='x', expand=True)
        self.command_button.pack(side='left')
        
        #: Pack Console Frame
        self.console_text_frame.pack(fill='both', expand=True)
        self.command_frame.pack(fill='x')
        
        #: Pack Main
        self.console_window_frame.pack(side='left', fill='both', expand=True)
        
        #: Set font and line break settings.
        self.change_font(self.console_font_sv.get(), self.console_size_sv.get())
        self.change_newline_break(self.nl_break_sv.get())
        
        #: Open previous COM port.
        if self.last_port:
            if self.config_manager.get('com_port', 'active') == 'n':
                ERR_LOGGER.debug(f'Setting current port to previous port.')
                self.com_port_sv.set(self.last_port)
                self.start_console_thread(self.last_port)

        #: Exit main window when closed.
        self.protocol('WM_DELETE_WINDOW', lambda: self.exit_main())
        
    def right_click_event(self, event):
        '''
        Right click event handler.
    
        @param event: Currently supports [Copy, Paste]
        '''
        try:
            ERR_LOGGER.debug('Configuring right-click behavior')
            self.right_click_menu.tk_popup(event.x_root, event.y_root)
            self.right_click_menu.entryconfigure('Copy', command=(lambda: event.widget.event_generate("<<Copy>>")))
            self.right_click_menu.entryconfigure('Paste', command=(lambda: event.widget.event_generate("<<Paste>>")))
        finally:
            self.right_click_menu.grab_release()
    
    def log_file_format(self):
        return f'Logfile_{time.strftime("%Y-%m-%d_%H%M", time.localtime())}_{random.choice(string.ascii_letters)}.log'
          
    def start_console_thread(self, com_port):
        '''
        Starts thread to establish serial connection and print serial data the console window.
        '''
        #: Checks if a previous connection is still active.
        if self.halt_threads_flag:
            ERR_LOGGER.debug('HALT_THREAD already enabled.')
            self.cancel_connect_flag = True
        else:
            self.halt_threads_flag = True
            
        if self.console_thread:
            ERR_LOGGER.warning(f'Attempting to close previous thread \'{self.console_thread.name}\'.')
            self.console_thread.join()
        self.console_thread = threading.Thread(target=self.serial_console, args=(com_port,), name='console')
        ERR_LOGGER.debug('starting \'console\' thread.')
        self.console_thread.start()
    
    def serial_console(self, com_port):
        '''
        Establishes a serial connection on the given COM port. Once established, prints serial data to the console 
        window, along with a time stamped log file.
        
        @param com_port: The COM port that will be opened.
        '''
        #: Connect to serial port
        ERR_LOGGER.info('Starting connection loop.')
        while True:
            
            #: Attempts to open serial connection.
            if dmf.change_port(com_port):
                self.console_window.config(state='normal')
                self.console_window.delete(1.0, 'end')
                self.console_window.insert('end', f'Opening serial connection on {self.com_port_sv.get()}...\n')
                self.console_window.config(state='disabled')
                self.console_window.see('end')
                ERR_LOGGER.info(f'Opened serial connection on {self.com_port_sv.get()}')
                self.halt_threads_flag = False
                
                #: Write COM port to settings.ini file
                ERR_LOGGER.debug(f'Attempting to write \'{dmf.serial_connection.name}\' to settings.ini')
                self.config_manager['com_port'] = {'port' : com_port, 'active' : 'y'}
                with open('settings.ini', 'w') as f:
                    self.config_manager.write(f)

                #: Closes extended window if open.
                if self.extend_window_flag:
                    ERR_LOGGER.debug('Attempting to close extended window.')
                    self.extend_window()
                break
            
            else:
                
                #: Checks if another connection is started.
                if self.cancel_connect_flag:
                    ERR_LOGGER.warning('A connection attempt was cancelled.')
                    self.cancel_connect_flag = False
                    return
                self.console_window.config(state='normal')
                self.console_window.insert('end', 
                                           f'Error opening serial connection on {com_port}. Retrying in 1 second...\n')
                self.console_window.config(state='disabled')
                ERR_LOGGER.info(f'Error opening serial connection on {com_port}.')
                time.sleep(1)
        
        #: Log file path.
        file_name = os.path.join(self.log_file_path, self.log_file_format())
        ERR_LOGGER.debug(f'Log_File path: {file_name}.')
        
        #: Write to console window.    
        ERR_LOGGER.info('Starting console loop.')
        while True:
            
            #: Stops console thread if puibtool is running.
            if self.run_puibtool_flag:
                ERR_LOGGER.info('Halting \'console\' thread to run puibtool.')
                return
            
            if not self.halt_threads_flag:
                    
                #: Get timestamp
                t = datetime.now()
                ct = f'[{t.strftime("%Y-%m-%d %H:%M:%S.%f")[:23]}]'

                #: Print to console and log.
                line = f'{dmf.listen_port()}\n'
                line_log = f'{ct} {line}'
                
                #: Connection error that couldn't be reestablished.
                if line == 'False\n':
                    self.console_window.config(state='normal')
                    self.console_window.insert('end', 'There was a connection error. Please reconnect the COM port.')
                    self.console_window.config(state='disabled')
                    return
                
                #: Second check when listen_port function is returned from.
                if self.halt_threads_flag:
                    ERR_LOGGER.warning('\'console\' thread has been halted.')
                    return

                if float(self.console_window.index('end')) > 2000.0:
                    self.auto_scroll_cutoff = 1.0
                elif float(self.console_window.index('end')) > 1000.0:
                    self.auto_scroll_cutoff = 0.999
                else:
                    self.auto_scroll_cutoff = 0.998
                
                #: Insert text into console window.
                self.auto_scroll = self.console_scrollbar.get()[1]
                self.console_window.config(state='normal')
                self.console_window.insert('end', line)
                self.console_window.config(state='disabled')
                if self.auto_scroll >= self.auto_scroll_cutoff:
                    self.console_window.see('end')
                
                #: Highlight target(s) in console.
                if self.highlight_target_list:
                    ERR_LOGGER.debug(f'Current highlight targets: {self.highlight_target_list}')
                    
                    #: Highlighting starts at the last line printed.
                    search_start = self.console_window.index('insert' + '-%dl'%1)
                    ERR_LOGGER.debug(f'Highlight search start index: {search_start}')
                    
                    if self.highlight_change_flag:
                        ERR_LOGGER.debug('Highlight Change. ' 
                                         'Attempting to remove previous highlight tag due.')
                        self.console_window.tag_remove('highlight', search_start, 'end')
                        self.highlight_change_flag = False
                    
                    #: Highlight all targets in the list.
                    for target in self.highlight_target_list:
                        if target in line:
                            ERR_LOGGER.info(f'Highlighting \'{target}\'')
                            search_offset = '+%dc'%len(target)
                            ERR_LOGGER.debug(f'Highlight search offset: {search_offset}')
                            index_start = self.console_window.search(target, search_start, 'end')
                            ERR_LOGGER.debug(f'Highlight index start: {index_start}')
                            index_end = index_start + search_offset
                            ERR_LOGGER.debug(f'Highlight index end: {index_end}')
                            try:
                                self.console_window.tag_add('highlight', index_start, index_end)
                                ERR_LOGGER.debug(f'Adding highlight tag.')
                            except tk.TclError as e:
                                ERR_LOGGER.error(f'Error when trying to highlight \'{target}\':\n {e}')
                            search_start = index_end.split('.')[0] + '.0'
                            ERR_LOGGER.debug(f'Highlight next search start index: {search_start}')
                
                #: Clear any previous highlighting.
                else:
                    if self.highlight_change_flag:
                        ERR_LOGGER.debug('Highlight list empty, removing last highlight tag.')
                        self.console_window.tag_remove('highlight', search_start, 'end')
                        self.highlight_change_flag = False

                #: Log file path was changed.
                if self.log_file_change_flag:
                    file_name = os.path.join(self.log_file_path, self.log_file_format())
                    ERR_LOGGER.info(f'Log_File path change: {file_name}.')
                    self.log_file_change_flag = False
                
                #: New log file requested.
                if self.new_log_flag:
                    file_name = os.path.join(self.log_file_path, self.log_file_format())
                    ERR_LOGGER.info(f'New log file started.')
                    self.new_log_flag = False
                
                #: Write to log file.
                try:
                    with open(file_name, 'a') as f:
                        if self.write_log_flag:
                            f.write(self.write_log_text)
                            self.write_log_flag = False
                        f.write(line_log)
                except UnicodeEncodeError as e:
                    ERR_LOGGER.error(e)
                    pass

            #: Joins thread if COM port is changed.
            else:
                ERR_LOGGER.warning('\'console\' thread has been halted.')
                return

    def send_console_command(self, command, force_cr=False):
        '''
        Writes the command to the serial port (unless the command is an error log level change).
        
        @param command: The data to be written.
        '''
        #: Changes error log level.
        if command == 'errorlevelcritical':
            self.change_error_log_level('CRITICAL')
            self.console_window.config(state='normal')
            self.console_window.insert('end', 'Error log level set to CRITICAL.\n')
            self.console_window.config(state='disabled')
            confirm = True
        elif command == 'errorlevelerror':
            self.change_error_log_level('ERROR')
            self.console_window.config(state='normal')
            self.console_window.insert('end', 'Error log level set to ERROR.\n')
            self.console_window.config(state='disabled')
            confirm = True
        elif command == 'errorlevelwarning':
            self.change_error_log_level('WARNING')
            self.console_window.config(state='normal')
            self.console_window.insert('end', 'Error log level set to WARNING.\n')
            self.console_window.config(state='disabled')
            confirm = True
        elif command == 'errorlevelinfo':
            self.change_error_log_level('INFO')
            self.console_window.config(state='normal')
            self.console_window.insert('end', 'Error log level set to INFO.\n')
            self.console_window.config(state='disabled')
            confirm = True
            
        #: Writes command.
        else:
            if force_cr:
                temp_lb = dmf.line_break_tx
                dmf.line_break_tx = [0, 1, 0]
                confirm = dmf.send_serial_command(command)
                dmf.line_break_tx = temp_lb
            else:
                confirm = dmf.send_serial_command(command)

        self.command_entry.delete(0, 'end')
        self.console_window.see('end')
        self.console_scrollbar.set(1.0, 1.0)
        return confirm
    
    def clear_console(self):
        '''
        Clear the console window.
        '''
        ERR_LOGGER.debug('Attempting to clear console window.')
        self.console_window.config(state='normal')
        self.console_window.delete(1.0, 'end')
        self.console_window.config(state='disabled')

    def start_status_thread(self):
        '''
        Starts thread to update status windows.
        '''
        if self.status_thread:
            ERR_LOGGER.warning(f'Attempting to close previous thread \'{self.status_thread.name}\'.')
            self.status_thread.join()
        self.status_thread = threading.Thread(target=self.update_status, name='status')
        ERR_LOGGER.debug(f'Starting \'status\' thread.')
        self.status_thread.start()
    
    def update_status(self):
        '''
        Checks the serial stream for the specified hooks and updates the corresponding widget with the current data.
        '''
        ERR_LOGGER.info('Starting status loop.')
        while True:
            time.sleep(0.01)
            if (not self.halt_threads_flag) and self.extend_window_flag:
                
                #: Stop thread if puibtool is running.
                if self.run_puibtool_flag:
                    ERR_LOGGER.info('Halting \'status\' thread to run puibtool.')
                    return
                    
                #: Device info check (must be triggered).
                if self.get_device_info_flag and (round( time.time() - T_START ) % 10) == 0:
                    ERR_LOGGER.info('Device info requested.')
                    dmf.parse_serial_data('Version')
                    if dmf.device_info["main"] != '' and dmf.device_info["imei"] != '':
                        ERR_LOGGER.debug('Updating device info.')
                        self.device_info_window.config(state='normal')
                        self.device_info_window.delete(1.0, 'end')
                        self.device_info_window.insert('end', f'IMEI: {dmf.device_info["imei"]}\n'
                                                  f'ICCID: {dmf.device_info["iccid"]}\n'
                                                  f'IMSI: {dmf.device_info["imsi"]}\n'
                                                  f'MSIDN: {dmf.device_info["msidn"]}\n'
                                                  f'MAIN FW: {dmf.device_info["main"]}\n'
                                                  f'SETT: {dmf.device_info["sett"]}\n'
                                                  f'VCM FW: {dmf.device_info["vcm"]}\n'
                                                  f'VCM_CFG: {dmf.device_info["vcm_cfg"]}\n'
                                                  f'BT: {dmf.device_info["bt"]}\n'
                                                  f'POWER: {dmf.device_info["power"]}')
                        self.device_info_window.config(state='disabled')
                        self.get_device_info_flag = False

                #: Update State and Voltage every 3 seconds.
                if (round( time.time() - T_START) % 3) == 0:
                    
                    #: Device status checks.
                    dmf.parse_serial_data(dmf.STATUS_HOOKS["state"])
                    dmf.parse_serial_data(dmf.STATUS_HOOKS["volts"])
                    dmf.parse_serial_data(dmf.STATUS_HOOKS["event"])

                    ERR_LOGGER.debug('Updating state and voltage.')
                    self.state_label.config(text=f'{dmf.current_status["state"]}\n'
                                            f'VIN: {dmf.current_status["vin"]}\n'
                                            f'BATT: {dmf.current_status["batt"]}')

                    #: State label coloring.
                    if dmf.current_status["state"] == 'Sleeping':
                        self.state_label.config(bg='#4470F6', fg='white')
                    elif dmf.current_status["state"] in ['Idling', 'Towing']:
                        self.state_label.config(bg='#E8E230', fg='black')
                    elif dmf.current_status["state"] == 'Stopped':
                        self.state_label.config(bg='#EA0000', fg='white')
                    elif dmf.current_status["state"] in ['Moving', 'Ignition On', 'Virtual Ignition On']:
                        self.state_label.config(bg='#18EE18', fg='black')
                    else:
                        self.state_label.config(bg='#F0F0F0', fg='black')
                    
                #: Check if the device has been reboot.
                #: Sets get_device_info_flag = True after reboot to update device status.
                if dmf.current_status["event"] == 'Device Reboot':
                    ERR_LOGGER.info('Waiting for device reboot.')
                    self.state_label.config(text='Rebooting...', bg='#F0F0F0', fg='black')
                    dmf.wait_for_reboot()
                    dmf.clear_info()
                    self.get_device_info_flag = True
                        
                time.sleep(0.8)
                
            #: Joins thread if COM port is changed.
            else:
                ERR_LOGGER.warning('\'status\' thread has been halted.')
                return

    def extend_window(self):
        '''
        Creates and destroys an extended window that will display the device info and current status.
        '''
        if dmf.serial_connection:
            
            #: Window toggle.
            self.extend_window_flag ^= True
            ERR_LOGGER.info(f'Extend Window={self.extend_window_flag}')
            
            #: Create extended window.
            if self.extend_window_flag:
                
                #: Extend window geometry.
                ERR_LOGGER.debug('Rendering extended window.')
                new_width = str(self.winfo_width() + 274)
                new_height = str(self.winfo_height())
                self.geometry(f'{new_width}x{new_height}')
                
                #: \u00AB = Arrow pointing right.
                self.extend_button.config(text='\u00AB')
                
                self.extend_frame = Frame(self)
                
                #: State widget
                self.state_title = Label(self.extend_frame, text='Current State', font=('Times', 12))
                self.state_label = Label(self.extend_frame, borderwidth=2, width=15, height=5, relief='solid', 
                                    font=('Times', 20))
                
                #: Device info widget
                self.device_info_title = Label(self.extend_frame, text='Device Info', font=('Times', 12))
                self.device_info_window = Text(self.extend_frame, borderwidth=2, width=38, height=10, relief='solid', 
                                        state='disabled', font=('Times', 10))
                
                #: Pack state and device info
                self.state_title.pack(side='top')
                self.state_label.pack(side='top')
                self.device_info_title.pack(side='top')
                self.device_info_window.pack(side='top')
                
                #: Pack extended frame and triggers device info collection.
                self.extend_frame.pack(side='left', fill='both', padx=20)
                self.get_device_info_flag = True
                self.start_status_thread()

            #: Destroy extended window.
            else:
                
                #: Reduce window geometry.
                ERR_LOGGER.debug('Destroying extended window.')
                new_width = str(self.winfo_width() - 274)
                new_height = str(self.winfo_height())
                self.geometry(f'{new_width}x{new_height}')
                
                #: \u00AB = Arrow pointing left.
                self.extend_button.config(text='\u00BB')
                
                #: Clear device info.
                dmf.clear_info()
                
                #: Erase extended window widgets and join thread.
                self.state_title.pack_forget()
                self.state_label.pack_forget()
                self.device_info_title.pack_forget()
                self.device_info_window.pack_forget()
                self.extend_frame.pack_forget()
                ERR_LOGGER.debug('Waiting for \'status\' thread to join.')
                if self.status_thread.is_alive(): self.status_thread.join()
    
    def start_new_log(self):
        self.new_log_yesno = askyesno('Start New Log', message='Start a new log file?')
        if self.new_log_yesno:
            self.new_log_flag = True
        return
    
    def change_newline_break(self, nl_break):
        '''
        Changes the current line break characters.
        '''
        #: line break is '\n'
        if nl_break == '<LF>':
            ERR_LOGGER.debug('Line break set to \'<LF>\'.')
            dmf.set_line_break([1,0,0], [1,0,0])
            self.nl_break_sv.set('<LF>')
        
        #: line break is '\r'
        elif nl_break == '<CR>':
            ERR_LOGGER.debug('Line break set to \'<CR>\'.')
            dmf.set_line_break([0,1,0], [0,1,0])
            self.nl_break_sv.set('<CR>')
            
        #: line break is '\r\n'
        else:
            ERR_LOGGER.debug('Line break set to \'<CRLF>\'.')
            dmf.set_line_break([0,0,1], [0,0,1])
            self.nl_break_sv.set('<CRLF>')
        
        #: Write change to settings.ini file.
        try: 
            self.config_manager['console']['line_break'] = nl_break
            ERR_LOGGER.info('Writing \'line_break\' to settings.ini')
            with open('settings.ini', 'w') as f:
                self.config_manager.write(f)

        except PermissionError as e:
            ERR_LOGGER.error(e)
                   
    def change_font(self, style, size):
        '''
        Changes the current console font.

        @param style: Selected font style.

        @param size: Selected font size.
        '''
        #: Change console widget font style and size.
        try:
            ERR_LOGGER.debug('Attempting to change font settings.')
            self.console_window.config(font=(style, int(size)))
            self.console_font_sv.set(style)
            self.console_size_sv.set(size)
        except tk.TclError as e:
            ERR_LOGGER.error(e)
        
        #: Save font style and size to settings.ini
        try:
            self.config_manager['console']['style'] = style
            self.config_manager['console']['size'] = size
            ERR_LOGGER.info('Writing \'style\' and \'size\' to settings.ini')
            with open('settings.ini', 'w') as f:
                self.config_manager.write(f)
        except PermissionError as e:
            ERR_LOGGER.error(e)

    def change_error_log_level(self, level):
        '''
        Changes the error logging level.
        
        @param level: The log level (INFO, WARNING, ERROR, or CRITICAL)
        '''
        ERR_LOGGER.debug(f'Changing error logging level to {level}.')
        ERR_HANDLER.setLevel(logging._nameToLevel[level])
        dmf.ERR_HANDLER.setLevel(logging._nameToLevel[level])
        
        #: Write change to settings.ini
        try:
            self.config_manager['error_logging'] = {'level' : level}
            ERR_LOGGER.info(f'Writing \'level={level}\' to settings.ini')
            with open('settings.ini', 'w') as f:
                self.config_manager.write(f)
        except PermissionError as e:
            ERR_LOGGER.error(e)
    
    def change_log_file_path(self, path):
        '''
        Changes the log file path for saved logs.
        
        @param path: The directory log files will be saved to.
        '''
        ERR_LOGGER.info(f'Changing log file path to: {path}')
        
        if not os.path.exists(path):
            os.mkdir(path)
        self.log_file_path = path
        self.log_file_change_flag = True
        
        #: Write change to settings.ini
        try:
            self.config_manager['log'] = {'path' : path}
            ERR_LOGGER.info(f'Writing \'path={path}\' to settings.ini')
            with open('settings.ini', 'w') as f:
                self.config_manager.write(f)
        except PermissionError as e:
            ERR_LOGGER.error(e)
        
    def settings_window(self):
        '''
        Open a Device Settings window.
        '''
        if self.sett:
            ERR_LOGGER.info('Closing previous settings window.')
            destroy_window(self.sett)
        self.sett = SettingsWindow(self)
        self.sett.lift()

    def puibtool_window(self):
        '''
        Open a PUIbtool window.
        '''
        if self.puib:
            ERR_LOGGER.info('Closing previous puibtool window.')
            destroy_window(self.puib)
        self.puib = PUIbtoolWindow(self)
        self.puib.lift()

    def log_parser_window(self):
        '''
        Open a Log Parser window.
        '''
        if self.lp:
            ERR_LOGGER.info('Closing previous log parser window.')
            destroy_window(self.lp)
        self.lp = LogParserWindow(self)
        self.lp.lift()
    
    def preferences_window(self):
        '''
        Open a preferences window.
        '''
        if self.pref:
            ERR_LOGGER.info('Closing previous preferences window.')
            destroy_window(self.pref)
        self.pref = PreferencesWindow(self)
        self.pref.lift()
        
    def highlight_console_window(self):
        '''
        Open a Highlight Console window.
        '''
        if self.hc:
            ERR_LOGGER.info('Closing previous highlight console window.')
            destroy_window(self.hc)
        self.hc = HighlightConsoleWindow(self)
        self.hc.lift()
        
    def write_to_log_window(self):
        '''
        Open a Write To Log window.
        '''
        if self.wtl:
            ERR_LOGGER.info('Closing previous write to log window.')
            destroy_window(self.wtl)
        self.wtl = WriteToLogWindow(self)
        self.wtl.lift()
    
    def change_window_title_window(self):
        '''
        Open a Change Window Title window.
        '''
        if self.cwt:
            ERR_LOGGER.info('Closing previous change window title window.')
            destroy_window(self.cwt)
        self.cwt = ChangeWindowTitle(self)
        self.cwt.lift()
    
    def add_carriage_return(self):
        '''
        Open an Add Carriage Return window.
        '''
        if self.acr:
            ERR_LOGGER.info('Closing previous add carriage return window.')
            destroy_window(self.acr)
        self.acr = AddCarriageReturnWindow(self)
        self.acr.lift()
        
    def exit_main(self):
        '''
        Close the COM port, join all active threads, destroy the Main window, and exit the program.
        '''
        #: Joins an thread still running.
        self.halt_threads_flag = True
        ERR_LOGGER.debug('Waiting for \'console\' thread to join.')
        if self.console_thread: self.console_thread.join()
        ERR_LOGGER.debug('Waiting for \'status\' thread to join.')
        if self.status_thread: self.status_thread.join()
        
        if dmf.serial_connection:
            
            #: Closes serial connection.
            ERR_LOGGER.debug(f'Attempting to close \'{dmf.serial_connection.name}\'.')
            if dmf.close_port():
                self.config_manager['com_port']['active'] = 'n'
                ERR_LOGGER.info('Writing \'active\' to settings.ini')
                with open('settings.ini', 'w') as f:
                    self.config_manager.write(f)
            else:
                try:
                    raise dmf.SerialException
                except dmf.SerialException as e:
                    ERR_LOGGER.error(e)
                    sys.exit(1)
                    
        ERR_LOGGER.info('Closing application.')
        self.destroy()
        sys.exit(0)
    

def destroy_window(window_object: Toplevel):
    '''
    Destroy the tkinter window that is passed in and sets the corresponding child window object to None.
    
    @param window_object: Tkinter window object.
    '''
    try:
        window_title = window_object.title()
    except tk.TclError as e:
        ERR_LOGGER.error('Could not get window object name.')
        ERR_LOGGER.error(e)
    ERR_LOGGER.info(f'Closing \'{window_title}\' window.')
    window_object.destroy()
    
    #: Sets child window objects back to None.
    if window_title == 'Device Settings':
        root.sett = None
        return
    if window_title == 'Run PUIbtool':
        root.puib = None
        return
    if window_title == 'Log Parser':
        root.lp = None
        return
    if window_title == 'Preferences':
        root.pref = None
        return
    if window_title == 'Highlight Console':
        root.hc = None
        return
    if window_title == 'Write To Log':
        root.wtl = None
        return
    if window_title == 'Change Window Title':
        root.cwt = None
        return
    if window_title == 'Add Carriage Return':
        root.acr = None
        return


def handle_exception(exc_type, exc_value, exc_traceback):
    '''
    Catches any unhandled sys or tkinter exceptions.
    '''
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    ERR_LOGGER.critical("Unhandled sys or tkinter exception:", exc_info=(exc_type, exc_value, exc_traceback))
    try:
        root.exit_main()
    except RuntimeError as e:
        ERR_LOGGER.error(e)
        sys.exit(1)


def handle_threading_exception(args):
    '''
    Catches any unhandled threading exceptions.
    '''
    ERR_LOGGER.critical("Unhandled threading exception:", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    try:
        root.exit_main()
    except RuntimeError as e:
        ERR_LOGGER.error(e)
        sys.exit(1)
    
    
if __name__ == ('__main__'):

    #: Tkinter root window
    ERR_LOGGER.critical('========== NEW APPLICATION INSTANCE STARTED ==========\n\n')
    ERR_LOGGER.debug('Creating root.')
    root = MainWindow()
    
    #: Exception handlers.
    ERR_LOGGER.debug('Creating exception handlers.')
    sys.excepthook = handle_exception
    root.report_callback_exception = handle_exception
    threading.excepthook = handle_threading_exception
    
    #: Run
    ERR_LOGGER.info('Starting main loop')
    root.mainloop()
    