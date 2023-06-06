import ctypes

# Load the shared library
example = ctypes.CDLL('./example.so')

# Define the function signature
example.multiply.restype = ctypes.c_int
example.multiply.argtypes = [ctypes.c_int, ctypes.c_int]

# Call the function
result = example.multiply(10, 20)

# Print the result
print("Python received result:", result)
