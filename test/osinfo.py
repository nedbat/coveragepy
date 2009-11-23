"""OS information for testing."""

import sys

if sys.hexversion >= 0x02050000 and sys.platform == 'win32':
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

else:
    def process_ram():
        """How much RAM is this process using? (no implementation)"""
        return 0
