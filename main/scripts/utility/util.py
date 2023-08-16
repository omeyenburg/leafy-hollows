# -*- coding: utf-8 -*-
import platform
import json
import glob
import uuid
import sys
import os


# Global variables
realistic = False # only for testing purposes
system = platform.system()


def generate_id():
    return str(uuid.uuid4()) # 2^128 unique ids; low collision chance