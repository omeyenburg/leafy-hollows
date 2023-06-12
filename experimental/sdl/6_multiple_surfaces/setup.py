from setuptools import setup, Extension
import platform
import shutil


# Create platform specific file path
os_name = platform.system()
graphics_library_name = "graphics-" + os_name.lower()
if os_name == 'Windows':
    graphics_library_name += platform.architecture()[0]


# Create extension from C file
graphics_module = Extension(
    graphics_library_name,
    sources=['graphics.c', 'glad/src/glad.c'],
    include_dirs=['glad/include'],
    libraries=['SDL2', 'SDL2_image', 'SDL2_ttf'],
    extra_compile_args=['-Wno-error']
)


# Create shared object file or dynamic link library, depending on platform
setup(
    name=graphics_library_name,
    version='1.0',
    description='graphics',
    ext_modules=[graphics_module],
)

# Delete temporary build folder
shutil.rmtree('build')
