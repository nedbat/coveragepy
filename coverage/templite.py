"""A simple Python template renderer, for a nano-subset of Django syntax."""

# Coincidentally named the same as http://code.activestate.com/recipes/496702/

import re


class CodeBuilder(object):
    """Build source code conveniently."""

    def __init__(self):
        self.code = []
        self.indent_amount = 0

    def add_line(self, line):
        """Add a line of source to the code.

        Don't include indentations or newlines.

        """
        self.code.append(" " * self.indent_amount)
        self.code.append(line)
        self.code.append("\n")

    def indent(self):
        """Increase the current indent for following lines."""
        self.indent_amount += 4

    def dedent(self):
        """Decrease the current indent for following lines."""
        self.indent_amount -= 4

    def get_function(self, fn_name):
        """Compile the code, and return the function `fn_name`."""
        assert self.indent_amount == 0
        g = {}
        code_text = "".join(self.code)
        exec(code_text, g)
        return g[fn_name]


class Templite(object):
    """A simple template renderer, for a nano-subset of Django syntax.

    Supported constructs are extended variable access::

        {{var.modifer.modifier|filter|filter}}

    loops::

        {% for var in list %}...{% endfor %}

    and ifs::

        {% if var %}...{% endif %}

    Comments are within curly-hash markers::

        {# This will be ignored #}

    Construct a Templite with the template text, then use `render` against a
    dictionary context to create a finished string.

    """
    def __init__(self, text, *contexts):
        """Construct a Templite with the given `text`.

        `contexts` are dictionaries of values to use for future renderings.
        These are good for filters and global values.

        """
        self.text = text
        self.context = {}
        for context in contexts:
            self.context.update(context)

        # We construct a function in source form, then compile it and hold onto
        # it, and execute it to create the template output.
        code = CodeBuilder()

        code.add_line("def render(ctx, dot):")
        code.indent()
        code.add_line("result = []")
        code.add_line("r = result.append")

        # Split the text to form a list of tokens.
        toks = re.split(r"(?s)({{.*?}}|{%.*?%}|{#.*?#})", text)

        ops_stack = []
        for tok in toks:
            if tok.startswith('{{'):
                # An expression to evaluate.
                code.add_line("r(str(%s))" % self.expr_code(tok[2:-2].strip()))
            elif tok.startswith('{#'):
                # Comment: ignore it and move on.
                continue
            elif tok.startswith('{%'):
                # Action tag: split into words and parse further.
                words = tok[2:-2].strip().split()
                if words[0] == 'if':
                    # An if statement: evaluate the expression to determine if.
                    assert len(words) == 2
                    ops_stack.append('if')
                    code.add_line("if %s:" % self.expr_code(words[1]))
                    code.indent()
                elif words[0] == 'for':
                    # A loop: iterate over expression result.
                    assert len(words) == 4 and words[2] == 'in'
                    ops_stack.append('for')
                    code.add_line(
                        "for ctx[%r] in %s:" % (
                            words[1],
                            self.expr_code(words[3])
                        )
                    )
                    code.indent()
                elif words[0].startswith('end'):
                    # Endsomething.  Pop the ops stack
                    end_what = words[0][3:]
                    if ops_stack[-1] != end_what:
                        raise SyntaxError("Mismatched end tag: %r" % end_what)
                    ops_stack.pop()
                    code.dedent()
                else:
                    raise SyntaxError("Don't understand tag: %r" % words[0])
            else:
                # Literal content.  If it isn't empty, output it.
                if tok:
                    code.add_line("r(%r)" % tok)

        if ops_stack:
            raise SyntaxError("Unmatched action tag: %r" % ops_stack[-1])

        code.add_line("return ''.join(result)")
        code.dedent()
        self.render_function = code.get_function('render')

    def expr_code(self, expr):
        """Generate a Python expression for `expr`."""
        if "|" in expr:
            pipes = expr.split("|")
            code = self.expr_code(pipes[0])
            for func in pipes[1:]:
                code = "ctx[%r](%s)" % (func, code)
        elif "." in expr:
            dots = expr.split(".")
            code = self.expr_code(dots[0])
            args = [repr(d) for d in dots[1:]]
            code = "dot(%s, %s)" % (code, ", ".join(args))
        else:
            code = "ctx[%r]" % expr
        return code

    def render(self, context=None):
        """Render this template by applying it to `context`.

        `context` is a dictionary of values to use in this rendering.

        """
        # Make the complete context we'll use.
        ctx = dict(self.context)
        if context:
            ctx.update(context)

        return self.render_function(ctx, self.do_dots)

    def do_dots(self, value, *dots):
        """Evaluate dotted expressions at runtime."""
        for dot in dots:
            try:
                value = getattr(value, dot)
            except AttributeError:
                value = value[dot]
            if hasattr(value, '__call__'):
                value = value()
        return value
