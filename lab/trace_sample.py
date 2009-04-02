import os, sys

global nest
nest = 0

def trace(frame, event, arg):
    #if event == 'line':
    global nest
    
    print "%s%s %s %d (%r)" % (
        "   " * nest,
        event,
        os.path.basename(frame.f_code.co_filename),
        frame.f_lineno,
        arg
        )
    
    if event == 'call':
        nest += 1
    if event == 'return':
        nest -= 1
        
    return trace

sys.settrace(trace)

import sample
#import littleclass
