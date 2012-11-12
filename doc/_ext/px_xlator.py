from docutils import nodes
from sphinx.writers.html import SmartyPantsHTMLTranslator
from sphinx.builders.html import StandaloneHTMLBuilder
import os

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
            # The id for the h2 tag is on the parent, move it 
            # down here so we'll get the right HTML.
            if not node['ids'] and len(node.parent['ids']) > 1:
                node['ids'] = [node.parent['ids'][1]]
            BaseHtmlXlator.visit_title(self, node)

    def visit_field_list(self, node):
        self.history = []

    def depart_field_list(self, node):
        if self.history:
            self.body.append("<history>\n")
            for hist in self.history:
                when, what = hist.split(',', 1)
                self.body.append("<what when='%s'>%s</what>\n" % (when, self.encode(what.strip())))
            self.body.append("</history>\n")
            
        if "beta" in self.builder.config.release:
            self.body.append("""
                <box>
                These docs are for a beta release, %s. 
                For the latest released version, see <a href='/code/coverage'>coverage.py</a>.
                </box>
                """ % self.builder.config.release)

    def visit_field(self, node):
        if node.children[0].astext() == 'history':
            self.history.append(node.children[1].astext())
        raise nodes.SkipChildren

    def depart_field(self, node):
        pass

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
        self.param_separator = node.child_text_separator
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
        
        if "beta" in self.config.release:
            self.px_uri = "/code/coverage/beta/"
        else:
            self.px_uri = "/code/coverage/"

    def get_target_uri(self, docname, typ=None):
        return self.px_uri + docname + self.link_suffix
