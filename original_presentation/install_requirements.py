# -*- coding: utf-8 -*-
from pip._internal.cli.main import main
from scripts.utility.file import load


for package in load("requirements.txt", split=True):
    try:
        main(['install', package])
    except:
        print("Could not install", package)
