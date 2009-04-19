"""A simple Python template renderer, for a nano-subset of Django syntax."""

# Started from http://blog.ianbicking.org/templating-via-dict-wrappers.html
# and http://jtauber.com/2006/05/templates.html
# and http://code.activestate.com/recipes/496730/

import re

class Templite(object):
    """A simple template renderer, for a nano-subset of Django syntax.
    
    """
    def __init__(self, text, *contexts):
        self.loops = []
        self.text = self._prepare(text)
        self.context = {}
        for context in contexts:
            self.context.update(context)

    def render(self, context=None):
        # Make the complete context we'll use.
        ctx = dict(self.context)
        if context:
            ctx.update(context)
            
        ctxaccess = ContextAccess(ctx)
        
        # Render the loops.
        for iloop, (loopvar, listvar, loopbody) in enumerate(self.loops):
            result = ""
            for listval in ctxaccess[listvar]:
                ctx[loopvar] = listval
                result += loopbody % ctxaccess
            ctx["loop:%d" % iloop] = result
            
        # Render the final template.
        return self.text % ctxaccess

    def _prepare(self, text):
        """Convert Django-style data references into Python-native ones."""
        # Pull out loops.
        text = re.sub(
            r"{% for ([a-z0-9_]+) in ([a-z0-9_.|]+) %}(.*){% endfor %}",
            self._loop_repl, text
            )
        # Protect actual percent signs in the text.
        text = text.replace("%", "%%")
        # Convert {{foo}} into %(foo)s
        text = re.sub(r"{{([^}]+)}}", r"%(\1)s", text)
        return text

    def _loop_repl(self, match):
        nloop = len(self.loops)
        # Append (loopvar, listvar, loopbody) to self.loops
        loopvar, listvar, loopbody = match.groups()
        loopbody = self._prepare(loopbody)
        self.loops.append((loopvar, listvar, loopbody))
        return "{{loop:%d}}" % nloop


class ContextAccess(object):
    
    def __init__(self, context):
        self.context = context

    def __getitem__(self, key):
        if "|" in key:
            pipes = key.split("|")
            value = self[pipes[0]]
            for func in pipes[1:]:
                value = self[func](value)
        elif "." in key:
            dots = key.split('.') 
            value = self[dots[0]]
            for dot in dots[1:]:
                value = getattr(value, dot)
                if callable(value):
                    value = value()
        else:
            value = self.context[key]
        return value
