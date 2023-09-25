# -*- coding: utf-8 -*-
from pip._internal.cli.main import main
from scripts.utility.file import read

for package in read("requirements.txt", split=True):
    try:
        main(['install', package])
    except:
        print("Could not install", package)
