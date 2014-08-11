"""Extension management for coverage.py"""

def load_extensions(modules, name):
    """Load extensions from `modules`, finding them by `name`.

    Yields the loaded extensions.

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
