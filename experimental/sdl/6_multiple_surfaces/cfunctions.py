import ctypes
import platform
import subprocess
import os

os_name = platform.system()
graphics_library_name = "graphics-" + os_name.lower()
if os_name == 'Windows':
    graphics_library_name += platform.architecture()[0] + ".dll"
else:
    graphics_library_name += ".so"


# The shared library file doesn't exist, run setup.py to build it
if not os.path.exists(graphics_library_name):
    subprocess.check_call(['python', 'setup.py', 'build_ext', '--inplace'], stdout=subprocess.DEVNULL)


# Load the shared library
graphics = ctypes.CDLL(graphics_library_name)

# Function prototypes
graphics.c_window.argtypes = [ctypes.c_char_p, ctypes.c_int]
graphics.c_window.restype = ctypes.c_int
graphics.window = lambda caption, fps_limit: graphics.c_window(caption.encode("utf-8"), fps_limit)

graphics.update.argtypes = []
graphics.update.restype = ctypes.c_int

graphics.c_load_image.argtypes = [ctypes.c_char_p]
graphics.c_load_image.restype = ctypes.c_int
graphics.load_image = lambda path: graphics.c_load_image(path.encode("utf-8"))

graphics.c_blit.argtypes = [ctypes.c_int] * 4
graphics.c_blit.restype = None
graphics.blit = lambda target, image, coords: graphics.c_blit(target, image, *coords)

graphics.c_rect.argtypes = [ctypes.c_int] * 8
graphics.c_rect.restype = None
graphics.rect = lambda target, color, coords: graphics.c_rect(target, *color, *coords)

graphics.c_circle.argtypes = [ctypes.c_int] * 8
graphics.c_circle.restype = None
graphics.circle = lambda target, color, coord, radius, width=0: graphics.c_circle(target, *color, *coord, radius, width)

graphics.c_pixel.argtypes = [ctypes.c_int] * 6
graphics.c_pixel.restype = None
graphics.pixel = lambda target, color, coord: graphics.c_pixel(target, *color, *coord)

graphics.c_load_font.argtypes = [ctypes.c_char_p, ctypes.c_int]
graphics.c_load_font.restype = ctypes.c_int
graphics.load_font = lambda path, size: graphics.c_load_font(path.encode("utf-8"), size)

graphics.c_write.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p] + [ctypes.c_int] * 5
graphics.c_write.restype = ctypes.c_int
graphics.write = lambda target, font, text, color, coord: graphics.c_write(target, font, text.encode("utf-8"), *color, *coord)

graphics.c_load_shader.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_char_p), ctypes.POINTER(ctypes.c_char_p), ctypes.c_int]
graphics.c_load_shader.restype = ctypes.c_int
graphics.load_shader = lambda vertexPath, fragmentPath, **variables: graphics.c_load_shader(
    vertexPath.encode("utf-8"), fragmentPath.encode("utf-8"),
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

graphics.c_get_mousepos.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
graphics.c_get_mousepos.restype = None
def p_get_mousepos():
    x, y = ctypes.c_int(), ctypes.c_int()
    graphics.c_get_mousepos(ctypes.byref(x), ctypes.byref(y))
    return x, y
graphics.get_mousepos = p_get_mousepos

graphics.get_fps.argtypes = []
graphics.get_fps.restype = ctypes.c_float