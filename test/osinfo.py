"""OS information for testing."""

import sys

if sys.version_info >= (2, 5) and sys.platform == 'win32':
    # Windows implementation
    def process_ram():
        """How much RAM is this process using? (Windows)"""
        import ctypes
        # lifted from:
        # lists.ubuntu.com/archives/bazaar-commits/2009-February/011990.html
        class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
            """Used by GetProcessMemoryInfo"""
            _fields_ = [('cb', ctypes.c_ulong),
                        ('PageFaultCount', ctypes.c_ulong),
                        ('PeakWorkingSetSize', ctypes.c_size_t),
                        ('WorkingSetSize', ctypes.c_size_t),
                        ('QuotaPeakPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t),
                        ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                        ('PagefileUsage', ctypes.c_size_t),
                        ('PeakPagefileUsage', ctypes.c_size_t),
                        ('PrivateUsage', ctypes.c_size_t),
                       ]

        mem_struct = PROCESS_MEMORY_COUNTERS_EX()
        ret = ctypes.windll.psapi.GetProcessMemoryInfo(
                    ctypes.windll.kernel32.GetCurrentProcess(),
                    ctypes.byref(mem_struct),
                    ctypes.sizeof(mem_struct)
                    )
        if not ret:
            return 0
        return mem_struct.PrivateUsage

elif sys.platform == 'linux2':
    # Linux implementation
    import os

    _scale = {'kb': 1024, 'mb': 1024*1024}

    def _VmB(key):
        """Read the /proc/PID/status file to find memory use."""
        try:
            # get pseudo file /proc/<pid>/status
            t = open('/proc/%d/status' % os.getpid())
            v = t.read()
            t.close()
        except IOError:
            return 0    # non-Linux?
         # get VmKey line e.g. 'VmRSS:  9999  kB\n ...'
        i = v.index(key)
        v = v[i:].split(None, 3)
        if len(v) < 3:
            return 0    # invalid format?
         # convert Vm value to bytes
        return int(float(v[1]) * _scale[v[2].lower()])

    def process_ram():
        """How much RAM is this process using? (Linux implementation)"""
        return _VmB('VmRSS')


else:
    # Don't have an implementation, at least satisfy the interface.
    def process_ram():
        """How much RAM is this process using? (placebo implementation)"""
        return 0
