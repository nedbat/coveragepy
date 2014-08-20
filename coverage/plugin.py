"""Plugin management for coverage.py"""

def load_plugins(modules, name):
    """Load plugins from `modules`, finding them by `name`.

    Yields the loaded plugins.

    """

    for module in modules:
        try:
            __import__(module)
            mod = sys.modules[module]
        except ImportError:
            blah()
            continue

        entry = getattr(mod, name, None)
        if entry:
            yield entry
