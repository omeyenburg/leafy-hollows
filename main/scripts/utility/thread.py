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
    if wait: # wait for normal fps
        time.sleep(2)
    if result is None:
        result = True
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
