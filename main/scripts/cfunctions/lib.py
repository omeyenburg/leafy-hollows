# -*- coding: utf-8 -*-
import subprocess
import platform
import ctypes
import glob
import sys
import os


library_prefix = "lib"

# Create platform-specific path
directory = os.path.dirname(os.path.realpath(__file__))
os_name = platform.system()
library_name = directory + "/" + library_prefix + "-" + os_name.lower()
if os_name == 'Windows':
    library_name += platform.architecture()[0]
library_paths = glob.glob(library_name + "*")

# Search for shared library or build it
if not library_paths:
    subprocess.check_call(['python', f'{directory}/setup.py', 'build_ext', '--inplace'], stdout=subprocess.DEVNULL)
library_path = glob.glob(library_name + "*")[0]

# Load the shared library
lib = ctypes.CDLL(library_path)

lib.c_print.argtypes = []
lib.c_print.restype = None


"""
# Function prototypes
graphics.c_init.argtypes = [ctypes.c_int, ctypes.c_int]
graphics.c_init.restype = ctypes.c_int

graphics.c_update.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
graphics.c_update.restype = ctypes.POINTER(ctypes.c_uint8)

graphics.c_quit.argtypes = []
graphics.c_quit.restype = None

graphics.c_info_max_tex_size = []
graphics.c_info_max_tex_size = ctypes.c_int

graphics.c_load_shader.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p), ctypes.c_int]
graphics.c_load_shader.restype = ctypes.c_int
graphics.load_shader = lambda vertex, fragment, **variables: graphics.c_load_shader(
    vertex.encode("utf-8"), fragment.encode("utf-8"),
    (ctypes.c_char_p * len(variables))(*map(lambda v: v.encode("utf-8"), variables.keys())),
    (ctypes.c_char_p * len(variables))(*map(lambda v: v.encode("utf-8"), variables.values())),
    len(variables))

graphics.c_update_shader_value.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
graphics.c_update_shader_value.restype = None
def p_update_shader_value(shader, index, value):
    if isinstance(value, int):
        c_value = ctypes.c_int(value)
    elif isinstance(value, float):
        c_value = ctypes.c_float(value)
    elif isinstance(value, (list, tuple)):
        if isinstance(value[0], int):
            c_value = (ctypes.c_int * len(value))(*value)
        elif isinstance(value[0], float):
            c_value = (ctypes.c_float * len(value))(*value)
    else:
        raise ValueError("Invalid value %r" % value)
    graphics.c_update_shader_value(shader, index, ctypes.byref(c_value))
graphics.update_shader_value = p_update_shader_value

graphics.activate_shader.argtypes = [ctypes.c_int]
graphics.activate_shader.restype = None

"""