import ctypes

# Load the shared library
graphics = ctypes.CDLL('./graphics.so')

# Function prototypes

# list:   ctypes.POINTER(ctypes.c_int)  ###  (ctypes.c_int * len(List)) * List
# string: ctypes.c_char_p               ###  String.encode("utf-8")


graphics.c_window.argtypes = [ctypes.c_char_p, ctypes.c_int]
graphics.c_window.restype = ctypes.c_int
graphics.window = lambda caption, fps_limit: graphics.c_window(caption.encode("utf-8"), fps_limit)

graphics.quit.argtypes = []
graphics.quit.restype = None

graphics.update.argtypes = []
graphics.update.restype = ctypes.c_int

graphics.c_load_image.argtypes = [ctypes.c_char_p]
graphics.c_load_image.restype = ctypes.c_int
graphics.load_image = lambda path: graphics.c_load_image(path.encode("utf-8"))

graphics.c_blit.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
graphics.c_blit.restype = None
graphics.blit = lambda image, coords: graphics.c_blit(image, *coords)


graphics.c_rect.argtypes = [ctypes.c_int] * 7
graphics.c_rect.restype = None
graphics.rect = lambda color, coords: graphics.c_rect(*color, *coords)

graphics.c_get_mousepos.argtypes = (ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
graphics.c_get_mousepos.restype = None
def py_get_mousepos():
    x, y = ctypes.c_int(), ctypes.c_int()
    graphics.c_get_mousepos(ctypes.byref(x), ctypes.byref(y))
    return x, y
graphics.get_mousepos = py_get_mousepos