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
import BuildEmulationFiles as bef
import OBDLibrary as obd
import tkinter as tk
import ast
import json
import os

from tkinter import Canvas, Frame, Scrollbar, Label, OptionMenu, Button, Entry, StringVar
from tkinter import messagebox


class MainWindow(tk.Tk):
    """
    Main Window for SAINT Emulation Builder
    """
    #: List of parameter units, ranges, and fields.
    text_list = ['Unit: on/off, Range: 0 - 1',
                 'Unit: revolutions/minute, Range: 0 - 16383',
                 'Unit: km/hour, Range: 0 - 255',
                 'Unit: %, Range: 0% - 100%',
                 'Unit: °C, Range : -40° - 215°',
                 'Unit: grams/second, Range: 0 - 655.35',
                 'Unit: %, Range: 0% - 100%',
                 'Unit: seconds, Range: 0 - 65535',
                 'Unit: km, Range: 0 - 65535',
                 'Unit: kPa, Range: 0 - 655350',
                 'Unit: %, Range: 0% - 100%',
                 'Unit: km, Range: 0 - 65535',
                 'Unit: ratio, Range: 0 - 1.99',
                 'Unit: minutes, Range: 0 - 65535',
                 'Unit: minutes, Range: 0 -65535',
                 'Unit: state encoded, Range: {0=None, 1=Gasoline, 4=Diesel, 8=Electric}',
                 'Unit: °C, Range: -40° - 215°',
                 'Unit: liters/hour, Range: 0 - 3276.75',
                 'Fields: [Run Time, Idle Time, PTO Run Time, Unit: seconds, Range: 0 - 4294967294',
                 'Fields: [Concentration, Temperature, Level], Unit: [%, °C, %], '
                 'Range: [0% - 63.75%, -40° - 215°, 0% - 100%]',
                 'Unit: grams/second, Range: 0 - 1310.7',
                 'Unit: km, Range: 0 - 429496729.5',
                 'Separate each VIN with a comma (<VIN 1>, <VIN 2>, etc.)',
                 '[DTC groups]. Put "quotes" around each DTC and enclose each group in square brackets ["DTC 1"]']

    #: List of parameter labels
    label_list = list(obd.OBD_ABBREVIATIONS.values())

    #: List of parameter abbreviations.
    abbrev_list = list(obd.OBD_ABBREVIATIONS.keys())

    #: List of parameter IDs.
    pid_list = [f'0x{value}' for value in obd.OBD_PID.values()]
    pid_list.extend(['VIN', 'DTC'])

    #: List of parameter StringVar()
    entry_list = []

    #: Path for saved parameters file.
    saved_parameters_path = os.path.join(os.path.dirname(__file__), 'saved_parameters.json')
    saved_parameters = None

    def __init__(self, *args, **kwargs):
        """
        Render the Main Window
        """
        super().__init__(*args, **kwargs)

        #: Check if saved_parameters.json exists and loads the content into saved_parameters.
        if os.path.exists(self.saved_parameters_path):
            with open(self.saved_parameters_path, 'r') as f:
                self.saved_parameters = json.load(f)

        #: Window title and icon.
        self.title('SAINT Emulation Builder')
        self.iconbitmap('puilogo.ico')

        #: Scrollable Canvas widget.
        self.mw_canvas = Canvas(self, width=900, height=900)
        self.mw_scrollbar = Scrollbar(self, command=self.mw_canvas.yview)
        self.mw_canvas.configure(yscrollcommand=self.mw_scrollbar.set)
        self.mw_canvas.bind('<Configure>', func=self._mw_canvas_configure)
        self.mw_canvas.bind_all('<MouseWheel>', func=self._mw_mouse_wheel)

        self.mw_canvas.pack(side='left')
        self.mw_scrollbar.pack(side='left', fill='y')

        #: Frame for widgets.
        self.mw_frame = Frame(self.mw_canvas)
        self.mw_canvas.create_window((0, 0), window=self.mw_frame, anchor='nw')

        #: Application Title.
        row = 0
        self.mw_title_label = Label(self.mw_frame, text='SAINT Emulation Builder', font=('Times New Roman', 18, 'bold'),
                                    justify='center')
        self.mw_title_label.grid(row=row, column=0, columnspan=2, padx=5, pady=30)

        #: CAN Type widgets.
        row = 1
        can_types = ['11', '29']
        self.can_sv = StringVar()
        self.can_label = Label(self.mw_frame, text='CAN Type')
        self.can_om = OptionMenu(self.mw_frame, self.can_sv, *can_types)
        self.can_label.grid(row=row, column=0, padx=5)
        self.can_om.grid(row=row, column=1, padx=5)

        #: Parameter widgets.
        row = 2
        for i, param_tuple in enumerate(zip(self.label_list, self.text_list, self.pid_list, self.abbrev_list)):
            #: Insert a blank row between each parameter.
            blank = Label(self.mw_frame, text='')
            blank.grid(row=row, column=0, columnspan=2, pady=10)

            #: Label and text widgets.
            row += 1
            self.entry_list.append(StringVar())
            param_label = Label(self.mw_frame, text=param_tuple[0])
            param_text = Label(self.mw_frame, text=param_tuple[1])
            param_label.grid(row=row, column=0, padx=5)
            param_text.grid(row=row, column=1, padx=5)

            #: PID, entry, and enable widgets.
            row += 1
            param_pid = Label(self.mw_frame, text=param_tuple[2])
            param_entry = Entry(self.mw_frame, textvariable=self.entry_list[i], width=70, relief='groove')
            param_pid.grid(row=row, column=0, padx=5)
            param_entry.grid(row=row, column=1, padx=5)

            #: Insert values from saved_parameters.json into entry widget.
            saved_entry = ', '.join(str(saved_item) for saved_item in self.saved_parameters[param_tuple[3]])
            param_entry.insert(0, saved_entry)

            row += 1

        self.mw_button = Button(self.mw_frame, text='Build Emulation Files', font=('Times New Roman', 16, 'bold'),
                                bg='#D1E8D0', command=self.build_files)
        self.mw_button.grid(row=row, column=0, columnspan=2, padx=5, pady=30)

    def _mw_canvas_configure(self, event):
        """
        Configure canvas scrollbar.
        """
        self.mw_canvas.configure(scrollregion=self.mw_canvas.bbox('all'))

    def _mw_mouse_wheel(self, event):
        """
        Enable mouse wheel scrolling.
        """
        self.mw_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

    def build_files(self):
        """
        Formats entries, saves them to a json file, then uses BuildEmulationFiles.py to create the emulation files.
        """

        #: List of parameter values entered by the user.
        value_list = []

        #: Loops through abbrev_list to associate a value with each PID.
        for i, abbrev in enumerate(self.abbrev_list):

            #: Check if entry is blank.
            if self.entry_list[i].get() != '':

                #: VIN can't use ast.literal_eval, so it is handled here.
                if abbrev == 'VIN':
                    value_list.append([j.strip() for j in self.entry_list[i].get().split(',')])

                #: Converts values entered as a string into a literal values like integers, tuples, or lists.
                else:
                    value_list.append(ast.literal_eval(self.entry_list[i].get()))

            #: Enters a blank value if entry is blank.
            else:
                value_list.append('')

        #: Creates a dictionary of parameter abbreviations : entered values
        file_data = dict(zip(self.abbrev_list, value_list))

        #: Writes dictionary to json file.
        with open('saved_parameters.json', 'w') as f:
            json.dump(file_data, f, indent=4)

        #: Removes any keys that have no values from the file_data dictionary.
        #: This is necessary since BuildEmulationFiles.py doesn't have handling for a key:value pair with no value. 
        data_pairs = {k: v for k, v in file_data.items() if v}

        #: Make directory for SAINT emulation files.
        dir_path = os.path.join(os.path.dirname(__file__), 'SAINT_Emulation')
        if not (os.path.exists(dir_path)):
            os.mkdir(dir_path)

        #: Build the emulation file.
        try:
            if bef.build_emulation_file(int(self.can_sv.get()), **data_pairs):
                messagebox.showinfo('Complete', message=f'SAINT Emulation Files created, they can '
                                                        f'be found at:\n{dir_path}')
            else:
                messagebox.showerror('Error', message='There was an error creating the emulation ')
        except ValueError:
            messagebox.showwarning('No CAN Type', message='Please select a CAN type.')


if __name__ == '__main__':
    root = MainWindow()
    root.mainloop()
