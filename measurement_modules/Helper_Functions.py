# -*- coding: utf-8 -*-
"""
Created on Thu Nov 12 10:56:06 2020

@author: Ryan Kaufman

purpose: Contain general helper functions that are useful for all instruments
"""
from hat_utilities import Controller_Module as CM
import numpy as np
import os 

def adjust(Param1, stepsize1): 
    in_string = ""
    while in_string.lower() != "q" :
        #have to use "q" to stop, can use left and right brackets to adjust stepsize up/down
        in_string = input(f"{Param1.name}: a for down, d for up (stepsize: {stepsize1})\nEnter to submit, q to quit")
        if in_string == "a": 
            Param1(Param1()-stepsize1)
            print(f"{Param1.name}: {Param1()}")
        if in_string == "d": 
            Param1(Param1()+stepsize1)
            print(f"{Param1.name}: {Param1()}")
        if in_string == "q": 
            break

def adjust_2(Params, stepsizes): 
    [Param1, Param2] = Params
    [stepsize1, stepsize2] = stepsizes
    in_string = ''
    while in_string.lower() != "q" :
        #have to use "q" to stop, can use left and right brackets to adjust stepsize up/down
        in_string = input(f"{Param1.name}: a for down, d for up\n{Param2.name}: [ for down, ] for up \nEnter to submit, q to quit\n")
        if in_string == "a": 
            Param1(Param1()-stepsize1)
            print(f"{Param1.name}: {Param1()}")
        if in_string == "d": 
            Param1(Param1()+stepsize1)
            print(f"{Param1.name}: {Param1()}")
        if in_string == "[": 
            Param2(Param2()-stepsize2)
            print(f"{Param2.name}: {Param2()}")
        if in_string == "]": 
            Param2(Param2()+stepsize2)
            print(f"{Param2.name}: {Param2()}")
        if in_string == "q": 
            break
        
def controller_adjust(Params, stepsizes):
    CM.sample_first_joystick(Params, stepsizes)
    
def shift_array_relative_to_middle(array, div_factor = 1e6):
    return (array-array[int(len(array)/2)])/div_factor

def get_name_from_path(path: str):
    
    return path.split('\\')[-1]

def log_normalize_to_row(x, y, arr, y_norm_val = None): 
    
    '''
    Takes in the inputs to a pcolor plot and normalizes each jth column in the 2d array to (i,j) value
    '''
    def normalize(arr, i):
        norm_row = arr[i]
        normed_arr = []
        for i, row in enumerate(arr):
            if i == 0: print(row)
            # print(f'{i}th row: {row}')
            normed_arr.append(row-norm_row)
        # print(normed_arr)
        return np.array(normed_arr)
    
    if y_norm_val == None: 
        return normalize(arr,0)
    else: 
        array_norm_row_index = np.where(np.isclose(y, y_norm_val, atol = 0.05))[0][0]
        return normalize(arr, array_norm_row_index)
def log_normalize_up_to_row(x, y, arr, y_norm_val = None): 
    
    '''
    Takes in the inputs to a pcolor plot and normalizes each jth column in the 2d array to (i,j) value
    '''
    def normalize(arr, norm_row):
        normed_arr = []
        for i, row in enumerate(arr):
            if i == 0: print(row)
            # print(f'{i}th row: {row}')
            normed_arr.append(row-norm_row)
        # print(normed_arr)
        return np.array(normed_arr)
    
    if y_norm_val == None: 
        return normalize(arr,0)
    else: 
        array_norm_row_index = np.where(np.isclose(y, y_norm_val, atol = 0.05))[0][0]
        norm_block = arr[0:array_norm_row_index]
        norm_arr = np.average(norm_block, axis = 0)
        return normalize(arr, norm_arr)
    
def select_closest_to_target(x_arr, arr, arr_target_val): 
    best_idx = np.argmin(np.abs(arr_target_val-np.array(arr)))
    return x_arr[best_idx]

def find_all_ddh5(cwd): 
    dirs = os.listdir(cwd)
    filepaths = []
    for path in dirs: 
        try:
            subs = os.listdir(cwd+'\\'+path)
            for sub in subs: 
                print(sub)
                if sub.split('.')[-1] == 'ddh5':  
                    filepaths.append(cwd+'\\'+path+'\\'+sub)
                else: 
                    for subsub in os.listdir(cwd+'\\'+path+'\\'+sub): 
                        if subsub.split('.')[-1] == 'ddh5':  
                            filepaths.append(cwd+'\\'+path+'\\'+sub+'\\'+subsub)
        except: #usually because the files are one directory higher than you'd expect
            if path.split('.')[-1] == 'ddh5':  
                    filepaths.append(cwd+'\\'+path)
    return filepaths
    
def load_instrument(inst_class, *args, **kwargs):
    try: 
        inst = inst_class(*args, **kwargs)
        return inst
    except AttributeError:
        pass    
    
    