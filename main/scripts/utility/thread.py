# -*- coding: utf-8 -*-
from threading import Thread, Event
import traceback
import time
import sys


threads = {}
error = Event()


def _thread(func, wait, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
    except:
        traceback.print_exc()
        error.set()
    if wait: # wait for normal fps
        time.sleep(2)
    threads[func] = result


def threaded(func, *args, wait=False, **kwargs):
    if error.is_set():
        sys.exit()
    if func in threads:
        if threads[func] is None:
            return
        result = threads[func]
        del threads[func]
        return result
    threads[func] = None
    thread = Thread(target=_thread, daemon=True, args=(func, wait, *args), kwargs=kwargs)
    thread.start()
    


def generate_world_thread(block_data, result):
    instance = world.World(block_data)
    time.sleep(2) # wait for normal fps
    result[0] = instance

def generate_world(window):
    result = [None]
    thread = Thread(target=Game.generate_world_thread, daemon=True, args=(window.block_data, result))
    thread.result = result
    thread.start()
    return thread

def get_world(thread: Thread):
    return thread.result[0]