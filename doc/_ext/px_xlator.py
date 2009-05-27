from docutils import nodes
from sphinx.writers.html import SmartyPantsHTMLTranslator
from sphinx.builders.html import StandaloneHTMLBuilder

def setup(app):
    app.add_builder(PxBuilder)


BaseHtmlXlator = SmartyPantsHTMLTranslator
class PxTranslator(BaseHtmlXlator):
    """Adjust the HTML translator into a .px translator.
    
    """

    def __init__(self, *args, **kwargs):
        BaseHtmlXlator.__init__(self, *args, **kwargs)
        #self.document.reporter.debug_flag = 1
        # To make the doc title be h0 (skipped), and the next h1.
        self.initial_header_level = 0

    def visit_section(self, node):
        self.section_level += 1

    def depart_section(self, node):
        self.section_level -= 1

    def visit_title(self, node):
        if self.section_level == 1:
            raise nodes.SkipNode
        else:
            BaseHtmlXlator.visit_title(self, node)

    # TODO: get history from here?
    def visit_field_list(self, node):
        raise nodes.SkipNode

    def depart_field_list(self, node):      pass
    def visit_field(self, node):            pass
    def depart_field(self, node):           pass
    def visit_field_name(self, node):       pass
    def depart_field_name(self, node):      pass
    def visit_field_body(self, node):       pass
    def depart_field_body(self, node):      pass

    def visit_literal_block(self, node):
        if node.rawsource != node.astext():
            # most probably a parsed-literal block -- don't highlight
            return BaseHtmlXlator.visit_literal_block(self, node)
        lang = self.highlightlang
        if node.has_key('language'):
            # code-block directives
            lang = node['language']
        self.body.append('<code lang="%s">' % lang)
        self.body.append(self.encode(node.rawsource))
        self.body.append('</code>\n')
        raise nodes.SkipNode

    def visit_desc_parameterlist(self, node):
        self.body.append('(')
        self.first_param = 1
    def depart_desc_parameterlist(self, node):
        self.body.append(')')


class PxBuilder(StandaloneHTMLBuilder):
    name = 'px'

    def init(self):
        self.config.html_theme = 'px'
        self.config.html_translator_class = "px_xlator.PxTranslator"

        super(PxBuilder, self).init()
        
        self.out_suffix = '.px'
        self.link_suffix = '.html'
        
        self.px_uri = "/code/coverage/"

    def get_target_uri(self, docname, typ=None):
        return self.px_uri + docname + self.link_suffix
