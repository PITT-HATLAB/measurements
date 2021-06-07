# -*- coding: utf-8 -*-
"""
Created on Sun Jan  3 12:47:58 2021

@author: Ryan Kaufman

Purpose: Perform logging of fridge state in a ddh5 dict that Plottr can refresh in real time, 
maintainable on the shared drive on a per-cooldown basis via a raspberry pi

Outline: 
    - raspberry pi runs this script on Crontab forever, depositing one ddh5 per log file in a folder named 
    ####### on the shared drive
    - from that shared drive, another script named ##### allows any PC with 
    Plottr and access to the shared drive to plot present and past fridge data
    - Plottr then facilitates the graphing tools, choice of axes, etc.
    
TODO: 
    - establish default settings for Plottr (plots, subplots, tables?)
"""
######################## Imports 
import os
import time
import numpy as np
import struct
from datetime import datetime
from plottr.data import datadict_storage as dds, datadict as dd
from plottr.apps.autoplot import main
#%%
import smtplib

    
import imaplib
import email
from email.header import decode_header
import webbrowser
import os
#email inbox reader from https://mail.google.com/mail/u/0/?tab=om#inbox/FMfcgxwLtsxhWNZfXhZbCDxBDTKkDDvd
# account credentials
username = "hatlabtest123@gmail.com"
password = "TXFridgeMonitor"

def clean(text):
    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)


def read_latest_message_and_delete(username, password):
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    # authenticate
    imap.login(username, password)
    
    status, messages = imap.select("INBOX")
    # number of top emails to fetch
    N = 1
    # total number of emails
    
    messages = int(messages[0])
    for i in range(messages, messages-N, -1):
        # fetch the email message by ID
        res, msg = imap.fetch(str(i), "(RFC822)")
        for response in msg:
            if isinstance(response, tuple):
                # pass
                # parse a bytes email into a message object
                msg = email.message_from_bytes(response[1])
                # decode the email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    # if it's a bytes, decode to str
                    subject = subject.decode(encoding)
                # decode email sender
                From, encoding = decode_header(msg.get("From"))[0]
                if isinstance(From, bytes):
                    From = From.decode(encoding)
                print("Subject:", subject)
                print("From:", From)
                # if the email message is multipart
                if msg.is_multipart():
                    pass
                else:
                    # extract content type of email
                    content_type = msg.get_content_type()
                    # get the email body
                    body = msg.get_payload(decode=True).decode()
                    if content_type == "text/plain":
                        # print only text email parts
                        print("="*100)
                        # close the connection and logout
                        imap.close()
                        imap.logout()
                        return From, body.split('\\\n')
    status, messages = imap.search(None, "ALL")
    for mail in messages:
        _, msg = imap.fetch(mail, "(RFC822)")
        # you can delete the for loop for performance if you have a long list of emails
        # because it is only for printing the SUBJECT of target email to delete
        for response in msg:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])
                # decode the email subject
                subject = decode_header(msg["Subject"])[0][0]
                if isinstance(subject, bytes):
                    # if it's a bytes type, decode to str
                    subject = subject.decode()
                print("Deleting", subject)
        # mark the mail as deleted.
        
        imap.store(mail, "+FLAGS", "\\Deleted")
        
# ret = read_latest_message_and_delete(username, password)
#%%
###################### Required Manual Information
#TX Fridge indexes, depends on sensor order in OI system
Indexes = {
    'Base Timestamp (s)': 2,
    'P2 Condensing pressure (Bar)': 3,
    'P1 Tank pressure (Bar)': 4,
    'P5 Forepump backpressure (Bar)': 5,
    'P3 Still Pressure (mBar)': 6,
    'P4 Turbo Backpressure (mBar)': 7,
    'OVC Pressure (mBar)': 8,
    'Water In (C)': 9,
    'Water Out (C)': 10,
    'Helium Temperature (C)':11,
    'Oil Temp (C)': 12,
    'Motor Current (A)': 13,
    'Low Pressure (bar)': 14, 
    'High Pressure (bar)': 15,
    'PT2 Head Timestamp (date)': 16,
    'PT2 Head Temp (K)': 17,
    'PT2 Head Probe Resistance (Ohm)': 18,
    'PT2 Plate Timestamp (date)':19, 
    'PT2 Plate Temp (K)': 20,
    'PT2 Plate Resistance (Ohm)': 21,
    'Still Plate Timestamp (date)': 22,
    'Still Plate Temp (K)': 23,
    'Still Plate Resistance (Ohm)': 24,
    'T100mK Plate Timestamp (date)': 25,
    'T100mK Plate Temp (K)': 26,
    'T100mK Plate Resistance (Ohm)': 27,
    'MC Cernox Timestamp (date)': 28,
    'MC Cernox Temp (K)': 29,
    'MC Cernox Resistance (Ohm)': 30, 
    'PT1 Head Timestamp (date)': 31, 
    'PT1 Head Temp (K)': 32, 
    'PT1 Head Resistance (Ohm)': 33,
    'PT1 Plate Timestamp (date)': 34,
    'PT1 Plate Temp (K)': 35,
    'PT1 Plate Resistance (Ohm)': 36,
    'MC RuOx Timestamp (date)': 37,
    'MC RuOx Temp (K)': 38, 
    'MC RuOx Resistance (Ohm)': 39,
    #in between here are empty channels for 40-54, each one formatted as a temp sensor.
    'Still Heater Power (W)': 55,
    'Chamber Heater Power (W)': 56, 
    'IVC Sorb Heater (W)': 57, 
    'Turbo Current (A)': 58, 
    'Turbo Power (W)': 59, 
    'Turbo Speed (Hz)': 60,
    'Turbo Motor (C)': 61, 
    'Turbo Bottom (C)': 62,
    }
FridgeData = dd.DataDict(
    #fridge info as a function of time
    ext_time = dict(unit = 'date'),
    Base_Timestamp = dict(axes = ['ext_time'],unit = 'date'),
    P2_Condensing_pressure = dict(axes = ['ext_time'],unit = 'Bar'),
    P1_Tank_pressure = dict(axes = ['ext_time'],unit = 'Bar'),
    P5_Forepump_backpressure = dict(axes = ['ext_time'],unit = 'Bar'),
    P3_Still_Pressure = dict(axes = ['ext_time'],unit = 'mBar'),
    P4_Turbo_Backpressure = dict(axes = ['ext_time'],unit = 'mBar'),
    OVC_Pressure = dict(axes = ['ext_time'],unit = 'mBar'),
    Water_In = dict(axes = ['ext_time'],unit = 'C'),
    Water_Out = dict(axes = ['ext_time'],unit = 'C'),
    Helium_Temperature = dict(axes = ['ext_time'],unit = 'C'),
    Oil_Temp = dict(axes = ['ext_time'],unit = 'C'),
    Motor_Current = dict(axes = ['ext_time'],unit = 'A'),
    Low_Pressure = dict(axes = ['ext_time'],unit = 'bar'),
    High_Pressure = dict(axes = ['ext_time'],unit = 'bar'),
    PT2_Head_Timestamp = dict(axes = ['ext_time'],unit = 'date'),
    PT2_Head_Temp = dict(axes = ['ext_time'],unit = 'K'),
    PT2_Head_Probe_Resistance = dict(axes = ['ext_time'],unit = 'Ohm'),
    PT2_Plate_Timestamp = dict(axes = ['ext_time'],unit = 'date'),
    PT2_Plate_Temp = dict(axes = ['ext_time'],unit = 'K'),
    PT2_Plate_Resistance = dict(axes = ['ext_time'],unit = 'Ohm'),
    Still_Plate_Timestamp = dict(axes = ['ext_time'],unit = 'date'),
    Still_Plate_Temp = dict(axes = ['ext_time'],unit = 'K'),
    Still_Plate_Resistance = dict(axes = ['ext_time'],unit = 'Ohm'),
    T100mK_Plate_Timestamp = dict(axes = ['ext_time'],unit = 'date'),
    T100mK_Plate_Temp = dict(axes = ['ext_time'],unit = 'K'),
    T100mK_Plate_Resistance = dict(axes = ['ext_time'],unit = 'Ohm'),
    MC_Cernox_Timestamp = dict(axes = ['ext_time'],unit = 'date'),
    MC_Cernox_Temp = dict(axes = ['ext_time'],unit = 'K'),
    MC_Cernox_Resistance = dict(axes = ['ext_time'],unit = 'Ohm'),
    PT1_Head_Timestamp = dict(axes = ['ext_time'],unit = 'date'),
    PT1_Head_Temp = dict(axes = ['ext_time'],unit = 'K'),
    PT1_Head_Resistance = dict(axes = ['ext_time'],unit = 'Ohm'),
    PT1_Plate_Timestamp = dict(axes = ['ext_time'],unit = 'date'),
    PT1_Plate_Temp = dict(axes = ['ext_time'],unit = 'K'),
    PT1_Plate_Resistance = dict(axes = ['ext_time'],unit = 'Ohm'),
    MC_RuOx_Timestamp = dict(axes = ['ext_time'],unit = 'date'),
    MC_RuOx_Temp = dict(axes = ['ext_time'],unit = 'K'),
    MC_RuOx_Resistance = dict(axes = ['ext_time'],unit = 'Ohm'),
    Still_Heater_Power = dict(axes = ['ext_time'],unit = 'W'),
    Chamber_Heater_Power = dict(axes = ['ext_time'],unit = 'W'),
    IVC_Sorb_Heater = dict(axes = ['ext_time'],unit = 'W'),
    Turbo_Current = dict(axes = ['ext_time'],unit = 'A'),
    Turbo_Power = dict(axes = ['ext_time'],unit = 'W'),
    Turbo_Speed = dict(axes = ['ext_time'],unit = 'Hz'),
    Turbo_Motor = dict(axes = ['ext_time'],unit = 'C'),
    Turbo_Bottom = dict(axes = ['ext_time'],unit = 'C')
    )

######################## Auxiliary Functions
def bin_to_float(b):
    """ Convert binary string to a float. """
    bf = int_to_bytes(int(b, 2), 8)  # 8 bytes needed for IEEE 754 binary64.
    return struct.unpack('>d', bf)[0]

def int_to_bytes(n, minlen=0):  # Helper function
    nbits = n.bit_length() + (1 if n < 0 else 0)  # +1 for any sign bit.
    nbytes = (nbits+7) // 8  # Number of whole bytes.
    b = bytearray()
    for _ in range(nbytes):
        b.append(n & 0xff)
        n >>= 8
    if minlen and len(b) < minlen: 
        b.extend([0] * (minlen-len(b)))
    return bytearray(reversed(b))  # High bytes first.

def read_log(filename):
    """
    Return the lastest value of log file
    """
    file_ = open(filename, "rb")
    read = file_.read()
    data = read[12288:]
    data_list = np.zeros(63)
    for j in range(63):
        double_float = ""
        for i in range(8):
            digit = 7-i
            temp = np.binary_repr(data[-504:][8*j + digit], 8)
            double_float+=temp
        data_list[j] = bin_to_float(double_float)
    return data_list

######################## Main Class

class Fridge_Logger(): 
    '''
    Purpose: Take vcf log file, log in format of a measurement to a ddh5 file stored in a specific directory
    '''
    def __init__(self, vcf_folderpath, ddh5_filepath, sensor_datadict, log_dict):
        self.vcf_folder = vcf_folderpath
        self.log_key = log_dict
        self.datadir = ddh5_filepath
        self.fridge_data = sensor_datadict
        self.fridge_data.validate()
        print('creating ddh5 file at '+self.datadir)
        self.fridge_writer = dds.DDH5Writer(self.datadir, self.fridge_data, name="Log_Test")
        self.fridge_writer.__enter__()

        print('file created')
        
        self.carriers = {
    	'att':    '@mms.att.net',
    	'tmobile':' @tmomail.net',
    	'verizon':  '@vtext.com',
    	'sprint':   '@page.nextel.com'
        }

    def AlertRyan(self, message):
            # Replace the number with your own, or consider using an argument\dict for multiple people.
    	to_number = '7247662540{}'.format(self.carriers['verizon'])
    	auth = ('hatlabtest123@gmail.com', 'TXFridgeMonitor')
    
    	# Establish a secure session with gmail's outgoing SMTP server using your gmail account
    	server = smtplib.SMTP( "smtp.gmail.com", 587 )
    	server.starttls()
    	server.login(auth[0], auth[1])
    
    	# Send text message through SMS gateway of destination number
    	server.sendmail(auth[0], to_number, message)
     
        #read the inbox for commands
        
    def get_new_logdata(self, filedir): 
        """
        Measurement action: takes in a file directory, gets all the vcf files, 
        then loads only the most recent one into the active ddh5 file via 
        the writer defined in __init__.

        Returns
        -------
        None.
        """
        #get an ordered dictionary of all the log file names with the values being the raw timestamps
        filedict = {}
        for filename in os.listdir(filedir): 
            filedict[filename] = os.path.getmtime(filedir+'\\'+filename)
        (last_modified_logfile, modified_timestamp) =  sorted(filedict.items(), key = lambda item: item[1])[-1]
        self.logfile_modified_date = datetime.fromtimestamp(modified_timestamp)
        return read_log(filedir+'\\'+last_modified_logfile)
        
        
    def save_log_data(self, raw_log_array): 
        self.fridge_writer.add_data(
            ext_time = datetime.now().timestamp(),
            Base_Timestamp = raw_log_array[self.log_key['Base Timestamp (s)']],
            P2_Condensing_pressure = raw_log_array[self.log_key['P2 Condensing pressure (Bar)']],
            P1_Tank_pressure = raw_log_array[self.log_key['P1 Tank pressure (Bar)']],
            P5_Forepump_backpressure = raw_log_array[self.log_key['P5 Forepump backpressure (Bar)']],
            P3_Still_Pressure = raw_log_array[self.log_key['P3 Still Pressure (mBar)']],
            P4_Turbo_Backpressure = raw_log_array[self.log_key['P4 Turbo Backpressure (mBar)']],
            OVC_Pressure = raw_log_array[self.log_key['OVC Pressure (mBar)']],
            Water_In = raw_log_array[self.log_key['Water In (C)']],
            Water_Out = raw_log_array[self.log_key['Water Out (C)']],
            Helium_Temperature = raw_log_array[self.log_key['Helium Temperature (C)']],
            Oil_Temp = raw_log_array[self.log_key['Oil Temp (C)']],
            Motor_Current = raw_log_array[self.log_key['Motor Current (A)']],
            Low_Pressure = raw_log_array[self.log_key['Low Pressure (bar)']],
            High_Pressure = raw_log_array[self.log_key['High Pressure (bar)']],
            PT2_Head_Timestamp = raw_log_array[self.log_key['PT2 Head Timestamp (date)']],
            PT2_Head_Temp = raw_log_array[self.log_key['PT2 Head Temp (K)']],
            PT2_Head_Probe_Resistance = raw_log_array[self.log_key['PT2 Head Probe Resistance (Ohm)']],
            PT2_Plate_Timestamp = raw_log_array[self.log_key['PT2 Plate Timestamp (date)']],
            PT2_Plate_Temp = raw_log_array[self.log_key['PT2 Plate Temp (K)']],
            PT2_Plate_Resistance = raw_log_array[self.log_key['PT2 Plate Resistance (Ohm)']],
            Still_Plate_Timestamp = raw_log_array[self.log_key['Still Plate Timestamp (date)']],
            Still_Plate_Temp = raw_log_array[self.log_key['Still Plate Temp (K)']],
            Still_Plate_Resistance = raw_log_array[self.log_key['Still Plate Resistance (Ohm)']],
            T100mK_Plate_Timestamp = raw_log_array[self.log_key['T100mK Plate Timestamp (date)']],
            T100mK_Plate_Temp = raw_log_array[self.log_key['T100mK Plate Temp (K)']],
            T100mK_Plate_Resistance = raw_log_array[self.log_key['T100mK Plate Resistance (Ohm)']],
            MC_Cernox_Timestamp = raw_log_array[self.log_key['MC Cernox Timestamp (date)']],
            MC_Cernox_Temp = raw_log_array[self.log_key['MC Cernox Temp (K)']],
            MC_Cernox_Resistance = raw_log_array[self.log_key['MC Cernox Resistance (Ohm)']],
            PT1_Head_Timestamp = raw_log_array[self.log_key['PT1 Head Timestamp (date)']],
            PT1_Head_Temp = raw_log_array[self.log_key['PT1 Head Temp (K)']],
            PT1_Head_Resistance = raw_log_array[self.log_key['PT1 Head Resistance (Ohm)']],
            PT1_Plate_Timestamp = raw_log_array[self.log_key['PT1 Plate Timestamp (date)']],
            PT1_Plate_Temp = raw_log_array[self.log_key['PT1 Plate Temp (K)']],
            PT1_Plate_Resistance = raw_log_array[self.log_key['PT1 Plate Resistance (Ohm)']],
            MC_RuOx_Timestamp = raw_log_array[self.log_key['MC RuOx Timestamp (date)']],
            MC_RuOx_Temp = raw_log_array[self.log_key['MC RuOx Temp (K)']],
            MC_RuOx_Resistance = raw_log_array[self.log_key['MC RuOx Resistance (Ohm)']],
            Still_Heater_Power = raw_log_array[self.log_key['Still Heater Power (W)']],
            Chamber_Heater_Power = raw_log_array[self.log_key['Chamber Heater Power (W)']],
            IVC_Sorb_Heater = raw_log_array[self.log_key['IVC Sorb Heater (W)']],
            Turbo_Current = raw_log_array[self.log_key['Turbo Current (A)']],
            Turbo_Power = raw_log_array[self.log_key['Turbo Power (W)']],
            Turbo_Speed = raw_log_array[self.log_key['Turbo Speed (Hz)']],
            Turbo_Motor = raw_log_array[self.log_key['Turbo Motor (C)']],
            Turbo_Bottom = raw_log_array[self.log_key['Turbo Bottom (C)']]
            )
    def make_new_ddh5(self, current_time, start_time):
        timediff = current_time-start_time
        if timediff > 43200: #12 hours
            self.fridge_writer = dds.DDH5Writer(self.datadir, self.fridge_data, name="Log_Test")
            self.fridge_writer.__enter__()
            return current_time
        else: 
            return start_time
            
    def monitor(self): 
        '''
        Performs the logging using the above supporting functions

        Returns
        -------
        None.

        '''
        start_time = time.time()
        logging = True
        print("Logging Fridge Data, use CTRL+C to interrupt")
        lastalerted = 0
        while logging: 
            current_time = time.time()
            start_time = self.make_new_ddh5(current_time, start_time)
            time.sleep(10)
            new_data = self.get_new_logdata(self.vcf_folder)
            self.save_log_data(new_data)
            latest_temp = new_data[self.log_key['MC RuOx Temp (K)']]
            msg = f"Latest Info: {str(datetime.now())}\nMC RuOx Temp: {new_data[self.log_key['MC RuOx Temp (K)']]}\nMC Cernox Temp (K): {new_data[self.log_key['MC Cernox Temp (K)']]}"
            print(msg)
            if latest_temp > 50e-3:
                if time.time() - lastalerted > 600:
                    self.AlertRyan(msg)
                    lastalerted = time.time()
    
    def duplicate_log(self): 
        pass
            
FL = Fridge_Logger(r"\\OI-PC\Hatridge", r"C:\Users\Hatlab_3\Documents\DDH5_Logs", FridgeData, Indexes)
FL.monitor()

#rtest



