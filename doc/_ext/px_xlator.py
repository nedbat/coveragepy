from docutils import nodes
from sphinx.writers.html import SmartyPantsHTMLTranslator
from sphinx.builders.html import StandaloneHTMLBuilder

def setup(app):
    app.add_builder(PxBuilder)


class PxTranslator(SmartyPantsHTMLTranslator):
    """Adjust the HTML translator into a .px translator.
    
    """

    def __init__(self, *args, **kwargs):
        SmartyPantsHTMLTranslator.__init__(self, *args, **kwargs)
        #self.document.reporter.debug_flag = 1
        
    def visit_section(self, node):
        self.section_level += 1

    def depart_section(self, node):
        self.section_level -= 1


    # TODO: get history from here?
    def visit_field_list(self, node):
        #self.document.reporter.debug_flag = 1;      # This should go somewhere else.
        raise nodes.SkipNode

    def depart_field_list(self, node):      pass
    def visit_field(self, node):            pass
    def depart_field(self, node):           pass
    def visit_field_name(self, node):       pass
    def depart_field_name(self, node):      pass
    def visit_field_body(self, node):       pass
    def depart_field_body(self, node):      pass

    def xx_visit_Text(self, node):
        self.body.append("XX")
        SmartyPantsHTMLTranslator.visit_Text(self, node)

    def visit_literal_block(self, node):
        if node.rawsource != node.astext():
            # most probably a parsed-literal block -- don't highlight
            return BaseTranslator.visit_literal_block(self, node)
        lang = self.highlightlang
        if node.has_key('language'):
            # code-block directives
            lang = node['language']
        self.body.append('<code lang="%s">' % lang)
        self.body.append(self.encode(node.rawsource))
        self.body.append('</code>\n')
        raise nodes.SkipNode
        
class PxBuilder(StandaloneHTMLBuilder):
    name = 'px'

    def init(self):
        self.config.html_theme = 'px'
        self.config.html_translator_class = "px_xlator.PxTranslator"

        super(PxBuilder, self).init()
        
        self.out_suffix = '.px'
        self.link_suffix = '.html'
