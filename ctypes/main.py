import ctypes
import timeit

# Load the shared library
example = ctypes.CDLL('./example.so')

# Define the function signature
example.loop.restype = ctypes.c_int
example.loop.argtypes = [ctypes.c_int, ctypes.c_int]

# Python function
def loop(x, y):
    result = 0
    for x in range(y):
        result += x
    return result

# Run functions
t1 = timeit.timeit("loop(10, 100)", globals=globals())
t2 = timeit.timeit("example.loop(10, 100)", globals=globals())

# Print time
print("Python:", t1)
print("C:", t2)
