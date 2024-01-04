
_window = None


def main(api):
    global _window
    from .widget import PresetExecutor

    if _window is None:
        _window = PresetExecutor(api)
    
    _window.show()
