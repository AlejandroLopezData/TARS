# brain/tracer.py
"""
Use the function emit to send messages to the tracer. The tracer will call all suscribed callbacks with the message and level.
"""
_listeners = []

def suscribe(callback):
    _listeners.append(callback)

def unsubscribe(callback):
    if callback in _listeners:
        _listeners.remove(callback)

def emit(mensaje: str, nivel: str = "info"):
    for callback in _listeners:
        try:
            callback(mensaje, nivel)
        except Exception:
            pass