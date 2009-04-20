"""Tests for coverage.template."""

from coverage.templite import Templite
import unittest

class AnyOldObject:
    pass

class TemplateTest(unittest.TestCase):
    
    def test_passthrough(self):
        # Strings without variables are passed through unchanged.
        self.assertEqual(Templite("Hello").render(), "Hello")
        self.assertEqual(
            Templite("Hello, 20% fun time!").render(),
            "Hello, 20% fun time!"
            )

    def test_variables(self):
        # Variables use {{var}} syntax.
        self.assertEqual(
            Templite("Hello, {{name}}!").render({'name':'Ned'}),
            "Hello, Ned!"
            )

    def test_pipes(self):
        # Variables can be filtered with pipes.
        data = {
            'name': 'Ned',
            'upper': lambda x: x.upper(),
            'second': lambda x: x[1],
            }
        self.assertEqual(
            Templite("Hello, {{name|upper}}!").render(data),
            "Hello, NED!"
            )
        # Pipes can be concatenated.
        self.assertEqual(
            Templite("Hello, {{name|upper|second}}!").render(data),
            "Hello, E!"
            )

    def test_reusability(self):
        # A single Templite can be used more than once with different data.
        globs = {
            'upper': lambda x: x.upper(),
            'punct': '!',
            }
        
        template = Templite("This is {{name|upper}}{{punct}}", globs)
        self.assertEqual(template.render({'name':'Ned'}), "This is NED!")
        self.assertEqual(template.render({'name':'Ben'}), "This is BEN!")

    def test_attribute(self):
        # Variables' attributes can be accessed with dots.
        obj = AnyOldObject()
        obj.a = "Ay"
        self.assertEqual(
            Templite("{{obj.a}}").render(locals()), "Ay"
            )

        obj2 = AnyOldObject()
        obj2.obj = obj
        obj2.b = "Bee"
        self.assertEqual(
            Templite("{{obj2.obj.a}} {{obj2.b}}").render(locals()), "Ay Bee"
            )
        
    def test_member_function(self):
        # Variables' member functions can be used, as long as they are nullary.
        class WithMemberFns:
            def ditto(self):
                return self.txt + self.txt
        obj = WithMemberFns()
        obj.txt = "Once"
        self.assertEqual(
            Templite("{{obj.ditto}}").render(locals()), "OnceOnce"
            )

    def test_loops(self):
        # Loops work like in Django.
        nums = [1,2,3,4]
        self.assertEqual(
            Templite("Look: {% for n in nums %}{{n}}, {% endfor %}done.").
                render(locals()), "Look: 1, 2, 3, 4, done."
            )
        # Loop iterables can be filtered.
        def rev(l):
            l = l[:]
            l.reverse()
            return l
        
        self.assertEqual(
            Templite("Look: {% for n in nums|rev %}{{n}}, {% endfor %}done.").
                render(locals()), "Look: 4, 3, 2, 1, done."
            )


if __name__ == '__main__':
    unittest.main()
