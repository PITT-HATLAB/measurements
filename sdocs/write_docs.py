from os import walk
import os
from subprocess import check_output


def delete_rst(rst_path):
    
    for (dirpath, dirnames, filenames) in walk(rst_path):
        
        for filename in filenames:
            
            if (filename != 'conf.py'):
                
                os.remove(rst_path + filename)
    

def write_rst(filename,indexrst,rst_path,dirpath):
    
    if filename[-3:] == '.py':
        
        if filename != '__init__.py':
        
            filename = filename[:-3]
            
            
            f = open(rst_path + filename + '.rst', "w",encoding='utf8')
            f.write(filename)
            f.write(' \n' + '='*len(filename) + '\n\n.. automodule:: ')
            f.write(filename)
            f.write('''\n   :members:\n   :undoc-members:\n   :show-inheritance:''')
            indexrst.write('   ' + filename + '\n')

def write_rst_dir(dirname,indexrst,depth):

    if dirname != '__pycache__' and dirname != '.ipynb_checkpoints':   
        
        indexrst.write('\n')
        
        if (depth == 0):
            indexrst.write('#'*len(dirname) + '\n')
            
        if (depth == 1):
            indexrst.write('*'*len(dirname) + '\n')
        
        if (depth == 2):
            indexrst.write('='*len(dirname) + '\n')
            
        if (depth == 3):
            indexrst.write('-'*len(dirname) + '\n')
            
        if (depth >= 4):
            indexrst.write('^'*len(dirname) + '\n')

        indexrst.write(dirname + '\n')
        

        if (depth == 0):
            indexrst.write('#'*len(dirname) + '\n\n')
            
        if (depth == 1):
            indexrst.write('*'*len(dirname) + '\n\n')
        
        if (depth == 2):
            indexrst.write('='*len(dirname) + '\n\n')
            
        if (depth == 3):
            indexrst.write('-'*len(dirname) + '\n\n')
            
        if (depth >= 4):
            indexrst.write('^'*len(dirname) + '\n\n')
            
        indexrst.write('''.. toctree::
   :maxdepth: 5
   :caption: Contents:\n\n''')

def begin_indexrst(rst_path):
    
    indexrst = open(rst_path + 'index.rst', "w", encoding='utf8')
    
    indexrst.write(r'''.. Hatlab Measurements documentation master file, created by
   sphinx-quickstart on Mon Oct  4 09:56:25 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Welcome to Hatlab Measurements's documentation!
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. toctree::
   :maxdepth: 1''')
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
        
def recursive_walk(code_path,rst_path,indexrst,depth):
    

    for (dirpath, dirnames, filenames) in walk(code_path):
        

        for filename in filenames:
            
            if (dirpath[-1] == '/'):
                
                write_rst(filename,indexrst,rst_path,dirpath+' '+str(depth))
                
        if (len(dirnames) > 0):
            
            for dirname in dirnames:
                
                if (dirpath[-1] == '/'):
                
                    write_rst_dir(dirname,indexrst,depth)
                                    
                    recursive_walk(code_path+dirname+'/',rst_path,indexrst,depth+1)


if __name__ == '__main__':

    rst_path = r'C:/Users/datataker2/Documents/GitHub/measurements/sdocs/source/'
    code_path = r'C:/Users/datataker2/Documents/GitHub/measurements/measurement_modules/'
    sdocs_path = 'C:\\Users\\datataker2\\Documents\\GitHub\\measurements\\sdocs\\'
    
    files = []
    dirs = []

    delete_rst(rst_path)
    
    depth = 0
    
    indexrst = begin_indexrst(rst_path)
    try:
        recursive_walk(code_path,rst_path,indexrst,depth)
        finish_indexrst(indexrst)
    except:
        indexrst.close()
        
    check_output('dir ' + sdocs_path, shell=True)
    print('Writing .rst files...')
    print(check_output('make clean ' + sdocs_path, shell=True))
    print(check_output('make html ' + sdocs_path, shell=True))