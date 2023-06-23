import ctypes

# Load the shared library
graphics = ctypes.CDLL('./graphics.so')

# Structure definition for the Window
class Window(ctypes.Structure):
    _fields_ = [("sdl_window", ctypes.c_void_p),
                ("context", ctypes.c_void_p),
                ("renderer", ctypes.c_void_p),
                ("width", ctypes.c_int),
                ("height", ctypes.c_int)]

# Function prototypes

# list:   ctypes.POINTER(ctypes.c_int)  ###  (ctypes.c_int * len(List)) * List
# string: ctypes.c_char_p               ###  String.encode("utf-8")

graphics.window.argtypes = [ctypes.c_char_p]
graphics.window.restype = Window

graphics.quit.argtypes = [Window]
graphics.quit.restype = None

graphics.update.argtypes = [Window]
graphics.update.restype = ctypes.c_int

#graphics.draw_rect.argtypes = [Window] + [ctypes.c_int] * 7
#graphics.draw_rect.restype = None

graphics.create_surface_and_texture.argtypes = [Window]
graphics.create_surface_and_texture.restype = None

graphics.draw_rect_to_surface.argtypes = [ctypes.c_int] * 7
graphics.draw_rect_to_surface.restype = None

graphics.blit_image_to_surface.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
graphics.blit_image_to_surface.restype = None



### SETUP DONE ###
### SETUP DONE ###
### SETUP DONE ###

# Create the window using the C code
window = graphics.window("Test".encode("utf-8"))
graphics.create_surface_and_texture(window)

# Use the window object
running = True
while running:
    # render
    #graphics.draw_rect(window, *(255, 0, 0), *(10, 10, 30, 30))
    graphics.blit_image_to_surface("tree.jpg".encode("utf-8"), 10, 10)
    running = graphics.update(window)

# Destroy the window
graphics.quit(window)
