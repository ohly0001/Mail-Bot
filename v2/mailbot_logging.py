import atexit
import os
from datetime import datetime
import traceback
from dateutil.tz import tzlocal
import threading

class Logger:
    rows = []
    _lock = threading.Lock()
    _base_path = os.path.join(os.path.dirname(__file__), "logs")

    def __init__(self, attached):
        self.classname = attached.__class__.__name__

    def _add(self, level, message, err=None):
        ts = datetime.now(tzlocal()).strftime("%x %X")
        if err is not None:
            # Include full stack trace if err is an exception
            stack = ''.join(traceback.format_exception(type(err), err, err.__traceback__))
            message = f"{message} - {stack}"
        with Logger._lock:
            Logger.rows.append(f"{ts} - {self.classname} - {level} - {message}\n")

    def info(self, msg):
        self._add("INFO", msg)

    def warn(self, msg):
        self._add("WARN", msg)

    def error(self, msg, err=None):
        self._add("ERR", msg, err)

    @classmethod
    def flush(cls):
        if not cls.rows:
            return
        dt = datetime.now(tzlocal())
        log_path = os.path.join(cls._base_path, dt.strftime("%Y"), dt.strftime("%b"))
        os.makedirs(log_path, exist_ok=True)
        filename = dt.strftime("%Y%m%d.log")
        path = os.path.join(log_path, filename)
        with cls._lock:
            with open(path, "a+", encoding="utf-8") as f:
                f.writelines(cls.rows)
            cls.rows.clear()