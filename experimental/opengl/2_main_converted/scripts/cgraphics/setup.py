from setuptools import setup, Extension
import platform
import shutil
import os

directory = os.path.dirname(os.path.realpath(__file__))

# Create platform specific file path
os_name = platform.system()
graphics_library_name = "graphics-" + os_name.lower()
if os_name == 'Windows':
    graphics_library_name += platform.architecture()[0]

# Create extension from C file
graphics_module = Extension(
    graphics_library_name,
    sources=[directory + "/graphics.c", directory + "/glad/src/glad.c"],
    include_dirs=[directory + "/glad/include"],
)

# Create shared object file or dynamic link library, depending on platform
setup(
    name=graphics_library_name,
    version='1.0',
    description='graphics',
    ext_modules=[graphics_module],
    script_args=['build', '--build-lib', directory],
)

# Delete temporary build folder
shutil.rmtree('build')