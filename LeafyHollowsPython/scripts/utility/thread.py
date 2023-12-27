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
    except Exception:
        traceback.print_exc()
        error.set()
        result = None
    if wait: # wait for normal fps
        time.sleep(2)
    threads[func] = (result, True)


def threaded(func, *args, wait=False, **kwargs):
    if error.is_set():
        sys.exit()
    if func in threads:
        if not threads[func][1]:
            return None, False
        result = threads[func][0]
        del threads[func]
        return result, True
    threads[func] = (None, False)
    thread = Thread(target=_thread, daemon=True, args=(func, wait, *args), kwargs=kwargs)
    thread.start()
    return None, False
