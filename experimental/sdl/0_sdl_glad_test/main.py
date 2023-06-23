import ctypes

# Load the shared library
graphics = ctypes.CDLL('./graphics.so')

# Structure definition for the Window
"""
class Window(ctypes.Structure):
    _fields_ = [("sdl_window", ctypes.c_void_p),
                ("context", ctypes.c_void_p),
                ("renderer", ctypes.c_void_p)]
"""

# Function prototypes

# list:   ctypes.POINTER(ctypes.c_int)  ###  (ctypes.c_int * len(List)) * List
# string: ctypes.c_char_p               ###  String.encode("utf-8")

graphics.create_window.argtypes = [ctypes.c_char_p]
graphics.create_window.restype = ctypes.c_int

graphics.quit.argtypes = []
graphics.quit.restype = None

graphics.update.argtypes = []
graphics.update.restype = ctypes.c_int

graphics.blit_image_to_surface.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
graphics.blit_image_to_surface.restype = None

graphics.draw_rect_to_surface.argtypes = [ctypes.c_int] * 7
graphics.draw_rect_to_surface.restype = None

graphics.create_surface_and_texture.argtypes = []
graphics.create_surface_and_texture.restype = None


### SETUP DONE ###
### SETUP DONE ###
### SETUP DONE ###

# Create the window using the C code
failed = graphics.create_window("Test".encode("utf-8"))
graphics.create_surface_and_texture()


# Use the window object
running = True
while running:
    # render
    graphics.draw_rect_to_surface(*(255, 0, 0), *(0, 0, 30, 30))
    graphics.blit_image_to_surface("tree.jpg".encode("utf-8"), 20, 20)
    running = graphics.update()

# Destroy the window
graphics.quit()
