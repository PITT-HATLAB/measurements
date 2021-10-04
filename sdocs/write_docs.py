from os import walk
import os

rst_path = r'C:/Users/datataker2/Documents/GitHub/measurements/sdocs/source/'
code_path = r'C:/Users/datataker2/Documents/GitHub/measurements/measurement_modules/'
        
files = []
dirs = []


def write_rst(filename,indexrst):
    
    if filename[-3:] == '.py':
        
        if filename != '__init__.py':
        
            filename = filename[:-3]
        
            rst_path = r'C:/Users/datataker2/Documents/GitHub/measurements/sdocs/source/'
            code_path = r'C:/Users/datataker2/Documents/GitHub/measurements/measurement_modules/'
            print(filename)
            
            f = open(rst_path + filename + '.rst', "w",encoding='utf8')
            f.write(filename)
            f.write(''' module\n==========================================\n\n.. automodule:: ''')
            f.write(filename)
            f.write('''\n   :members:\n   :undoc-members:\n   :show-inheritance:''')
            indexrst.write('   ' + filename + '\n')

def begin_indexrst():
    
    indexrst = open(rst_path + 'index.rst', "w", encoding='utf8')
    
    indexrst.write(r'''.. Hatlab Measurements documentation master file, created by
   sphinx-quickstart on Mon Oct  4 09:56:25 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Hatlab Measurements's documentation!
===============================================

.. toctree::
   :maxdepth: 5
   :caption: Contents:''')
    indexrst.write('\n')
    indexrst.write('\n')
    return indexrst
    
def finish_indexrst(indexrst):
    
    indexrst.write('''
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
    ''')
    
    indexrst.close()
        
def recursive_walk(path):
    
    indexrst = begin_indexrst()
    
    for (dirpath, dirnames, filenames) in walk(path):
        
        for filename in filenames:
            
            write_rst(filename,indexrst)
        
        if (len(dirpath) > 0):
            
            for dirname in dirnames:
                
                recursive_walk(path+r'dirname/')
                
    finish_indexrst(indexrst)

recursive_walk(code_path)