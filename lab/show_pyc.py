# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt

import binascii
import dis
import marshal
import struct
import sys
import time
import types


def show_pyc_file(fname):
    f = open(fname, "rb")
    magic = f.read(4)
    print("magic %s" % (binascii.hexlify(magic)))
    read_date_and_size = True
    if sys.version_info >= (3, 7):
        # 3.7 added a flags word
        flags = struct.unpack('<L', f.read(4))[0]
        hash_based = flags & 0x01
        check_source = flags & 0x02
        print("flags 0x%08x" % (flags,))
        if hash_based:
            source_hash = f.read(8)
            read_date_and_size = False
    if read_date_and_size:
        moddate = f.read(4)
        modtime = time.asctime(time.localtime(struct.unpack('<L', moddate)[0]))
        print("moddate %s (%s)" % (binascii.hexlify(moddate), modtime))
        if sys.version_info >= (3, 3):
            # 3.3 added another long to the header (size).
            size = f.read(4)
            print("pysize %s (%d)" % (binascii.hexlify(size), struct.unpack('<L', size)[0]))
    code = marshal.load(f)
    show_code(code)

def show_py_file(fname):
    text = open(fname).read().replace('\r\n', '\n')
    show_py_text(text, fname=fname)

def show_py_text(text, fname="<string>"):
    code = compile(text, fname, "exec")
    show_code(code)

CO_FLAGS = [
    ('CO_OPTIMIZED',                0x00001),
    ('CO_NEWLOCALS',                0x00002),
    ('CO_VARARGS',                  0x00004),
    ('CO_VARKEYWORDS',              0x00008),
    ('CO_NESTED',                   0x00010),
    ('CO_GENERATOR',                0x00020),
    ('CO_NOFREE',                   0x00040),
    ('CO_COROUTINE',                0x00080),
    ('CO_ITERABLE_COROUTINE',       0x00100),
    ('CO_ASYNC_GENERATOR',          0x00200),
    ('CO_GENERATOR_ALLOWED',        0x01000),
    ('CO_FUTURE_DIVISION',          0x02000),
    ('CO_FUTURE_ABSOLUTE_IMPORT',   0x04000),
    ('CO_FUTURE_WITH_STATEMENT',    0x08000),
    ('CO_FUTURE_PRINT_FUNCTION',    0x10000),
    ('CO_FUTURE_UNICODE_LITERALS',  0x20000),
    ('CO_FUTURE_BARRY_AS_BDFL',     0x40000),
    ('CO_FUTURE_GENERATOR_STOP',    0x80000),
]

def show_code(code, indent='', number=None):
    label = ""
    if number is not None:
        label = "%d: " % number
    print("%s%scode" % (indent, label))
    indent += '   '
    print("%sname %r" % (indent, code.co_name))
    print("%sargcount %d" % (indent, code.co_argcount))
    print("%snlocals %d" % (indent, code.co_nlocals))
    print("%sstacksize %d" % (indent, code.co_stacksize))
    print("%sflags %04x: %s" % (indent, code.co_flags, flag_words(code.co_flags, CO_FLAGS)))
    show_hex("code", code.co_code, indent=indent)
    dis.disassemble(code)
    print("%sconsts" % indent)
    for i, const in enumerate(code.co_consts):
        if type(const) == types.CodeType:
            show_code(const, indent+'   ', number=i)
        else:
            print("   %s%d: %r" % (indent, i, const))
    print("%snames %r" % (indent, code.co_names))
    print("%svarnames %r" % (indent, code.co_varnames))
    print("%sfreevars %r" % (indent, code.co_freevars))
    print("%scellvars %r" % (indent, code.co_cellvars))
    print("%sfilename %r" % (indent, code.co_filename))
    print("%sfirstlineno %d" % (indent, code.co_firstlineno))
    show_hex("lnotab", code.co_lnotab, indent=indent)

def show_hex(label, h, indent):
    h = binascii.hexlify(h)
    if len(h) < 60:
        print("%s%s %s" % (indent, label, h.decode('ascii')))
    else:
        print("%s%s" % (indent, label))
        for i in range(0, len(h), 60):
            print("%s   %s" % (indent, h[i:i+60].decode('ascii')))

def flag_words(flags, flag_defs):
    words = []
    for word, flag in flag_defs:
        if flag & flags:
            words.append(word)
    return ", ".join(words)

def show_file(fname):
    if fname.endswith('pyc'):
        show_pyc_file(fname)
    elif fname.endswith('py'):
        show_py_file(fname)
    else:
        print("Odd file:", fname)

def main(args):
    if args[0] == '-c':
        show_py_text(" ".join(args[1:]).replace(";", "\n"))
    else:
        for a in args:
            show_file(a)

if __name__ == '__main__':
    main(sys.argv[1:])
