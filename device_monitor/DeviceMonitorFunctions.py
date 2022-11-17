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
import logging
import os
import sys
import time

from serial import Serial, SerialException
from serial.tools import list_ports

#: CONSTANTS
#: Error logger
ERR_LOGGER = logging.getLogger(__name__)
ERR_LOGGER.setLevel(logging.DEBUG)
ERR_HANDLER = logging.FileHandler(filename=os.path.join(os.path.dirname(__file__),'ErrorLog.log'), encoding='latin-1')
ERR_HANDLER.setLevel(logging.INFO)
ERR_HANDLER.setFormatter(logging.Formatter('%(asctime)s - %(name)-s:%(threadName)s - %(levelname)s - %(message)s'))
ERR_LOGGER.addHandler(ERR_HANDLER)

#: List of available COM ports
SERIAL_PORTS = [comport.name for comport in list_ports.comports()]

#: Valid device states.
VALID_STATES = ('Boot', 'Stopped', 'Moving', 'Sleeping', 'Reserved', 'PwrProtect', 'Idling', 'Towing', 'Speeding')

#: Device event statuses.
EVENTS = {'EVENT_IGNITION_ON' : 'Ignition On', 
          'IGNITION_OFF' : 'Ignition Off', 
          'EVENT_VIRTUAL_IGN_ON' : 'Virtual Ignition On', 
          'VIRTUAL_IGN_OFF' : 'Virtual Ignition Off',
          'DEVICE_REBOOT' : 'Device Reboot', 
          'END_OF_TOW': 'End of Tow'}

#: Device info search hooks.
INFO_HOOKS = {'main' : 'main=', 
              'sett' : 'sett=',
              'vcm' : 'vcm=',
              'vcm_cfg' : 'vcm_cfg=',
              'bt' : 'bt=',
              'power' : 'power=',
              'imei': 'imei=',
              'imsi': 'imsi=',
              'iccid': 'iccid=',
              'msidn': 'msidn='}

STATUS_HOOKS = {'volts' : 'Vin', 
                'state' : 'sats:', 
                'event' : '>< >< ><'}


#: VARIABLES
#: Serial object
serial_connection = None

#: Current working COM port.
working_com_port = None

#: Serial connection semaphore
serial_safe = False

#: Queue for serial data.
serial_data = []

#: Data queue semaphore
data_safe = True

device_sleep = False

#: New line break for serial messages.
#: ['\n', '\r', '\r\n']
line_break_rx = [1, 0, 0]
line_break_tx = [1, 0, 0]

#: Device info dictionary
device_info = {'main' : '',
               'sett' : '',
               'vcm' : '',
               'vcm_cfg' : '',
               'bt' : '',
               'power' : '',
               'imei': '',
               'imsi': '',
               'iccid': '',
               'msidn': ''}

current_status = {'state' : 'Reading State...', 
                  'vin': 'Reading...', 
                  'batt' : 'Reading...', 
                  'event': 'Waiting for\nEvent Status...'}

current_settings = {'settings[01]' : '',
                    'settings[02]' : '',
                    'settings[03]' : '',
                    'settings[04]' : '',
                    'settings[05]' : '',
                    'settings[06]' : '',
                    'settings[07]' : '',
                    'settings[08]' : '',
                    'settings[09]' : '',
                    'settings[10]' : '',
                    'settings[11]' : '',
                    'settings[12]' : '',
                    'settings[13]' : '',
                    'settings[14]' : '',
                    'settings[15]' : '',
                    'settings[16]' : '',
                    'settings[17]' : '',
                    'settings[18]' : '',
                    'settings[19]' : '',
                    'settings[20]' : '',
                    'settings[21]' : '',
                    'settings[22]' : '',
                    'settings[23]' : '',
                    'settings[24]' : '',
                    'settings[25]' : '',
                    'settings[26]' : '',
                    'settings[27]' : '',
                    'settings[28]' : '',
                    'settings[29]' : '',
                    'settings[30]' : '',
                    'settings[31]' : '',
                    'settings[32]' : '',
                    'settings[33]' : '',
                    'settings[34]' : '',
                    'settings[35]' : '',
                    'settings[36]' : '',
                    'settings[37]' : '',
                    'settings[38]' : '',
                    'settings[39]' : '',
                    'settings[40]' : '',
                    'settings[41]' : '',
                    'settings[42]' : '',
                    'settings[43]' : '',
                    'settings[44]' : '',
                    'settings[45]' : '',
                    'settings[46]' : '',
                    'settings[47]' : '',
                    'settings[48]' : '',
                    'settings[49]' : '',
                    'settings[50]' : '',
                    'settings[51]' : '',
                    'settings[52]' : '',
                    'settings[53]' : '',
                    'settings[54]' : '',
                    'settings[55]' : '',
                    'settings[56]' : '',
                    'settings[57]' : '',
                    'settings[58]' : '',
                    'settings[59]' : '',
                    'settings[60]' : '',
                    'settings[61]' : '',
                    'settings[62]' : '',
                    'settings[63]' : '',
                    'settings[64]' : '',
                    'settings[65]' : '',
                    'settings[66]' : '',
                    'settings[67]' : '',
                    'settings[68]' : '',
                    'settings[69]' : '',
                    'settings[70]' : '',
                    'settings[71]' : '',
                    'settings[72]' : '',
                    'settings[73]' : '',
                    'settings[74]' : '',
                    'settings[75]' : '',
                    'settings[76]' : '',
                    'settings[77]' : '',
                    'settings[78]' : '',
                    'settings[79]' : '',
                    'settings[80]' : '',
                    'settings[81]' : '',
                    'settings[82]' : '',
                    'settings[83]' : '',
                    'settings[84]' : '',
                    'settings[85]' : '',
                    'settings[86]' : '',
                    'settings[87]' : '',
                    'settings[88]' : '',
                    'settings[89]' : '',
                    'settings[90]' : '',
                    'settings[91]' : '',
                    'settings[92]' : '',
                    'settings[93]' : '',
                    'settings[94]' : '',
                    'settings[95]' : '',
                    'settings[96]' : '',
                    'settings[97]' : '',
                    'settings[98]' : '',
                    'settings[99]' : '',
                    'settings[100]' : '',
                    'settings[101]' : '',
                    'settings[102]' : '',
                    'settings[103]' : '',
                    'settings[104]' : '',
                    'settings[105]' : '',
                    'settings[106]' : '',
                    'settings[107]' : '',
                    'settings[108]' : '',
                    'settings[109]' : '',
                    'settings[110]' : '',
                    'settings[111]' : '',
                    'settings[112]' : '',
                    'settings[113]' : '',
                    'settings[114]' : '',
                    'settings[115]' : '',
                    'settings[116]' : '',
                    'settings[117]' : '',
                    'settings[118]' : '',
                    'settings[119]' : '',
                    'settings[120]' : '',
                    'settings[121]' : '',
                    'settings[122]' : ''}


def open_port(com_port):
    '''
    Opens a serial connection. Once the connection has been opened, it gets assigned to the 
    serial_connection variable. This function should only be called by change_port() to avoid 
    collisions.
    
    @param com_port: The COM port.
    
    @return: True if the connection was successfully opened, False if the connection could not be opened.
    '''
    global serial_connection, working_com_port, serial_safe
    
    #: Returns true if a connection is already open.
    if serial_connection:
        ERR_LOGGER.warning('A connection is already open.')
        serial_safe = True
        working_com_port = com_port
        return True
    
    #: Attempts to open a connection on selected port.
    try:
        ERR_LOGGER.info(f'Opening serial connection on {com_port}.')
        ser = Serial(port=com_port, baudrate=115200, timeout=3, write_timeout=1)
        if not ser.isOpen():
            ser.open()
        serial_connection = ser
        serial_safe = True
        working_com_port = com_port
        ERR_LOGGER.info(f'Connection opened: {serial_connection.name}, {serial_connection.baudrate}, '
                        f'{serial_connection.bytesize}, {serial_connection.parity}')
        return True
    
    #: Failed to open connection.
    except SerialException as e:
        ERR_LOGGER.error(e)
        return False


def close_port():
    '''
    Closes the current serial connection.
    
    @return: True if the serial connection was closed successfully, False if there was an error.
    '''
    global serial_connection, working_com_port, serial_safe
    
    #: Attempts to closed current connection.
    try:
        if serial_connection:
            ERR_LOGGER.info(f'Closing serial connection on {serial_connection.name}.')
            serial_safe = False
            serial_connection.flush()
            serial_connection.close()
            serial_connection = None
            working_com_port = None
            serial_data.clear()
        return True

    #: Failed to close current connection.
    except SerialException as e:
        ERR_LOGGER.error(e)
        return False


def change_port(com_port):
    '''
    Closes the current serial connection, if active, and opens a new one.
    
    @param com_port: The new COM port.
    
    @return: open_port()
    '''
    
    #: Checks if a connection is already opened.
    if serial_connection:
        ERR_LOGGER.info(f'Changing serial port from {working_com_port} to {com_port}.')
        if not close_port():
            return False
    return open_port(com_port)


def reconnect():
    '''
    Attempt to reconnect to the current working port.
    
    @return: True if connection is reestablished, False otherwise.
    '''
    try:
        if serial_connection:
            
            #: Close, then re-open serial connection.
            serial_connection.close()
            serial_connection.open()
            if serial_connection.isOpen():
                return True
            else:
                return False
        else:
            return change_port(working_com_port)
        
    except SerialException as e:
        ERR_LOGGER.error(e)
        return False
    
    
def listen_port():
    '''
    Reads data from the serial buffer. Creates a string from the characters read until the line break 
    character is reached. Appends the serial_data queue with the string and returns it.
    
    @return: A string containing each character read until the line break is reached.
    '''
    global serial_safe, data_safe, device_sleep, line_break_rx

    line = ''
    t_start = time.time()
    
    while True:
        if serial_safe:
            try:
                
                #: Decodes byte to 'latin-1'
                c = str(serial_connection.read(), 'latin-1')
                
                #: Serial buffer is empty.
                if len(c) == 0:
                    c = ''
                    
                #: c is new line.
                if c == '\n':
                    if line_break_rx[0] and line != '':
                        break
                    elif line_break_rx[2] == 2 and line != '':
                        line_break_rx[2] = 1
                        break
                    else:
                        c = ''
                        
                #: c is carriage return.
                if c == '\r':
                    if line_break_rx[1] and line != '':
                        break
                    elif line_break_rx[2] and line != '':
                        line_break_rx[2] = 2
                        c = ''
                    else:
                        c = ''

                #: Create string.
                line += c
                
                #: A new line character hasn't appeared on the buffer for over 10 seconds.
                #: This usually occurs when the device in sleep or power protect mode.
                if time.time() - t_start > 10:
                    line = f'...'
                    break
            
            #: Tries to reestablish serial connection if it was closed by device.
            except SerialException as e:
                ERR_LOGGER.error(e)
                serial_safe = False
                error_count = 0
                
                #: Tries to reconnect 5 times.
                while not reconnect():
                    if error_count == 5:
                        ERR_LOGGER.error('Could not reestablish a serial connection.')
                        return False
                    error_count += 1
                    ERR_LOGGER.info(f'Trying to reestablish serial connection ({error_count}/5)')
                    time.sleep(1)
                    
                #: Reconnected successfully.
                ERR_LOGGER.info(f'Successfully reconnected to {working_com_port}.')
                serial_safe = True
                return f'Reconnected to {working_com_port}.\n'

        else:
            ERR_LOGGER.info('Serial data is not currently safe to access.')
            return 'Seral connection closed.\n'

    #: Ignores queue size during reboot since it's unsafe to access.
    if current_status["event"] == 'Device Reboot':
        serial_data.append(line)
        return line 

    else:
        
        #: Clears queue if it grows too large.
        if len(serial_data) > 500:
            while not data_safe: pass
            data_safe = False
            try:
                raise QueueFull
            except QueueFull as e:
                ERR_LOGGER.error(e)
            serial_data.clear()
            data_safe = True
                
        #: Begins popping items from queue to reduce growth.
        if len(serial_data) > 200:
            if data_safe:
                data_safe = False
                serial_data.pop(0)
                data_safe = True
        
        if device_sleep:
            if '.' not in line:
                current_status["state"] = 'Stopped'
                device_sleep = False
        
        serial_data.append(line)
        return line
    

def parse_serial_data(target):
    '''
    Searches the serial_data queue for the target and updates the device_info and current_status values 
    when the target has been found. The queue entry is popped to ensure it isn't read again.
    
    @param target: The hook being searched for. Search hooks are defined in INFO_HOOKS and STATUS_HOOKS.
    '''
    global data_safe, device_sleep

    #: Check if something is in queue.
    if len(serial_data) > 0:
        
        if data_safe:
            data_safe = False
            
            #: Settings have been requested.
            if target == 'Settings':
                if not send_serial_command('settings'):
                    data_safe = True
                    return
                time.sleep(6)

                #: Queue is copied to ensure data isn't pushed out before it can be read.
                #: Queue is then cleared.
                temp_sett = serial_data.copy()
                serial_data.clear()
                data_safe = True

                for key in current_settings:
                    for line in temp_sett:
                        if key in line.replace('\t', ''):
                            try:
                                current_settings[key] = line.split('=', 1)[1].lstrip()

                            except IndexError as e:
                                ERR_LOGGER.error(e)
                                return
                return

            #: Device info has been requested.
            elif target == 'Version':
                if not send_serial_command('version'):
                    data_safe = True
                    return
                time.sleep(1)

                #: Queue is copied to ensure data isn't pushed out before it can be read.
                #: Queue is then cleared.
                temp_ver = serial_data.copy()
                serial_data.clear()
                data_safe = True

                for key in INFO_HOOKS:
                    for line in temp_ver:
                        if INFO_HOOKS[key] in line:
                            try:
                                temp_info_item = line.split(INFO_HOOKS[key])[1]
                                if temp_info_item.find(' ') != -1:
                                    temp_info_item = temp_info_item[:temp_info_item.find(' ')]
                                device_info[key] = temp_info_item

                            except IndexError as e:
                                ERR_LOGGER.error(e)
                                return
                return

            #: Voltage, State, or Event data has been requested.
            else:            
                for i, line in enumerate(serial_data):
                    if target in line:
                        try:
                            
                            #: Target is main voltage and battery voltage.
                            if target == STATUS_HOOKS["volts"]:
                                if 'Batt' in line:
                                    current_status["vin"] = line.split('Vin')[1].lstrip().split(' ')[0] + ' mV'
                                    current_status["batt"] = line.split('Batt')[1].lstrip().split(' ')[0] + ' mV'
                                serial_data.clear()
                                break

                            #: Target is current state.
                            if target == STATUS_HOOKS["state"]:
                                temp_state = line[20:].split(' ')[0]
                                if temp_state in VALID_STATES:
                                    if current_status["event"] in ['Ignition On', 'Virtual Ignition On'] \
                                    and temp_state == 'Moving':
                                        current_status["state"] = current_status["event"]
                                    elif temp_state == 'Sleeping' and not device_sleep:
                                        current_status["state"] = 'Stopped'
                                    else:
                                        current_status["state"] = temp_state
                                    
                                    #: Gets main voltage and battery voltage from state message when possible.
                                    if 'Vin' in line:
                                        current_status["vin"] = line.split('Vin')[1].lstrip().split(' ')[0] + ' mV'
                                        current_status["batt"] = line.split('Batt')[1].lstrip().split(' ')[0] + ' mV'

                            #: Target is last event.
                            if target == STATUS_HOOKS["event"]:
                                current_status["event"] = EVENTS[line[9:].split(' ')[0]]
                                serial_data.clear()
                                break

                        #: Index error likely due to serial data line formatting being different than expected.
                        #: This can often be caused by interference during serial data transmission.
                        except IndexError as e:
                            ERR_LOGGER.error(e)
                            break

                        #: Key error likely due to a formatting error in the last event line.
                        #: This can often be caused by interference during serial data transmission.
                        except KeyError as e:
                            ERR_LOGGER.error(e)
                            break
                        
                    #: Device is sleeping.
                    if line == '...':
                        current_status["state"] = 'Sleeping'
                        device_sleep = True
                        serial_data.clear()
                        break
            
            data_safe = True
            return

        #: Data buffer is unsafe to access.
        else:
            ERR_LOGGER.info('Serial data is not currently safe to access.')
            time.sleep(0.5)
            return


def wait_for_reboot():
    '''
    Waits until device has rebooted, then returns True.

    @return: True when device has rebooted.
    '''
    global data_safe

    data_safe = False
    t_start = time.time()
    while True:
        time.sleep(0.5)
        for line in serial_data:

            #: Waits for console message or 210 seconds.
            #: Once complete, clears 'main' and 'imei' from DEVICE_INFO, along with SERIAL_DATA.
            if ('devStateChange: curr=Boot' in line) or ((time.time() - t_start) > 210):
                time.sleep(30)
                ERR_LOGGER.info('Reboot complete.')
                current_status["event"] = 'Reboot Complete'
                device_info["main"] = ''
                device_info["imei"] = ''
                serial_data.clear()
                data_safe = True
                return True


def send_serial_command(command):
    '''
    Writes a serial command to the buffer.
    
    @param command: The command that will be written.

    @return: True if write was successful, False otherwise.
    '''
    #: Appends the selected line break onto the command.
    if line_break_tx[0]:
        nl_char = '\n'
    elif line_break_tx[1]:
        nl_char = '\r'
    else:
        nl_char = '\r\n'
    command_nl = command + nl_char
    
    if serial_safe:
        try:
            #: Flushes any pending bytes from output buffer.
            if serial_connection.out_waiting > 0:
                serial_connection.reset_output_buffer()
                ERR_LOGGER.debug('Serial output buffer flushed.')
            
            #: Writes command.
            ERR_LOGGER.info(f'Writing \'{command}\' to serial port.')
            serial_connection.write(command_nl.encode("utf-8"))
            time.sleep(0.05)
            return True
        
        except SerialException as e:
            ERR_LOGGER.error(e)
            return False
        
    else:
        return False


def clear_info():
    '''
    Clears the device_info dictionary.
    '''
    for key in device_info:
        device_info[key] = ''
    

def clear_settings():
    '''
    Clears the current_settings dictionary.
    '''
    for key in current_settings:
        current_settings[key] = ''
        

def set_line_break(rx, tx):
    '''
    Line break setter.
    
    @param rx: receive line break setting.
    
    @param tx: transmit line break setting.
    '''
    global line_break_rx, line_break_tx
    
    line_break_rx = rx
    line_break_tx = tx
    

def handle_exception(exc_type, exc_value, exc_traceback):
    '''
    Catches any unhandled exceptions.
    '''
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    ERR_LOGGER.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    sys.exit(1)

#: Exception handler.
sys.excepthook = handle_exception

   
class QueueFull(Exception):
    '''
    Exception that is raised when serial_data is full.
    Prints exception to Error Log for debugging purposes.
    '''
    def __init__(self, error_msg='The data queue is too large and must be cleared'):
        self.error_msg = error_msg
        
    def __str__(self):
        return f'QueueFull: {self.error_msg} ({len(serial_data)}).'