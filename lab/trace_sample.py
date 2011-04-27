import os, sys

global nest
nest = 0

def trace(frame, event, arg):
    #if event == 'line':
    global nest
    
    print "%s%s %s %d" % (
        "   " * nest,
        event,
        os.path.basename(frame.f_code.co_filename),
        frame.f_lineno,
        )
    
    if event == 'call':
        nest += 1
    if event == 'return':
        nest -= 1
        
    return trace

def trace2(frame, event, arg):
    #if event == 'line':
    global nest
    
    print "2: %s%s %s %d" % (
        "   " * nest,
        event,
        os.path.basename(frame.f_code.co_filename),
        frame.f_lineno,
        )
    
    if event == 'call':
        nest += 1
    if event == 'return':
        nest -= 1
        
    return trace2

sys.settrace(trace)

def bar():
    print "nar"

a = 26
def foo(n):
    a = 28
    sys.settrace(sys.gettrace())
    bar()
    a = 30  
    return 2*n

print foo(a)
#import sample
#import littleclass
