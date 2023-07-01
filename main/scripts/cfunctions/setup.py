from setuptools import setup, Extension
import platform
import shutil
import os


library_prefix = "lib"


directory = os.path.dirname(os.path.realpath(__file__))

# Create platform specific file path
os_name = platform.system()
library_name = library_prefix + "-" + os_name.lower()
if os_name == 'Windows':
    library_name += platform.architecture()[0]

# Create extension from C file
module = Extension(
    name=library_name,
    sources=[directory + "/" + library_prefix + ".c"],
    extra_compile_args=["-std=c99"]
)

# Create shared object file or dynamic link library, depending on platform
setup(
    name=library_name,
    version='1.0',
    ext_modules=[module],
    script_args=['build', '--build-lib', directory]
)

# Delete temporary build folder
if os.path.exists(directory + '/build'):
    shutil.rmtree(directory + '/build')