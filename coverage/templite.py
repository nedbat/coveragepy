"""A simple Python template renderer, for a nano-subset of Django syntax."""

# Started from http://blog.ianbicking.org/templating-via-dict-wrappers.html
# and http://jtauber.com/2006/05/templates.html
# and http://code.activestate.com/recipes/496730/
# Coincidentally named the same as http://code.activestate.com/recipes/496702/

import re

class Templite(object):
    """A simple template renderer, for a nano-subset of Django syntax.

    Supported constructs are extended variable access::
    
        {{var.modifer.modifier|filter|filter}}
        
    and loops::
    
        {% for var in list %}...{% endfor %}
    
    Construct a Templite with the template text, then use `render` against a
    dictionary context to create a finished string.
    
    """
    def __init__(self, text, *contexts):
        """Construct a Templite with the given `text`.
        
        `contexts` are dictionaries of values to use for future renderings.
        These are good for filters and global values.
        
        """
        self.loops = []
        self.text = self._prepare(text)
        self.context = {}
        for context in contexts:
            self.context.update(context)

    def render(self, context=None):
        """Render this template by applying it to `context`.
        
        `context` is a dictionary of values to use in this rendering.
        
        """
        # Make the complete context we'll use.
        ctx = dict(self.context)
        if context:
            ctx.update(context)
            
        ctxaccess = _ContextAccess(ctx)
        
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
            r"(?s){% for ([a-z0-9_]+) in ([a-z0-9_.|]+) %}(.*?){% endfor %}",
            self._loop_prepare, text
            )
        # Protect actual percent signs in the text.
        text = text.replace("%", "%%")
        # Convert {{foo}} into %(foo)s
        text = re.sub(r"{{(.+?)}}", r"%(\1)s", text)
        return text

    def _loop_prepare(self, match):
        """Prepare a loop body for `_prepare`."""
        nloop = len(self.loops)
        # Append (loopvar, listvar, loopbody) to self.loops
        loopvar, listvar, loopbody = match.groups()
        loopbody = self._prepare(loopbody)
        self.loops.append((loopvar, listvar, loopbody))
        return "{{loop:%d}}" % nloop


class _ContextAccess(object):
    """A mediator for a context.
    
    Implements __getitem__ on a context for Templite, so that string formatting
    references can pull data from the context.
    
    """
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
                try:
                    value = getattr(value, dot)
                except AttributeError:
                    value = value[dot]
                if callable(value):
                    value = value()
        else:
            value = self.context[key]
        return value
