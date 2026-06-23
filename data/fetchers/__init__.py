import threading

# py_mini_racer (V8 engine used by some AKShare functions) is not thread-safe.
# All AKShare calls must acquire this lock to prevent concurrent access crashes.
_AK_LOCK = threading.Lock()
